"""create_visitors_and_reception_inquiries_tables

Revision ID: 721c276bdd9d
Revises: f6k5y7t8c9d0
Create Date: 2026-09-06 17:09:05.630685

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '721c276bdd9d'
down_revision: Union[str, Sequence[str], None] = 'f6k5y7t8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema to create visitors and reception_inquiries tables."""
    op.create_table(
        'visitors',
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('visitor_name', sa.String(length=150), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('id_proof_type', sa.Enum('AADHAAR', 'PAN', 'PASSPORT', 'DRIVING_LICENSE', 'VOTER_ID', 'OTHER', name='id_proof_type'), nullable=True),
        sa.Column('id_proof_number', sa.String(length=100), nullable=True),
        sa.Column('purpose', sa.String(length=255), nullable=False),
        sa.Column('host_type', sa.Enum('TEACHER', 'STAFF', 'STUDENT', 'OTHER', name='host_type'), nullable=True),
        sa.Column('host_id', sa.UUID(), nullable=True),
        sa.Column('check_in_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('check_out_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('EXPECTED', 'CHECKED_IN', 'CHECKED_OUT', 'EXPIRED', 'CANCELLED', name='visitor_status'), nullable=False),
        sa.Column('pass_number', sa.String(length=50), nullable=True),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('visitors', schema=None) as batch_op:
        batch_op.create_index('ix_visitors_check_in_time', ['check_in_time'], unique=False)
        batch_op.create_index('ix_visitors_host', ['school_id', 'host_type', 'host_id'], unique=False)
        batch_op.create_index('ix_visitors_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_visitors_school_phone', ['school_id', 'phone'], unique=False)
        batch_op.create_index('ix_visitors_school_status', ['school_id', 'status'], unique=False)
        batch_op.create_index('ix_visitors_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_visitor_school_pass_number',
            ['school_id', 'pass_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false AND pass_number IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND pass_number IS NOT NULL')
        )

    op.create_table(
        'reception_inquiries',
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('visitor_id', sa.UUID(), nullable=True),
        sa.Column('contact_name', sa.String(length=150), nullable=False),
        sa.Column('contact_phone', sa.String(length=20), nullable=False),
        sa.Column('contact_email', sa.String(length=255), nullable=True),
        sa.Column('subject', sa.String(length=255), nullable=False),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('host_type', sa.Enum('TEACHER', 'STAFF', 'STUDENT', 'OTHER', name='host_type'), nullable=True),
        sa.Column('host_id', sa.UUID(), nullable=True),
        sa.Column('appointment_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'RESOLVED', 'CANCELLED', name='reception_inquiry_status'), nullable=False),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['visitor_id'], ['visitors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('reception_inquiries', schema=None) as batch_op:
        batch_op.create_index('ix_reception_inquiries_appointment', ['school_id', 'appointment_time'], unique=False)
        batch_op.create_index('ix_reception_inquiries_host', ['school_id', 'host_type', 'host_id'], unique=False)
        batch_op.create_index('ix_reception_inquiries_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_reception_inquiries_school_status', ['school_id', 'status'], unique=False)
        batch_op.create_index('ix_reception_inquiries_status', ['status'], unique=False)
        batch_op.create_index('ix_reception_inquiries_visitor_id', ['visitor_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    with op.batch_alter_table('reception_inquiries', schema=None) as batch_op:
        batch_op.drop_index('ix_reception_inquiries_visitor_id')
        batch_op.drop_index('ix_reception_inquiries_status')
        batch_op.drop_index('ix_reception_inquiries_school_status')
        batch_op.drop_index('ix_reception_inquiries_school_id')
        batch_op.drop_index('ix_reception_inquiries_host')
        batch_op.drop_index('ix_reception_inquiries_appointment')

    op.drop_table('reception_inquiries')

    with op.batch_alter_table('visitors', schema=None) as batch_op:
        batch_op.drop_index(
            'uq_visitor_school_pass_number',
            postgresql_where=sa.text('is_deleted = false AND pass_number IS NOT NULL'),
            sqlite_where=sa.text('is_deleted = 0 AND pass_number IS NOT NULL')
        )
        batch_op.drop_index('ix_visitors_status')
        batch_op.drop_index('ix_visitors_school_status')
        batch_op.drop_index('ix_visitors_school_phone')
        batch_op.drop_index('ix_visitors_school_id')
        batch_op.drop_index('ix_visitors_host')
        batch_op.drop_index('ix_visitors_check_in_time')

    op.drop_table('visitors')
