"""create_teacher_substitutions_table

Revision ID: l8p054qr14n1
Revises: l7o943pq03m0
Create Date: 2026-08-12 19:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l8p054qr14n1'
down_revision: Union[str, Sequence[str], None] = 'l7o943pq03m0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create teacher_substitutions table
    op.create_table(
        'teacher_substitutions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('timetable_entry_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('timetable_entries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('original_teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('substitute_teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('substitution_date', sa.Date(), nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 2. Create indexes on teacher_substitutions
    op.create_index('ix_teacher_substitutions_school_id', 'teacher_substitutions', ['school_id'])
    op.create_index('ix_teacher_substitutions_entry_id', 'teacher_substitutions', ['timetable_entry_id'])
    op.create_index('ix_teacher_substitutions_substitute_date', 'teacher_substitutions', ['substitute_teacher_id', 'substitution_date'])
    op.create_index('ix_teacher_substitutions_original_date', 'teacher_substitutions', ['original_teacher_id', 'substitution_date'])

    op.create_index(
        'uq_teacher_substitution_active_slot',
        'teacher_substitutions',
        ['timetable_entry_id', 'substitution_date'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )

    # 3. Create partial unique index on timetables for single active published timetable
    op.create_index(
        'uq_timetable_active_published',
        'timetables',
        ['school_id', 'academic_year_id', 'section_id'],
        unique=True,
        postgresql_where=sa.text("status = 'PUBLISHED' AND is_active = true AND is_deleted = false"),
        sqlite_where=sa.text("status = 'PUBLISHED' AND is_active = 1 AND is_deleted = 0"),
    )


def downgrade() -> None:
    # 1. Drop partial index on timetables
    op.drop_index('uq_timetable_active_published', table_name='timetables')

    # 2. Drop indexes on teacher_substitutions
    op.drop_index('uq_teacher_substitution_active_slot', table_name='teacher_substitutions')
    op.drop_index('ix_teacher_substitutions_original_date', table_name='teacher_substitutions')
    op.drop_index('ix_teacher_substitutions_substitute_date', table_name='teacher_substitutions')
    op.drop_index('ix_teacher_substitutions_entry_id', table_name='teacher_substitutions')
    op.drop_index('ix_teacher_substitutions_school_id', table_name='teacher_substitutions')

    # 3. Drop teacher_substitutions table
    op.drop_table('teacher_substitutions')
