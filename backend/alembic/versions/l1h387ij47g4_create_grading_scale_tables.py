"""create_grading_scale_tables

Revision ID: l1h387ij47g4
Revises: k0g276hi36f3
Create Date: 2026-08-11 09:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'l1h387ij47g4'
down_revision: Union[str, Sequence[str], None] = 'k0g276hi36f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'grade_scales',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_grade_scale_active_name",
        "grade_scales",
        ["school_id", "name"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )

    op.create_index(
        "uq_grade_scale_active_default",
        "grade_scales",
        ["school_id"],
        unique=True,
        postgresql_where=sa.text("is_default = true AND is_deleted = false"),
    )

    op.create_index('ix_grade_scales_school_id', 'grade_scales', ['school_id'], unique=False)

    op.create_table(
        'grade_scale_entries',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('grade_scale_id', sa.UUID(), nullable=False),
        sa.Column('grade_code', sa.String(length=10), nullable=False),
        sa.Column('min_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('max_percentage', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('grade_point', sa.Numeric(precision=4, scale=2), nullable=False, server_default='0.00'),
        sa.Column('description', sa.String(length=100), nullable=True),
        sa.Column('is_pass', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.CheckConstraint('min_percentage >= 0', name='ck_grade_scale_entry_min_pct_non_negative'),
        sa.CheckConstraint('max_percentage <= 100', name='ck_grade_scale_entry_max_pct_bounds'),
        sa.CheckConstraint('min_percentage <= max_percentage', name='ck_grade_scale_entry_min_le_max'),
        sa.CheckConstraint('grade_point >= 0', name='ck_grade_scale_entry_grade_point_non_negative'),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['grade_scale_id'], ['grade_scales.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_grade_scale_entry_active_code",
        "grade_scale_entries",
        ["grade_scale_id", "grade_code"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )

    op.create_index('ix_grade_scale_entries_grade_scale_id', 'grade_scale_entries', ['grade_scale_id'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_grade_scale_entries_grade_scale_id', table_name='grade_scale_entries')
    op.drop_index('uq_grade_scale_entry_active_code', table_name='grade_scale_entries')
    op.drop_table('grade_scale_entries')

    op.drop_index('ix_grade_scales_school_id', table_name='grade_scales')
    op.drop_index('uq_grade_scale_active_default', table_name='grade_scales')
    op.drop_index('uq_grade_scale_active_name', table_name='grade_scales')
    op.drop_table('grade_scales')
