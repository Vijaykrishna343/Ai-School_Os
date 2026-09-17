"""widen_notification_idempotency_key_to_255

Revision ID: 7aaaba637c7f
Revises: b5683cd19824
Create Date: 2026-09-08 22:59:29.931795

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '7aaaba637c7f'
down_revision: Union[str, Sequence[str], None] = 'b5683cd19824'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Widen notifications.idempotency_key from VARCHAR(100) to VARCHAR(255).

    Composite idempotency keys such as
    'homework_published:{hw_uuid}:student:{student_uuid}:in_app'
    exceed the previous 100-char limit (they are ~109 chars).
    """
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.alter_column(
            'idempotency_key',
            existing_type=sa.VARCHAR(length=100),
            type_=sa.String(length=255),
            existing_nullable=True,
        )


def downgrade() -> None:
    """Narrow notifications.idempotency_key back to VARCHAR(100)."""
    with op.batch_alter_table('notifications', schema=None) as batch_op:
        batch_op.alter_column(
            'idempotency_key',
            existing_type=sa.String(length=255),
            type_=sa.VARCHAR(length=100),
            existing_nullable=True,
        )
