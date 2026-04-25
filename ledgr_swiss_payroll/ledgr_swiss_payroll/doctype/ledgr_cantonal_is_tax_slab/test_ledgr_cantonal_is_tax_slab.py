import unittest
import frappe


class TestLEDGRCantonalISTaxSlab(unittest.TestCase):
    def test_doctype_exists(self):
        self.assertTrue(frappe.db.exists("DocType", "LEDGR Cantonal IS Tax Slab"))
