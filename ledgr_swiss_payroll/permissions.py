"""RBAC wrappers — proxient vers ledgr_core.utils.mandate_filter."""
import frappe

from ledgr_core.utils import mandate_filter


def employee_filter(user=None):
    return mandate_filter("Employee", user or frappe.session.user)


def salary_slip_filter(user=None):
    return mandate_filter("Salary Slip", user or frappe.session.user)


def salary_structure_filter(user=None):
    return mandate_filter("Salary Structure", user or frappe.session.user)


def salary_structure_assignment_filter(user=None):
    return mandate_filter("Salary Structure Assignment", user or frappe.session.user)


def payroll_entry_filter(user=None):
    return mandate_filter("Payroll Entry", user or frappe.session.user)


def salary_certificate_filter(user=None):
    return mandate_filter("LEDGR Salary Certificate", user or frappe.session.user)


def lpp_institution_filter(user=None):
    return mandate_filter("LEDGR LPP Institution", user or frappe.session.user)
