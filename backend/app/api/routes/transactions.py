import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import CategoryResponse, TransactionResponse, TransactionUpdate

router = APIRouter(prefix="/api", tags=["transactions"])


@router.get("/transactions", response_model=list[TransactionResponse])
def list_transactions(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    account_id: uuid.UUID | None = None,
    category_id: uuid.UUID | None = None,
    search: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    is_transfer: bool | None = None,
    limit: int = Query(100, le=500),
    offset: int = 0,
):
    q = (
        db.query(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .options(joinedload(Transaction.category))
        .filter(Account.user_id == user.id)
    )
    if account_id:
        q = q.filter(Transaction.account_id == account_id)
    if category_id:
        q = q.filter(Transaction.category_id == category_id)
    if search:
        like = f"%{search}%"
        q = q.filter(or_(Transaction.merchant.ilike(like), Transaction.raw_description.ilike(like)))
    if date_from:
        q = q.filter(Transaction.date >= date_from)
    if date_to:
        q = q.filter(Transaction.date <= date_to)
    if is_transfer is not None:
        q = q.filter(Transaction.is_transfer == is_transfer)

    return q.order_by(Transaction.date.desc(), Transaction.created_at.desc()).offset(offset).limit(limit).all()


@router.patch("/transactions/{transaction_id}", response_model=TransactionResponse)
def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    transaction = (
        db.query(Transaction)
        .join(Account, Account.id == Transaction.account_id)
        .filter(Transaction.id == transaction_id, Account.user_id == user.id)
        .first()
    )
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    updates = payload.model_dump(exclude_unset=True)
    if "category_id" in updates and updates["category_id"] is not None:
        category = db.get(Category, updates["category_id"])
        if not category:
            raise HTTPException(status_code=400, detail="Category not found")
        # A manual correction is a ground-truth signal — mark full confidence.
        transaction.category_confidence = 1.0

    for field, value in updates.items():
        setattr(transaction, field, value)

    db.add(transaction)
    db.commit()
    db.refresh(transaction)
    return transaction


@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return (
        db.query(Category)
        .filter(or_(Category.is_system.is_(True), Category.user_id == user.id))
        .order_by(Category.name)
        .all()
    )
