import unittest
from decimal import Decimal
from datetime import date
import frappe


class TestLEDGRAHVRate(unittest.TestCase):
    def test_2026_rate_present(self):
        r = frappe.get_doc("LEDGR AHV Rate", "AHV-2026-01-01")
        self.assertEqual(r.active_from, date(2026, 1, 1))
        self.assertEqual(Decimal(str(r.ahv_employee_pct)), Decimal("4.35"))
        self.assertEqual(r.ac_threshold, 148200)
