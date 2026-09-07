"""create ai foundation tables

Revision ID: a1f0u2n3d4a5
Revises: v5w611xy82u1
Create Date: 2026-08-26 19:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1f0u2n3d4a5'
down_revision = 'v5w611xy82u1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. ai_provider_configs
    op.create_table(
        'ai_provider_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('provider_type', sa.String(length=50), nullable=False, server_default='MOCK'),
        sa.Column('model_name', sa.String(length=100), nullable=True, server_default='mock-default-v1'),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('allow_external_ai', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_provider_configs_school_id'), 'ai_provider_configs', ['school_id'], unique=False)

    # 2. ai_audit_logs
    op.create_table(
        'ai_audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('capability', sa.String(length=50), nullable=False),
        sa.Column('provider_type', sa.String(length=50), nullable=False),
        sa.Column('model_name', sa.String(length=100), nullable=True),
        sa.Column('prompt_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_tokens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('estimated_cost_usd', sa.Numeric(precision=10, scale=6), nullable=False, server_default='0.0'),
        sa.Column('latency_ms', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='SUCCESS'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['identity_users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_ai_audit_logs_capability'), 'ai_audit_logs', ['capability'], unique=False)
    op.create_index(op.f('ix_ai_audit_logs_school_id'), 'ai_audit_logs', ['school_id'], unique=False)
    op.create_index(op.f('ix_ai_audit_logs_user_id'), 'ai_audit_logs', ['user_id'], unique=False)

    # 3. ai_usage_limits
    op.create_table(
        'ai_usage_limits',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('monthly_token_quota', sa.Integer(), nullable=False, server_default='1000000'),
        sa.Column('used_tokens_current_month', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quota_reset_date', sa.Date(), nullable=False),
        sa.Column('is_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('now()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id')
    )
    op.create_index(op.f('ix_ai_usage_limits_school_id'), 'ai_usage_limits', ['school_id'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_ai_usage_limits_school_id'), table_name='ai_usage_limits')
    op.drop_table('ai_usage_limits')
    op.drop_index(op.f('ix_ai_audit_logs_user_id'), table_name='ai_audit_logs')
    op.drop_index(op.f('ix_ai_audit_logs_school_id'), table_name='ai_audit_logs')
    op.drop_index(op.f('ix_ai_audit_logs_capability'), table_name='ai_audit_logs')
    op.drop_table('ai_audit_logs')
    op.drop_index(op.f('ix_ai_provider_configs_school_id'), table_name='ai_provider_configs')
    op.drop_table('ai_provider_configs')
