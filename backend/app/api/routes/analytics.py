from collections import defaultdict
from datetime import date
from decimal import Decimal

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, joinedload

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.analytics import CategoryBreakdownItem, MonthlyPoint, RecurringItem, SummaryResponse

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _month_bounds(month: str) -> tuple[date, date]:
    year, mon = (int(p) for p in month.split("-"))
    start = date(year, mon, 1)
    end = start + relativedelta(months=1)
    return start, end


def _current_month() -> str:
    today = date.today()
    return f"{today.year:04d}-{today.month:02d}"


def _user_transactions_query(db: Session, user: User):
    return db.query(Transaction).join(Account, Account.id == Transaction.account_id).filter(
        Account.user_id == user.id, Transaction.is_transfer.is_(False)
    )


@router.get("/summary", response_model=SummaryResponse)
def summary(
    month: str = Query(default_factory=_current_month),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start, end = _month_bounds(month)
    rows = _user_transactions_query(db, user).filter(Transaction.date >= start, Transaction.date < end).all()

    income = sum((t.amount for t in rows if t.amount > 0), Decimal("0"))
    expenses = sum((-t.amount for t in rows if t.amount < 0), Decimal("0"))
    net = income - expenses
    savings_rate = float(net / income) if income > 0 else 0.0

    return SummaryResponse(income=income, expenses=expenses, net=net, savings_rate=round(savings_rate, 4))


@router.get("/monthly", response_model=list[MonthlyPoint])
def monthly(
    months: int = Query(6, le=24),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    today = date.today()
    range_start = date(today.year, today.month, 1) - relativedelta(months=months - 1)
    rows = _user_transactions_query(db, user).filter(Transaction.date >= range_start).all()

    buckets: dict[str, dict[str, Decimal]] = defaultdict(lambda: {"income": Decimal("0"), "expenses": Decimal("0")})
    for t in rows:
        key = f"{t.date.year:04d}-{t.date.month:02d}"
        if t.amount > 0:
            buckets[key]["income"] += t.amount
        else:
            buckets[key]["expenses"] += -t.amount

    points: list[MonthlyPoint] = []
    for i in range(months):
        d = range_start + relativedelta(months=i)
        key = f"{d.year:04d}-{d.month:02d}"
        b = buckets.get(key, {"income": Decimal("0"), "expenses": Decimal("0")})
        points.append(MonthlyPoint(month=key, income=b["income"], expenses=b["expenses"], net=b["income"] - b["expenses"]))
    return points


@router.get("/categories", response_model=list[CategoryBreakdownItem])
def categories(
    month: str = Query(default_factory=_current_month),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    start, end = _month_bounds(month)
    rows = (
        _user_transactions_query(db, user)
        .options(joinedload(Transaction.category).joinedload(Category.parent))
        .filter(Transaction.date >= start, Transaction.date < end, Transaction.amount < 0)
        .all()
    )

    totals: dict[str, Decimal] = defaultdict(lambda: Decimal("0"))
    ids: dict[str, object] = {}
    for t in rows:
        if t.category is None:
            name = "Uncategorized"
            cat_id = None
        else:
            top = t.category.parent if t.category.parent is not None else t.category
            name = top.name
            cat_id = top.id
        totals[name] += -t.amount
        ids[name] = cat_id

    grand_total = sum(totals.values(), Decimal("0"))
    items = [
        CategoryBreakdownItem(
            category_id=ids[name],
            category_name=name,
            total=total,
            percentage=round(float(total / grand_total) * 100, 1) if grand_total > 0 else 0.0,
            color=None,
        )
        for name, total in totals.items()
    ]
    items.sort(key=lambda i: i.total, reverse=True)
    return items


@router.get("/recurring", response_model=list[RecurringItem])
def recurring(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    rows = (
        _user_transactions_query(db, user)
        .options(joinedload(Transaction.category))
        .filter(Transaction.amount < 0, Transaction.merchant.isnot(None))
        .all()
    )

    by_merchant: dict[str, list[Transaction]] = defaultdict(list)
    for t in rows:
        by_merchant[t.merchant].append(t)

    items: list[RecurringItem] = []
    for merchant, txns in by_merchant.items():
        distinct_months = {(t.date.year, t.date.month) for t in txns}
        if len(distinct_months) < 2:
            continue
        amounts = [-t.amount for t in txns]
        avg_amount = sum(amounts, Decimal("0")) / len(amounts)
        category_name = txns[-1].category.name if txns[-1].category else None
        items.append(
            RecurringItem(
                merchant=merchant,
                average_amount=round(avg_amount, 2),
                occurrences=len(distinct_months),
                category_name=category_name,
            )
        )

    items.sort(key=lambda i: i.average_amount, reverse=True)
    return items
