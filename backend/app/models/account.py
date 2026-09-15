import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class AccountType(str, Enum):
    bank = "bank"
    credit_card = "credit_card"
    wallet = "wallet"


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    institution: Mapped[str | None] = mapped_column(String(255), nullable=True)
    account_type: Mapped[AccountType] = mapped_column(String(20), default=AccountType.bank)
    last_four: Mapped[str | None] = mapped_column(String(4), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="accounts")
    statements: Mapped[list["Statement"]] = relationship(back_populates="account", cascade="all, delete-orphan")
    transactions: Mapped[list["Transaction"]] = relationship(back_populates="account", cascade="all, delete-orphan")
