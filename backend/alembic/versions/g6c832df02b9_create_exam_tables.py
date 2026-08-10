"""create_exam_tables

Revision ID: g6c832df02b9
Revises: f5b721e901a8
Create Date: 2026-08-08 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'g6c832df02b9'
down_revision: Union[str, Sequence[str], None] = 'f5b721e901a8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    exam_type_enum = postgresql.ENUM(
        'REGULAR', 'RETEST', 'OTHER',
        name='exam_type',
        create_type=False
    )
    exam_type_enum.create(op.get_bind(), checkfirst=True)

    exam_status_enum = postgresql.ENUM(
        'DRAFT', 'SCHEDULED', 'ONGOING', 'COMPLETED', 'CANCELLED',
        name='exam_status',
        create_type=False
    )
    exam_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'exams',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column(
            'exam_type',
            postgresql.ENUM(
                'REGULAR', 'RETEST', 'OTHER',
                name='exam_type',
                create_type=False
            ),
            nullable=False
        ),

        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column(
            'status',
            postgresql.ENUM(
                'DRAFT', 'SCHEDULED', 'ONGOING', 'COMPLETED', 'CANCELLED',
                name='exam_status',
                create_type=False
            ),
            nullable=False,
            server_default='DRAFT'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_exam_active_name",
        "exams",
        ["school_id", "academic_year_id", "name"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_exams_academic_year_id', 'exams', ['academic_year_id'], unique=False)
    op.create_index('ix_exams_end_date', 'exams', ['end_date'], unique=False)
    op.create_index('ix_exams_school_id', 'exams', ['school_id'], unique=False)
    op.create_index('ix_exams_start_date', 'exams', ['start_date'], unique=False)
    op.create_index('ix_exams_status', 'exams', ['status'], unique=False)

    op.create_table(
        'exam_schedules',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('school_class_id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('subject_id', sa.UUID(), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('maximum_marks', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('passing_marks', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['exam_id'], ['exams.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_exam_schedule_active",
        "exam_schedules",
        ["exam_id", "section_id", "subject_id", "exam_date"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_exam_schedules_academic_year_id', 'exam_schedules', ['academic_year_id'], unique=False)
    op.create_index('ix_exam_schedules_class_id', 'exam_schedules', ['school_class_id'], unique=False)
    op.create_index('ix_exam_schedules_exam_date', 'exam_schedules', ['exam_date'], unique=False)
    op.create_index('ix_exam_schedules_exam_id', 'exam_schedules', ['exam_id'], unique=False)
    op.create_index('ix_exam_schedules_school_id', 'exam_schedules', ['school_id'], unique=False)
    op.create_index('ix_exam_schedules_search', 'exam_schedules', ['school_id', 'academic_year_id', 'section_id', 'exam_date'], unique=False)
    op.create_index('ix_exam_schedules_section_id', 'exam_schedules', ['section_id'], unique=False)
    op.create_index('ix_exam_schedules_subject_id', 'exam_schedules', ['subject_id'], unique=False)

    op.create_table(
        'student_exam_results',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('exam_schedule_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('marks_obtained', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('remarks', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['exam_schedule_id'], ['exam_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        "uq_student_exam_result_active",
        "student_exam_results",
        ["exam_schedule_id", "student_id"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_student_exam_results_exam_schedule_id', 'student_exam_results', ['exam_schedule_id'], unique=False)
    op.create_index('ix_student_exam_results_student_id', 'student_exam_results', ['student_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_student_exam_results_student_id', table_name='student_exam_results')
    op.drop_index('ix_student_exam_results_exam_schedule_id', table_name='student_exam_results')
    op.drop_index('uq_student_exam_result_active', table_name='student_exam_results')
    op.drop_table('student_exam_results')

    op.drop_index('ix_exam_schedules_subject_id', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_section_id', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_search', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_school_id', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_exam_id', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_exam_date', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_class_id', table_name='exam_schedules')
    op.drop_index('ix_exam_schedules_academic_year_id', table_name='exam_schedules')
    op.drop_index('uq_exam_schedule_active', table_name='exam_schedules')
    op.drop_table('exam_schedules')

    op.drop_index('ix_exams_status', table_name='exams')
    op.drop_index('ix_exams_start_date', table_name='exams')
    op.drop_index('ix_exams_school_id', table_name='exams')
    op.drop_index('ix_exams_end_date', table_name='exams')
    op.drop_index('ix_exams_academic_year_id', table_name='exams')
    op.drop_index('uq_exam_active_name', table_name='exams')
    op.drop_table('exams')

    exam_status_enum = postgresql.ENUM(
        'DRAFT', 'SCHEDULED', 'ONGOING', 'COMPLETED', 'CANCELLED',
        name='exam_status'
    )
    exam_status_enum.drop(op.get_bind(), checkfirst=True)

    exam_type_enum = postgresql.ENUM(
        'REGULAR', 'RETEST', 'OTHER',
        name='exam_type'
    )
    exam_type_enum.drop(op.get_bind(), checkfirst=True)
