import uuid
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    parent_id: uuid.UUID | None
    icon: str | None
    color: str | None

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    date: date
    amount: Decimal
    raw_description: str
    merchant: str | None
    category: CategoryResponse | None
    is_transfer: bool
    is_refund: bool
    is_recurring: bool

    class Config:
        from_attributes = True


class TransactionUpdate(BaseModel):
    category_id: uuid.UUID | None = None
    is_transfer: bool | None = None
    is_refund: bool | None = None
    merchant: str | None = None


class AccountResponse(BaseModel):
    id: uuid.UUID
    name: str
    institution: str | None
    account_type: str
    last_four: str | None

    class Config:
        from_attributes = True


class AccountCreate(BaseModel):
    name: str
    institution: str | None = None
    account_type: str = "bank"
    last_four: str | None = None


class StatementResponse(BaseModel):
    id: uuid.UUID
    account_id: uuid.UUID
    filename: str
    status: str
    error_message: str | None
    transaction_count: int
    period_start: date | None
    period_end: date | None

    class Config:
        from_attributes = True
