"""Tests pain.001 generator — XSD validation + error cases."""
import os
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch

import frappe
import lxml.etree as ET

from ledgr_swiss_payroll.exceptions import InvalidPain001
from ledgr_swiss_payroll.pain001 import NS, generate_pain001, _validate_xsd


APP_PATH = frappe.get_app_path("ledgr_swiss_payroll")
GOLDEN_DIR = Path(APP_PATH) / "tests" / "golden"


def _mock_payroll_entry(name="PE-001", company="_Test Co", posting_date=None):
    pe = MagicMock()
    pe.name = name
    pe.company = company
    pe.posting_date = posting_date or date(2026, 6, 30)
    return pe


def _mock_slip(name, employee, net_pay, start_date=None):
    s = MagicMock()
    s.name = name
    s.employee = employee
    s.net_pay = net_pay
    s.start_date = start_date or date(2026, 6, 1)
    return s


def _mock_employee(name, employee_name, iban):
    e = MagicMock()
    e.name = name
    e.employee_name = employee_name
    e.ledgr_iban = iban
    e.get = lambda k: getattr(e, k, None)
    return e


class TestPain001Generator(unittest.TestCase):

    def test_no_settings_payroll_iban_raises(self):
        with patch("ledgr_swiss_payroll.pain001.frappe") as mock_frappe:
            mock_frappe.get_doc.return_value = _mock_payroll_entry()
            mock_frappe.db.get_value.return_value = None
            with self.assertRaises(InvalidPain001):
                generate_pain001("PE-NO-IBAN")

    def test_empty_payroll_entry_raises(self):
        with patch("ledgr_swiss_payroll.pain001.frappe") as mock_frappe:
            mock_frappe.get_doc.return_value = _mock_payroll_entry()
            mock_frappe.db.get_value.return_value = "CH9300762011623852957"
            mock_frappe.get_all.return_value = []
            with self.assertRaises(InvalidPain001):
                generate_pain001("PE-EMPTY")

    def test_missing_creditor_iban_raises(self):
        with patch("ledgr_swiss_payroll.pain001.frappe") as mock_frappe:
            pe = _mock_payroll_entry()
            slip = _mock_slip("SLIP-1", "EMP-001", 5000)
            emp = _mock_employee("EMP-001", "No IBAN", None)

            mock_frappe.get_doc.side_effect = lambda dt, n=None: {
                "Payroll Entry": pe,
                "Salary Slip": slip,
                "Employee": emp,
            }.get(dt, MagicMock())
            mock_frappe.db.get_value.return_value = "CH9300762011623852957"
            mock_frappe.get_all.return_value = ["SLIP-1"]
            mock_frappe.get_app_path.side_effect = lambda app, *parts: os.path.join(APP_PATH, *parts)

            with self.assertRaises(InvalidPain001):
                generate_pain001("PE-001")

    def test_negative_net_pay_raises(self):
        with patch("ledgr_swiss_payroll.pain001.frappe") as mock_frappe:
            pe = _mock_payroll_entry(name="PE-NEG")
            slip = _mock_slip("SLIP-NEG", "EMP-002", -100)
            emp = _mock_employee("EMP-002", "Negative Pay", "CH9300762011623852957")

            def _get_doc(dt, n=None):
                if dt == "Payroll Entry":
                    return pe
                if dt == "Salary Slip":
                    return slip
                return emp

            mock_frappe.get_doc.side_effect = _get_doc
            mock_frappe.db.get_value.return_value = "CH9300762011623852957"
            mock_frappe.get_all.return_value = ["SLIP-NEG"]
            mock_frappe.get_app_path.side_effect = lambda app, *parts: os.path.join(APP_PATH, *parts)

            with self.assertRaises(InvalidPain001):
                generate_pain001("PE-NEG")

    def test_valid_xml_xsd_validates(self):
        with patch("ledgr_swiss_payroll.pain001.frappe") as mock_frappe:
            pe = _mock_payroll_entry(name="PE-OK")
            slips_data = [
                ("SLIP-A", "EMP-A", 4500.50, "Alice Müller", "CH9300762011623852957"),
                ("SLIP-B", "EMP-B", 3800.25, "Bob Dupont", "CH4308307000289537320"),
            ]
            slip_objs = [_mock_slip(n, e, p) for n, e, p, _, _ in slips_data]
            emp_objs = {
                e: _mock_employee(e, nm, ib)
                for _, e, _, nm, ib in slips_data
            }

            call_count = {"slip_idx": 0}

            def _get_doc(dt, n=None):
                if dt == "Payroll Entry":
                    return pe
                if dt == "Salary Slip":
                    obj = slip_objs[call_count["slip_idx"]]
                    call_count["slip_idx"] += 1
                    return obj
                if dt == "Employee":
                    return emp_objs[n]
                return MagicMock()

            mock_frappe.get_doc.side_effect = _get_doc
            mock_frappe.db.get_value.return_value = "CH9300762011623852957"
            mock_frappe.get_all.return_value = [s[0] for s in slips_data]
            mock_frappe.get_app_path.side_effect = lambda app, *parts: os.path.join(APP_PATH, *parts)

            xml_bytes = generate_pain001("PE-OK")

            self.assertIsInstance(xml_bytes, bytes)
            self.assertIn(b"CstmrCdtTrfInitn", xml_bytes)
            self.assertIn(b"Alice", xml_bytes)
            self.assertIn(b"Bob", xml_bytes)
            self.assertIn(b"4500.50", xml_bytes)
            self.assertIn(b"3800.25", xml_bytes)

            doc = ET.fromstring(xml_bytes)
            ns = {"p": NS}
            txs = doc.findall(".//p:CdtTrfTxInf", ns)
            self.assertEqual(len(txs), 2)

    def test_xsd_validates_golden_file(self):
        golden = GOLDEN_DIR / "pain001-2-employees.xml"
        if not golden.exists():
            self.skipTest("Golden file not yet generated")
        xml_bytes = golden.read_bytes()
        _validate_xsd(xml_bytes)


class TestIBANValidators(unittest.TestCase):

    def test_valid_ch_iban_normalized(self):
        from ledgr_swiss_payroll.validators import validate_employee_iban
        doc = MagicMock()
        doc.get = lambda k: getattr(doc, k, None)
        doc.ledgr_iban = "CH93 0076 2011 6238 5295 7"
        validate_employee_iban(doc)
        self.assertEqual(doc.ledgr_iban, "CH9300762011623852957")

    def test_invalid_iban_raises(self):
        from ledgr_swiss_payroll.validators import validate_employee_iban
        doc = MagicMock()
        doc.get = lambda k: getattr(doc, k, None)
        doc.ledgr_iban = "DE89370400440532013000"
        with self.assertRaises(Exception):
            validate_employee_iban(doc)

    def test_empty_iban_ok(self):
        from ledgr_swiss_payroll.validators import validate_employee_iban
        doc = MagicMock()
        doc.get = lambda k: None
        validate_employee_iban(doc)

    def test_mandate_iban_validated(self):
        from ledgr_swiss_payroll.validators import validate_mandate_payroll_iban
        doc = MagicMock()
        doc.get = lambda k: getattr(doc, k, None)
        doc.payroll_iban = "CH93 0076 2011 6238 5295 7"
        validate_mandate_payroll_iban(doc)
        self.assertEqual(doc.payroll_iban, "CH9300762011623852957")
