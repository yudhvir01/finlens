import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

DATE_FORMATS = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%d-%m-%Y",
    "%m/%d/%Y",
    "%d %b %Y",
    "%d-%b-%Y",
    "%d %B %Y",
    "%d/%m/%y",
    "%d-%m-%y",
]

_AMOUNT_CLEAN_RE = re.compile(r"[^\d.\-]")


@dataclass
class ParsedTransaction:
    date: date
    amount: Decimal  # signed: positive = money in, negative = money out
    raw_description: str


def parse_date(value: str) -> date | None:
    value = value.strip()
    if not value:
        return None
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_amount(value: str) -> Decimal | None:
    """Parses a currency string like "₹1,234.50", "(500.00)", "1234.5 Dr" into a Decimal.

    A value wrapped in parentheses or suffixed with "Dr"/"DR" is treated as negative,
    matching common Indian bank statement conventions.
    """
    if value is None:
        return None
    raw = value.strip()
    if not raw:
        return None

    negative = False
    if raw.startswith("(") and raw.endswith(")"):
        negative = True
        raw = raw[1:-1]
    if re.search(r"\bDr\.?$", raw, re.IGNORECASE):
        negative = True
    if raw.startswith("-"):
        negative = True

    cleaned = _AMOUNT_CLEAN_RE.sub("", raw)
    if not cleaned or cleaned == "-":
        return None

    try:
        amount = Decimal(cleaned)
    except InvalidOperation:
        return None

    amount = abs(amount)
    return -amount if negative else amount
