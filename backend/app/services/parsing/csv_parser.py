import csv
import io

from app.services.parsing.common import ParsedTransaction, parse_amount, parse_date

DATE_COLUMNS = {"date", "transaction date", "txn date", "value date", "posting date", "tran date"}
DESC_COLUMNS = {"description", "narration", "particulars", "details", "transaction details", "remarks", "transaction remarks"}
DEBIT_COLUMNS = {"debit", "withdrawal", "withdrawal amt", "withdrawal amt.", "debit amount", "dr"}
CREDIT_COLUMNS = {"credit", "deposit", "deposit amt", "deposit amt.", "credit amount", "cr"}
AMOUNT_COLUMNS = {"amount", "transaction amount"}


def _match_column(headers: list[str], candidates: set[str]) -> str | None:
    for header in headers:
        if header.strip().lower() in candidates:
            return header
    return None


class CSVParseError(Exception):
    pass


def parse_csv(content: bytes) -> list[ParsedTransaction]:
    text = content.decode("utf-8-sig", errors="replace")
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise CSVParseError("Could not find a header row in this CSV file")

    headers = list(reader.fieldnames)
    date_col = _match_column(headers, DATE_COLUMNS)
    desc_col = _match_column(headers, DESC_COLUMNS)
    debit_col = _match_column(headers, DEBIT_COLUMNS)
    credit_col = _match_column(headers, CREDIT_COLUMNS)
    amount_col = _match_column(headers, AMOUNT_COLUMNS)

    if date_col is None:
        raise CSVParseError(
            "Couldn't find a date column. Expected one of: " + ", ".join(sorted(DATE_COLUMNS))
        )
    if amount_col is None and debit_col is None and credit_col is None:
        raise CSVParseError(
            "Couldn't find an amount column (either a single 'Amount' column, "
            "or separate 'Debit'/'Credit' columns)."
        )

    results: list[ParsedTransaction] = []
    for row in reader:
        raw_date = row.get(date_col, "") or ""
        parsed_date = parse_date(raw_date)
        if parsed_date is None:
            continue

        amount = None
        if amount_col:
            amount = parse_amount(row.get(amount_col, ""))
        else:
            debit = parse_amount(row.get(debit_col, "")) if debit_col else None
            credit = parse_amount(row.get(credit_col, "")) if credit_col else None
            if credit:
                amount = abs(credit)
            elif debit:
                amount = -abs(debit)

        if amount is None or amount == 0:
            continue

        description_parts = []
        if desc_col:
            description_parts.append(row.get(desc_col, "") or "")
        else:
            # No recognizable description column — fall back to every column
            # that isn't the date/amount columns, joined together.
            used = {date_col, debit_col, credit_col, amount_col}
            for header in headers:
                if header not in used:
                    value = (row.get(header) or "").strip()
                    if value:
                        description_parts.append(value)

        description = " ".join(p.strip() for p in description_parts if p.strip()) or "Unknown transaction"

        results.append(ParsedTransaction(date=parsed_date, amount=amount, raw_description=description))

    return results
