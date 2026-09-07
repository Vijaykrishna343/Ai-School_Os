"""create hostel management tables

Revision ID: w6x712yz93v1
Revises: v5w611xy82u0
Create Date: 2026-08-24 22:00:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "w6x712yz93v1"
down_revision = "v5w611xy82u0"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. hostel_buildings
    op.create_table(
        "hostel_buildings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("gender_designation", sa.String(length=20), nullable=False, server_default="BOYS"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_building_school_code", "hostel_buildings", ["school_id", "code"], unique=True)

    # 2. hostel_rooms
    op.create_table(
        "hostel_rooms",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("building_id", sa.UUID(), nullable=False),
        sa.Column("room_number", sa.String(length=20), nullable=False),
        sa.Column("floor", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("room_type", sa.String(length=50), nullable=False, server_default="STANDARD"),
        sa.Column("capacity", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["building_id"], ["hostel_buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_room_bldg_number", "hostel_rooms", ["building_id", "room_number"], unique=True)

    # 3. hostel_beds
    op.create_table(
        "hostel_beds",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("bed_number", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="AVAILABLE"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["room_id"], ["hostel_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_bed_room_number", "hostel_beds", ["room_id", "bed_number"], unique=True)

    # 4. hostel_allocations
    op.create_table(
        "hostel_allocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("building_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("bed_id", sa.UUID(), nullable=False),
        sa.Column("allocated_at", sa.Date(), nullable=False),
        sa.Column("released_at", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="ACTIVE"),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["bed_id"], ["hostel_beds.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["building_id"], ["hostel_buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["room_id"], ["hostel_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_alloc_student", "hostel_allocations", ["school_id", "student_id"])
    op.create_index("idx_hostel_alloc_bed", "hostel_allocations", ["bed_id"])

    # 5. hostel_attendances
    op.create_table(
        "hostel_attendances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("attendance_date", sa.Date(), nullable=False),
        sa.Column("building_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PRESENT"),
        sa.Column("recorded_by_id", sa.UUID(), nullable=True),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["building_id"], ["hostel_buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["recorded_by_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["hostel_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_att_student_date", "hostel_attendances", ["school_id", "student_id", "attendance_date"], unique=True)

    # 6. hostel_outpasses
    op.create_table(
        "hostel_outpasses",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("building_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.UUID(), nullable=False),
        sa.Column("requested_by_id", sa.UUID(), nullable=True),
        sa.Column("reason", sa.String(length=255), nullable=False),
        sa.Column("destination", sa.String(length=255), nullable=False),
        sa.Column("departure_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expected_return_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("actual_checkout_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("actual_return_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("emergency_contact", sa.String(length=50), nullable=True),
        sa.Column("remarks", sa.String(length=255), nullable=True),
        sa.Column("approved_by_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["approved_by_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["building_id"], ["hostel_buildings.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["requested_by_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["room_id"], ["hostel_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_outpass_student", "hostel_outpasses", ["school_id", "student_id"])
    op.create_index("idx_hostel_outpass_status", "hostel_outpasses", ["school_id", "status"])

    # 7. hostel_fee_structures
    op.create_table(
        "hostel_fee_structures",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("amount", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_fee_struct_school", "hostel_fee_structures", ["school_id", "academic_year_id"])

    # 8. hostel_fee_allocations
    op.create_table(
        "hostel_fee_allocations",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("student_id", sa.UUID(), nullable=False),
        sa.Column("fee_structure_id", sa.UUID(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("amount_due", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("paid_amount", sa.Numeric(precision=10, scale=2), nullable=False, server_default="0.00"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="UNPAID"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["fee_structure_id"], ["hostel_fee_structures.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["student_id"], ["students.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_hostel_fee_alloc_student", "hostel_fee_allocations", ["school_id", "student_id"])


def downgrade() -> None:
    op.drop_table("hostel_fee_allocations")
    op.drop_table("hostel_fee_structures")
    op.drop_table("hostel_outpasses")
    op.drop_table("hostel_attendances")
    op.drop_table("hostel_allocations")
    op.drop_table("hostel_beds")
    op.drop_table("hostel_rooms")
    op.drop_table("hostel_buildings")
