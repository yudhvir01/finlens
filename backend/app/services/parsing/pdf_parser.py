import io
import re
from decimal import Decimal, InvalidOperation

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfplumber.utils.exceptions import PdfminerException

from app.services.parsing.common import ParsedTransaction, parse_amount, parse_date
from app.services.parsing.csv_parser import AMOUNT_COLUMNS, CREDIT_COLUMNS, DATE_COLUMNS, DEBIT_COLUMNS, DESC_COLUMNS


class PDFParseError(Exception):
    pass


class PDFPasswordRequired(Exception):
    """Raised when a PDF is encrypted and the given password (if any) didn't open it."""


def _header_index(headers: list[str], candidates: set[str]) -> int | None:
    for i, header in enumerate(headers):
        if (header or "").strip().lower() in candidates:
            return i
    return None


def parse_pdf(content: bytes, password: str = "") -> list[ParsedTransaction]:
    """Best-effort bank statement PDF parser.

    Tries two strategies and keeps whichever finds more transactions:

    1. Real tables (page.extract_tables()) — works for statements that
       render as actual bordered/ruled tables.
    2. Free-text ledger layout — many Indian bank statements have no table
       structure at all: a date on its own line, a wrapped narration
       spanning one or more lines, then "amount   balance   ref" trailing
       the last narration line. There's no separate debit/credit column, so
       the sign is inferred from whether the running balance went up or
       down against the previous transaction.

    Raises PDFPasswordRequired if the PDF is encrypted and `password` (empty
    string if none was supplied) doesn't open it — most Indian bank
    statements are password-protected by default (often PAN + DOB).
    """
    try:
        pdf_context = pdfplumber.open(io.BytesIO(content), password=password)
    except PDFPasswordIncorrect as exc:
        raise PDFPasswordRequired() from exc
    except PdfminerException as exc:
        # pdfplumber wraps every pdfminer error in its own exception type,
        # so the wrong-password case has to be unwrapped to tell it apart
        # from a genuinely corrupt/unsupported PDF.
        if isinstance(exc.args[0] if exc.args else None, PDFPasswordIncorrect):
            raise PDFPasswordRequired() from exc
        raise PDFParseError(f"Couldn't open this PDF: {exc}") from exc

    with pdf_context as pdf:
        pages = pdf.pages
        table_results = _parse_tables(pages)
        freeform_results = _parse_freeform(pages)

    results = freeform_results if len(freeform_results) > len(table_results) else table_results

    if not results:
        raise PDFParseError(
            "Couldn't find any transactions in this PDF. This parser handles statements "
            "with a real table, or a text ledger with a date/narration/amount/balance "
            "layout — scanned or image-only statements aren't supported yet."
        )

    return results


def _parse_tables(pages) -> list[ParsedTransaction]:
    results: list[ParsedTransaction] = []
    header_row: list[str] | None = None
    date_i = desc_i = debit_i = credit_i = amount_i = None

    for page in pages:
        tables = page.extract_tables()
        for table in tables:
            if not table:
                continue
            for row in table:
                cells = [(c or "").strip() for c in row]
                if not any(cells):
                    continue

                if header_row is None:
                    candidate_date_i = _header_index(cells, DATE_COLUMNS)
                    if candidate_date_i is not None:
                        header_row = cells
                        date_i = candidate_date_i
                        desc_i = _header_index(cells, DESC_COLUMNS)
                        debit_i = _header_index(cells, DEBIT_COLUMNS)
                        credit_i = _header_index(cells, CREDIT_COLUMNS)
                        amount_i = _header_index(cells, AMOUNT_COLUMNS)
                        continue

                if date_i is None or date_i >= len(cells):
                    continue

                parsed_date = parse_date(cells[date_i])
                if parsed_date is None:
                    continue

                amount = None
                if amount_i is not None and amount_i < len(cells):
                    amount = parse_amount(cells[amount_i])
                else:
                    debit = parse_amount(cells[debit_i]) if debit_i is not None and debit_i < len(cells) else None
                    credit = parse_amount(cells[credit_i]) if credit_i is not None and credit_i < len(cells) else None
                    if credit:
                        amount = abs(credit)
                    elif debit:
                        amount = -abs(debit)

                if amount is None or amount == 0:
                    continue

                if desc_i is not None and desc_i < len(cells) and cells[desc_i]:
                    description = cells[desc_i]
                else:
                    skip = {date_i, debit_i, credit_i, amount_i}
                    description = " ".join(
                        c for i, c in enumerate(cells) if i not in skip and c
                    ) or "Unknown transaction"

                results.append(ParsedTransaction(date=parsed_date, amount=amount, raw_description=description))

    return results


_DATE_LINE_RE = re.compile(r"^(\d{2}[-/]\d{2}[-/]\d{4})\s*$")
# A trailing "amount   balance   [ref]" at the end of a line — the ref (cheque
# number, last-4-of-something, etc.) is optional and, when present, is not
# itself decimal-formatted, which is what tells it apart from the balance.
_TRAIL_AMOUNT_RE = re.compile(r"(\d[\d,]*\.\d{2})\s+(\d[\d,]*\.\d{2})(?:\s+\S+)?\s*$")
_CREDIT_HINTS = ("salary", "credit", "int.pd", "interest", "refund", "reversal", "cashback")


def _clean_decimal(raw: str) -> Decimal | None:
    try:
        return Decimal(raw.replace(",", ""))
    except InvalidOperation:
        return None


def _parse_freeform(pages) -> list[ParsedTransaction]:
    results: list[ParsedTransaction] = []
    prev_balance: Decimal | None = None
    current_date = None
    narration_lines: list[str] = []

    for page in pages:
        text = page.extract_text() or ""
        for raw_line in text.split("\n"):
            line = raw_line.strip()

            date_match = _DATE_LINE_RE.match(line)
            if date_match:
                current_date = parse_date(date_match.group(1))
                narration_lines = []
                continue

            if current_date is None:
                continue

            trail_match = _TRAIL_AMOUNT_RE.search(line)
            if trail_match:
                amount = _clean_decimal(trail_match.group(1))
                balance = _clean_decimal(trail_match.group(2))
                prefix = line[: trail_match.start()].strip()
                if prefix:
                    narration_lines.append(prefix)

                if amount and amount != 0:
                    if balance is not None and prev_balance is not None:
                        signed_amount = amount if balance > prev_balance else -amount
                    elif balance is not None:
                        # First transaction in the document — no prior balance to
                        # diff against, so fall back to a keyword guess.
                        guess_text = " ".join(narration_lines).lower()
                        signed_amount = amount if any(h in guess_text for h in _CREDIT_HINTS) else -amount
                    else:
                        signed_amount = -amount

                    description = " ".join(narration_lines).strip() or "Unknown transaction"
                    results.append(ParsedTransaction(date=current_date, amount=signed_amount, raw_description=description))

                if balance is not None:
                    prev_balance = balance
                current_date = None
                narration_lines = []
                continue

            if line:
                narration_lines.append(line)

    return results
