"""add_start_end_date_reason_to_enrollment_history

Revision ID: m1q165rs25o2
Revises: l8p054qr14n1
Create Date: 2026-08-12 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'm1q165rs25o2'
down_revision: Union[str, Sequence[str], None] = 'l8p054qr14n1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student_enrollment_histories', sa.Column('start_date', sa.Date(), nullable=True))
    op.add_column('student_enrollment_histories', sa.Column('end_date', sa.Date(), nullable=True))
    op.add_column('student_enrollment_histories', sa.Column('reason', sa.String(length=255), nullable=True))


def downgrade() -> None:
    op.drop_column('student_enrollment_histories', 'reason')
    op.drop_column('student_enrollment_histories', 'end_date')
    op.drop_column('student_enrollment_histories', 'start_date')
