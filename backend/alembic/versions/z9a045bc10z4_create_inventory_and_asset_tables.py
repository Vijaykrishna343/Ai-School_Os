"""create_inventory_and_asset_tables

Revision ID: z9a045bc10z4
Revises: z9a045bc09z3
Create Date: 2026-09-13 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc10z4'
down_revision: Union[str, Sequence[str], None] = 'z9a045bc09z3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. inventory_categories
    op.create_table(
        'inventory_categories',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_categories', schema=None) as batch_op:
        batch_op.create_index('ix_inventory_categories_school_id', ['school_id'], unique=False)
        batch_op.create_index(
            'uq_inventory_category_school_code',
            ['school_id', 'code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 2. inventory_locations
    op.create_table(
        'inventory_locations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('location_type', sa.Enum('WAREHOUSE', 'STORE_ROOM', 'LAB', 'LIBRARY_STORE', 'OFFICE', 'CLASSROOM', 'SPORTS_ROOM', 'OTHER', name='inventorylocationtype', native_enum=False), nullable=False),
        sa.Column('parent_location_id', sa.UUID(), nullable=True),
        sa.Column('building_name', sa.String(length=100), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_location_id'], ['inventory_locations.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_locations', schema=None) as batch_op:
        batch_op.create_index('ix_inventory_locations_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_inventory_locations_parent_id', ['parent_location_id'], unique=False)
        batch_op.create_index(
            'uq_inventory_location_school_code',
            ['school_id', 'code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 3. inventory_vendors
    op.create_table(
        'inventory_vendors',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('contact_name', sa.String(length=100), nullable=True),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=30), nullable=True),
        sa.Column('address', sa.String(length=500), nullable=True),
        sa.Column('tax_id', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_vendors', schema=None) as batch_op:
        batch_op.create_index('ix_inventory_vendors_school_id', ['school_id'], unique=False)
        batch_op.create_index(
            'uq_inventory_vendor_school_code',
            ['school_id', 'code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 4. inventory_items
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('category_id', sa.UUID(), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('item_type', sa.Enum('CONSUMABLE', 'ASSET', name='inventoryitemtype', native_enum=False), nullable=False),
        sa.Column('unit_of_measure', sa.String(length=30), nullable=False, server_default='PCS'),
        sa.Column('track_individually', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('reorder_level', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['category_id'], ['inventory_categories.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_items', schema=None) as batch_op:
        batch_op.create_index('ix_inventory_items_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_inventory_items_category_id', ['category_id'], unique=False)
        batch_op.create_index('ix_inventory_items_item_type', ['item_type'], unique=False)
        batch_op.create_index(
            'uq_inventory_item_school_code',
            ['school_id', 'item_code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 5. inventory_stock
    op.create_table(
        'inventory_stock',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('item_id', sa.UUID(), nullable=False),
        sa.Column('location_id', sa.UUID(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reserved_quantity', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('last_counted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('quantity >= 0', name='ck_inventory_stock_quantity_non_negative'),
        sa.CheckConstraint('reserved_quantity >= 0', name='ck_inventory_stock_reserved_non_negative'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_stock', schema=None) as batch_op:
        batch_op.create_index('ix_inventory_stock_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_inventory_stock_item_id', ['item_id'], unique=False)
        batch_op.create_index('ix_inventory_stock_location_id', ['location_id'], unique=False)
        batch_op.create_index(
            'uq_inventory_stock_item_location',
            ['school_id', 'item_id', 'location_id'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 6. physical_assets
    op.create_table(
        'physical_assets',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('item_id', sa.UUID(), nullable=False),
        sa.Column('location_id', sa.UUID(), nullable=True),
        sa.Column('vendor_id', sa.UUID(), nullable=True),
        sa.Column('asset_tag', sa.String(length=50), nullable=False),
        sa.Column('serial_number', sa.String(length=100), nullable=True),
        sa.Column('model_number', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('AVAILABLE', 'ASSIGNED', 'IN_REPAIR', 'DAMAGED', 'LOST', 'RETIRED', 'DISPOSED', name='assetstatus', native_enum=False), nullable=False),
        sa.Column('condition', sa.Enum('EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'DAMAGED', name='assetcondition', native_enum=False), nullable=False),
        sa.Column('purchase_date', sa.Date(), nullable=True),
        sa.Column('purchase_cost', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('warranty_expiry_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.String(length=1000), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['location_id'], ['inventory_locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vendor_id'], ['inventory_vendors.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('physical_assets', schema=None) as batch_op:
        batch_op.create_index('ix_physical_assets_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_physical_assets_item_id', ['item_id'], unique=False)
        batch_op.create_index('ix_physical_assets_location_id', ['location_id'], unique=False)
        batch_op.create_index('ix_physical_assets_vendor_id', ['vendor_id'], unique=False)
        batch_op.create_index('ix_physical_assets_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_physical_asset_school_tag',
            ['school_id', 'asset_tag'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 7. inventory_stock_movements
    op.create_table(
        'inventory_stock_movements',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('item_id', sa.UUID(), nullable=False),
        sa.Column('source_location_id', sa.UUID(), nullable=True),
        sa.Column('destination_location_id', sa.UUID(), nullable=True),
        sa.Column('movement_type', sa.Enum('PURCHASE_RECEIPT', 'ISSUE', 'TRANSFER', 'RETURN', 'ADJUSTMENT', 'DISCARD', name='inventorystockmovementtype', native_enum=False), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('reference_number', sa.String(length=100), nullable=True),
        sa.Column('vendor_id', sa.UUID(), nullable=True),
        sa.Column('performed_by_user_id', sa.UUID(), nullable=True),
        sa.Column('movement_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('quantity > 0', name='ck_inv_movement_quantity_positive'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['source_location_id'], ['inventory_locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['destination_location_id'], ['inventory_locations.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['vendor_id'], ['inventory_vendors.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['performed_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('inventory_stock_movements', schema=None) as batch_op:
        batch_op.create_index('ix_inv_movements_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_inv_movements_item_id', ['item_id'], unique=False)
        batch_op.create_index('ix_inv_movements_src_loc_id', ['source_location_id'], unique=False)
        batch_op.create_index('ix_inv_movements_dst_loc_id', ['destination_location_id'], unique=False)
        batch_op.create_index('ix_inv_movements_type', ['movement_type'], unique=False)
        batch_op.create_index('ix_inv_movements_date', ['movement_date'], unique=False)

    # 8. asset_assignments
    op.create_table(
        'asset_assignments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('asset_id', sa.UUID(), nullable=False),
        sa.Column('assignment_type', sa.Enum('STAFF', 'STUDENT', 'CLASSROOM', 'DEPARTMENT', 'LOCATION', 'OTHER', name='assetassignmenttype', native_enum=False), nullable=False),
        sa.Column('teacher_id', sa.UUID(), nullable=True),
        sa.Column('student_id', sa.UUID(), nullable=True),
        sa.Column('classroom_id', sa.UUID(), nullable=True),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('department_name', sa.String(length=100), nullable=True),
        sa.Column('assigned_date', sa.Date(), nullable=False),
        sa.Column('expected_return_date', sa.Date(), nullable=True),
        sa.Column('actual_return_date', sa.Date(), nullable=True),
        sa.Column('assigned_by_user_id', sa.UUID(), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'RETURNED', 'TRANSFERRED', name='assetassignmentstatus', native_enum=False), nullable=False),
        sa.Column('condition_on_assignment', sa.Enum('EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'DAMAGED', name='assetcondition', native_enum=False), nullable=False),
        sa.Column('condition_on_return', sa.Enum('EXCELLENT', 'GOOD', 'FAIR', 'POOR', 'DAMAGED', name='assetcondition', native_enum=False), nullable=True),
        sa.Column('remarks', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['asset_id'], ['physical_assets.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['classroom_id'], ['classrooms.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_by_user_id'], ['identity_users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('asset_assignments', schema=None) as batch_op:
        batch_op.create_index('ix_asset_assignments_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_asset_assignments_asset_id', ['asset_id'], unique=False)
        batch_op.create_index('ix_asset_assignments_teacher_id', ['teacher_id'], unique=False)
        batch_op.create_index('ix_asset_assignments_student_id', ['student_id'], unique=False)
        batch_op.create_index('ix_asset_assignments_classroom_id', ['classroom_id'], unique=False)
        batch_op.create_index('ix_asset_assignments_user_id', ['user_id'], unique=False)
        batch_op.create_index('ix_asset_assignments_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_active_asset_assignment',
            ['school_id', 'asset_id'],
            unique=True,
            postgresql_where=sa.text("is_deleted = false AND status = 'ACTIVE'"),
            sqlite_where=sa.text("is_deleted = 0 AND status = 'ACTIVE'")
        )


def downgrade() -> None:
    op.drop_table('asset_assignments')
    op.drop_table('inventory_stock_movements')
    op.drop_table('physical_assets')
    op.drop_table('inventory_stock')
    op.drop_table('inventory_items')
    op.drop_table('inventory_vendors')
    op.drop_table('inventory_locations')
    op.drop_table('inventory_categories')
