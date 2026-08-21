"""create_academic_terms_table

Revision ID: l3j509kl69i6
Revises: l2i498jk58h5
Create Date: 2026-08-11 12:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l3j509kl69i6'
down_revision: Union[str, Sequence[str], None] = 'l2i498jk58h5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create academic_terms table
    op.create_table(
        'academic_terms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('code', sa.String(length=20), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. Indexes on academic_terms
    op.create_index('ix_academic_terms_school_id', 'academic_terms', ['school_id'])
    op.create_index('ix_academic_terms_academic_year_id', 'academic_terms', ['academic_year_id'])
    op.create_index('ix_academic_terms_is_active', 'academic_terms', ['is_active'])

    op.create_index(
        'uq_academic_term_active_name',
        'academic_terms',
        ['academic_year_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )
    op.create_index(
        'uq_academic_term_active_code',
        'academic_terms',
        ['academic_year_id', 'code'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )

    # 3. Add academic_term_id to exams table
    with op.batch_alter_table('exams') as batch_op:
        batch_op.add_column(sa.Column('academic_term_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_terms.id', ondelete='SET NULL', name='fk_exams_academic_term_id'), nullable=True))
    op.create_index('ix_exams_academic_term_id', 'exams', ['academic_term_id'])


def downgrade() -> None:
    # 1. Drop academic_term_id from exams table
    op.drop_index('ix_exams_academic_term_id', table_name='exams')
    op.drop_column('exams', 'academic_term_id')

    # 2. Drop indexes on academic_terms
    op.drop_index('uq_academic_term_active_code', table_name='academic_terms')
    op.drop_index('uq_academic_term_active_name', table_name='academic_terms')
    op.drop_index('ix_academic_terms_is_active', table_name='academic_terms')
    op.drop_index('ix_academic_terms_academic_year_id', table_name='academic_terms')
    op.drop_index('ix_academic_terms_school_id', table_name='academic_terms')

    # 3. Drop academic_terms table
    op.drop_table('academic_terms')
