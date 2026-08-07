"""
create_subjects_table

Revision ID: 19700c81318a
Revises: e30192043d2f
Create Date: 2026-07-29 14:42:56.386688
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ENUM

# revision identifiers, used by Alembic.
revision: str = "19700c81318a"
down_revision: Union[str, Sequence[str], None] = "e30192043d2f"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Used only by the table column
subject_status_enum = ENUM(
    "ACTIVE",
    "INACTIVE",
    name="subject_status",
)


def upgrade() -> None:
    """Upgrade schema."""


    op.create_table(
        "subjects",

        sa.Column(
            "school_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "subject_code",
            sa.String(20),
            nullable=False,
        ),

        sa.Column(
            "subject_name",
            sa.String(100),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),

        sa.Column(
            "is_optional",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "status",
            subject_status_enum,
            nullable=False,
            server_default=sa.text("'ACTIVE'"),
        ),

        sa.Column(
            "id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),

        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),

        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            ondelete="CASCADE",
        ),

        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_subjects_school_id",
        "subjects",
        ["school_id"],
    )

    op.create_index(
        "ix_subjects_subject_code",
        "subjects",
        ["subject_code"],
    )

    op.create_index(
        "ix_subjects_subject_name",
        "subjects",
        ["subject_name"],
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_index(
        "ix_subjects_subject_name",
        table_name="subjects",
    )

    op.drop_index(
        "ix_subjects_subject_code",
        table_name="subjects",
    )

    op.drop_index(
        "ix_subjects_school_id",
        table_name="subjects",
    )

    op.drop_table("subjects")

