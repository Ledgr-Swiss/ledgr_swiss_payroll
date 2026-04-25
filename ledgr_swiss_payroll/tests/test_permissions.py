"""Tests RBAC — vérifient que les 7 wrappers proxient correctement vers mandate_filter."""
import unittest
from unittest.mock import patch

import frappe

from ledgr_swiss_payroll import permissions


class TestPermissionsWrappers(unittest.TestCase):
    @patch("ledgr_swiss_payroll.permissions.mandate_filter")
    def test_employee_filter_proxies_correctly(self, mock_mandate):
        mock_mandate.return_value = "name in ('A', 'B')"
        result = permissions.employee_filter("Administrator")
        mock_mandate.assert_called_once_with("Employee", "Administrator")
        self.assertEqual(result, "name in ('A', 'B')")

    @patch("ledgr_swiss_payroll.permissions.mandate_filter")
    def test_salary_slip_filter_proxies_correctly(self, mock_mandate):
        mock_mandate.return_value = ""
        permissions.salary_slip_filter("Administrator")
        mock_mandate.assert_called_once_with("Salary Slip", "Administrator")

    def test_default_user_is_session_user(self):
        with patch("ledgr_swiss_payroll.permissions.mandate_filter") as mock_mandate:
            mock_mandate.return_value = ""
            permissions.salary_certificate_filter()
            args = mock_mandate.call_args[0]
            self.assertEqual(args[0], "LEDGR Salary Certificate")
            self.assertEqual(args[1], frappe.session.user)

    def test_all_seven_wrappers_exist(self):
        for name in [
            "employee_filter",
            "salary_slip_filter",
            "salary_structure_filter",
            "salary_structure_assignment_filter",
            "payroll_entry_filter",
            "salary_certificate_filter",
            "lpp_institution_filter",
        ]:
            self.assertTrue(hasattr(permissions, name), f"Wrapper {name} manquant")
