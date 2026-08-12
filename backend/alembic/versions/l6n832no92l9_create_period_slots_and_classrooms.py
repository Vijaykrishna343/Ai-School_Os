"""create_period_slots_and_classrooms_tables

Revision ID: l6n832no92l9
Revises: l5m721mn81k8
Create Date: 2026-08-11 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'l6n832no92l9'
down_revision: Union[str, Sequence[str], None] = 'l5m721mn81k8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

period_type_values = ('REGULAR', 'BREAK', 'ASSEMBLY', 'LUNCH')
room_type_values = ('CLASSROOM', 'LABORATORY', 'AUDITORIUM', 'SPORTS_GROUND')


def upgrade() -> None:
    # 1. Create enums safely
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DO $$ BEGIN CREATE TYPE period_type AS ENUM ('REGULAR', 'BREAK', 'ASSEMBLY', 'LUNCH'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")
        op.execute("DO $$ BEGIN CREATE TYPE room_type AS ENUM ('CLASSROOM', 'LABORATORY', 'AUDITORIUM', 'SPORTS_GROUND'); EXCEPTION WHEN duplicate_object THEN NULL; END $$;")

    period_type_col = postgresql.ENUM(*period_type_values, name='period_type', create_type=False) if bind.dialect.name == 'postgresql' else sa.String(20)
    room_type_col = postgresql.ENUM(*room_type_values, name='room_type', create_type=False) if bind.dialect.name == 'postgresql' else sa.String(30)

    # 2. Create period_slots table
    op.create_table(
        'period_slots',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('period_type', period_type_col, nullable=False, server_default='REGULAR'),
        sa.Column('start_time', sa.Time(), nullable=False),
        sa.Column('end_time', sa.Time(), nullable=False),
        sa.Column('display_order', sa.Integer(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 3. Indexes on period_slots
    op.create_index('ix_period_slots_school_id', 'period_slots', ['school_id'])
    op.create_index(
        'uq_period_slot_order',
        'period_slots',
        ['school_id', 'display_order'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )

    # 4. Create classrooms table
    op.create_table(
        'classrooms',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('room_number', sa.String(length=30), nullable=False),
        sa.Column('building_name', sa.String(length=100), nullable=True),
        sa.Column('capacity', sa.Integer(), nullable=False, server_default='40'),
        sa.Column('room_type', room_type_col, nullable=False, server_default='CLASSROOM'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    )

    # 5. Indexes on classrooms
    op.create_index('ix_classrooms_school_id', 'classrooms', ['school_id'])
    op.create_index(
        'uq_classroom_room_number',
        'classrooms',
        ['school_id', 'room_number'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )


def downgrade() -> None:
    # 1. Drop indexes on classrooms
    op.drop_index('uq_classroom_room_number', table_name='classrooms')
    op.drop_index('ix_classrooms_school_id', table_name='classrooms')

    # 2. Drop classrooms table
    op.drop_table('classrooms')

    # 3. Drop indexes on period_slots
    op.drop_index('uq_period_slot_order', table_name='period_slots')
    op.drop_index('ix_period_slots_school_id', table_name='period_slots')

    # 4. Drop period_slots table
    op.drop_table('period_slots')

    # 5. Drop enums
    bind = op.get_bind()
    if bind.dialect.name == 'postgresql':
        op.execute("DROP TYPE IF EXISTS room_type CASCADE;")
        op.execute("DROP TYPE IF EXISTS period_type CASCADE;")
