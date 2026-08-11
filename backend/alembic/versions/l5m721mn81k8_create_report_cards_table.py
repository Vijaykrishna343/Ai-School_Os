"""create_report_cards_table

Revision ID: l5m721mn81k8
Revises: l4k610lm70j7
Create Date: 2026-08-11 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l5m721mn81k8'
down_revision: Union[str, Sequence[str], None] = 'l4k610lm70j7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

report_card_status_values = ('DRAFT', 'FINALIZED', 'PUBLISHED')


def upgrade() -> None:
    # 1. Create report_card_status enum safely
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DO $$ BEGIN CREATE TYPE report_card_status AS ENUM ('DRAFT', 'FINALIZED', 'PUBLISHED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

    # 2. Create report_cards table
    op.create_table(
        'report_cards',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_term_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_terms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade_scale_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('grade_scales.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('evaluation_config_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('evaluation_configs.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('status', postgresql.ENUM(*report_card_status_values, name='report_card_status', create_type=False), nullable=False, server_default='DRAFT'),
        sa.Column('total_max_marks', sa.Numeric(precision=7, scale=2), nullable=False, server_default='0.00'),
        sa.Column('total_obtained_marks', sa.Numeric(precision=7, scale=2), nullable=False, server_default='0.00'),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('overall_grade', sa.String(length=10), nullable=False, server_default='N/A'),
        sa.Column('overall_grade_point', sa.Numeric(precision=4, scale=2), nullable=False, server_default='0.00'),
        sa.Column('gpa', sa.Numeric(precision=4, scale=2), nullable=True),
        sa.Column('is_passed', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('total_working_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('present_days', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('attendance_percentage', sa.Numeric(precision=5, scale=2), nullable=False, server_default='0.00'),
        sa.Column('teacher_remarks', sa.Text(), nullable=True),
        sa.Column('principal_remarks', sa.Text(), nullable=True),
        sa.Column('finalized_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finalized_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('published_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('published_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_report_cards_school_id', 'report_cards', ['school_id'])
    op.create_index('ix_report_cards_academic_year_id', 'report_cards', ['academic_year_id'])
    op.create_index('ix_report_cards_academic_term_id', 'report_cards', ['academic_term_id'])
    op.create_index('ix_report_cards_student_id', 'report_cards', ['student_id'])
    op.create_index('ix_report_cards_section_id', 'report_cards', ['section_id'])
    op.create_index('ix_report_cards_status', 'report_cards', ['status'])

    op.create_index(
        'uq_report_card_student_term_active',
        'report_cards',
        ['school_id', 'academic_year_id', 'academic_term_id', 'student_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false AND academic_term_id IS NOT NULL'),
        sqlite_where=sa.text('is_deleted = 0 AND academic_term_id IS NOT NULL'),
    )
    op.create_index(
        'uq_report_card_student_year_active',
        'report_cards',
        ['school_id', 'academic_year_id', 'student_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false AND academic_term_id IS NULL'),
        sqlite_where=sa.text('is_deleted = 0 AND academic_term_id IS NULL'),
    )

    # 3. Create report_card_item_snapshots table
    op.create_table(
        'report_card_item_snapshots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('report_card_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('report_cards.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('subject_name', sa.String(length=100), nullable=False),
        sa.Column('subject_code', sa.String(length=20), nullable=False),
        sa.Column('max_marks', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('obtained_marks', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('grade_code', sa.String(length=10), nullable=False),
        sa.Column('grade_point', sa.Numeric(precision=4, scale=2), nullable=False, server_default='0.00'),
        sa.Column('is_pass', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    op.create_index('ix_report_card_item_snapshots_report_card_id', 'report_card_item_snapshots', ['report_card_id'])
    op.create_index('ix_report_card_item_snapshots_subject_id', 'report_card_item_snapshots', ['subject_id'])


def downgrade() -> None:
    op.drop_index('ix_report_card_item_snapshots_subject_id', table_name='report_card_item_snapshots')
    op.drop_index('ix_report_card_item_snapshots_report_card_id', table_name='report_card_item_snapshots')
    op.drop_table('report_card_item_snapshots')

    op.drop_index('uq_report_card_student_year_active', table_name='report_cards')
    op.drop_index('uq_report_card_student_term_active', table_name='report_cards')
    op.drop_index('ix_report_cards_status', table_name='report_cards')
    op.drop_index('ix_report_cards_section_id', table_name='report_cards')
    op.drop_index('ix_report_cards_student_id', table_name='report_cards')
    op.drop_index('ix_report_cards_academic_term_id', table_name='report_cards')
    op.drop_index('ix_report_cards_academic_year_id', table_name='report_cards')
    op.drop_index('ix_report_cards_school_id', table_name='report_cards')
    op.drop_table('report_cards')

    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TYPE IF EXISTS report_card_status CASCADE;")
