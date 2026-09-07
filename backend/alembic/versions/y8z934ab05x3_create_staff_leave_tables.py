"""create staff_leave tables

Revision ID: y8z934ab05x3
Revises: x7y823za04w2
Create Date: 2026-08-25 13:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "y8z934ab05x3"
down_revision = "x7y823za04w2"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. staff_leave_types
    op.create_table(
        "staff_leave_types",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("code", sa.String(length=30), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("max_days_per_year", sa.Numeric(precision=5, scale=2), nullable=False, server_default="12.00"),
        sa.Column("requires_attachment", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_paid", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "code", "is_deleted", name="uq_staff_leave_types_school_code"),
    )
    op.create_index("ix_staff_leave_types_school_id", "staff_leave_types", ["school_id"])
    op.create_index("ix_staff_leave_types_code", "staff_leave_types", ["code"])

    # 2. staff_leave_balances
    op.create_table(
        "staff_leave_balances",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=False),
        sa.Column("leave_type_id", sa.UUID(), nullable=False),
        sa.Column("allocated_days", sa.Numeric(precision=5, scale=2), nullable=False, server_default="12.00"),
        sa.Column("used_days", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("pending_days", sa.Numeric(precision=5, scale=2), nullable=False, server_default="0.00"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["leave_type_id"], ["staff_leave_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "teacher_id", "academic_year_id", "leave_type_id", "is_deleted", name="uq_staff_leave_balances_teacher_year_type"),
    )
    op.create_index("ix_staff_leave_balances_school_id", "staff_leave_balances", ["school_id"])
    op.create_index("ix_staff_leave_balances_teacher_id", "staff_leave_balances", ["teacher_id"])
    op.create_index("ix_staff_leave_balances_academic_year_id", "staff_leave_balances", ["academic_year_id"])
    op.create_index("ix_staff_leave_balances_leave_type_id", "staff_leave_balances", ["leave_type_id"])

    # 3. staff_leave_requests
    op.create_table(
        "staff_leave_requests",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("teacher_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=False),
        sa.Column("leave_type_id", sa.UUID(), nullable=False),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=False),
        sa.Column("requested_days", sa.Numeric(precision=5, scale=2), nullable=False, server_default="1.00"),
        sa.Column("half_day_type", sa.String(length=20), nullable=False, server_default="FULL_DAY"),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("attachment_url", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="PENDING"),
        sa.Column("requested_by_user_id", sa.UUID(), nullable=True),
        sa.Column("approved_by_user_id", sa.UUID(), nullable=True),
        sa.Column("rejected_by_user_id", sa.UUID(), nullable=True),
        sa.Column("cancelled_by_user_id", sa.UUID(), nullable=True),
        sa.Column("approval_remarks", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejected_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("cancelled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint("end_date >= start_date", name="ck_staff_leave_requests_date_range"),
        sa.CheckConstraint("requested_days > 0", name="ck_staff_leave_requests_positive_days"),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["approved_by_user_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["cancelled_by_user_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["leave_type_id"], ["staff_leave_types.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["rejected_by_user_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["requested_by_user_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_leave_requests_school_id", "staff_leave_requests", ["school_id"])
    op.create_index("ix_staff_leave_requests_teacher_id", "staff_leave_requests", ["teacher_id"])
    op.create_index("ix_staff_leave_requests_academic_year_id", "staff_leave_requests", ["academic_year_id"])
    op.create_index("ix_staff_leave_requests_status", "staff_leave_requests", ["status"])
    op.create_index("ix_staff_leave_requests_start_date", "staff_leave_requests", ["start_date"])
    op.create_index("ix_staff_leave_requests_end_date", "staff_leave_requests", ["end_date"])

    # 4. staff_leave_approval_history
    op.create_table(
        "staff_leave_approval_history",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("leave_request_id", sa.UUID(), nullable=False),
        sa.Column("action_by_user_id", sa.UUID(), nullable=False),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("from_status", sa.String(length=20), nullable=True),
        sa.Column("to_status", sa.String(length=20), nullable=False),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["action_by_user_id"], ["identity_users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["leave_request_id"], ["staff_leave_requests.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_leave_approval_history_school_id", "staff_leave_approval_history", ["school_id"])
    op.create_index("ix_staff_leave_approval_history_request_id", "staff_leave_approval_history", ["leave_request_id"])


def downgrade() -> None:
    op.drop_table("staff_leave_approval_history")
    op.drop_table("staff_leave_requests")
    op.drop_table("staff_leave_balances")
    op.drop_table("staff_leave_types")
