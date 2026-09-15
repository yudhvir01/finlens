import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.user import User
from app.schemas.transaction import AccountCreate, AccountResponse

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


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


@router.delete("/{account_id}", status_code=204)
def delete_account(account_id: uuid.UUID, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    account = db.query(Account).filter(Account.id == account_id, Account.user_id == user.id).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    db.delete(account)
    db.commit()
