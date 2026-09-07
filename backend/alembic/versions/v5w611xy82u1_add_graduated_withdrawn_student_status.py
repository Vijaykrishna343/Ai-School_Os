"""add graduated and withdrawn to student_status enum

Revision ID: v5w611xy82u1
Revises: 76666b50cdbf
Create Date: 2026-08-26 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision = "v5w611xy82u1"
down_revision = "76666b50cdbf"
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        enum_values = ["GRADUATED", "WITHDRAWN"]
        for val in enum_values:
            bind.execute(sa.text(f"ALTER TYPE student_status ADD VALUE IF NOT EXISTS '{val}';"))

def downgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "postgresql":
        # Safe drop and recreate strategy
        bind.execute(sa.text("ALTER TYPE student_status RENAME TO student_status_old;"))
        bind.execute(sa.text("CREATE TYPE student_status AS ENUM ('ACTIVE', 'INACTIVE', 'TRANSFERRED', 'PASSED_OUT', 'DROPPED');"))
        bind.execute(sa.text("ALTER TABLE students ALTER COLUMN status TYPE student_status USING status::text::student_status;"))
        bind.execute(sa.text("DROP TYPE student_status_old;"))
