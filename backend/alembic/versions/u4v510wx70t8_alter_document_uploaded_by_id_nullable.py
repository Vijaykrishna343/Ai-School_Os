"""
Alter documents.uploaded_by_id to nullable (Phase 24.5 Remediation).

Revision ID: u4v510wx70t8
Revises: t3u409vw69s7
Create Date: 2026-08-20 12:25:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'u4v510wx70t8'
down_revision: Union[str, None] = 't3u409vw69s7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Alter documents.uploaded_by_id column to nullable=True."""
    with op.batch_alter_table('documents') as batch_op:
        batch_op.alter_column('uploaded_by_id', existing_type=sa.UUID(), nullable=True)


def downgrade() -> None:
    """
    Revert documents.uploaded_by_id column to nullable=False.
    
    Precondition Warning: Downgrading requires that no records have uploaded_by_id IS NULL.
    """
    with op.batch_alter_table('documents') as batch_op:
        batch_op.alter_column('uploaded_by_id', existing_type=sa.UUID(), nullable=False)
