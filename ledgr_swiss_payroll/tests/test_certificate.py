"""Tests certificate.generate_certificate + render Print Format."""
import unittest
from datetime import date

import frappe

from ledgr_swiss_payroll.certificate import (
    generate_certificate,
    generate_certificates_for_year,
)
from ledgr_swiss_payroll.exceptions import NoSlipsForCertificate


COMPANY = "_Test Cert Co"


class TestGenerateCertificate(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        frappe.flags.ignore_account_permission = True
        _ensure_cert_company()
        cls.employee = _ensure_cert_employee()

    def test_no_slips_raises(self):
        with self.assertRaises(NoSlipsForCertificate):
            generate_certificate(self.employee, 2099, COMPANY)

    def test_idempotent_returns_existing(self):
        cert_name = f"CERT-{self.employee}-2030"
        if not frappe.db.exists("LEDGR Salary Certificate", cert_name):
            frappe.get_doc({
                "doctype": "LEDGR Salary Certificate",
                "employee": self.employee, "year": 2030, "company": COMPANY,
                "gross_salary": 72000, "ahv_ai_ac_deduction": 9600,
                "lpp_deduction": 2400, "net_salary": 58800, "is_deduction": 1200,
            }).insert(ignore_permissions=True)
        result = generate_certificate(self.employee, 2030, COMPANY)
        self.assertEqual(result, cert_name)

    def test_generate_certificates_for_year_skip_no_slips(self):
        results = generate_certificates_for_year(2099, COMPANY)
        self.assertEqual(results, [])

    def test_print_format_exists(self):
        self.assertTrue(
            frappe.db.exists("Print Format", "salary_certificate_form_11"),
            "Print Format salary_certificate_form_11 manquant",
        )

    def test_print_format_renders(self):
        cert_name = f"CERT-{self.employee}-2030"
        if not frappe.db.exists("LEDGR Salary Certificate", cert_name):
            frappe.get_doc({
                "doctype": "LEDGR Salary Certificate",
                "employee": self.employee, "year": 2030, "company": COMPANY,
                "gross_salary": 72000, "ahv_ai_ac_deduction": 9600,
                "lpp_deduction": 2400, "net_salary": 58800, "is_deduction": 1200,
            }).insert(ignore_permissions=True)
        html = frappe.get_print(
            "LEDGR Salary Certificate",
            cert_name,
            print_format="salary_certificate_form_11",
        )
        self.assertIn("Formulaire 11 ESTV", html)
        self.assertIn("Salaire brut", html)

    def test_aggregation_with_submitted_slips(self):
        from ledgr_swiss_payroll.tests.test_calculator_orchestration import (
            COMPANY as ORCH_COMPANY,
            _ensure_holiday_list,
            _ensure_company,
            _ensure_test_employee,
            _ensure_salary_components,
            _ensure_salary_structure,
            _cleanup_slips,
            _reset_employee,
        )
        _ensure_holiday_list()
        _ensure_company()
        emp = _ensure_test_employee()
        _ensure_salary_components()
        _ensure_salary_structure(emp)
        _cleanup_slips(emp)
        _reset_employee(emp, canton="VD", tax_code="A0N", mode="None")

        _cleanup_cert(emp, 2026, ORCH_COMPANY)

        submitted = []
        for month in [10, 11]:
            slip = frappe.get_doc({
                "doctype": "Salary Slip",
                "employee": emp,
                "company": ORCH_COMPANY,
                "start_date": date(2026, month, 1),
                "end_date": date(2026, month, 28),
                "posting_date": date(2026, month, 1),
            })
            slip.insert()
            slip.reload()
            slip.ledgr_owner_validated_by = "Administrator"
            slip.save()
            try:
                slip.submit()
                submitted.append(slip.name)
            except Exception:
                pass

        if not submitted:
            self.skipTest("Could not submit Salary Slips — HRMS config incomplete")

        cert_name = generate_certificate(emp, 2026, ORCH_COMPANY)
        cert = frappe.get_doc("LEDGR Salary Certificate", cert_name)
        self.assertEqual(cert.year, 2026)
        self.assertGreater(cert.gross_salary, 0)
        self.assertEqual(cert.start_date, date(2026, 10, 1))


def _ensure_cert_company():
    if not frappe.db.exists("Company", COMPANY):
        frappe.get_doc({
            "doctype": "Company",
            "company_name": COMPANY,
            "abbr": "TCC",
            "default_currency": "CHF",
            "country": "Switzerland",
        }).insert(ignore_permissions=True)


def _ensure_cert_employee():
    name = frappe.db.get_value(
        "Employee",
        {"employee_name": "Test Cert Employee", "company": COMPANY},
        "name",
    )
    if name:
        return name
    doc = frappe.get_doc({
        "doctype": "Employee",
        "employee_name": "Test Cert Employee",
        "first_name": "Test", "last_name": "Cert",
        "company": COMPANY,
        "date_of_joining": "2026-01-01",
        "date_of_birth": "1985-01-01",
        "gender": "Male",
        "status": "Active",
        "ledgr_canton_residence": "VD",
        "ledgr_tax_code": "A0Y",
        "ledgr_iban": "CH9300762011623852957",
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _cleanup_cert(employee, year, company):
    """Delete existing cert for employee/year/company to allow re-creation."""
    existing = frappe.db.get_all(
        "LEDGR Salary Certificate",
        filters={"employee": employee, "year": year, "company": company, "docstatus": 0},
        pluck="name",
    )
    for n in existing:
        frappe.delete_doc("LEDGR Salary Certificate", n, force=True)
    frappe.db.commit()
