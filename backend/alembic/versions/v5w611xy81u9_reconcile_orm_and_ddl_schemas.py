"""reconcile_orm_and_ddl_schemas

Revision ID: v5w611xy81u9
Revises: u4v510wx70t8
Create Date: 2026-08-20 22:10:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "v5w611xy81u9"
down_revision: Union[str, Sequence[str], None] = "u4v510wx70t8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. identity_users missing columns
    op.add_column(
        "identity_users",
        sa.Column(
            "status",
            sa.String(length=50),
            nullable=False,
            server_default="ACTIVE",
        ),
    )
    op.add_column(
        "identity_users",
        sa.Column(
            "suspended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "identity_users",
        sa.Column(
            "suspension_reason",
            sa.String(length=500),
            nullable=True,
        ),
    )

    # 2. homeworks missing column
    op.add_column(
        "homeworks",
        sa.Column(
            "published_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # 3. student_certificates missing columns
    op.add_column(
        "student_certificates",
        sa.Column(
            "purpose",
            sa.String(length=255),
            nullable=True,
        ),
    )
    op.add_column(
        "student_certificates",
        sa.Column(
            "reason_for_leaving",
            sa.String(length=500),
            nullable=True,
        ),
    )
    op.add_column(
        "student_certificates",
        sa.Column(
            "conduct",
            sa.String(length=100),
            nullable=True,
        ),
    )
    op.add_column(
        "student_certificates",
        sa.Column(
            "metadata_json",
            sa.JSON(),
            nullable=True,
        ),
    )
    op.alter_column(
        "student_certificates",
        "certificate_data",
        existing_type=sa.JSON(),
        nullable=True,
    )

    # 4. schools missing columns
    op.add_column(
        "schools",
        sa.Column(
            "subscription_tier",
            sa.String(length=50),
            nullable=False,
            server_default="STANDARD",
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "max_students",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "max_teachers",
            sa.Integer(),
            nullable=True,
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "trial_ends_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "subscription_expires_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "grace_period_ends_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "suspended_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )
    op.add_column(
        "schools",
        sa.Column(
            "suspension_reason",
            sa.String(length=500),
            nullable=True,
        ),
    )

    # 5. progression_executions missing columns
    op.add_column(
        "progression_executions",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "progression_executions",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )

    # 6. progression_execution_items missing columns
    op.add_column(
        "progression_execution_items",
        sa.Column(
            "is_deleted",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )
    op.add_column(
        "progression_execution_items",
        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column("progression_execution_items", "deleted_at")
    op.drop_column("progression_execution_items", "is_deleted")
    op.drop_column("progression_executions", "deleted_at")
    op.drop_column("progression_executions", "is_deleted")
    op.drop_column("schools", "suspension_reason")
    op.drop_column("schools", "suspended_at")
    op.drop_column("schools", "grace_period_ends_at")
    op.drop_column("schools", "subscription_expires_at")
    op.drop_column("schools", "trial_ends_at")
    op.drop_column("schools", "max_teachers")
    op.drop_column("schools", "max_students")
    op.drop_column("schools", "subscription_tier")
    op.drop_column("student_certificates", "metadata_json")
    op.drop_column("student_certificates", "conduct")
    op.drop_column("student_certificates", "reason_for_leaving")
    op.drop_column("student_certificates", "purpose")
    op.drop_column("homeworks", "published_at")
    op.drop_column("identity_users", "suspension_reason")
    op.drop_column("identity_users", "suspended_at")
    op.drop_column("identity_users", "status")
