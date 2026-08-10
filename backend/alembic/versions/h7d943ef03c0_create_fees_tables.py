"""create_fees_tables

Revision ID: h7d943ef03c0
Revises: g6c832df02b9
Create Date: 2026-08-10 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = 'h7d943ef03c0'
down_revision: Union[str, Sequence[str], None] = 'g6c832df02b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    fee_category_enum = postgresql.ENUM(
        'TUITION', 'ADMISSION', 'TRANSPORTATION', 'EXAMINATION', 'BOOKS',
        'STUDY_MATERIAL', 'UNIFORM', 'ID_CARD', 'TIE', 'BELT', 'SHOES',
        'DIARY', 'ACTIVITY', 'MISCELLANEOUS', 'OTHER',
        name='fee_category',
        create_type=False
    )
    fee_category_enum.create(op.get_bind(), checkfirst=True)

    fee_structure_status_enum = postgresql.ENUM(
        'DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED',
        name='fee_structure_status',
        create_type=False
    )
    fee_structure_status_enum.create(op.get_bind(), checkfirst=True)

    student_fee_assignment_status_enum = postgresql.ENUM(
        'PENDING', 'PARTIALLY_PAID', 'PAID', 'CANCELLED',
        name='student_fee_assignment_status',
        create_type=False
    )
    student_fee_assignment_status_enum.create(op.get_bind(), checkfirst=True)

    discount_type_enum = postgresql.ENUM(
        'SIBLING_CONCESSION', 'SCHOLARSHIP', 'STAFF_CONCESSION',
        'MANAGEMENT_CONCESSION', 'SPECIAL_DISCOUNT', 'OTHER',
        name='discount_type',
        create_type=False
    )
    discount_type_enum.create(op.get_bind(), checkfirst=True)

    payment_mode_enum = postgresql.ENUM(
        'CASH', 'UPI', 'BANK_TRANSFER', 'CARD', 'CHEQUE', 'OTHER',
        name='payment_mode',
        create_type=False
    )
    payment_mode_enum.create(op.get_bind(), checkfirst=True)

    # 1. fee_structures
    op.create_table(
        'fee_structures',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('school_class_id', sa.UUID(), nullable=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column(
            'status',
            postgresql.ENUM(
                'DRAFT', 'ACTIVE', 'INACTIVE', 'ARCHIVED',
                name='fee_structure_status',
                create_type=False
            ),
            nullable=False,
            server_default='DRAFT'
        ),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_fee_structure_active_name",
        "fee_structures",
        ["school_id", "academic_year_id", "school_class_id", "name"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_fee_structures_school_id', 'fee_structures', ['school_id'], unique=False)
    op.create_index('ix_fee_structures_academic_year_id', 'fee_structures', ['academic_year_id'], unique=False)
    op.create_index('ix_fee_structures_school_class_id', 'fee_structures', ['school_class_id'], unique=False)
    op.create_index('ix_fee_structures_status', 'fee_structures', ['status'], unique=False)

    # 2. fee_items
    op.create_table(
        'fee_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('fee_structure_id', sa.UUID(), nullable=False),
        sa.Column(
            'category',
            postgresql.ENUM(
                'TUITION', 'ADMISSION', 'TRANSPORTATION', 'EXAMINATION', 'BOOKS',
                'STUDY_MATERIAL', 'UNIFORM', 'ID_CARD', 'TIE', 'BELT', 'SHOES',
                'DIARY', 'ACTIVITY', 'MISCELLANEOUS', 'OTHER',
                name='fee_category',
                create_type=False
            ),
            nullable=False
        ),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['fee_structures.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fee_items_fee_structure_id', 'fee_items', ['fee_structure_id'], unique=False)
    op.create_index('ix_fee_items_category', 'fee_items', ['category'], unique=False)

    # 3. student_fee_assignments
    op.create_table(
        'student_fee_assignments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('fee_structure_id', sa.UUID(), nullable=False),
        sa.Column(
            'status',
            postgresql.ENUM(
                'PENDING', 'PARTIALLY_PAID', 'PAID', 'CANCELLED',
                name='student_fee_assignment_status',
                create_type=False
            ),
            nullable=False,
            server_default='PENDING'
        ),
        sa.Column('due_date', sa.Date(), nullable=True),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fee_structure_id'], ['fee_structures.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_student_fee_assignment_active",
        "student_fee_assignments",
        ["school_id", "academic_year_id", "student_id", "fee_structure_id"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_student_fee_assignments_school_id', 'student_fee_assignments', ['school_id'], unique=False)
    op.create_index('ix_student_fee_assignments_academic_year_id', 'student_fee_assignments', ['academic_year_id'], unique=False)
    op.create_index('ix_student_fee_assignments_student_id', 'student_fee_assignments', ['student_id'], unique=False)
    op.create_index('ix_student_fee_assignments_fee_structure_id', 'student_fee_assignments', ['fee_structure_id'], unique=False)
    op.create_index('ix_student_fee_assignments_status', 'student_fee_assignments', ['status'], unique=False)

    # 4. student_fee_items
    op.create_table(
        'student_fee_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('student_fee_assignment_id', sa.UUID(), nullable=False),
        sa.Column('fee_item_id', sa.UUID(), nullable=True),
        sa.Column(
            'category',
            postgresql.ENUM(
                'TUITION', 'ADMISSION', 'TRANSPORTATION', 'EXAMINATION', 'BOOKS',
                'STUDY_MATERIAL', 'UNIFORM', 'ID_CARD', 'TIE', 'BELT', 'SHOES',
                'DIARY', 'ACTIVITY', 'MISCELLANEOUS', 'OTHER',
                name='fee_category',
                create_type=False
            ),
            nullable=False
        ),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('is_optional', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_applicable', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['fee_item_id'], ['fee_items.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_fee_assignment_id'], ['student_fee_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_student_fee_items_assignment_id', 'student_fee_items', ['student_fee_assignment_id'], unique=False)
    op.create_index('ix_student_fee_items_category', 'student_fee_items', ['category'], unique=False)

    # 5. fee_discounts
    op.create_table(
        'fee_discounts',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('student_fee_assignment_id', sa.UUID(), nullable=False),
        sa.Column(
            'discount_type',
            postgresql.ENUM(
                'SIBLING_CONCESSION', 'SCHOLARSHIP', 'STAFF_CONCESSION',
                'MANAGEMENT_CONCESSION', 'SPECIAL_DISCOUNT', 'OTHER',
                name='discount_type',
                create_type=False
            ),
            nullable=False
        ),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_fee_assignment_id'], ['student_fee_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_fee_discounts_assignment_id', 'fee_discounts', ['student_fee_assignment_id'], unique=False)
    op.create_index('ix_fee_discounts_type', 'fee_discounts', ['discount_type'], unique=False)

    # 6. fee_payments
    op.create_table(
        'fee_payments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_fee_assignment_id', sa.UUID(), nullable=False),
        sa.Column('receipt_number', sa.String(length=100), nullable=False),
        sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column('payment_date', sa.Date(), nullable=False),
        sa.Column(
            'payment_mode',
            postgresql.ENUM(
                'CASH', 'UPI', 'BANK_TRANSFER', 'CARD', 'CHEQUE', 'OTHER',
                name='payment_mode',
                create_type=False
            ),
            nullable=False
        ),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_by_user_id', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['deleted_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_fee_assignment_id'], ['student_fee_assignments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index(
        "uq_fee_payment_receipt",
        "fee_payments",
        ["school_id", "receipt_number"],
        unique=True,
        postgresql_where=sa.text("is_deleted = false"),
    )
    op.create_index('ix_fee_payments_school_id', 'fee_payments', ['school_id'], unique=False)
    op.create_index('ix_fee_payments_assignment_id', 'fee_payments', ['student_fee_assignment_id'], unique=False)
    op.create_index('ix_fee_payments_receipt_number', 'fee_payments', ['receipt_number'], unique=False)
    op.create_index('ix_fee_payments_payment_date', 'fee_payments', ['payment_date'], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('ix_fee_payments_payment_date', table_name='fee_payments')
    op.drop_index('ix_fee_payments_receipt_number', table_name='fee_payments')
    op.drop_index('ix_fee_payments_assignment_id', table_name='fee_payments')
    op.drop_index('ix_fee_payments_school_id', table_name='fee_payments')
    op.drop_index('uq_fee_payment_receipt', table_name='fee_payments')
    op.drop_table('fee_payments')

    op.drop_index('ix_fee_discounts_type', table_name='fee_discounts')
    op.drop_index('ix_fee_discounts_assignment_id', table_name='fee_discounts')
    op.drop_table('fee_discounts')

    op.drop_index('ix_student_fee_items_category', table_name='student_fee_items')
    op.drop_index('ix_student_fee_items_assignment_id', table_name='student_fee_items')
    op.drop_table('student_fee_items')

    op.drop_index('ix_student_fee_assignments_status', table_name='student_fee_assignments')
    op.drop_index('ix_student_fee_assignments_fee_structure_id', table_name='student_fee_assignments')
    op.drop_index('ix_student_fee_assignments_student_id', table_name='student_fee_assignments')
    op.drop_index('ix_student_fee_assignments_academic_year_id', table_name='student_fee_assignments')
    op.drop_index('ix_student_fee_assignments_school_id', table_name='student_fee_assignments')
    op.drop_index('uq_student_fee_assignment_active', table_name='student_fee_assignments')
    op.drop_table('student_fee_assignments')

    op.drop_index('ix_fee_items_category', table_name='fee_items')
    op.drop_index('ix_fee_items_fee_structure_id', table_name='fee_items')
    op.drop_table('fee_items')

    op.drop_index('ix_fee_structures_status', table_name='fee_structures')
    op.drop_index('ix_fee_structures_school_class_id', table_name='fee_structures')
    op.drop_index('ix_fee_structures_academic_year_id', table_name='fee_structures')
    op.drop_index('ix_fee_structures_school_id', table_name='fee_structures')
    op.drop_index('uq_fee_structure_active_name', table_name='fee_structures')
    op.drop_table('fee_structures')

    payment_mode_enum = postgresql.ENUM(name='payment_mode')
    payment_mode_enum.drop(op.get_bind(), checkfirst=True)

    discount_type_enum = postgresql.ENUM(name='discount_type')
    discount_type_enum.drop(op.get_bind(), checkfirst=True)

    student_fee_assignment_status_enum = postgresql.ENUM(name='student_fee_assignment_status')
    student_fee_assignment_status_enum.drop(op.get_bind(), checkfirst=True)

    fee_structure_status_enum = postgresql.ENUM(name='fee_structure_status')
    fee_structure_status_enum.drop(op.get_bind(), checkfirst=True)

    fee_category_enum = postgresql.ENUM(name='fee_category')
    fee_category_enum.drop(op.get_bind(), checkfirst=True)
