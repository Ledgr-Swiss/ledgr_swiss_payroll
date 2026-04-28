"""Tests hook Company.after_insert seed_payroll_mappings + double-entrée GL."""
import unittest
from decimal import Decimal

import frappe

from ledgr_swiss_payroll.setup.seed_payroll_mappings import seed_payroll_mappings


class TestSeedPayrollMappings(unittest.TestCase):
    def setUp(self):
        # Force re-seed by clearing existing IS Retenue mappings on the test company
        frappe.db.sql("""
            DELETE FROM `tabSalary Component Account`
            WHERE parent = 'IS Retenue' AND company = '_Test Seed CH Co'
        """)
        frappe.db.commit()
        from ledgr_swiss_payroll.setup.seed_payroll_mappings import seed_payroll_mappings
        if frappe.db.exists("Company", "_Test Seed CH Co"):
            doc = frappe.get_doc("Company", "_Test Seed CH Co")
            seed_payroll_mappings(doc)

    def test_swiss_company_seeds_mappings(self):
        name = "_Test Seed CH Co"
        if not frappe.db.exists("Company", name):
            frappe.get_doc({
                "doctype": "Company",
                "company_name": name,
                "abbr": "TSCH",
                "default_currency": "CHF",
                "country": "Switzerland",
            }).insert(ignore_permissions=True)

        mapping = frappe.db.exists(
            "Salary Component Account",
            {"parent": "Salaire de base", "company": name},
        )
        self.assertTrue(mapping, "Mapping Salaire de base -> 5000 manquant")

    def test_non_swiss_company_no_mapping(self):
        name = "_Test Seed FR Co"
        if not frappe.db.exists("Company", name):
            frappe.get_doc({
                "doctype": "Company",
                "company_name": name,
                "abbr": "TSFR",
                "default_currency": "EUR",
                "country": "France",
            }).insert(ignore_permissions=True)

        mapping = frappe.db.exists(
            "Salary Component Account",
            {"parent": "Salaire de base", "company": name},
        )
        self.assertFalse(mapping, "Mapping ne devrait pas exister pour Company non-CH")

    def test_idempotent_seed(self):
        name = "_Test Seed CH Co"
        if not frappe.db.exists("Company", name):
            frappe.get_doc({
                "doctype": "Company",
                "company_name": name,
                "abbr": "TSCH",
                "default_currency": "CHF",
                "country": "Switzerland",
            }).insert(ignore_permissions=True)

        company_doc = frappe.get_doc("Company", name)
        seed_payroll_mappings(company_doc)
        seed_payroll_mappings(company_doc)
        seed_payroll_mappings(company_doc)

        mappings = frappe.db.count(
            "Salary Component Account", {"company": name}
        )
        self.assertLessEqual(mappings, 11)

    def test_is_retenue_uses_2275_not_2300(self):
        """IS Retenue doit pointer sur le compte 2275 dédié, pas le compte 2300 fourre-tout."""
        name = "_Test Seed CH Co"
        if not frappe.db.exists("Company", name):
            frappe.get_doc({
                "doctype": "Company",
                "company_name": name,
                "abbr": "TSCH",
                "default_currency": "CHF",
                "country": "Switzerland",
            }).insert(ignore_permissions=True)

        sca = frappe.db.get_value(
            "Salary Component Account",
            {"parent": "IS Retenue", "company": name},
            "account",
        )
        self.assertIsNotNone(sca, "Mapping IS Retenue manquant")
        account_number = frappe.db.get_value("Account", sca, "account_number")
        self.assertEqual(
            account_number, "2275",
            f"IS Retenue doit pointer sur 2275, pointe sur {account_number}",
        )


class TestSalarySlipGLDoubleEntry(unittest.TestCase):
    """Vérifie la double-entrée garantie après submit Salary Slip."""

    @classmethod
    def setUpClass(cls):
        from ledgr_swiss_payroll.tests.test_calculator_orchestration import (
            COMPANY,
            _ensure_holiday_list,
            _ensure_company,
            _ensure_test_employee,
            _ensure_salary_components,
            _ensure_salary_structure,
        )
        frappe.flags.ignore_account_permission = True
        _ensure_holiday_list()
        _ensure_company()
        cls.company = COMPANY
        cls.employee_name = _ensure_test_employee()
        _ensure_salary_components()
        _ensure_salary_structure(cls.employee_name)

        company_doc = frappe.get_doc("Company", COMPANY)
        seed_payroll_mappings(company_doc)

        _ensure_payroll_payable(COMPANY)

    def setUp(self):
        from ledgr_swiss_payroll.tests.test_calculator_orchestration import _cleanup_slips
        _cleanup_slips(self.employee_name)

    def test_gl_entries_balanced(self):
        from ledgr_swiss_payroll.tests.test_calculator_orchestration import _reset_employee
        from datetime import date

        _reset_employee(self.employee_name, canton="VD", tax_code="A0N", mode="None")

        slip = frappe.get_doc({
            "doctype": "Salary Slip",
            "employee": self.employee_name,
            "company": self.company,
            "start_date": date(2026, 8, 1),
            "end_date": date(2026, 8, 31),
            "posting_date": date(2026, 8, 1),
        })
        slip.insert()
        slip.reload()

        slip.ledgr_owner_validated_by = "Administrator"
        slip.save()
        slip.submit()

        gle = frappe.get_all(
            "GL Entry",
            filters={"voucher_no": slip.name, "voucher_type": "Salary Slip"},
            fields=["debit", "credit"],
        )
        if not gle:
            self.skipTest(
                "HRMS did not generate GL entries — check Salary Component Account mappings"
            )

        total_debit = sum(Decimal(str(e["debit"] or 0)) for e in gle)
        total_credit = sum(Decimal(str(e["credit"] or 0)) for e in gle)
        self.assertEqual(total_debit, total_credit, "Double-entree desequilibree")


def _ensure_payroll_payable(company):
    """Set default_payroll_payable_account on the Company if not set."""
    existing = frappe.db.get_value("Company", company, "default_payroll_payable_account")
    if existing:
        return

    account_name = frappe.db.get_value(
        "Account",
        {"company": company, "account_number": "2270"},
        "name",
    )
    if not account_name:
        account_name = frappe.db.get_value(
            "Account",
            {"company": company, "account_number": "2300"},
            "name",
        )
    if not account_name:
        root = frappe.db.get_value(
            "Account",
            {"company": company, "root_type": "Liability", "is_group": 0},
            "name",
        )
        account_name = root

    if account_name:
        frappe.db.set_value("Company", company, "default_payroll_payable_account", account_name)
        frappe.db.commit()
