"""Tests apply_swiss_payroll_calculations — orchestration Salary Slip."""
import unittest
from datetime import date
from decimal import Decimal

import frappe


COMPANY = "_Test Swiss Payroll Co"
HOLIDAY_LIST = "_Test SP Holiday List 2026"


class TestSalarySlipOrchestration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        frappe.flags.ignore_account_permission = True
        _ensure_holiday_list()
        _ensure_company()
        cls.employee_name = _ensure_test_employee()
        _ensure_salary_components()
        _ensure_salary_structure(cls.employee_name)

    def setUp(self):
        _cleanup_slips(self.employee_name)

    def test_salary_slip_calc_basic(self):
        _reset_employee(self.employee_name, canton="VD", tax_code="A0N", mode="None")
        slip = _make_slip(self.employee_name, date(2026, 6, 1), date(2026, 6, 30))
        avs = next((d for d in slip.deductions if d.salary_component == "AVS/AI/AC Employé"), None)
        self.assertIsNotNone(avs, "AVS/AI/AC Employé manquant")

    def test_thirteenth_full_december(self):
        _reset_employee(self.employee_name, canton="VD", tax_code="A0N", mode="Full December")
        slip = _make_slip(self.employee_name, date(2026, 12, 1), date(2026, 12, 31))
        thirteenth = next((e for e in slip.earnings if e.salary_component == "13e Salaire"), None)
        self.assertIsNotNone(thirteenth, "13e Salaire absent en décembre Full December")
        self.assertGreater(Decimal(str(thirteenth.amount)), Decimal("0"))

    def test_thirteenth_none_no_component(self):
        _reset_employee(self.employee_name, canton="VD", tax_code="A0N", mode="None")
        slip = _make_slip(self.employee_name, date(2026, 11, 1), date(2026, 11, 30))
        thirteenth = next((e for e in slip.earnings if e.salary_component == "13e Salaire"), None)
        self.assertIsNone(thirteenth)

    def test_anomaly_logged_on_missing_canton(self):
        _reset_employee(self.employee_name, canton=None, tax_code=None, mode="None")
        slip = _make_slip(self.employee_name, date(2026, 7, 1), date(2026, 7, 31))
        import json
        codes = [a["code"] for a in json.loads(slip.ledgr_anomalies or "[]")]
        self.assertIn("MISSING_CANTON_RESIDENCE", codes)


def _cleanup_slips(employee_name):
    """Delete all draft salary slips for the test employee."""
    slips = frappe.get_all(
        "Salary Slip",
        filters={"employee": employee_name, "docstatus": 0},
        pluck="name",
    )
    for s in slips:
        frappe.delete_doc("Salary Slip", s, force=True)
    frappe.db.commit()


def _ensure_holiday_list():
    if frappe.db.exists("Holiday List", HOLIDAY_LIST):
        return
    hl = frappe.get_doc({
        "doctype": "Holiday List",
        "holiday_list_name": HOLIDAY_LIST,
        "from_date": "2024-01-01",
        "to_date": "2027-12-31",
        "holidays": [
            {"holiday_date": "2026-01-01", "description": "Nouvel An"},
            {"holiday_date": "2026-08-01", "description": "Fête nationale"},
            {"holiday_date": "2026-12-25", "description": "Noël"},
        ],
    })
    hl.insert(ignore_permissions=True)


def _ensure_company():
    if not frappe.db.exists("Company", COMPANY):
        doc = frappe.get_doc({
            "doctype": "Company",
            "company_name": COMPANY,
            "abbr": "TSPC",
            "default_currency": "CHF",
            "country": "Switzerland",
            "default_holiday_list": HOLIDAY_LIST,
        })
        doc.insert(ignore_permissions=True)
    else:
        frappe.db.set_value("Company", COMPANY, "default_holiday_list", HOLIDAY_LIST)
        frappe.db.commit()


def _ensure_test_employee():
    existing = frappe.db.get_value(
        "Employee",
        {"employee_name": "Test Swiss Payroll Employee", "company": COMPANY},
        "name",
    )
    if existing:
        emp = frappe.get_doc("Employee", existing)
        emp.holiday_list = HOLIDAY_LIST
        emp.ledgr_canton_residence = "VD"
        emp.ledgr_tax_code = "A0N"
        emp.ledgr_iban = "CH9300762011623852957"
        emp.save(ignore_permissions=True)
        return existing
    doc = frappe.get_doc({
        "doctype": "Employee",
        "employee_name": "Test Swiss Payroll Employee",
        "first_name": "Test",
        "last_name": "Employee",
        "company": COMPANY,
        "date_of_joining": "2024-01-01",
        "date_of_birth": "1985-01-01",
        "gender": "Male",
        "status": "Active",
        "holiday_list": HOLIDAY_LIST,
        "ledgr_canton_residence": "VD",
        "ledgr_tax_code": "A0N",
        "ledgr_iban": "CH9300762011623852957",
    })
    doc.insert(ignore_permissions=True)
    return doc.name


def _reset_employee(name, canton, tax_code, mode):
    emp = frappe.get_doc("Employee", name)
    emp.ledgr_canton_residence = canton
    emp.ledgr_tax_code = tax_code
    emp.ledgr_thirteenth_month_mode = mode
    emp.save(ignore_permissions=True)


def _ensure_salary_components():
    components = [
        ("Salaire de base", "SBASE", "Earning"),
        ("13e Salaire", "SAL13E", "Earning"),
        ("AVS/AI/AC Employé", "AVSEMP", "Deduction"),
        ("IS Retenue", "ISRET", "Deduction"),
        ("AC Solidarité", "ACSOL", "Deduction"),
    ]
    for comp_name, abbr, ctype in components:
        if not frappe.db.exists("Salary Component", comp_name):
            frappe.get_doc({
                "doctype": "Salary Component",
                "salary_component": comp_name,
                "salary_component_abbr": abbr,
                "type": ctype,
            }).insert(ignore_permissions=True)


def _ensure_salary_structure(employee_name):
    ss_name = "_Test SP Salary Structure"
    if not frappe.db.exists("Salary Structure", ss_name):
        structure = frappe.get_doc({
            "doctype": "Salary Structure",
            "name": ss_name,
            "company": COMPANY,
            "is_active": "Yes",
            "currency": "CHF",
            "payroll_frequency": "Monthly",
            "earnings": [{"salary_component": "Salaire de base", "amount": 6000}],
            "deductions": [],
        })
        structure.insert(ignore_permissions=True)
        structure.submit()

    existing_ssa = frappe.db.exists(
        "Salary Structure Assignment",
        {"employee": employee_name, "salary_structure": ss_name, "docstatus": 1},
    )
    if not existing_ssa:
        assignment = frappe.get_doc({
            "doctype": "Salary Structure Assignment",
            "employee": employee_name,
            "salary_structure": ss_name,
            "from_date": "2024-01-01",
            "company": COMPANY,
            "base": 6000,
        })
        assignment.insert(ignore_permissions=True)
        assignment.submit()


def _make_slip(employee_name, start, end):
    """Create, insert, reload and return a Salary Slip."""
    slip = frappe.get_doc({
        "doctype": "Salary Slip",
        "employee": employee_name,
        "company": COMPANY,
        "start_date": start,
        "end_date": end,
        "posting_date": start,
    })
    slip.insert()
    slip.reload()
    return slip
