"""pain.001.001.03 generator — ISO 20022 Swiss CH profile pour versements salaires."""
from datetime import datetime
from decimal import Decimal
from uuid import uuid4

import frappe
import lxml.etree as ET

from ledgr_swiss_payroll.exceptions import InvalidPain001


NS = "http://www.six-interbank-clearing.com/de/pain.001.001.03.ch.02.xsd"
NSMAP = {None: NS}


def generate_pain001(payroll_entry_name):
    """Generate pain.001.001.03 CH XML bytes for a Payroll Entry.

    Returns bytes (UTF-8 XML).

    Raises InvalidPain001 if:
      - debtor IBAN missing
      - any creditor IBAN missing
      - any net_pay <= 0
      - XSD validation fails
    """
    pe = frappe.get_doc("Payroll Entry", payroll_entry_name)

    debtor_iban = frappe.db.get_value(
        "LEDGR Mandate Settings",
        {"company": pe.company},
        "payroll_iban",
    )
    if not debtor_iban:
        raise InvalidPain001(
            f"Pas de LEDGR Mandate Settings.payroll_iban pour Company {pe.company}"
        )

    slip_names = frappe.get_all(
        "Salary Slip",
        filters={"payroll_entry": pe.name, "docstatus": 1},
        pluck="name",
    )
    if not slip_names:
        raise InvalidPain001(f"Aucune Salary Slip submitted pour Payroll Entry {pe.name}")

    slips = [frappe.get_doc("Salary Slip", n) for n in slip_names]

    msg_id = f"LEDGR-{pe.name}-{uuid4().hex[:8]}"
    cre_dt_tm = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
    nb_of_txs = str(len(slips))
    ctrl_sum = sum(Decimal(str(s.net_pay or 0)) for s in slips)

    if ctrl_sum <= 0:
        raise InvalidPain001(f"Total versements <= 0 ({ctrl_sum})")

    root = ET.Element(f"{{{NS}}}Document", nsmap=NSMAP)
    cstmr = ET.SubElement(root, f"{{{NS}}}CstmrCdtTrfInitn")

    grp = ET.SubElement(cstmr, f"{{{NS}}}GrpHdr")
    ET.SubElement(grp, f"{{{NS}}}MsgId").text = msg_id
    ET.SubElement(grp, f"{{{NS}}}CreDtTm").text = cre_dt_tm
    ET.SubElement(grp, f"{{{NS}}}NbOfTxs").text = nb_of_txs
    ET.SubElement(grp, f"{{{NS}}}CtrlSum").text = str(ctrl_sum.quantize(Decimal("0.01")))
    initg_pty = ET.SubElement(grp, f"{{{NS}}}InitgPty")
    ET.SubElement(initg_pty, f"{{{NS}}}Nm").text = pe.company[:70]

    pmt_inf = ET.SubElement(cstmr, f"{{{NS}}}PmtInf")
    ET.SubElement(pmt_inf, f"{{{NS}}}PmtInfId").text = pe.name[:35]
    ET.SubElement(pmt_inf, f"{{{NS}}}PmtMtd").text = "TRF"
    ET.SubElement(pmt_inf, f"{{{NS}}}BtchBookg").text = "true"
    ET.SubElement(pmt_inf, f"{{{NS}}}NbOfTxs").text = nb_of_txs
    ET.SubElement(pmt_inf, f"{{{NS}}}CtrlSum").text = str(ctrl_sum.quantize(Decimal("0.01")))

    pmt_dt = pe.posting_date if hasattr(pe, "posting_date") and pe.posting_date else None
    exec_dt = pmt_dt.strftime("%Y-%m-%d") if pmt_dt else cre_dt_tm[:10]
    ET.SubElement(pmt_inf, f"{{{NS}}}ReqdExctnDt").text = exec_dt

    dbtr = ET.SubElement(pmt_inf, f"{{{NS}}}Dbtr")
    ET.SubElement(dbtr, f"{{{NS}}}Nm").text = pe.company[:70]

    dbtr_acct = ET.SubElement(pmt_inf, f"{{{NS}}}DbtrAcct")
    dbtr_acct_id = ET.SubElement(dbtr_acct, f"{{{NS}}}Id")
    ET.SubElement(dbtr_acct_id, f"{{{NS}}}IBAN").text = debtor_iban

    dbtr_agt = ET.SubElement(pmt_inf, f"{{{NS}}}DbtrAgt")
    ET.SubElement(dbtr_agt, f"{{{NS}}}FinInstnId")

    for slip in slips:
        emp = frappe.get_doc("Employee", slip.employee)
        if not emp.get("ledgr_iban"):
            raise InvalidPain001(f"Employee {emp.name} sans IBAN")
        if (slip.net_pay or 0) <= 0:
            raise InvalidPain001(f"Salary Slip {slip.name} avec net_pay <= 0")

        tx = ET.SubElement(pmt_inf, f"{{{NS}}}CdtTrfTxInf")
        pmt_id = ET.SubElement(tx, f"{{{NS}}}PmtId")
        ET.SubElement(pmt_id, f"{{{NS}}}EndToEndId").text = slip.name[:35]

        amt = ET.SubElement(tx, f"{{{NS}}}Amt")
        instd = ET.SubElement(amt, f"{{{NS}}}InstdAmt")
        instd.set("Ccy", "CHF")
        instd.text = str(Decimal(str(slip.net_pay)).quantize(Decimal("0.01")))

        cdtr = ET.SubElement(tx, f"{{{NS}}}Cdtr")
        ET.SubElement(cdtr, f"{{{NS}}}Nm").text = emp.employee_name[:70]

        cdtr_acct = ET.SubElement(tx, f"{{{NS}}}CdtrAcct")
        cdtr_acct_id = ET.SubElement(cdtr_acct, f"{{{NS}}}Id")
        ET.SubElement(cdtr_acct_id, f"{{{NS}}}IBAN").text = emp.ledgr_iban

        rmt_inf = ET.SubElement(tx, f"{{{NS}}}RmtInf")
        period_label = ""
        if slip.start_date:
            period_label = f"Salaire {slip.start_date.strftime('%m/%Y')}"
        ET.SubElement(rmt_inf, f"{{{NS}}}Ustrd").text = period_label or "Salaire"

    xml_bytes = ET.tostring(
        root, xml_declaration=True, encoding="UTF-8", pretty_print=True
    )
    _validate_xsd(xml_bytes)
    return xml_bytes


def _validate_xsd(xml_bytes):
    schema_path = frappe.get_app_path(
        "ledgr_swiss_payroll", "data", "xsd", "pain.001.001.03.ch.02.xsd"
    )
    schema = ET.XMLSchema(ET.parse(schema_path))
    try:
        doc = ET.fromstring(xml_bytes)
        schema.assertValid(doc)
    except ET.DocumentInvalid as e:
        raise InvalidPain001(f"XSD validation failed: {e}")
