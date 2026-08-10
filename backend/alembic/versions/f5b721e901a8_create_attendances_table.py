"""create_attendances_table

Revision ID: f5b721e901a8
Revises: a7ce9ec3026e
Create Date: 2026-08-08 16:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'f5b721e901a8'
down_revision: Union[str, Sequence[str], None] = 'a7ce9ec3026e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    attendance_status_enum = postgresql.ENUM(
        'PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'EXCUSED',
        name='attendance_status',
        create_type=False
    )
    attendance_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        'attendances',
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('school_class_id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('recorded_by_user_id', sa.UUID(), nullable=True),
        sa.Column('attendance_date', sa.Date(), nullable=False),
        sa.Column(
            'status',
            postgresql.ENUM(
                'PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'EXCUSED',
                name='attendance_status',
                create_type=False
            ),
            nullable=False
        ),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['recorded_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(
        "uq_student_daily_attendance_active",
        "attendances",
        [
            "school_id",
            "academic_year_id",
            "section_id",
            "student_id",
            "attendance_date",
        ],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_attendances_academic_year_id', 'attendances', ['academic_year_id'], unique=False)
    op.create_index('ix_attendances_class_id', 'attendances', ['school_class_id'], unique=False)
    op.create_index('ix_attendances_date', 'attendances', ['attendance_date'], unique=False)
    op.create_index('ix_attendances_school_id', 'attendances', ['school_id'], unique=False)
    op.create_index('ix_attendances_section_date', 'attendances', ['school_id', 'section_id', 'attendance_date'], unique=False)
    op.create_index('ix_attendances_section_id', 'attendances', ['section_id'], unique=False)
    op.create_index('ix_attendances_status', 'attendances', ['status'], unique=False)
    op.create_index('ix_attendances_student_id', 'attendances', ['student_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('uq_student_daily_attendance_active', table_name='attendances')
    op.drop_index('ix_attendances_student_id', table_name='attendances')
    op.drop_index('ix_attendances_status', table_name='attendances')
    op.drop_index('ix_attendances_section_id', table_name='attendances')
    op.drop_index('ix_attendances_section_date', table_name='attendances')
    op.drop_index('ix_attendances_school_id', table_name='attendances')
    op.drop_index('ix_attendances_date', table_name='attendances')
    op.drop_index('ix_attendances_class_id', table_name='attendances')
    op.drop_index('ix_attendances_academic_year_id', table_name='attendances')
    op.drop_table('attendances')

    attendance_status_enum = postgresql.ENUM(
        'PRESENT', 'ABSENT', 'LATE', 'HALF_DAY', 'EXCUSED',
        name='attendance_status'
    )
    attendance_status_enum.drop(op.get_bind(), checkfirst=True)
