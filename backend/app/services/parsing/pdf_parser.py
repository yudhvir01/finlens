import io

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

    Works well for statements that render as real tables (most net-banking
    exports). Statements that are scanned images, or lay out transactions as
    free text rather than a table, will need a bank-specific parser — this is
    a starting point, not a universal solution.

    Raises PDFPasswordRequired if the PDF is encrypted and `password` (empty
    string if none was supplied) doesn't open it — most Indian bank
    statements are password-protected by default (often PAN + DOB).
    """
    results: list[ParsedTransaction] = []

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
        header_row: list[str] | None = None
        date_i = desc_i = debit_i = credit_i = amount_i = None

        for page in pdf.pages:
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

    if not results:
        raise PDFParseError(
            "Couldn't detect any transaction table in this PDF. This parser handles "
            "statements with a real tabular layout — scanned or image-only statements "
            "aren't supported yet."
        )

    return results
