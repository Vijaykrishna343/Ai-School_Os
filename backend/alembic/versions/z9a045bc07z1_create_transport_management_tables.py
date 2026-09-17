"""create_transport_management_tables

Revision ID: z9a045bc07z1
Revises: 7aaaba637c7f
Create Date: 2026-09-09 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'z9a045bc07z1'
down_revision: Union[str, Sequence[str], None] = '7aaaba637c7f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. transport_vehicles
    op.create_table(
        'transport_vehicles',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('registration_number', sa.String(length=50), nullable=False),
        sa.Column('vehicle_code', sa.String(length=50), nullable=False),
        sa.Column('vehicle_type', sa.Enum('BUS', 'VAN', 'MINIBUS', 'AUTO', 'OTHER', name='vehicletype', native_enum=False), nullable=False),
        sa.Column('seating_capacity', sa.Integer(), nullable=False),
        sa.Column('fuel_type', sa.Enum('DIESEL', 'PETROL', 'CNG', 'ELECTRIC', 'HYBRID', name='fueltype', native_enum=False), nullable=False),
        sa.Column('insurance_expiry_date', sa.Date(), nullable=True),
        sa.Column('fitness_expiry_date', sa.Date(), nullable=True),
        sa.Column('gps_device_id', sa.String(length=100), nullable=True),
        sa.Column('status', sa.Enum('ACTIVE', 'MAINTENANCE', 'DECOMMISSIONED', name='vehiclestatus', native_enum=False), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('seating_capacity > 0', name='ck_transport_vehicle_capacity_positive'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('transport_vehicles', schema=None) as batch_op:
        batch_op.create_index('ix_transport_vehicles_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_transport_vehicles_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_transport_vehicle_school_reg',
            ['school_id', 'registration_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )
        batch_op.create_index(
            'uq_transport_vehicle_school_code',
            ['school_id', 'vehicle_code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 2. transport_drivers
    op.create_table(
        'transport_drivers',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('license_number', sa.String(length=100), nullable=False),
        sa.Column('license_expiry_date', sa.Date(), nullable=True),
        sa.Column('contact_number', sa.String(length=30), nullable=False),
        sa.Column('emergency_contact', sa.String(length=30), nullable=True),
        sa.Column('staff_id', sa.UUID(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['staff_id'], ['teachers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('transport_drivers', schema=None) as batch_op:
        batch_op.create_index('ix_transport_drivers_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_transport_drivers_is_active', ['is_active'], unique=False)
        batch_op.create_index(
            'uq_transport_driver_school_license',
            ['school_id', 'license_number'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 3. transport_routes
    op.create_table(
        'transport_routes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('route_code', sa.String(length=50), nullable=False),
        sa.Column('route_name', sa.String(length=150), nullable=False),
        sa.Column('description', sa.String(length=255), nullable=True),
        sa.Column('vehicle_id', sa.UUID(), nullable=True),
        sa.Column('driver_id', sa.UUID(), nullable=True),
        sa.Column('attendant_name', sa.String(length=150), nullable=True),
        sa.Column('attendant_phone', sa.String(length=30), nullable=True),
        sa.Column('morning_start_time', sa.Time(), nullable=True),
        sa.Column('evening_start_time', sa.Time(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['vehicle_id'], ['transport_vehicles.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['driver_id'], ['transport_drivers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('transport_routes', schema=None) as batch_op:
        batch_op.create_index('ix_transport_routes_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_transport_routes_vehicle_id', ['vehicle_id'], unique=False)
        batch_op.create_index('ix_transport_routes_driver_id', ['driver_id'], unique=False)
        batch_op.create_index('ix_transport_routes_is_active', ['is_active'], unique=False)
        batch_op.create_index(
            'uq_transport_route_school_code',
            ['school_id', 'route_code'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 4. transport_route_stops
    op.create_table(
        'transport_route_stops',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('stop_name', sa.String(length=150), nullable=False),
        sa.Column('stop_code', sa.String(length=50), nullable=False),
        sa.Column('sequence_order', sa.Integer(), nullable=False),
        sa.Column('morning_pickup_time', sa.Time(), nullable=True),
        sa.Column('afternoon_drop_time', sa.Time(), nullable=True),
        sa.Column('landmark', sa.String(length=255), nullable=True),
        sa.Column('pickup_fee_amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('sequence_order > 0', name='ck_transport_stop_sequence_positive'),
        sa.CheckConstraint('pickup_fee_amount >= 0', name='ck_transport_stop_fee_non_negative'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['transport_routes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('transport_route_stops', schema=None) as batch_op:
        batch_op.create_index('ix_transport_route_stops_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_transport_route_stops_route_id', ['route_id'], unique=False)
        batch_op.create_index('ix_transport_route_stops_sequence', ['route_id', 'sequence_order'], unique=False)
        batch_op.create_index(
            'uq_transport_stop_route_sequence',
            ['route_id', 'sequence_order'],
            unique=True,
            postgresql_where=sa.text('is_deleted = false'),
            sqlite_where=sa.text('is_deleted = 0')
        )

    # 5. student_transport_allocations
    op.create_table(
        'student_transport_allocations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('route_id', sa.UUID(), nullable=False),
        sa.Column('pickup_stop_id', sa.UUID(), nullable=True),
        sa.Column('drop_stop_id', sa.UUID(), nullable=True),
        sa.Column('academic_year_id', sa.UUID(), nullable=False),
        sa.Column('allocation_type', sa.Enum('TWO_WAY', 'PICKUP_ONLY', 'DROP_ONLY', name='transportallocationtype', native_enum=False), nullable=False),
        sa.Column('status', sa.Enum('ACTIVE', 'SUSPENDED', 'CANCELLED', name='transportallocationstatus', native_enum=False), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('remarks', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['route_id'], ['transport_routes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['pickup_stop_id'], ['transport_route_stops.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['drop_stop_id'], ['transport_route_stops.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['academic_year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('student_transport_allocations', schema=None) as batch_op:
        batch_op.create_index('ix_student_transport_alloc_school_id', ['school_id'], unique=False)
        batch_op.create_index('ix_student_transport_alloc_student_id', ['student_id'], unique=False)
        batch_op.create_index('ix_student_transport_alloc_route_id', ['route_id'], unique=False)
        batch_op.create_index('ix_student_transport_alloc_academic_year_id', ['academic_year_id'], unique=False)
        batch_op.create_index('ix_student_transport_alloc_status', ['status'], unique=False)
        batch_op.create_index(
            'uq_active_student_transport_alloc',
            ['school_id', 'student_id', 'academic_year_id'],
            unique=True,
            postgresql_where=sa.text("is_deleted = false AND status = 'ACTIVE'"),
            sqlite_where=sa.text("is_deleted = 0 AND status = 'ACTIVE'")
        )


def downgrade() -> None:
    op.drop_table('student_transport_allocations')
    op.drop_table('transport_route_stops')
    op.drop_table('transport_routes')
    op.drop_table('transport_drivers')
    op.drop_table('transport_vehicles')
