"""create_identity_users_table

Revision ID: c5bdad0bb5f3
Revises: 19700c81318a
Create Date: 2026-08-01 18:17:02.437547
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "c5bdad0bb5f3"
down_revision: Union[str, Sequence[str], None] = "19700c81318a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create Identity Users table."""

    op.create_table(
        "identity_users",

        # ==========================================================
        # Tenant
        # ==========================================================
        sa.Column(
            "school_id",
            sa.UUID(),
            nullable=False,
        ),

        # ==========================================================
        # Authentication
        # ==========================================================
        sa.Column(
            "email",
            sa.String(length=255),
            nullable=False,
        ),

        sa.Column(
            "username",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "password_hash",
            sa.String(length=255),
            nullable=False,
        ),

        # ==========================================================
        # Personal
        # ==========================================================
        sa.Column(
            "first_name",
            sa.String(length=100),
            nullable=False,
        ),

        sa.Column(
            "last_name",
            sa.String(length=100),
            nullable=True,
        ),

        sa.Column(
            "phone",
            sa.String(length=20),
            nullable=True,
        ),

        # ==========================================================
        # Status
        # ==========================================================
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.true(),
        ),

        sa.Column(
            "is_verified",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),

        sa.Column(
            "last_login",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        # ==========================================================
        # CommonModel Fields
        # ==========================================================
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
            server_default=sa.false(),
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

    # ==========================================================
    # Indexes
    # ==========================================================

    op.create_index(
        "ix_identity_users_school_id",
        "identity_users",
        ["school_id"],
    )

    op.create_index(
        "ix_identity_users_email",
        "identity_users",
        ["email"],
    )

    op.create_index(
        "ix_identity_users_username",
        "identity_users",
        ["username"],
    )

    # ==========================================================
    # Composite Unique Constraints
    # ==========================================================

    is_sqlite = op.get_bind().dialect.name == 'sqlite'
    if not is_sqlite:
        op.create_unique_constraint(
            "uq_identity_users_school_email",
            "identity_users",
            ["school_id", "email"],
        )
        op.create_unique_constraint(
            "uq_identity_users_school_username",
            "identity_users",
            ["school_id", "username"],
        )
    else:
        with op.batch_alter_table("identity_users") as batch_op:
            batch_op.create_unique_constraint(
                "uq_identity_users_school_email",
                ["school_id", "email"],
            )
            batch_op.create_unique_constraint(
                "uq_identity_users_school_username",
                ["school_id", "username"],
            )


def downgrade() -> None:
    """Drop Identity Users table."""

    op.drop_constraint(
        "uq_identity_users_school_username",
        "identity_users",
        type_="unique",
    )

    op.drop_constraint(
        "uq_identity_users_school_email",
        "identity_users",
        type_="unique",
    )

    op.drop_index(
        "ix_identity_users_username",
        table_name="identity_users",
    )

    op.drop_index(
        "ix_identity_users_email",
        table_name="identity_users",
    )

    op.drop_index(
        "ix_identity_users_school_id",
        table_name="identity_users",
    )

    op.drop_table("identity_users")