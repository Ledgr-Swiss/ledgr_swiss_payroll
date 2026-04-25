"""Tests compute_thirteenth_month — 7 scenarios."""
import unittest
from datetime import date
from decimal import Decimal

from ledgr_swiss_payroll.calculator import compute_thirteenth_month


class TestComputeThirteenthMonth(unittest.TestCase):
    def test_full_december_full_year(self):
        r = compute_thirteenth_month(
            mode="Full December",
            base_monthly=Decimal("6000"),
            slip_month=12,
            date_of_joining=date(2024, 1, 1),
            relieving_date=None,
            year=2026,
        )
        self.assertEqual(r, Decimal("6000.00"))

    def test_full_december_partial_year_join_may(self):
        r = compute_thirteenth_month(
            mode="Full December",
            base_monthly=Decimal("6000"),
            slip_month=12,
            date_of_joining=date(2026, 5, 1),
            relieving_date=None,
            year=2026,
        )
        self.assertEqual(r, Decimal("4000.00"))

    def test_half_june_december_june(self):
        r = compute_thirteenth_month(
            mode="Half June+December",
            base_monthly=Decimal("6000"),
            slip_month=6,
            date_of_joining=date(2024, 1, 1),
            relieving_date=None,
            year=2026,
        )
        self.assertEqual(r, Decimal("3000.00"))

    def test_monthly_full_year(self):
        for month in [1, 6, 12]:
            r = compute_thirteenth_month(
                mode="Monthly (1/13)",
                base_monthly=Decimal("6000"),
                slip_month=month,
                date_of_joining=date(2024, 1, 1),
                relieving_date=None,
                year=2026,
            )
            self.assertEqual(r, Decimal("500.00"))

    def test_mode_none_returns_zero(self):
        r = compute_thirteenth_month(
            mode="None",
            base_monthly=Decimal("6000"),
            slip_month=12,
            date_of_joining=date(2024, 1, 1),
            relieving_date=None,
            year=2026,
        )
        self.assertEqual(r, Decimal("0"))

    def test_full_december_relieving_october(self):
        r = compute_thirteenth_month(
            mode="Full December",
            base_monthly=Decimal("6000"),
            slip_month=12,
            date_of_joining=date(2026, 1, 1),
            relieving_date=date(2026, 10, 31),
            year=2026,
        )
        self.assertEqual(r, Decimal("5000.00"))

    def test_unknown_mode_returns_zero(self):
        r = compute_thirteenth_month(
            mode="Quarterly",
            base_monthly=Decimal("6000"),
            slip_month=3,
            date_of_joining=date(2024, 1, 1),
            relieving_date=None,
            year=2026,
        )
        self.assertEqual(r, Decimal("0"))
