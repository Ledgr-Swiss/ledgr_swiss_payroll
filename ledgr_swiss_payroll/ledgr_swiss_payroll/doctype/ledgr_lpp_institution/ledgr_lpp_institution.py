import re

import frappe
from frappe import _
from frappe.model.document import Document


IBAN_CH_LI_RE = re.compile(r"^(CH|LI)[0-9]{2}[A-Z0-9]{5}[A-Z0-9]{12}$")


class LEDGRLPPInstitution(Document):
    def validate(self):
        if self.iban:
            cleaned = self.iban.replace(" ", "").upper()
            if not IBAN_CH_LI_RE.match(cleaned):
                frappe.throw(_("IBAN invalide — doit être CH/LI au format 21 caractères."))
            self.iban = cleaned
