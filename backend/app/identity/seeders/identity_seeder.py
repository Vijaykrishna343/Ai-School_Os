from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.identity.seeders.permission_seeder import permission_seeder
from app.identity.seeders.role_permission_seeder import role_permission_seeder
from app.identity.seeders.role_seeder import role_seeder

logger = get_logger(__name__)


def seed_identity(db: Session) -> dict[str, Any]:
    """
    Master seeder function for Identity module.

    Initializes permissions, system roles, and role-permission matrix assignments.
    Idempotent and safe to run multiple times against a fresh or existing database.

    Args:
        db: Active SQLAlchemy database session.

    Returns:
        dict containing summary statistics of created and skipped entities.
    """
    try:
        # Phase 1: Permissions
        logger.info("Seeding Permissions...")
        perm_stats = permission_seeder.seed(db)
        logger.info(f"{perm_stats['created']} permissions created")
        logger.info(f"{perm_stats['skipped']} skipped")

        # Phase 2: Roles
        logger.info("Seeding Roles...")
        role_stats = role_seeder.seed(db)
        logger.info(f"{role_stats['created']} roles created")
        logger.info(f"{role_stats['skipped']} skipped")

        # Phase 3: Role Permission Assignments
        logger.info("Assigning Permissions...")
        assign_stats = role_permission_seeder.seed(db)
        logger.info(f"{assign_stats['created']} assignments created")
        logger.info(f"{assign_stats['skipped']} skipped")

        logger.info("Success")

        summary = {
            "permissions_created": perm_stats["created"],
            "permissions_skipped": perm_stats["skipped"],
            "roles_created": role_stats["created"],
            "roles_skipped": role_stats["skipped"],
            "assignments_created": assign_stats["created"],
            "assignments_skipped": assign_stats["skipped"],
        }
        return summary

    except Exception as e:
        db.rollback()
        logger.error(
            f"Failed to seed identity data: {str(e)}",
            exc_info=True,
        )
        raise
