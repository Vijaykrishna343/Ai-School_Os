"""create_timetables_and_entries_tables

Revision ID: l7o943pq03m0
Revises: l6n832no92l9
Create Date: 2026-08-12 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l7o943pq03m0'
down_revision: Union[str, Sequence[str], None] = 'l6n832no92l9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

timetable_status_values = ('DRAFT', 'PUBLISHED', 'ARCHIVED')
day_of_week_values = ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY')


def upgrade() -> None:
    # 1. Create enums safely
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DO $$ BEGIN CREATE TYPE timetable_status AS ENUM ('DRAFT', 'PUBLISHED', 'ARCHIVED'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
        op.execute("DO $$ BEGIN CREATE TYPE day_of_week AS ENUM ('MONDAY', 'TUESDAY', 'WEDNESDAY', 'THURSDAY', 'FRIDAY', 'SATURDAY', 'SUNDAY'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

    timetable_status_col = (
        postgresql.ENUM(*timetable_status_values, name='timetable_status', create_type=False)
        if bind.dialect.name == 'postgresql'
        else sa.String(20)
    )
    day_of_week_col = (
        postgresql.ENUM(*day_of_week_values, name='day_of_week', create_type=False)
        if bind.dialect.name == 'postgresql'
        else sa.String(20)
    )

    # 2. Create timetables table
    op.create_table(
        'timetables',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_year_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_years.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('section_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('sections.id', ondelete='CASCADE'), nullable=False),
        sa.Column('academic_term_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('academic_terms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('status', timetable_status_col, nullable=False, server_default='DRAFT'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. Indexes on timetables
    op.create_index('ix_timetables_school_id', 'timetables', ['school_id'])
    op.create_index('ix_timetables_academic_year_id', 'timetables', ['academic_year_id'])
    op.create_index('ix_timetables_school_class_id', 'timetables', ['school_class_id'])
    op.create_index('ix_timetables_section_id', 'timetables', ['section_id'])
    op.create_index('ix_timetables_academic_term_id', 'timetables', ['academic_term_id'])
    op.create_index('ix_timetables_status', 'timetables', ['status'])

    # 4. Create timetable_entries table
    op.create_table(
        'timetable_entries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('timetable_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('timetables.id', ondelete='CASCADE'), nullable=False),
        sa.Column('period_slot_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('period_slots.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),
        sa.Column('classroom_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('classrooms.id', ondelete='SET NULL'), nullable=True),
        sa.Column('day_of_week', day_of_week_col, nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 5. Indexes on timetable_entries
    op.create_index('ix_timetable_entries_timetable_id', 'timetable_entries', ['timetable_id'])
    op.create_index('ix_timetable_entries_period_slot_id', 'timetable_entries', ['period_slot_id'])
    op.create_index('ix_timetable_entries_subject_id', 'timetable_entries', ['subject_id'])
    op.create_index('ix_timetable_entries_teacher_slot', 'timetable_entries', ['teacher_id', 'day_of_week', 'period_slot_id'])
    op.create_index('ix_timetable_entries_room_slot', 'timetable_entries', ['classroom_id', 'day_of_week', 'period_slot_id'])

    op.create_index(
        'uq_timetable_entry_slot',
        'timetable_entries',
        ['timetable_id', 'day_of_week', 'period_slot_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )


def downgrade() -> None:
    # 1. Drop indexes on timetable_entries
    op.drop_index('uq_timetable_entry_slot', table_name='timetable_entries')
    op.drop_index('ix_timetable_entries_room_slot', table_name='timetable_entries')
    op.drop_index('ix_timetable_entries_teacher_slot', table_name='timetable_entries')
    op.drop_index('ix_timetable_entries_subject_id', table_name='timetable_entries')
    op.drop_index('ix_timetable_entries_period_slot_id', table_name='timetable_entries')
    op.drop_index('ix_timetable_entries_timetable_id', table_name='timetable_entries')

    # 2. Drop timetable_entries table
    op.drop_table('timetable_entries')

    # 3. Drop indexes on timetables
    op.drop_index('ix_timetables_status', table_name='timetables')
    op.drop_index('ix_timetables_academic_term_id', table_name='timetables')
    op.drop_index('ix_timetables_section_id', table_name='timetables')
    op.drop_index('ix_timetables_school_class_id', table_name='timetables')
    op.drop_index('ix_timetables_academic_year_id', table_name='timetables')
    op.drop_index('ix_timetables_school_id', table_name='timetables')

    # 4. Drop timetables table
    op.drop_table('timetables')

    # 5. Drop enums
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TYPE IF EXISTS day_of_week CASCADE;")
        op.execute("DROP TYPE IF EXISTS timetable_status CASCADE;")
