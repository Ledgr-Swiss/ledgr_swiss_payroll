"""Whitelisted API endpoints — appelés depuis client JS."""
import frappe

from ledgr_swiss_payroll.pain001 import generate_pain001


@frappe.whitelist()
def download_pain001(payroll_entry):
    """Génère pain.001 XML et retourne en fichier binaire."""
    xml_bytes = generate_pain001(payroll_entry)

    frappe.local.response.filename = f"{payroll_entry}-pain001.xml"
    frappe.local.response.filecontent = xml_bytes
    frappe.local.response.type = "binary"
    frappe.local.response["content-type"] = "application/xml"
