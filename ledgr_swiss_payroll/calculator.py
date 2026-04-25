"""Calculator orchestration Salary Slip + 13ème salaire."""
from datetime import date
from decimal import Decimal

import frappe

from ledgr_swiss_payroll.ahv import compute_employee_social_charges
from ledgr_swiss_payroll.helpers import quantize_chf
from ledgr_swiss_payroll.is_tax import compute_is


def compute_thirteenth_month(
    mode,
    base_monthly,
    slip_month,
    date_of_joining,
    relieving_date,
    year,
):
    """Compute le montant du component "13e Salaire" à ajouter sur le slip courant.

    Args:
        mode: "None" | "Full December" | "Half June+December" | "Monthly (1/13)"
        base_monthly: Decimal — montant component "Salaire de base" courant
        slip_month: int — 1..12 (doc.start_date.month)
        date_of_joining: date — date d'entrée employé
        relieving_date: date | None — date de sortie (None si toujours en poste)
        year: int — année du slip (doc.start_date.year)

    Returns:
        Decimal en CHF (centime). Decimal("0") si aucun versement attendu ce mois.
    """
    if mode == "None":
        return Decimal("0")

    base_monthly = Decimal(base_monthly)

    year_start = date(year, 1, 1)
    year_end = date(year, 12, 31)
    period_start = max(date_of_joining, year_start)
    period_end = min(relieving_date or year_end, year_end)
    months_worked = (
        (period_end.year - period_start.year) * 12
        + (period_end.month - period_start.month)
        + 1
    )
    prorata = Decimal(months_worked) / Decimal(12)

    if mode == "Full December" and slip_month == 12:
        return quantize_chf(base_monthly * prorata)
    if mode == "Half June+December" and slip_month in (6, 12):
        return quantize_chf(base_monthly * prorata / Decimal(2))
    if mode == "Monthly (1/13)":
        return quantize_chf(base_monthly / Decimal(12) * prorata)

    return Decimal("0")


def apply_swiss_payroll_calculations(slip, method=None):
    """Orchestre le calcul Salary Slip suisse.

    Pipeline :
      1. Salary Structure -> gross_pay (déjà calculé par HRMS)
      1bis. compute_thirteenth_month -> ajout component "13e Salaire" si requis
      2. compute_employee_social_charges -> AVS/AI/APG/AC + AC solidarity
      3. compute_is -> IS Retenue (revenu après AHV)
    """
    employee = frappe.get_doc("Employee", slip.employee)

    base_amount = _component_amount(slip, "Salaire de base")
    thirteenth = compute_thirteenth_month(
        mode=employee.get("ledgr_thirteenth_month_mode") or "None",
        base_monthly=base_amount,
        slip_month=slip.start_date.month,
        date_of_joining=employee.date_of_joining,
        relieving_date=employee.relieving_date,
        year=slip.start_date.year,
    )
    if thirteenth > 0:
        _add_or_update_earning(slip, "13e Salaire", thirteenth)
        slip.gross_pay = sum(Decimal(str(e.amount)) for e in slip.earnings)

    gross_pay = Decimal(str(slip.gross_pay))

    rate = _active_ahv_rate(slip.start_date)
    charges = compute_employee_social_charges(gross_pay, rate)

    avs_total = (
        charges["ahv_employee"]
        + charges["ai_employee"]
        + charges["apg_employee"]
        + charges["ac_employee"]
    )
    _add_or_update_deduction(slip, "AVS/AI/AC Employé", avs_total)

    if charges["ac_solidarity"] > 0:
        _add_or_update_deduction(slip, "AC Solidarité", charges["ac_solidarity"])

    revenu_is = gross_pay - avs_total - charges["ac_solidarity"]
    canton_code = frappe.db.get_value(
        "LEDGR Payroll Canton Config",
        employee.ledgr_canton_residence,
        "canton_code",
    ) if employee.get("ledgr_canton_residence") else None

    if canton_code and employee.get("ledgr_tax_code"):
        try:
            is_retenue = compute_is(
                canton_code,
                employee.ledgr_tax_code,
                revenu_is,
                slip.start_date,
            )
            if is_retenue > 0:
                _add_or_update_deduction(slip, "IS Retenue", is_retenue)
        except Exception:
            pass


def _component_amount(slip, component_name):
    for e in slip.earnings or []:
        if e.salary_component == component_name:
            return Decimal(str(e.amount or 0))
    return Decimal("0")


def _add_or_update_earning(slip, component_name, amount):
    for e in slip.earnings or []:
        if e.salary_component == component_name:
            e.amount = float(amount)
            return
    slip.append("earnings", {
        "salary_component": component_name,
        "amount": float(amount),
    })


def _add_or_update_deduction(slip, component_name, amount):
    for d in slip.deductions or []:
        if d.salary_component == component_name:
            d.amount = float(amount)
            return
    slip.append("deductions", {
        "salary_component": component_name,
        "amount": float(amount),
    })


def _active_ahv_rate(slip_date):
    """Récupère le LEDGR AHV Rate actif pour une date."""
    name = frappe.db.sql(
        """
        SELECT name FROM `tabLEDGR AHV Rate`
         WHERE active_from <= %(d)s
           AND (active_until IS NULL OR active_until >= %(d)s)
         ORDER BY active_from DESC LIMIT 1
        """,
        {"d": slip_date},
        as_dict=True,
    )
    if not name:
        raise frappe.exceptions.ValidationError(
            f"Aucun LEDGR AHV Rate actif à la date {slip_date}"
        )
    return frappe.get_doc("LEDGR AHV Rate", name[0]["name"])
