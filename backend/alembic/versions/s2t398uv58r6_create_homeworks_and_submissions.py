"""
Create homeworks and homework_submissions tables (Phase 23).

Revision ID: s2t398uv58r6
Revises: r1s287tu47q5
Create Date: 2026-08-20 11:20:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 's2t398uv58r6'
down_revision: Union[str, None] = 'r1s287tu47q5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. homeworks table
    op.create_table(
        'homeworks',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_class_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('assigned_date', sa.Date(), nullable=False),
        sa.Column('due_date', sa.Date(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('DRAFT', 'PUBLISHED', 'CLOSED', name='homework_status_enum', native_enum=False),
            nullable=False,
            server_default='DRAFT',
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subject_id'], ['subjects.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_homeworks_school_id', 'homeworks', ['school_id'], unique=False)
    op.create_index('ix_homeworks_teacher_id', 'homeworks', ['teacher_id'], unique=False)
    op.create_index('ix_homeworks_school_class_id', 'homeworks', ['school_class_id'], unique=False)
    op.create_index('ix_homeworks_section_id', 'homeworks', ['section_id'], unique=False)
    op.create_index('ix_homeworks_subject_id', 'homeworks', ['subject_id'], unique=False)
    op.create_index('ix_homeworks_due_date', 'homeworks', ['due_date'], unique=False)
    op.create_index('ix_homeworks_status', 'homeworks', ['status'], unique=False)

    # 2. homework_submissions table
    op.create_table(
        'homework_submissions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('homework_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'status',
            sa.Enum('SUBMITTED', 'RESUBMITTED', 'REVIEWED', 'GRADED', 'LATE', name='submission_status_enum', native_enum=False),
            nullable=False,
            server_default='SUBMITTED',
        ),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('grade', sa.String(length=50), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('reviewed_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['homework_id'], ['homeworks.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['reviewed_by_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_homework_submissions_school_id', 'homework_submissions', ['school_id'], unique=False)
    op.create_index('ix_homework_submissions_homework_id', 'homework_submissions', ['homework_id'], unique=False)
    op.create_index('ix_homework_submissions_student_id', 'homework_submissions', ['student_id'], unique=False)
    op.create_index('ix_homework_submissions_status', 'homework_submissions', ['status'], unique=False)


def downgrade() -> None:
    op.drop_table('homework_submissions')
    op.drop_table('homeworks')
