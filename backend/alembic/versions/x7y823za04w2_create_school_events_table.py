"""create school_events table

Revision ID: x7y823za04w2
Revises: w6x712yz93v1
Create Date: 2026-08-24 22:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "x7y823za04w2"
down_revision = "w6x712yz93v1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "school_events",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("school_id", sa.UUID(), nullable=False),
        sa.Column("academic_year_id", sa.UUID(), nullable=True),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("event_type", sa.String(length=50), nullable=False, server_default="HOLIDAY"),
        sa.Column("start_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("end_datetime", sa.DateTime(timezone=True), nullable=False),
        sa.Column("all_day", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("venue", sa.String(length=255), nullable=True),
        sa.Column("organizer_id", sa.UUID(), nullable=True),
        sa.Column("audience_scope", sa.String(length=50), nullable=False, server_default="SCHOOL"),
        sa.Column("target_class_id", sa.UUID(), nullable=True),
        sa.Column("target_section_id", sa.UUID(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["academic_year_id"], ["academic_years.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["organizer_id"], ["identity_users.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["school_id"], ["schools.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["target_class_id"], ["school_classes.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["target_section_id"], ["sections.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_school_event_school_id", "school_events", ["school_id"])
    op.create_index("idx_school_event_dates", "school_events", ["school_id", "start_datetime", "end_datetime"])
    op.create_index("idx_school_event_audience", "school_events", ["school_id", "audience_scope", "status"])


def downgrade() -> None:
    op.drop_table("school_events")
