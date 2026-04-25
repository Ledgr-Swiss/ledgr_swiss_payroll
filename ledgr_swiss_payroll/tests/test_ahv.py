"""Tests AHV/AI/APG/AC — pure function, pas besoin de Frappe DB."""
import unittest
from decimal import Decimal

from ledgr_swiss_payroll.ahv import compute_employee_social_charges


RATE_2026 = {
    "ahv_employee_pct": 4.35,
    "ai_employee_pct": 0.7,
    "apg_employee_pct": 0.25,
    "ac_employee_pct": 1.1,
    "ac_threshold": 148200,
    "ac_solidarity_pct": 0.5,
}


class TestComputeAHV(unittest.TestCase):
    def test_basic_under_threshold(self):
        r = compute_employee_social_charges(Decimal("5000"), RATE_2026)
        self.assertEqual(r["ahv_employee"], Decimal("217.50"))
        self.assertEqual(r["ai_employee"], Decimal("35.00"))
        self.assertEqual(r["apg_employee"], Decimal("12.50"))
        self.assertEqual(r["ac_employee"], Decimal("55.00"))
        self.assertEqual(r["ac_solidarity"], Decimal("0.00"))

    def test_at_threshold(self):
        r = compute_employee_social_charges(Decimal("12350"), RATE_2026)
        self.assertEqual(r["ac_employee"], Decimal("135.85"))
        self.assertEqual(r["ac_solidarity"], Decimal("0.00"))

    def test_above_threshold_with_solidarity(self):
        r = compute_employee_social_charges(Decimal("20000"), RATE_2026)
        self.assertEqual(r["ac_employee"], Decimal("135.85"))
        self.assertEqual(r["ac_solidarity"], Decimal("38.25"))

    def test_zero_gross(self):
        r = compute_employee_social_charges(Decimal("0"), RATE_2026)
        self.assertEqual(r["ahv_employee"], Decimal("0.00"))
        self.assertEqual(r["ai_employee"], Decimal("0.00"))
        self.assertEqual(r["ac_solidarity"], Decimal("0.00"))

    def test_no_solidarity_pct_configured(self):
        rate_no_sol = {**RATE_2026, "ac_solidarity_pct": 0}
        r = compute_employee_social_charges(Decimal("20000"), rate_no_sol)
        self.assertEqual(r["ac_solidarity"], Decimal("0.00"))
