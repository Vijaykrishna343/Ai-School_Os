from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.identity.models.role import IdentityRole
from app.identity.repositories import role_repository

logger = get_logger(__name__)

DEFAULT_ROLES: list[dict[str, Any]] = [
    {
        "name": "Super Admin",
        "description": "System Super Administrator with full platform access across all resources.",
        "is_system": True,
    },
    {
        "name": "School Admin",
        "description": "School Administrator with full access to school management and operations.",
        "is_system": True,
    },
    {
        "name": "Principal",
        "description": "School Principal with full administrative and academic oversight access.",
        "is_system": True,
    },
    {
        "name": "Vice Principal",
        "description": "Vice Principal with administrative and academic oversight access.",
        "is_system": True,
    },
    {
        "name": "Teacher",
        "description": "Teacher with access to attendance, subjects, student viewing, and marks.",
        "is_system": True,
    },
    {
        "name": "Class Teacher",
        "description": "Class Teacher with class management, attendance, student viewing, and marks.",
        "is_system": True,
    },
    {
        "name": "Receptionist",
        "description": "Receptionist with access to student and parent registration and viewing.",
        "is_system": True,
    },
    {
        "name": "Accountant",
        "description": "Accountant with access to fee management and student viewing.",
        "is_system": True,
    },
    {
        "name": "Parent",
        "description": "Parent with access to view student profile, attendance, fees, and marks.",
        "is_system": True,
    },
    {
        "name": "Student",
        "description": "Student with access to personal attendance, fees, and marks.",
        "is_system": True,
    },
]


class RoleSeeder:
    """
    Idempotent seeder for system roles.
    """

    def seed(self, db: Session) -> dict[str, int]:
        created = 0
        skipped = 0

        for role_data in DEFAULT_ROLES:
            existing = role_repository.get_by_name(
                db=db,
                school_id=None,
                name=role_data["name"],
            )

            if existing is not None:
                skipped += 1
            else:
                role = IdentityRole(
                    school_id=None,
                    name=role_data["name"],
                    description=role_data["description"],
                    is_system=role_data["is_system"],
                )
                role_repository.create(db, role)
                created += 1

        return {
            "created": created,
            "skipped": skipped,
            "total": created + skipped,
        }


role_seeder = RoleSeeder()
