import logging
import uuid
from datetime import date as date_

from sqlalchemy.orm import Session

from app.core.crypto import decrypt_secret, encrypt_secret
from app.models.transaction import Statement, StatementStatus, Transaction
from app.services.categorize import suggest_category
from app.services.category_repo import get_uncategorized, load_system_category_map
from app.services.normalize import clean_merchant, looks_like_transfer
from app.services.parsing.csv_parser import CSVParseError, parse_csv
from app.services.parsing.pdf_parser import PDFParseError, PDFPasswordRequired, parse_pdf

logger = logging.getLogger(__name__)


class UnsupportedFileType(Exception):
    pass


def ingest_statement(
    db: Session,
    statement: Statement,
    filename: str,
    content: bytes,
    password: str | None = None,
    remember_password: bool = True,
) -> None:
    """Never lets an exception escape to the caller — a statement always ends
    up as done/failed/password_required, never stuck at "processing" with the
    request itself crashing (that used to be possible: an unhandled parsing
    error would 500 the whole upload request after the row was already
    created, leaving it stuck forever with no way to retry).
    """
    try:
        _ingest_statement(db, statement, filename, content, password, remember_password)
    except PDFPasswordRequired:
        account = statement.account
        db.rollback()
        statement.status = StatementStatus.password_required
        statement.error_message = (
            "This PDF didn't unlock with the saved password — enter the current one."
            if password is None and account.statement_password_encrypted
            else "This PDF is password protected."
        )
        db.add(statement)
        db.commit()
    except (CSVParseError, PDFParseError, UnsupportedFileType) as exc:
        db.rollback()
        statement.status = StatementStatus.failed
        statement.error_message = str(exc)
        db.add(statement)
        db.commit()
    except Exception:
        logger.exception("Unexpected error ingesting statement %s", statement.id)
        db.rollback()
        statement.status = StatementStatus.failed
        statement.error_message = "Something went wrong parsing this file. Try again, or a different export format."
        db.add(statement)
        db.commit()


def _ingest_statement(
    db: Session,
    statement: Statement,
    filename: str,
    content: bytes,
    password: str | None,
    remember_password: bool,
) -> None:
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    account = statement.account

    if extension == "csv":
        parsed = parse_csv(content)
    elif extension == "pdf":
        parsed = _parse_pdf_with_password(db, account, content, password, remember_password)
    else:
        raise UnsupportedFileType(f"Unsupported file type: .{extension}. Upload a CSV or PDF statement.")

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


def _parse_pdf_with_password(db: Session, account, content: bytes, password: str | None, remember_password: bool):
    """Tries, in order: an explicitly-given password, then the account's saved
    one. On success with a freshly-given password, remembers it (encrypted)
    on the account for next time. Raises PDFPasswordRequired if neither works.
    """
    if password:
        parsed = parse_pdf(content, password=password)
        if remember_password:
            account.statement_password_encrypted = encrypt_secret(password)
            db.add(account)
        return parsed

    saved = decrypt_secret(account.statement_password_encrypted) if account.statement_password_encrypted else None
    return parse_pdf(content, password=saved or "")
