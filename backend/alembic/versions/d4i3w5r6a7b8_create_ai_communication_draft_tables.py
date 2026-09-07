"""create ai communication draft tables

Revision ID: d4i3w5r6a7b8
Revises: c3h2w4r5a6b7
Create Date: 2026-09-02 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'd4i3w5r6a7b8'
down_revision: Union[str, None] = 'c3h2w4r5a6b7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_communication_drafts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('created_by_user_id', sa.UUID(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=False, server_default='ANNOUNCEMENT'),
        sa.Column('target_audience', sa.String(length=50), nullable=False, server_default='PARENTS'),
        sa.Column('tone', sa.String(length=30), nullable=False, server_default='FORMAL'),
        sa.Column('prompt_summary', sa.Text(), nullable=False),
        sa.Column('channel_variants', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('pii_redact_log', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('token_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_comm_school_category', 'ai_communication_drafts', ['school_id', 'category'])
    op.create_index('idx_ai_comm_school_created', 'ai_communication_drafts', ['school_id', 'created_at'])


def downgrade() -> None:
    op.drop_index('idx_ai_comm_school_created', table_name='ai_communication_drafts')
    op.drop_index('idx_ai_comm_school_category', table_name='ai_communication_drafts')
    op.drop_table('ai_communication_drafts')
