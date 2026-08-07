"""create_teachers_table

Revision ID: e30192043d2f
Revises: 04b289984b39
Create Date: 2026-07-28 19:50:41.389388
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision: str = "e30192043d2f"
down_revision: Union[str, Sequence[str], None] = "04b289984b39"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Existing PostgreSQL ENUMs
gender_enum = ENUM(
    "MALE",
    "FEMALE",
    "OTHER",
    name="gender",
    create_type=False,
)

blood_group_enum = ENUM(
    "A_POSITIVE",
    "A_NEGATIVE",
    "B_POSITIVE",
    "B_NEGATIVE",
    "AB_POSITIVE",
    "AB_NEGATIVE",
    "O_POSITIVE",
    "O_NEGATIVE",
    "UNKNOWN",
    name="blood_group",
    create_type=False,
)

# New ENUM
teacher_status_enum = ENUM(
    "ACTIVE",
    "INACTIVE",
    "ON_LEAVE",
    "RESIGNED",
    name="teacher_status",
    create_type=False,
)


def upgrade() -> None:

    # Create only the new enum
    teacher_status_enum.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "teachers",

        sa.Column("school_id", sa.UUID(), nullable=False),

        sa.Column("employee_id", sa.String(30), nullable=False),

        sa.Column("first_name", sa.String(100), nullable=False),

        sa.Column("middle_name", sa.String(100), nullable=True),

        sa.Column("last_name", sa.String(100), nullable=True),

        sa.Column("gender", gender_enum, nullable=False),

        sa.Column("blood_group", blood_group_enum, nullable=True),

        sa.Column("date_of_birth", sa.Date(), nullable=False),

        sa.Column("joining_date", sa.Date(), nullable=False),

        sa.Column("qualification", sa.String(255), nullable=False),

        sa.Column("specialization", sa.String(255), nullable=True),

        sa.Column(
            "experience_years",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),

        sa.Column(
            "salary",
            sa.Numeric(10, 2),
            nullable=True,
),

        sa.Column("phone", sa.String(15), nullable=False),

        sa.Column("email", sa.String(255), nullable=False),

        sa.Column("emergency_contact", sa.String(15), nullable=True),

        sa.Column("profile_photo_url", sa.String(500), nullable=True),

        sa.Column("address_line1", sa.String(255), nullable=False),

        sa.Column("address_line2", sa.String(255), nullable=True),

        sa.Column("city", sa.String(100), nullable=False),

        sa.Column("district", sa.String(100), nullable=False),

        sa.Column("state", sa.String(100), nullable=False),

        sa.Column("country", sa.String(100), nullable=False),

        sa.Column("postal_code", sa.String(10), nullable=False),

        

        sa.Column("remarks", sa.String(500), nullable=True),

        sa.Column("status", teacher_status_enum, nullable=False),

        sa.Column("id", sa.UUID(), nullable=False),

        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),

        sa.Column("is_deleted", sa.Boolean(), nullable=False),

        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),

        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),

        sa.UniqueConstraint("employee_id"),

        sa.UniqueConstraint("email"),

        sa.UniqueConstraint("phone"),
    )

    op.create_index("ix_teachers_email", "teachers", ["email"])
    op.create_index("ix_teachers_employee_id", "teachers", ["employee_id"])
    op.create_index("ix_teachers_first_name", "teachers", ["first_name"])
    op.create_index("ix_teachers_last_name", "teachers", ["last_name"])
    op.create_index("ix_teachers_phone", "teachers", ["phone"])
    op.create_index("ix_teachers_school_id", "teachers", ["school_id"])
    op.create_index("ix_teachers_status", "teachers", ["status"])


def downgrade() -> None:

    op.drop_index("ix_teachers_status", table_name="teachers")
    op.drop_index("ix_teachers_school_id", table_name="teachers")
    op.drop_index("ix_teachers_phone", table_name="teachers")
    op.drop_index("ix_teachers_last_name", table_name="teachers")
    op.drop_index("ix_teachers_first_name", table_name="teachers")
    op.drop_index("ix_teachers_employee_id", table_name="teachers")
    op.drop_index("ix_teachers_email", table_name="teachers")

    op.drop_table("teachers")
    