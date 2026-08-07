"""add_rbac_tables

Revision ID: a7ce9ec3026e
Revises: c5bdad0bb5f3
Create Date: 2026-08-02 20:54:18.163967
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# ---------------------------------------------------------------------
# Revision identifiers
# ---------------------------------------------------------------------

revision: str = "a7ce9ec3026e"
down_revision: Union[str, Sequence[str], None] = "c5bdad0bb5f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create RBAC tables."""

    # ==============================================================
    # Identity Permissions
    # ==============================================================

    op.create_table(
        "identity_permissions",

        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.String(255),
            nullable=True,
        ),

        sa.Column(
            "module",
            sa.String(50),
            nullable=False,
        ),

        sa.Column(
            "action",
            sa.String(50),
            nullable=False,
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
        ),

        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_identity_permissions",
        ),

        sa.UniqueConstraint(
            "name",
            name="uq_identity_permissions_name",
        ),

        comment="Stores all permissions available in the system.",
    )

    op.create_index(
        "ix_identity_permissions_name",
        "identity_permissions",
        ["name"],
    )

    op.create_index(
        "ix_identity_permissions_module",
        "identity_permissions",
        ["module"],
    )

    # ==============================================================
    # Identity Roles
    # ==============================================================

    op.create_table(
        "identity_roles",

        sa.Column(
            "school_id",
            sa.UUID(),
            nullable=True,
        ),

        sa.Column(
            "name",
            sa.String(100),
            nullable=False,
        ),

        sa.Column(
            "description",
            sa.String(255),
            nullable=True,
        ),

        sa.Column(
            "is_system",
            sa.Boolean(),
            nullable=False,
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
        ),

        sa.Column(
            "deleted_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),

        sa.PrimaryKeyConstraint(
            "id",
            name="pk_identity_roles",
        ),

        sa.ForeignKeyConstraint(
            ["school_id"],
            ["schools.id"],
            name="fk_identity_roles_school",
            ondelete="CASCADE",
        ),

        sa.UniqueConstraint(
            "school_id",
            "name",
            name="uq_identity_roles_school_name",
        ),

        comment="Stores roles available within each school.",
    )

    op.create_index(
        "ix_identity_roles_school_id",
        "identity_roles",
        ["school_id"],
    )

    op.create_index(
        "ix_identity_roles_name",
        "identity_roles",
        ["name"],
    )

    # ==============================================================
    # Identity Role Permissions
    # ==============================================================

    op.create_table(
        "identity_role_permissions",

        sa.Column(
            "role_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "permission_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "role_id",
            "permission_id",
            name="pk_identity_role_permissions",
        ),

        sa.ForeignKeyConstraint(
            ["role_id"],
            ["identity_roles.id"],
            name="fk_identity_role_permissions_role",
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["identity_permissions.id"],
            name="fk_identity_role_permissions_permission",
            ondelete="CASCADE",
        ),

        comment="Associates roles with permissions.",
    )

    # ==============================================================
    # Identity User Roles
    # ==============================================================

    op.create_table(
        "identity_user_roles",

        sa.Column(
            "user_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.Column(
            "role_id",
            sa.UUID(),
            nullable=False,
        ),

        sa.PrimaryKeyConstraint(
            "user_id",
            "role_id",
            name="pk_identity_user_roles",
        ),

        sa.ForeignKeyConstraint(
            ["user_id"],
            ["identity_users.id"],
            name="fk_identity_user_roles_user",
            ondelete="CASCADE",
        ),

        sa.ForeignKeyConstraint(
            ["role_id"],
            ["identity_roles.id"],
            name="fk_identity_user_roles_role",
            ondelete="CASCADE",
        ),

        comment="Associates users with roles.",
    )


def downgrade() -> None:
    """Drop RBAC tables."""

    # ==============================================================
    # User Roles
    # ==============================================================

    op.drop_table("identity_user_roles")

    # ==============================================================
    # Role Permissions
    # ==============================================================

    op.drop_table("identity_role_permissions")

    # ==============================================================
    # Roles
    # ==============================================================

    op.drop_index(
        "ix_identity_roles_name",
        table_name="identity_roles",
    )

    op.drop_index(
        "ix_identity_roles_school_id",
        table_name="identity_roles",
    )

    op.drop_table("identity_roles")

    # ==============================================================
    # Permissions
    # ==============================================================

    op.drop_index(
        "ix_identity_permissions_module",
        table_name="identity_permissions",
    )

    op.drop_index(
        "ix_identity_permissions_name",
        table_name="identity_permissions",
    )

    op.drop_table("identity_permissions")