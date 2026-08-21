"""
Create documents table (Phase 24).

Revision ID: t3u409vw69s7
Revises: s2t398uv58r6
Create Date: 2026-08-20 11:25:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 't3u409vw69s7'
down_revision: Union[str, None] = 's2t398uv58r6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'owner_type',
            sa.Enum('STUDENT', 'STAFF', name='ownertype', native_enum=False),
            nullable=False,
        ),
        sa.Column('owner_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'document_type',
            sa.Enum(
                'BIRTH_CERTIFICATE', 'STUDENT_ID', 'PREVIOUS_SCHOOL_CERT',
                'TRANSFER_CERTIFICATE', 'BONAFIDE_CERTIFICATE', 'PASSPORT_PHOTO',
                'ADMISSION_DOC', 'QUALIFICATION_CERT', 'EXPERIENCE_CERT',
                'IDENTITY_DOC', 'JOINING_DOC', 'APPOINTMENT_DOC', 'OTHER',
                name='documentcategory', native_enum=False
            ),
            nullable=False,
            server_default='OTHER',
        ),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('original_filename', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=512), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('checksum', sa.String(length=64), nullable=False),
        sa.Column(
            'status',
            sa.Enum('UPLOADED', 'VERIFIED', 'REJECTED', name='documentstatus', native_enum=False),
            nullable=False,
            server_default='UPLOADED',
        ),
        sa.Column('uploaded_by_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('verified_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('verified_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.String(length=1000), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1', nullable=False),
        sa.Column('is_current', sa.Boolean(), server_default=sa.text('true'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['verified_by_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('storage_key')
    )
    op.create_index('ix_documents_school_id', 'documents', ['school_id'], unique=False)
    op.create_index('ix_documents_owner', 'documents', ['owner_type', 'owner_id'], unique=False)
    op.create_index('ix_documents_status', 'documents', ['status'], unique=False)
    op.create_index('ix_documents_category', 'documents', ['document_type'], unique=False)


def downgrade() -> None:
    op.drop_table('documents')
