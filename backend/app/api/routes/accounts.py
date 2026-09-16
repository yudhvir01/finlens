import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.crypto import decrypt_secret, encrypt_secret
from app.db.session import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.transaction import AccountCreate, AccountResponse, AccountUpdate, StatementPasswordResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


def _get_owned_account(db: Session, account_id: uuid.UUID, user: User) -> Account:
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return account


@router.get("", response_model=list[AccountResponse])
def list_accounts(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Account).filter(Account.user_id == user.id).order_by(Account.created_at).all()


@router.post("", response_model=AccountResponse, status_code=201)
def create_account(payload: AccountCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = Account(user_id=user.id, **payload.model_dump())
    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.patch("/{account_id}", response_model=AccountResponse)
def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    account = _get_owned_account(db, account_id, user)
    updates = payload.model_dump(exclude_unset=True)

    if "statement_password" in updates:
        new_password = updates.pop("statement_password")
        account.statement_password_encrypted = encrypt_secret(new_password) if new_password else None

    for field, value in updates.items():
        setattr(account, field, value)

    db.add(account)
    db.commit()
    db.refresh(account)
    return account


@router.get("/{account_id}/statement-password", response_model=StatementPasswordResponse)
def get_statement_password(account_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = _get_owned_account(db, account_id, user)
    if not account.statement_password_encrypted:
        return StatementPasswordResponse(password=None)
    return StatementPasswordResponse(password=decrypt_secret(account.statement_password_encrypted))


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = _get_owned_account(db, account_id, user)
    db.delete(account)
    db.commit()
