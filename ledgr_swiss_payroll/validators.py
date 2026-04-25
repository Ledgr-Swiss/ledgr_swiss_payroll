"""Validators sur Salary Slip — workflow validation entreprise + anomalies soft."""
import json
from datetime import datetime

import frappe
from frappe import _


def validate_owner_approval(doc, method=None):
    """before_submit : refuse submit si dirigeant n'a pas validé.

    Override admissible pour LEDGR Fiduciary Manager (avec msgprint warning traçable).
    """
    if doc.get("ledgr_owner_validated_by"):
        return

    user_roles = frappe.get_roles(frappe.session.user)
    if "LEDGR Fiduciary Manager" in user_roles:
        frappe.msgprint(
            _(
                "Salary Slip soumise sans validation du dirigeant "
                "(override LEDGR Fiduciary Manager)"
            ),
            indicator="orange",
            title=_("Override workflow"),
        )
        return

    frappe.throw(
        _(
            "Le dirigeant doit valider ce Salary Slip avant soumission "
            "(champ ledgr_owner_validated_by manquant)."
        ),
        title=_("Validation employeur requise"),
    )


def refresh_anomalies(doc, method=None):
    """validate hook : détecte 6 anomalies soft, sérialise dans ledgr_anomalies."""
    anomalies = []

    employee = frappe.get_doc("Employee", doc.employee) if doc.get("employee") else None

    if employee:
        if not employee.get("ledgr_canton_residence"):
            anomalies.append(_anomaly(
                "MISSING_CANTON_RESIDENCE",
                "warning",
                f"Employee {employee.name} sans canton de résidence",
            ))
        if not employee.get("ledgr_tax_code"):
            anomalies.append(_anomaly(
                "MISSING_TAX_CODE",
                "warning",
                f"Employee {employee.name} sans code tarif IS",
            ))
        if not employee.get("ledgr_iban"):
            anomalies.append(_anomaly(
                "MISSING_IBAN",
                "warning",
                f"Employee {employee.name} sans IBAN (bloquant pour pain.001)",
            ))
        if not employee.get("ledgr_lpp_institution"):
            anomalies.append(_anomaly(
                "LPP_NOT_CONFIGURED",
                "info",
                f"Employee {employee.name} sans caisse LPP configurée",
            ))

        thirteenth_mode = employee.get("ledgr_thirteenth_month_mode") or "None"
        if thirteenth_mode != "None":
            has_base = any(
                e.salary_component == "Salaire de base"
                for e in (doc.get("earnings") or [])
            )
            if not has_base:
                anomalies.append(_anomaly(
                    "THIRTEENTH_MISSING_BASE",
                    "warning",
                    "Mode 13ème activé mais component 'Salaire de base' absent du slip courant",
                ))

    if (employee
            and employee.get("ledgr_canton_residence")
            and employee.get("ledgr_tax_code")
            and doc.get("gross_pay")):
        canton = frappe.db.get_value(
            "LEDGR Payroll Canton Config", employee.ledgr_canton_residence, "canton_code"
        )
        slab = frappe.db.exists(
            "LEDGR Cantonal IS Tax Slab",
            {
                "canton": canton,
                "code_tarif": employee.ledgr_tax_code,
                "active_from": ["<=", doc.start_date],
            },
        )
        if not slab:
            anomalies.append(_anomaly(
                "IS_BRACKET_NOT_FOUND",
                "critical",
                f"Aucun barème IS pour canton={canton}, code={employee.ledgr_tax_code}, "
                f"date={doc.start_date}",
            ))

    doc.ledgr_anomalies = json.dumps(anomalies) if anomalies else ""


def _anomaly(code, severity, message):
    return {
        "code": code,
        "severity": severity,
        "message": message,
        "detected_at": datetime.utcnow().isoformat(),
    }
