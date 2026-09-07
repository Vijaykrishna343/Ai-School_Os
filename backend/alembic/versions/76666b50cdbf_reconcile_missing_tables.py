"""reconcile missing tables

Revision ID: 76666b50cdbf
Revises: a0b156cd07z5
Create Date: 2026-08-25 22:08:01.620780

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '76666b50cdbf'
down_revision: Union[str, Sequence[str], None] = 'a0b156cd07z5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. background_jobs table
    op.create_table('background_jobs',
    sa.Column('school_id', sa.UUID(), nullable=False),
    sa.Column('created_by_user_id', sa.UUID(), nullable=False),
    sa.Column('job_type', sa.Enum('BATCH_REPORT_CARD_GEN', 'BULK_NOTIFICATION_DISPATCH', 'BULK_STUDENT_IMPORT', name='jobtype', native_enum=False), nullable=False),
    sa.Column('status', sa.Enum('QUEUED', 'PROCESSING', 'COMPLETED', 'FAILED', 'CANCELLED', name='jobstatus', native_enum=False), nullable=False),
    sa.Column('progress_percentage', sa.Integer(), nullable=False),
    sa.Column('processed_items', sa.Integer(), nullable=False),
    sa.Column('total_items', sa.Integer(), nullable=False),
    sa.Column('payload', sa.JSON(), nullable=False),
    sa.Column('result', sa.JSON(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('idempotency_key', sa.String(length=100), nullable=True),
    sa.Column('retry_count', sa.Integer(), nullable=False),
    sa.Column('max_retries', sa.Integer(), nullable=False),
    sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['created_by_user_id'], ['identity_users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('background_jobs', schema=None) as batch_op:
        batch_op.create_index('ix_background_jobs_idempotency', ['idempotency_key'], unique=True)
        batch_op.create_index('ix_background_jobs_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_background_jobs_status', ['status'], unique=False)
        batch_op.create_index('ix_background_jobs_type', ['job_type'], unique=False)

    # 2. cash_sessions table
    op.create_table('cash_sessions',
    sa.Column('school_id', sa.UUID(), nullable=False),
    sa.Column('opened_by_user_id', sa.UUID(), nullable=False),
    sa.Column('closed_by_user_id', sa.UUID(), nullable=True),
    sa.Column('session_date', sa.Date(), nullable=False),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('opening_balance', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('expected_cash_collected', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('expected_non_cash_collected', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('actual_counted_cash', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('variance', sa.Numeric(precision=12, scale=2), nullable=True),
    sa.Column('notes', sa.String(length=500), nullable=True),
    sa.Column('opened_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('closed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('is_deleted', sa.Boolean(), nullable=False),
    sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    sa.ForeignKeyConstraint(['closed_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
    sa.ForeignKeyConstraint(['opened_by_user_id'], ['identity_users.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('cash_sessions', schema=None) as batch_op:
        batch_op.create_index('ix_cash_sessions_opened_by', ['opened_by_user_id'], unique=False)
        batch_op.create_index('ix_cash_sessions_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_cash_sessions_session_date', ['session_date'], unique=False)
        batch_op.create_index('ix_cash_sessions_status', ['status'], unique=False)


def downgrade() -> None:
    with op.batch_alter_table('cash_sessions', schema=None) as batch_op:
        batch_op.drop_index('ix_cash_sessions_status')
        batch_op.drop_index('ix_cash_sessions_session_date')
        batch_op.drop_index('ix_cash_sessions_school_id')
        batch_op.drop_index('ix_cash_sessions_opened_by')

    op.drop_table('cash_sessions')
    with op.batch_alter_table('background_jobs', schema=None) as batch_op:
        batch_op.drop_index('ix_background_jobs_type')
        batch_op.drop_index('ix_background_jobs_status')
        batch_op.drop_index('ix_background_jobs_school_id')
        batch_op.drop_index('ix_background_jobs_idempotency')

    op.drop_table('background_jobs')
