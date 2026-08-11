"""add_student_promotion_and_tc_tables

Revision ID: j9f165gh25e2
Revises: i8e054fg14d1
Create Date: 2026-08-10 20:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'j9f165gh25e2'
down_revision: Union[str, Sequence[str], None] = 'i8e054fg14d1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'student_enrollment_histories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('school_class_id', sa.UUID(), nullable=False),
        sa.Column('section_id', sa.UUID(), nullable=False),
        sa.Column('roll_number', sa.String(length=20), nullable=False),
        sa.Column(
            'enrollment_status',
            sa.Enum(
                'ENROLLED',
                'PROMOTED',
                'RETAINED',
                'GRADUATED',
                'TRANSFERRED',
                'WITHDRAWN',
                'COMPLETED',
                name='enrollment_status',
            ),
            nullable=False,
        ),
        sa.Column(
            'promotion_decision',
            sa.Enum(
                'PENDING',
                'PROMOTED',
                'RETAINED',
                'GRADUATED',
                'TRANSFERRED',
                'WITHDRAWN',
                name='promotion_decision',
            ),
            nullable=False,
        ),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['section_id'], ['sections.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'student_id', 'academic_year_id', name='uq_student_enrollment_history_year'),
    )
    op.create_index('ix_enrollment_history_academic_year_id', 'student_enrollment_histories', ['academic_year_id'], unique=False)
    op.create_index('ix_enrollment_history_class_id', 'student_enrollment_histories', ['school_class_id'], unique=False)
    op.create_index('ix_enrollment_history_decision', 'student_enrollment_histories', ['promotion_decision'], unique=False)
    op.create_index('ix_enrollment_history_school_id', 'student_enrollment_histories', ['school_id'], unique=False)
    op.create_index('ix_enrollment_history_section_id', 'student_enrollment_histories', ['section_id'], unique=False)
    op.create_index('ix_enrollment_history_status', 'student_enrollment_histories', ['enrollment_status'], unique=False)
    op.create_index('ix_enrollment_history_student_id', 'student_enrollment_histories', ['student_id'], unique=False)

    op.create_table(
        'transfer_certificates',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('tc_number', sa.String(length=50), nullable=False),
        sa.Column('issue_date', sa.Date(), nullable=False),
        sa.Column('leaving_date', sa.Date(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('destination_school', sa.String(length=255), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column(
            'status',
            sa.Enum(
                'DRAFT',
                'ISSUED',
                'CANCELLED',
                name='transfer_certificate_status',
            ),
            nullable=False,
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('school_id', 'tc_number', name='uq_tc_school_number'),
    )
    op.create_index('ix_tc_academic_year_id', 'transfer_certificates', ['academic_year_id'], unique=False)
    op.create_index('ix_tc_number', 'transfer_certificates', ['tc_number'], unique=False)
    op.create_index('ix_tc_school_id', 'transfer_certificates', ['school_id'], unique=False)
    op.create_index('ix_tc_status', 'transfer_certificates', ['status'], unique=False)
    op.create_index('ix_tc_student_id', 'transfer_certificates', ['student_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_tc_student_id', table_name='transfer_certificates')
    op.drop_index('ix_tc_status', table_name='transfer_certificates')
    op.drop_index('ix_tc_school_id', table_name='transfer_certificates')
    op.drop_index('ix_tc_number', table_name='transfer_certificates')
    op.drop_index('ix_tc_academic_year_id', table_name='transfer_certificates')
    op.drop_table('transfer_certificates')

    op.drop_index('ix_enrollment_history_student_id', table_name='student_enrollment_histories')
    op.drop_index('ix_enrollment_history_status', table_name='student_enrollment_histories')
    op.drop_index('ix_enrollment_history_section_id', table_name='student_enrollment_histories')
    op.drop_index('ix_enrollment_history_school_id', table_name='student_enrollment_histories')
    op.drop_index('ix_enrollment_history_decision', table_name='student_enrollment_histories')
    op.drop_index('ix_enrollment_history_class_id', table_name='student_enrollment_histories')
    op.drop_index('ix_enrollment_history_academic_year_id', table_name='student_enrollment_histories')
    op.drop_table('student_enrollment_histories')
