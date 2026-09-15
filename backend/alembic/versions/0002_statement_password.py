"""add saved statement password to accounts

Revision ID: 0002
Revises: 0001
Create Date: 2026-09-15
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("accounts", sa.Column("statement_password_encrypted", sa.String(500), nullable=True))


def downgrade() -> None:
    op.drop_column("accounts", "statement_password_encrypted")
