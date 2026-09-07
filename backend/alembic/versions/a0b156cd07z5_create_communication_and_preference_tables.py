"""Create user_communication_preferences, notification_templates, and in_app_notification_reads tables

Revision ID: a0b156cd07z5
Revises: z9a045bc06y4
Create Date: 2026-08-25 14:00:00.000000
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "a0b156cd07z5"
down_revision: Union[str, Sequence[str], None] = "z9a045bc06y4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. user_communication_preferences
    op.create_table(
        "user_communication_preferences",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("enable_in_app", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_email", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_sms", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_whatsapp", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_attendance", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_fees", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_exams", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_events", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_hostel", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_leave", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_emergency", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("enable_announcements", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["identity_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "user_id", name="uq_user_comm_pref_school_user"),
    )
    op.create_index("ix_user_comm_pref_school_user", "user_communication_preferences", ["school_id", "user_id"], unique=False)
    op.create_index(op.f("ix_user_communication_preferences_school_id"), "user_communication_preferences", ["school_id"], unique=False)
    op.create_index(op.f("ix_user_communication_preferences_user_id"), "user_communication_preferences", ["user_id"], unique=False)

    # 2. notification_templates
    op.create_table(
        "notification_templates",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("template_key", sa.String(length=100), nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("category", sa.String(length=50), server_default="ANNOUNCEMENT", nullable=False),
        sa.Column("title_template", sa.String(length=255), nullable=False),
        sa.Column("body_template", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", "template_key", name="uq_notif_tpl_school_key"),
    )
    op.create_index("ix_notification_templates_school_key", "notification_templates", ["school_id", "template_key"], unique=False)
    op.create_index(op.f("ix_notification_templates_school_id"), "notification_templates", ["school_id"], unique=False)
    op.create_index(op.f("ix_notification_templates_template_key"), "notification_templates", ["template_key"], unique=False)

    # 3. in_app_notification_reads
    op.create_table(
        "in_app_notification_reads",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("school_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("notification_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["notification_id"], ["notifications.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["identity_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "notification_id", name="uq_in_app_read_user_notif"),
    )
    op.create_index("ix_in_app_read_user", "in_app_notification_reads", ["user_id"], unique=False)
    op.create_index(op.f("ix_in_app_notification_reads_notification_id"), "in_app_notification_reads", ["notification_id"], unique=False)
    op.create_index(op.f("ix_in_app_notification_reads_school_id"), "in_app_notification_reads", ["school_id"], unique=False)
    op.create_index(op.f("ix_in_app_notification_reads_user_id"), "in_app_notification_reads", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_table("in_app_notification_reads")
    op.drop_table("notification_templates")
    op.drop_table("user_communication_preferences")
