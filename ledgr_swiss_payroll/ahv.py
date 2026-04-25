"""AHV/AI/APG/AC calculator — pure function, no Frappe access."""
from decimal import Decimal

from ledgr_swiss_payroll.helpers import quantize_chf


def compute_employee_social_charges(gross_monthly, rate):
    """Compute employee social charges for a monthly gross salary.

    Args:
        gross_monthly: Decimal — montant brut mensuel CHF
        rate: dict ou Document — row of LEDGR AHV Rate

    Returns:
        dict avec clés ahv_employee, ai_employee, apg_employee, ac_employee,
        ac_solidarity. Toutes les valeurs sont des Decimal en CHF (centime).
    """
    g = Decimal(gross_monthly)
    if g <= 0:
        return {
            "ahv_employee": Decimal("0.00"),
            "ai_employee": Decimal("0.00"),
            "apg_employee": Decimal("0.00"),
            "ac_employee": Decimal("0.00"),
            "ac_solidarity": Decimal("0.00"),
        }

    def _pct(value):
        return Decimal(str(_extract(rate, value)))

    ahv_employee = quantize_chf(g * _pct("ahv_employee_pct") / Decimal(100))
    ai_employee = quantize_chf(g * _pct("ai_employee_pct") / Decimal(100))
    apg_employee = quantize_chf(g * _pct("apg_employee_pct") / Decimal(100))

    ac_threshold_monthly = Decimal(str(_extract(rate, "ac_threshold"))) / Decimal(12)

    if g <= ac_threshold_monthly:
        ac_employee = quantize_chf(g * _pct("ac_employee_pct") / Decimal(100))
        ac_solidarity = Decimal("0.00")
    else:
        ac_employee = quantize_chf(ac_threshold_monthly * _pct("ac_employee_pct") / Decimal(100))
        excess = g - ac_threshold_monthly
        solidarity_pct = _pct("ac_solidarity_pct") if _extract(rate, "ac_solidarity_pct") else Decimal(0)
        ac_solidarity = quantize_chf(excess * solidarity_pct / Decimal(100))

    return {
        "ahv_employee": ahv_employee,
        "ai_employee": ai_employee,
        "apg_employee": apg_employee,
        "ac_employee": ac_employee,
        "ac_solidarity": ac_solidarity,
    }


def _extract(rate, key):
    """Récupère un champ depuis dict ou Document."""
    if isinstance(rate, dict):
        return rate.get(key) or 0
    return getattr(rate, key, 0) or 0
