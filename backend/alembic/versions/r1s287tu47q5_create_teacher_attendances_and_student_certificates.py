"""
Create teacher_attendances and student_certificates tables (Phase 22).

Revision ID: r1s287tu47q5
Revises: q5d3_add_notif_audit
Create Date: 2026-08-20 11:15:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'r1s287tu47q5'
down_revision: Union[str, None] = 'q5d3_add_notif_audit'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. teacher_attendances table
    op.create_table(
        'teacher_attendances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column(
            'status',
            sa.Enum('PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'EXCUSED', 'HOLIDAY', name='attendancestatus', native_enum=False),
            nullable=False,
            server_default='PRESENT',
        ),
        sa.Column('check_in_time', sa.String(length=20), nullable=True),
        sa.Column('check_out_time', sa.String(length=20), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_teacher_attendances_school_id', 'teacher_attendances', ['school_id'], unique=False)
    op.create_index('ix_teacher_attendances_teacher_id', 'teacher_attendances', ['teacher_id'], unique=False)
    op.create_index('ix_teacher_attendances_date', 'teacher_attendances', ['attendance_date'], unique=False)
    op.create_index('ix_teacher_attendances_status', 'teacher_attendances', ['status'], unique=False)
    op.create_index(
        'uq_teacher_daily_attendance_active',
        'teacher_attendances',
        ['school_id', 'teacher_id', 'attendance_date'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0')
    )

    # 2. student_certificates table
    op.create_table(
        'student_certificates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('student_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('issued_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'certificate_type',
            sa.Enum('TC', 'BONAFIDE', name='certificatetype', native_enum=False),
            nullable=False,
        ),
        sa.Column('certificate_number', sa.String(length=100), nullable=False),
        sa.Column('issued_date', sa.Date(), nullable=False),
        sa.Column('certificate_data', sa.JSON(), nullable=False),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issued_by_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_student_certificates_school_id', 'student_certificates', ['school_id'], unique=False)
    op.create_index('ix_student_certificates_student_id', 'student_certificates', ['student_id'], unique=False)
    op.create_index('ix_student_certificates_type', 'student_certificates', ['certificate_type'], unique=False)
    op.create_index('ix_student_certificates_issued_date', 'student_certificates', ['issued_date'], unique=False)
    op.create_index(
        'uq_student_certificate_number_active',
        'student_certificates',
        ['school_id', 'certificate_number'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0')
    )


def downgrade() -> None:
    op.drop_table('student_certificates')
    op.drop_table('teacher_attendances')
