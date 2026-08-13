"""create_class_progression_rules_table

Revision ID: n2r276st36p3
Revises: m1q165rs25o2
Create Date: 2026-08-12 22:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'n2r276st36p3'
down_revision: Union[str, Sequence[str], None] = 'm1q165rs25o2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'class_progression_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('school_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_class_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), nullable=True),
        sa.Column('is_terminal', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), server_default='false', nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
    )

    op.create_index(
        'uq_class_progression_school_source',
        'class_progression_rules',
        ['school_id', 'source_class_id'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
        sqlite_where=sa.text('is_deleted = 0'),
    )

    op.create_index('ix_class_progression_school_id', 'class_progression_rules', ['school_id'])
    op.create_index('ix_class_progression_source_class_id', 'class_progression_rules', ['source_class_id'])
    op.create_index('ix_class_progression_target_class_id', 'class_progression_rules', ['target_class_id'])
    op.create_index('ix_class_progression_is_terminal', 'class_progression_rules', ['is_terminal'])


def downgrade() -> None:
    op.drop_index('ix_class_progression_is_terminal', table_name='class_progression_rules')
    op.drop_index('ix_class_progression_target_class_id', table_name='class_progression_rules')
    op.drop_index('ix_class_progression_source_class_id', table_name='class_progression_rules')
    op.drop_index('ix_class_progression_school_id', table_name='class_progression_rules')
    op.drop_index('uq_class_progression_school_source', table_name='class_progression_rules')
    op.drop_table('class_progression_rules')
