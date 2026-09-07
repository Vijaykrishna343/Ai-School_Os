"""create ai student risk assessment tables

Revision ID: c3h2w4r5a6b7
Revises: b2g1v3o4e5r6
Create Date: 2026-08-26 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c3h2w4r5a6b7'
down_revision: Union[str, None] = 'b2g1v3o4e5r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'ai_student_risk_assessments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('risk_level', sa.String(length=30), nullable=False, server_default='INSUFFICIENT_DATA'),
        sa.Column('risk_score', sa.Numeric(precision=3, scale=2), nullable=True),
        sa.Column('confidence', sa.Numeric(precision=3, scale=2), nullable=False, server_default='0.00'),
        sa.Column('scoring_version', sa.String(length=50), nullable=False, server_default='deterministic-v1'),
        sa.Column('attendance_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('attendance_trend_delta', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('exam_average_percentage', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('exam_trend_delta', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('homework_submission_rate', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('failed_subjects_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('data_sufficiency_status', sa.String(length=30), nullable=False, server_default='INSUFFICIENT'),
        sa.Column('sample_counts', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('risk_factors', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('recommended_interventions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('NOW()')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ai_risk_school_student', 'ai_student_risk_assessments', ['school_id', 'student_id'])
    op.create_index('idx_ai_risk_school_section', 'ai_student_risk_assessments', ['school_id', 'section_id'])
    op.create_index('idx_ai_risk_school_year', 'ai_student_risk_assessments', ['school_id', 'academic_year_id'])
    op.create_index('idx_ai_risk_student_assessed', 'ai_student_risk_assessments', ['student_id', 'assessed_at'])


def downgrade() -> None:
    op.drop_index('idx_ai_risk_student_assessed', table_name='ai_student_risk_assessments')
    op.drop_index('idx_ai_risk_school_year', table_name='ai_student_risk_assessments')
    op.drop_index('idx_ai_risk_school_section', table_name='ai_student_risk_assessments')
    op.drop_index('idx_ai_risk_school_student', table_name='ai_student_risk_assessments')
    op.drop_table('ai_student_risk_assessments')
