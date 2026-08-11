"""create_evaluation_configs_table

Revision ID: l4k610lm70j7
Revises: l3j509kl69i6
Create Date: 2026-08-11 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l4k610lm70j7'
down_revision: Union[str, Sequence[str], None] = 'l3j509kl69i6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

calculation_mode_values = ('SIMPLE_TOTAL', 'WEIGHTED_ASSESSMENT_TYPE')
retest_policy_values = ('REPLACE_ORIGINAL', 'BEST_ATTEMPT', 'LATEST_ATTEMPT')
rounding_mode_values = ('ROUND_HALF_UP', 'ROUND_FLOOR', 'ROUND_CEIL')


def upgrade() -> None:
    # 1. Create enums safely
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DO $$ BEGIN CREATE TYPE calculation_mode AS ENUM ('SIMPLE_TOTAL', 'WEIGHTED_ASSESSMENT_TYPE'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
        op.execute("DO $$ BEGIN CREATE TYPE retest_policy AS ENUM ('REPLACE_ORIGINAL', 'BEST_ATTEMPT', 'LATEST_ATTEMPT'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
        op.execute("DO $$ BEGIN CREATE TYPE rounding_mode AS ENUM ('ROUND_HALF_UP', 'ROUND_FLOOR', 'ROUND_CEIL'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

    # 2. Create evaluation_configs table
    op.create_table(
        'evaluation_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('calculation_mode', postgresql.ENUM(*calculation_mode_values, name='calculation_mode', create_type=False), nullable=False, server_default='SIMPLE_TOTAL'),
        sa.Column('retest_policy', postgresql.ENUM(*retest_policy_values, name='retest_policy', create_type=False), nullable=False, server_default='REPLACE_ORIGINAL'),
        sa.Column('rounding_mode', postgresql.ENUM(*rounding_mode_values, name='rounding_mode', create_type=False), nullable=False, server_default='ROUND_HALF_UP'),
        sa.Column('gpa_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_evaluation_configs_school_id', 'evaluation_configs', ['school_id'])
    op.create_index('ix_evaluation_configs_academic_year_id', 'evaluation_configs', ['academic_year_id'])
    op.create_index(
        'uq_evaluation_config_active_name',
        'evaluation_configs',
        ['school_id', 'academic_year_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_evaluation_config_active_default',
        'evaluation_configs',
        ['school_id', 'academic_year_id'],
        unique=True,
        postgresql_where=sa.text('is_default = true AND is_deleted = false'),
        sqlite_where=sa.text('is_default = 1 AND is_deleted = 0'),
    )

    # 3. Create assessment_type_weightages table
    op.create_table(
        'assessment_type_weightages',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('evaluation_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_configs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('assessment_type', postgresql.ENUM('FORMATIVE_ASSESSMENT', 'SUMMATIVE_ASSESSMENT', 'UNIT_TEST', 'PERIODIC_TEST', 'QUARTERLY', 'HALF_YEARLY', 'TERM', 'PRE_FINAL', 'QUARTER_FINAL', 'SEMI_FINAL', 'FINAL', 'OTHER', name='assessment_type', create_type=False), nullable=False),
        sa.Column('weightage_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.CheckConstraint('weightage_percentage >= 0 AND weightage_percentage <= 100', name='ck_assessment_type_weightage_pct_bounds'),
    )

    op.create_index('ix_assessment_type_weightages_config_id', 'assessment_type_weightages', ['evaluation_config_id'])
    op.create_index(
        'uq_assessment_type_weightage_active',
        'assessment_type_weightages',
        ['evaluation_config_id', 'assessment_type'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )


def downgrade() -> None:
    op.drop_index('uq_assessment_type_weightage_active', table_name='assessment_type_weightages')
    op.drop_index('ix_assessment_type_weightages_config_id', table_name='assessment_type_weightages')
    op.drop_table('assessment_type_weightages')

    op.drop_index('uq_evaluation_config_active_default', table_name='evaluation_configs')
    op.drop_index('uq_evaluation_config_active_name', table_name='evaluation_configs')
    op.drop_index('ix_evaluation_configs_academic_year_id', table_name='evaluation_configs')
    op.drop_index('ix_evaluation_configs_school_id', table_name='evaluation_configs')
    op.drop_table('evaluation_configs')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TYPE IF EXISTS rounding_mode CASCADE;")
        op.execute("DROP TYPE IF EXISTS retest_policy CASCADE;")
        op.execute("DROP TYPE IF EXISTS calculation_mode CASCADE;")
