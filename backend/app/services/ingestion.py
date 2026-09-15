import uuid
from datetime import date as date_

from sqlalchemy.orm import Session

from app.models.transaction import Statement, StatementStatus, Transaction
from app.services.categorize import suggest_category
from app.services.category_repo import get_uncategorized, load_system_category_map
from app.services.normalize import clean_merchant, looks_like_transfer
from app.services.parsing.csv_parser import CSVParseError, parse_csv
from app.services.parsing.pdf_parser import PDFParseError, parse_pdf


class UnsupportedFileType(Exception):
    pass


def ingest_statement(db: Session, statement: Statement, filename: str, content: bytes) -> None:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    try:
        if extension == "csv":
            parsed = parse_csv(content)
        elif extension == "pdf":
            parsed = parse_pdf(content)
        else:
            raise UnsupportedFileType(f"Unsupported file type: .{extension}. Upload a CSV or PDF statement.")
    except (CSVParseError, PDFParseError, UnsupportedFileType) as exc:
        statement.status = StatementStatus.failed
        statement.error_message = str(exc)
        db.add(statement)
        db.commit()
        return

    category_map = load_system_category_map(db)
    uncategorized = get_uncategorized(db)

    dates: list[date_] = []
    for item in parsed:
        merchant = clean_merchant(item.raw_description)
        is_transfer = looks_like_transfer(item.raw_description)

        category = None
        confidence = None
        suggestion = suggest_category(merchant, item.raw_description, item.amount)
        if suggestion:
            parent_name, child_name, confidence = suggestion
            category = category_map.get((parent_name, child_name))
        if category is None and not is_transfer:
            category = uncategorized

        transaction = Transaction(
            id=uuid.uuid4(),
            account_id=statement.account_id,
            statement_id=statement.id,
            category_id=category.id if category else None,
            date=item.date,
            amount=item.amount,
            raw_description=item.raw_description,
            merchant=merchant,
            is_transfer=is_transfer,
            category_confidence=confidence,
        )
        db.add(transaction)
        dates.append(item.date)

    statement.status = StatementStatus.done
    statement.transaction_count = len(parsed)
    if dates:
        statement.period_start = min(dates)
        statement.period_end = max(dates)
    db.add(statement)
    db.commit()
