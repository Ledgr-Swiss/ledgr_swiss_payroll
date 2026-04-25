"""Tests d exactitude IS — gamma-strict.

Each test uses a value computed from the official ESTV tariff files
(tar26{kt}.txt) shipped with the app. Source: ESTV Quellensteuertarife
fuer den Import in Lohnbuchhaltungssysteme, valid 2026-01-01.

30 tests: 6 per canton (VD, FR, GE, NE, JU).
"""
import unittest
from datetime import date
from decimal import Decimal

from ledgr_swiss_payroll.is_tax import compute_is, clear_cache
from ledgr_swiss_payroll.exceptions import ISBracketNotFound


class TestISExactitudeVD(unittest.TestCase):

    def test_a0n_below_threshold(self):
        result = compute_is("VD", "A0N", Decimal("2000"), date(2026, 6, 1))
        self.assertEqual(result, Decimal("0.00"))

    def test_a0n_5500(self):
        result = compute_is("VD", "A0N", Decimal("5500"), date(2026, 6, 1))
        self.assertEqual(result, Decimal("536.80"))

    def test_a0n_10000(self):
        result = compute_is("VD", "A0N", Decimal("10000"), date(2026, 6, 1))
        self.assertEqual(result, Decimal("1569.00"))

    def test_b1n_8200(self):
        result = compute_is("VD", "B1N", Decimal("8200"), date(2026, 6, 1))
        self.assertEqual(result, Decimal("574.00"))

    def test_c2n_6000(self):
        result = compute_is("VD", "C2N", Decimal("6000"), date(2026, 6, 1))
        self.assertEqual(result, Decimal("519.00"))

    def test_h1n_5500(self):
        result = compute_is("VD", "H1N", Decimal("5500"), date(2026, 6, 1))
        self.assertEqual(result, Decimal("197.45"))


class TestISExactitudeFR(unittest.TestCase):

    def test_a0n_5500(self):
        result = compute_is("FR", "A0N", Decimal("5500"), date(2026, 3, 15))
        self.assertEqual(result, Decimal("628.65"))

    def test_a0y_5500(self):
        result = compute_is("FR", "A0Y", Decimal("5500"), date(2026, 3, 15))
        self.assertEqual(result, Decimal("628.65"))

    def test_b2n_8000(self):
        result = compute_is("FR", "B2N", Decimal("8000"), date(2026, 3, 15))
        self.assertEqual(result, Decimal("420.00"))

    def test_c1y_7000(self):
        result = compute_is("FR", "C1Y", Decimal("7000"), date(2026, 3, 15))
        self.assertEqual(result, Decimal("753.20"))

    def test_h2n_6500(self):
        result = compute_is("FR", "H2N", Decimal("6500"), date(2026, 3, 15))
        self.assertEqual(result, Decimal("240.50"))

    def test_a0n_below_threshold(self):
        result = compute_is("FR", "A0N", Decimal("1500"), date(2026, 3, 15))
        self.assertEqual(result, Decimal("0.00"))


class TestISExactitudeGE(unittest.TestCase):

    def test_a0n_5500(self):
        result = compute_is("GE", "A0N", Decimal("5500"), date(2026, 1, 31))
        self.assertEqual(result, Decimal("484.55"))

    def test_b1n_8200(self):
        result = compute_is("GE", "B1N", Decimal("8200"), date(2026, 1, 31))
        self.assertEqual(result, Decimal("204.18"))

    def test_c0n_6000(self):
        result = compute_is("GE", "C0N", Decimal("6000"), date(2026, 1, 31))
        self.assertEqual(result, Decimal("590.40"))

    def test_h1n_7000(self):
        result = compute_is("GE", "H1N", Decimal("7000"), date(2026, 1, 31))
        self.assertEqual(result, Decimal("121.10"))

    def test_a3n_10000(self):
        result = compute_is("GE", "A3N", Decimal("10000"), date(2026, 1, 31))
        self.assertEqual(result, Decimal("535.00"))

    def test_a0n_below_threshold(self):
        result = compute_is("GE", "A0N", Decimal("2000"), date(2026, 1, 31))
        self.assertEqual(result, Decimal("0.00"))


class TestISExactitudeNE(unittest.TestCase):

    def test_a0n_5500(self):
        result = compute_is("NE", "A0N", Decimal("5500"), date(2026, 9, 1))
        self.assertEqual(result, Decimal("667.70"))

    def test_b0n_7000(self):
        result = compute_is("NE", "B0N", Decimal("7000"), date(2026, 9, 1))
        self.assertEqual(result, Decimal("653.10"))

    def test_c3n_9000(self):
        result = compute_is("NE", "C3N", Decimal("9000"), date(2026, 9, 1))
        self.assertEqual(result, Decimal("1033.20"))

    def test_h1n_6000(self):
        result = compute_is("NE", "H1N", Decimal("6000"), date(2026, 9, 1))
        self.assertEqual(result, Decimal("238.80"))

    def test_a5n_12000(self):
        result = compute_is("NE", "A5N", Decimal("12000"), date(2026, 9, 1))
        self.assertEqual(result, Decimal("1244.40"))

    def test_a0n_below_threshold(self):
        result = compute_is("NE", "A0N", Decimal("1000"), date(2026, 9, 1))
        self.assertEqual(result, Decimal("0.00"))


class TestISExactitudeJU(unittest.TestCase):

    def test_a0y_5500(self):
        result = compute_is("JU", "A0Y", Decimal("5500"), date(2026, 7, 1))
        self.assertEqual(result, Decimal("642.95"))

    def test_b1y_8200(self):
        result = compute_is("JU", "B1Y", Decimal("8200"), date(2026, 7, 1))
        self.assertEqual(result, Decimal("697.00"))

    def test_c0y_6000(self):
        result = compute_is("JU", "C0Y", Decimal("6000"), date(2026, 7, 1))
        self.assertEqual(result, Decimal("746.40"))

    def test_h2y_7500(self):
        result = compute_is("JU", "H2Y", Decimal("7500"), date(2026, 7, 1))
        self.assertEqual(result, Decimal("493.50"))

    def test_a3y_10000(self):
        result = compute_is("JU", "A3Y", Decimal("10000"), date(2026, 7, 1))
        self.assertEqual(result, Decimal("1113.00"))

    def test_a0y_below_threshold(self):
        result = compute_is("JU", "A0Y", Decimal("400"), date(2026, 7, 1))
        self.assertEqual(result, Decimal("0.00"))


class TestISBracketNotFound(unittest.TestCase):

    def test_unknown_canton(self):
        with self.assertRaises(ISBracketNotFound):
            compute_is("ZH", "A0N", Decimal("5000"), date(2026, 6, 1))

    def test_unknown_code(self):
        with self.assertRaises(ISBracketNotFound):
            compute_is("VD", "Z9Z", Decimal("5000"), date(2026, 6, 1))

    def test_future_year(self):
        with self.assertRaises(ISBracketNotFound):
            compute_is("VD", "A0N", Decimal("5000"), date(2030, 1, 1))
