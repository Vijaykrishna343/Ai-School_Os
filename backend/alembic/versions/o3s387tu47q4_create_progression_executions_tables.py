"""create_progression_executions_tables

Revision ID: o3s387tu47q4
Revises: n2r276st36p3
Create Date: 2026-08-13 11:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'o3s387tu47q4'
down_revision: Union[str, Sequence[str], None] = 'n2r276st36p3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create progression_executions table
    op.create_table(
        'progression_executions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('target_academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('execution_plan_hash', sa.String(length=64), nullable=False),
        sa.Column('idempotency_key', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), server_default='PENDING', nullable=False),
        sa.Column('total_students', sa.Integer(), server_default='0', nullable=False),
        sa.Column('promoted_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('graduated_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('retained_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('blocked_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('excluded_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('error_summary', sa.Text(), nullable=True),
        sa.Column('initiated_by_user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('identity_users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # Idempotency Unique Constraint
    op.create_index(
        'uq_progression_execution_idempotency',
        'progression_executions',
        ['school_id', 'idempotency_key'],
        unique=True,
    )

    # Active Execution Partial Unique Index (Single active run per school)
    op.create_index(
        'uq_progression_execution_active_school',
        'progression_executions',
        ['school_id'],
        unique=True,
        postgresql_where=sa.text("status IN ('PENDING', 'RUNNING')"),
        sqlite_where=sa.text("status IN ('PENDING', 'RUNNING')"),
    )

    op.create_index('ix_progression_execution_school_id', 'progression_executions', ['school_id'])
    op.create_index('ix_progression_execution_source_ay', 'progression_executions', ['source_academic_year_id'])
    op.create_index('ix_progression_execution_target_ay', 'progression_executions', ['target_academic_year_id'])
    op.create_index('ix_progression_execution_status', 'progression_executions', ['status'])

    # 2. Create progression_execution_items table
    op.create_table(
        'progression_execution_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('execution_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('progression_executions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('school_classes.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('source_section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('source_roll_number', sa.String(length=20), nullable=True),
        sa.Column('target_class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('school_classes.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('target_section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='RESTRICT'), nullable=True),
        sa.Column('allocated_roll_number', sa.String(length=20), nullable=True),
        sa.Column('decision', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_progression_exec_items_execution_id', 'progression_execution_items', ['execution_id'])
    op.create_index('ix_progression_exec_items_student_id', 'progression_execution_items', ['student_id'])


def downgrade() -> None:
    op.drop_index('ix_progression_exec_items_student_id', table_name='progression_execution_items')
    op.drop_index('ix_progression_exec_items_execution_id', table_name='progression_execution_items')
    op.drop_table('progression_execution_items')

    op.drop_index('ix_progression_execution_status', table_name='progression_executions')
    op.drop_index('ix_progression_execution_target_ay', table_name='progression_executions')
    op.drop_index('ix_progression_execution_source_ay', table_name='progression_executions')
    op.drop_index('ix_progression_execution_school_id', table_name='progression_executions')
    op.drop_index('uq_progression_execution_active_school', table_name='progression_executions')
    op.drop_index('uq_progression_execution_idempotency', table_name='progression_executions')
    op.drop_table('progression_executions')
