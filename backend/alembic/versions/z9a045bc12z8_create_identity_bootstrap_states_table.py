"""create_identity_bootstrap_states_table

Revision ID: z9a045bc12z8
Revises: z9a045bc12z7
Create Date: 2026-09-23 20:30:00.000000

"""
from typing import Sequence, Union
import uuid

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc12z8'
down_revision: Union[str, Sequence[str], None] = 'z9a045bc12z7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    table = op.create_table(
        'identity_bootstrap_states',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('scope', sa.String(length=50), nullable=False),
        sa.Column('is_completed', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_by_id', sa.UUID(), sa.ForeignKey('identity_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )
    op.create_index('ix_identity_bootstrap_states_scope', 'identity_bootstrap_states', ['scope'], unique=True)

    # Backfill platform bootstrap state based on existing user population
    conn = op.get_bind()
    user_count = conn.execute(sa.text("SELECT COUNT(*) FROM identity_users WHERE is_deleted = false")).scalar() or 0
    is_completed = user_count > 0

    conn.execute(
        sa.text(
            """
            INSERT INTO identity_bootstrap_states (id, scope, is_completed, completed_at, created_at, updated_at, is_deleted)
            VALUES (:id, 'platform', :is_completed, CASE WHEN :is_completed THEN CURRENT_TIMESTAMP ELSE NULL END, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, false)
            ON CONFLICT (scope) DO NOTHING
            """
        ),
        {"id": uuid.uuid4(), "is_completed": is_completed}
    )


def downgrade() -> None:
    op.drop_index('ix_identity_bootstrap_states_scope', table_name='identity_bootstrap_states')
    op.drop_table('identity_bootstrap_states')
