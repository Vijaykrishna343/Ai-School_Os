"""add school_status enum values

Revision ID: v5w611xy82u0
Revises: v5w611xy81u9
Create Date: 2026-08-21 11:00:00.000000

"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "v5w611xy82u0"
down_revision = "v5w611xy81u9"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add missing enum values to PostgreSQL school_status enum type safely
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        enum_values = ["TRIAL", "PAYMENT_DUE", "GRACE_PERIOD", "SUSPENDED", "BLOCKED", "CANCELLED"]
        for val in enum_values:
            bind.execute(sa.text(f"ALTER TYPE school_status ADD VALUE IF NOT EXISTS '{val}';"))


def downgrade() -> None:
    pass
