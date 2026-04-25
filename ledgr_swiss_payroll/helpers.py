"""Helpers — arithmetic et arrondis paie."""
from decimal import Decimal, ROUND_HALF_EVEN


def quantize_chf(amount):
    """Arrondi au centime CHF (ROUND_HALF_EVEN).

    Différent de ledgr_core.utils.round_chf qui arrondit à 0.05 CHF (factures).
    """
    return Decimal(amount).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
