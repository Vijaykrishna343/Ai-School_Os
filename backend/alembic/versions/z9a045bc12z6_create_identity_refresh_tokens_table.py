"""create_identity_refresh_tokens_table

Revision ID: z9a045bc12z6
Revises: z9a045bc11z5
Create Date: 2026-09-22 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc12z6'
down_revision: Union[str, Sequence[str], None] = 'z9a045bc11z5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'identity_refresh_tokens',
        sa.Column('id', sa.UUID(), primary_key=True, nullable=False),
        sa.Column('school_id', sa.UUID(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.UUID(), sa.ForeignKey('identity_users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('jti', sa.String(length=64), nullable=False),
        sa.Column('token_hash', sa.String(length=128), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('revocation_reason', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
    )
    op.create_index('ix_identity_refresh_tokens_school_id', 'identity_refresh_tokens', ['school_id'])
    op.create_index('ix_identity_refresh_tokens_user_id', 'identity_refresh_tokens', ['user_id'])
    op.create_index('ix_identity_refresh_tokens_jti', 'identity_refresh_tokens', ['jti'], unique=True)
    op.create_index('ix_identity_refresh_tokens_token_hash', 'identity_refresh_tokens', ['token_hash'])
    op.create_index('ix_identity_refresh_tokens_expires_at', 'identity_refresh_tokens', ['expires_at'])
    op.create_index('ix_identity_refresh_tokens_is_revoked', 'identity_refresh_tokens', ['is_revoked'])


def downgrade() -> None:
    op.drop_index('ix_identity_refresh_tokens_is_revoked', table_name='identity_refresh_tokens')
    op.drop_index('ix_identity_refresh_tokens_expires_at', table_name='identity_refresh_tokens')
    op.drop_index('ix_identity_refresh_tokens_token_hash', table_name='identity_refresh_tokens')
    op.drop_index('ix_identity_refresh_tokens_jti', table_name='identity_refresh_tokens')
    op.drop_index('ix_identity_refresh_tokens_user_id', table_name='identity_refresh_tokens')
    op.drop_index('ix_identity_refresh_tokens_school_id', table_name='identity_refresh_tokens')
    op.drop_table('identity_refresh_tokens')
