"""
Phase 27.2 Alembic Migration: Add provider_name and provider_message_id to notifications table
Revision ID: b5683cd19824
Revises: a1367fe18523
Create Date: 2026-09-07
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b5683cd19824'
down_revision: Union[str, None] = 'a1367fe18523'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('notifications', sa.Column('provider_name', sa.String(length=50), nullable=True))
    op.add_column('notifications', sa.Column('provider_message_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('notifications', 'provider_message_id')
    op.drop_column('notifications', 'provider_name')
