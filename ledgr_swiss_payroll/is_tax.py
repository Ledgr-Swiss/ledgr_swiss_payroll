"""IS (impôt à la source) calculator — in-memory lookup from ESTV tariff files.

Loads ESTV fixed-width TXT files (tar{YY}{kt}.txt) shipped with the app.
Binary search finds the bracket for a given (canton, code, monthly_revenue).
Files are parsed once per (canton, year) and cached in memory.

Record format (Recordart 06, positions 1-indexed):
  01-02  record type (06)
  03-04  transaction (01=new)
  05-06  canton
  07-16  QSt code (10 chars padded)
  17-24  valid from YYYYMMDD
  25-33  income from (9 digits, last 2 = centimes)
  34-42  tariff step (9 digits, last 2 = centimes)
  43     sex (space)
  44-45  children (2 digits)
  46-54  min tax (9 digits, last 2 = centimes)
  55-59  tax rate (5 digits, last 2 = decimals, i.e. 00715 = 7.15%)
  60-62  status (space)
"""
import bisect
from datetime import date
from decimal import Decimal, ROUND_HALF_EVEN
from pathlib import Path

from ledgr_swiss_payroll.exceptions import ISBracketNotFound

DATA_DIR = Path(__file__).parent / "data" / "is-baremes"

_tariff_cache: dict[tuple[str, int], dict[str, list[tuple[int, int, int, int]]]] = {}


def _parse_tariff_file(file_path: Path) -> dict[str, list[tuple[int, int, int, int]]]:
    tariffs: dict[str, list[tuple[int, int, int, int]]] = {}
    with open(file_path, "r", encoding="latin-1") as f:
        for line in f:
            if len(line.rstrip()) < 59 or line[0:2] != "06":
                continue
            code = line[6:16].strip()
            income_from = int(line[24:33])
            step = int(line[33:42])
            min_tax = int(line[45:54])
            rate = int(line[54:59])
            if code not in tariffs:
                tariffs[code] = []
            tariffs[code].append((income_from, step, min_tax, rate))
    for code in tariffs:
        tariffs[code].sort()
    return tariffs


def _get_tariffs(canton: str, year: int) -> dict[str, list[tuple[int, int, int, int]]]:
    cache_key = (canton.upper(), year)
    if cache_key not in _tariff_cache:
        yy = str(year)[2:]
        file_path = DATA_DIR / str(year) / f"tar{yy}{canton.lower()}.txt"
        if not file_path.exists():
            raise ISBracketNotFound(canton, "?", Decimal(0), date(year, 1, 1))
        _tariff_cache[cache_key] = _parse_tariff_file(file_path)
    return _tariff_cache[cache_key]


def compute_is(
    canton: str, tax_code: str, monthly_revenue: Decimal, slip_date: date
) -> Decimal:
    """Compute IS withholding tax.

    Args:
        canton: 2-letter canton code (e.g. "VD")
        tax_code: ESTV tariff code (e.g. "A0N", "B2Y", "H1N")
        monthly_revenue: gross monthly income in CHF
        slip_date: date of the salary slip (determines tariff year)

    Returns:
        Tax amount in CHF, rounded to centime (ROUND_HALF_EVEN).
        Swiss 0.05 rounding is NOT applied here (done at slip level).

    Raises:
        ISBracketNotFound: no matching bracket for the given parameters.
    """
    tariffs = _get_tariffs(canton, slip_date.year)

    if tax_code not in tariffs:
        raise ISBracketNotFound(canton, tax_code, monthly_revenue, slip_date)

    brackets = tariffs[tax_code]
    rev_ct = int(monthly_revenue * 100)

    starts = [b[0] for b in brackets]
    idx = bisect.bisect_right(starts, rev_ct) - 1
    if idx < 0:
        raise ISBracketNotFound(canton, tax_code, monthly_revenue, slip_date)

    income_from, step, min_tax_ct, rate_100 = brackets[idx]

    if rev_ct > income_from + step - 1:
        raise ISBracketNotFound(canton, tax_code, monthly_revenue, slip_date)

    rate = Decimal(rate_100) / Decimal(10000)
    tax_by_rate = (monthly_revenue * rate).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_EVEN
    )
    min_tax = Decimal(min_tax_ct) / Decimal(100)

    return max(tax_by_rate, min_tax)


def clear_cache():
    """Clear tariff cache (useful for testing)."""
    _tariff_cache.clear()
