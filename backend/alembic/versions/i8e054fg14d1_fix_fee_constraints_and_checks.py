"""fix_fee_constraints_and_checks

Revision ID: i8e054fg14d1
Revises: h7d943ef03c0
Create Date: 2026-08-10 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'i8e054fg14d1'
down_revision: Union[str, Sequence[str], None] = 'h7d943ef03c0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. Drop existing unique index that fails for NULL school_class_id in PostgreSQL
    op.drop_index('uq_fee_structure_active_name', table_name='fee_structures')

    # 2. Create partial unique index for class-specific fee structures
    op.create_index(
        'uq_fee_structure_active_name_class',
        'fee_structures',
        ['school_id', 'academic_year_id', 'school_class_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false AND school_class_id IS NOT NULL'),
    )

    # 3. Create partial unique index for school-wide fee structures (where school_class_id IS NULL)
    op.create_index(
        'uq_fee_structure_active_name_noclass',
        'fee_structures',
        ['school_id', 'academic_year_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false AND school_class_id IS NULL'),
    )

    # 4. Add database CHECK constraints for monetary amounts
    op.create_check_constraint(
        'ck_fee_items_amount_non_negative',
        'fee_items',
        sa.text('amount >= 0'),
    )
    op.create_check_constraint(
        'ck_student_fee_items_amount_non_negative',
        'student_fee_items',
        sa.text('amount >= 0'),
    )
    op.create_check_constraint(
        'ck_fee_discounts_amount_positive',
        'fee_discounts',
        sa.text('amount > 0'),
    )
    op.create_check_constraint(
        'ck_fee_payments_amount_positive',
        'fee_payments',
        sa.text('amount > 0'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('ck_fee_payments_amount_positive', 'fee_payments', type_='check')
    op.drop_constraint('ck_fee_discounts_amount_positive', 'fee_discounts', type_='check')
    op.drop_constraint('ck_student_fee_items_amount_non_negative', 'student_fee_items', type_='check')
    op.drop_constraint('ck_fee_items_amount_non_negative', 'fee_items', type_='check')

    op.drop_index('uq_fee_structure_active_name_noclass', table_name='fee_structures')
    op.drop_index('uq_fee_structure_active_name_class', table_name='fee_structures')

    op.create_index(
        'uq_fee_structure_active_name',
        'fee_structures',
        ['school_id', 'academic_year_id', 'school_class_id', 'name'],
        unique=True,
        postgresql_where=sa.text('is_deleted = false'),
    )
