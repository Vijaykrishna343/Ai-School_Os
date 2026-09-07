"""Add idempotency_key, retry_count, max_retries to notifications table

Revision ID: z9a045bc06y4
Revises: y8z934ab05x3
Create Date: 2026-08-25 13:30:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "z9a045bc06y4"
down_revision: Union[str, Sequence[str], None] = "y8z934ab05x3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("idempotency_key", sa.String(length=100), nullable=True))
    op.add_column("notifications", sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("notifications", sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"))
    op.create_index(op.f("ix_notifications_idempotency_key"), "notifications", ["idempotency_key"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_notifications_idempotency_key"), table_name="notifications")
    op.drop_column("notifications", "max_retries")
    op.drop_column("notifications", "retry_count")
    op.drop_column("notifications", "idempotency_key")
