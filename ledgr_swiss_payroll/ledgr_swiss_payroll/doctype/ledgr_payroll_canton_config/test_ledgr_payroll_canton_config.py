import unittest
import frappe


class TestLEDGRPayrollCantonConfig(unittest.TestCase):
    def test_five_cantons_loaded(self):
        names = frappe.get_all("LEDGR Payroll Canton Config", pluck="canton_code")
        self.assertEqual(set(names), {"VD", "FR", "GE", "NE", "JU"})

    def test_canton_name_fr(self):
        vd = frappe.get_doc("LEDGR Payroll Canton Config", "VD")
        self.assertEqual(vd.canton_name_fr, "Vaud")
