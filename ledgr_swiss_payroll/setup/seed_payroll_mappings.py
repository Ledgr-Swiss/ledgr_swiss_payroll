"""Hook Company.after_insert : seed Salary Component Account si CH + chart Käfer/VEKA."""
import json

import frappe


def seed_payroll_mappings(doc, method=None):
    if doc.country != "Switzerland":
        return

    if not frappe.db.exists("Account", {"company": doc.name, "account_number": "5000"}):
        return

    fixture_path = frappe.get_app_path(
        "ledgr_swiss_payroll", "setup", "data", "salary_component_account_kaefer.json"
    )
    with open(fixture_path) as f:
        mappings = json.load(f)

    for m in mappings:
        if frappe.db.exists("Salary Component Account", {
            "parent": m["component"],
            "company": doc.name,
        }):
            continue

        account_name = _resolve_account(doc.name, m["account_number"])
        if not account_name:
            continue

        sca = frappe.new_doc("Salary Component Account")
        sca.parent = m["component"]
        sca.parenttype = "Salary Component"
        sca.parentfield = "accounts"
        sca.company = doc.name
        sca.account = account_name
        sca.insert(ignore_permissions=True)


def _resolve_account(company, account_number):
    return frappe.db.get_value(
        "Account",
        {"company": company, "account_number": account_number},
        "name",
    )
