import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.transaction import Statement, StatementStatus
from app.models.user import User
from app.schemas.transaction import StatementResponse
from app.services.ingestion import ingest_statement

router = APIRouter(prefix="/api", tags=["statements"])

MAX_UPLOAD_BYTES = 15 * 1024 * 1024


def _get_owned_account(db: Session, account_id: uuid.UUID, user: User) -> Account:
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.post("/accounts/{account_id}/statements", response_model=StatementResponse, status_code=201)
async def upload_statement(
    account_id: uuid.UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = _get_owned_account(db, account_id, user)

    content = await file.read()
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File is too large (15MB limit)")

    statement = Statement(
        account_id=account.id,
        filename=file.filename or "statement",
        status=StatementStatus.processing,
    )
    db.add(statement)
    db.commit()
    db.refresh(statement)

    # Synchronous for the MVP — statements are small enough to parse inline.
    # A production build would enqueue this onto the Redis/RQ worker instead.
    ingest_statement(db, statement, statement.filename, content)
    db.refresh(statement)
    return statement


@router.get("/statements", response_model=list[StatementResponse])
def list_statements(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Statement)
        .join(Account, Account.id == Statement.account_id)
        .filter(Account.user_id == user.id)
        .order_by(Statement.uploaded_at.desc())
        .all()
    )
