"""Certificat de salaire annuel — agrégation Salary Slips submitted."""
from datetime import date
from decimal import Decimal

import frappe

from ledgr_swiss_payroll.exceptions import NoSlipsForCertificate


def generate_certificate(employee, year, company):
    """Crée un LEDGR Salary Certificate à partir des Salary Slip Submitted de l'année.

    Idempotent : skip si déjà existant pour (employee, year, company) en docstatus 0|1.
    Returns le name du certificat (existant ou nouveau).
    """
    existing = frappe.db.get_value(
        "LEDGR Salary Certificate",
        {"employee": employee, "year": year, "company": company, "docstatus": ["<", 2]},
    )
    if existing:
        return existing

    slip_names = frappe.get_all(
        "Salary Slip",
        filters={
            "employee": employee,
            "company": company,
            "docstatus": 1,
            "start_date": [">=", date(year, 1, 1)],
            "end_date": ["<=", date(year, 12, 31)],
        },
        pluck="name",
    )
    if not slip_names:
        raise NoSlipsForCertificate(employee, year, company)

    slips = [frappe.get_doc("Salary Slip", n) for n in slip_names]

    cert = frappe.new_doc("LEDGR Salary Certificate")
    cert.employee = employee
    cert.year = year
    cert.company = company
    cert.start_date = min(s.start_date for s in slips)
    cert.end_date = max(s.end_date for s in slips)

    cert.gross_salary = float(sum(_to_decimal(s.gross_pay) for s in slips))
    cert.ahv_ai_ac_deduction = float(_sum_component_across_slips(slips, "AVS/AI/AC Employé"))
    cert.lpp_deduction = float(_sum_component_across_slips(slips, "LPP Employé"))
    cert.is_deduction = float(_sum_component_across_slips(slips, "IS Retenue"))
    cert.net_salary = float(
        _to_decimal(cert.gross_salary)
        - _to_decimal(cert.ahv_ai_ac_deduction)
        - _to_decimal(cert.lpp_deduction)
        - _to_decimal(cert.is_deduction)
    )

    cert.insert(ignore_permissions=True)
    return cert.name


def generate_certificates_for_year(year, company):
    """Batch — un certificat par Employee actif de la Company sur l'année."""
    employees = frappe.get_all(
        "Employee",
        filters={"company": company, "status": ["in", ["Active", "Left"]]},
        pluck="name",
    )
    results = []
    for emp in employees:
        try:
            results.append(generate_certificate(emp, year, company))
        except NoSlipsForCertificate:
            continue
    return results


def _sum_component_across_slips(slips, component_name):
    total = Decimal("0")
    for slip in slips:
        for d in (slip.deductions or []):
            if d.salary_component == component_name:
                total += _to_decimal(d.amount)
        for e in (slip.earnings or []):
            if e.salary_component == component_name:
                total += _to_decimal(e.amount)
    return total


def _to_decimal(v):
    return Decimal(str(v or 0))
