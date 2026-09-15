import uuid
from decimal import Decimal

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    income: Decimal
    expenses: Decimal
    net: Decimal
    savings_rate: float


class MonthlyPoint(BaseModel):
    month: str  # "2026-09"
    income: Decimal
    expenses: Decimal
    net: Decimal


class CategoryBreakdownItem(BaseModel):
    category_id: uuid.UUID | None
    category_name: str
    total: Decimal
    percentage: float
    color: str | None


class RecurringItem(BaseModel):
    merchant: str
    average_amount: Decimal
    occurrences: int
    category_name: str | None
