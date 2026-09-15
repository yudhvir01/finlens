# Importing every model here registers it on Base.metadata as a side effect —
# the single place Alembic's env.py and anything needing the full schema
# should import from, instead of importing model modules directly (which,
# combined with app.db.base, is what caused a circular import before).
from app.models.account import Account
from app.models.category import Category
from app.models.transaction import Statement, Transaction
from app.models.user import User

__all__ = ["Account", "Category", "Statement", "Transaction", "User"]
