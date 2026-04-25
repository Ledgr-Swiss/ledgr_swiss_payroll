"""Tests validators : workflow validation entreprise + anomalies soft."""
import json
import unittest
from unittest.mock import MagicMock, patch

import frappe

from ledgr_swiss_payroll.validators import refresh_anomalies, validate_owner_approval


class FakeDoc(dict):
    """Petit shim qui ressemble à un Document Frappe (get + attr)."""

    def __init__(self, **kwargs):
        super().__init__(kwargs)
        for k, v in kwargs.items():
            setattr(self, k, v)

    def get(self, key, default=None):
        return super().get(key, default)


class TestValidateOwnerApproval(unittest.TestCase):
    def test_validated_owner_passes(self):
        doc = FakeDoc(ledgr_owner_validated_by="user@x.ch")
        validate_owner_approval(doc)

    def test_no_validation_blocks_non_fid_manager(self):
        doc = FakeDoc(ledgr_owner_validated_by=None)
        with patch("frappe.get_roles", return_value=["LEDGR Accountant"]):
            with self.assertRaises(frappe.exceptions.ValidationError):
                validate_owner_approval(doc)

    def test_fid_manager_override_msgprint(self):
        doc = FakeDoc(ledgr_owner_validated_by=None)
        with patch("frappe.get_roles", return_value=["LEDGR Fiduciary Manager"]):
            with patch("frappe.msgprint") as mock_msg:
                validate_owner_approval(doc)
                mock_msg.assert_called_once()


class TestRefreshAnomalies(unittest.TestCase):
    def _employee_mock(self, **fields):
        defaults = {
            "name": "EMP-001",
            "ledgr_canton_residence": "VD",
            "ledgr_tax_code": "A0Y",
            "ledgr_iban": "CH9300762011623852957",
            "ledgr_lpp_institution": "LPP-TEST-CO-Caisse X",
            "ledgr_thirteenth_month_mode": "None",
        }
        defaults.update(fields)

        m = MagicMock()
        m.get.side_effect = lambda key, default=None, _d=defaults: _d.get(key, default)
        for k, v in defaults.items():
            setattr(m, k, v)
        m.name = defaults["name"]
        return m

    @patch("frappe.get_doc")
    def test_missing_canton_anomaly(self, mock_get):
        mock_get.return_value = self._employee_mock(ledgr_canton_residence=None)
        doc = FakeDoc(employee="EMP-001", earnings=[], gross_pay=5000, start_date="2026-06-01")
        refresh_anomalies(doc)
        codes = [a["code"] for a in json.loads(doc.ledgr_anomalies or "[]")]
        self.assertIn("MISSING_CANTON_RESIDENCE", codes)

    @patch("frappe.get_doc")
    def test_missing_tax_code_anomaly(self, mock_get):
        mock_get.return_value = self._employee_mock(ledgr_tax_code=None)
        doc = FakeDoc(employee="EMP-001", earnings=[], gross_pay=5000, start_date="2026-06-01")
        refresh_anomalies(doc)
        codes = [a["code"] for a in json.loads(doc.ledgr_anomalies or "[]")]
        self.assertIn("MISSING_TAX_CODE", codes)

    @patch("frappe.get_doc")
    def test_missing_iban_anomaly(self, mock_get):
        mock_get.return_value = self._employee_mock(ledgr_iban=None)
        doc = FakeDoc(employee="EMP-001", earnings=[], gross_pay=5000, start_date="2026-06-01")
        refresh_anomalies(doc)
        codes = [a["code"] for a in json.loads(doc.ledgr_anomalies or "[]")]
        self.assertIn("MISSING_IBAN", codes)

    @patch("frappe.get_doc")
    def test_lpp_not_configured_anomaly(self, mock_get):
        mock_get.return_value = self._employee_mock(ledgr_lpp_institution=None)
        doc = FakeDoc(employee="EMP-001", earnings=[], gross_pay=5000, start_date="2026-06-01")
        refresh_anomalies(doc)
        codes = [a["code"] for a in json.loads(doc.ledgr_anomalies or "[]")]
        self.assertIn("LPP_NOT_CONFIGURED", codes)

    @patch("frappe.get_doc")
    def test_thirteenth_missing_base_anomaly(self, mock_get):
        mock_get.return_value = self._employee_mock(ledgr_thirteenth_month_mode="Full December")
        doc = FakeDoc(
            employee="EMP-001",
            earnings=[type("E", (), {"salary_component": "Heures supplémentaires"})()],
            gross_pay=300,
            start_date="2026-12-01",
        )
        refresh_anomalies(doc)
        codes = [a["code"] for a in json.loads(doc.ledgr_anomalies or "[]")]
        self.assertIn("THIRTEENTH_MISSING_BASE", codes)

    @patch("frappe.db.exists", return_value=False)
    @patch("frappe.db.get_value", return_value="VD")
    @patch("frappe.get_doc")
    def test_is_bracket_not_found_anomaly(self, mock_get, mock_gv, mock_exists):
        mock_get.return_value = self._employee_mock()
        doc = FakeDoc(
            employee="EMP-001",
            earnings=[],
            gross_pay=5000,
            start_date="2026-06-01",
        )
        refresh_anomalies(doc)
        codes = [a["code"] for a in json.loads(doc.ledgr_anomalies or "[]")]
        self.assertIn("IS_BRACKET_NOT_FOUND", codes)
