from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.identity.models.permission import IdentityPermission
from app.identity.repositories import (
    permission_repository,
    role_permission_repository,
    role_repository,
)

logger = get_logger(__name__)

ROLE_PERMISSIONS_MATRIX: dict[str, list[str]] = {
    "Super Admin": [
        "*",
    ],
    "School Admin": [
        "school.*",
        "academic_year.*",
        "academic_term.*",
        "class.*",
        "section.*",
        "student.*",
        "teacher.*",
        "parent.*",
        "subject.*",
        "attendance.*",
        "fees.*",
        "user.*",
        "role.*",
        "permission.*",
        "exam.*",
        "marks.*",
        "grading.*",
        "evaluation_config.*",
        "report_card.*",
        "timetable.*",
        "reports.*",
        "user_role.*",
        "role_permission.*",
        "progression_matrix.*",
        "progression.*",
        "teacher_attendance.*",
        "homework.*",
        "documents.*",
        "notification.*",
        "substitution.*",
        "hostel.*",
        "events.*",
        "staff_leave.*",
        "ai.*",
        "transport.*",
        "library.*",
        "admissions.*",
        "inventory.*",
        "teacher_cockpit.*",
    ],
    "Principal": [
        "academic_term.view",
        "student.*",
        "teacher.*",
        "parent.*",
        "attendance.*",
        "subject.*",
        "class.*",
        "section.*",
        "fees.*",
        "grading.view",
        "evaluation_config.view",
        "exam.*",
        "exam_schedule.*",
        "student_exam_result.*",
        "report_card.*",
        "reports.*",
        "homework.*",
        "documents.*",
        "notification.*",
        "timetable.*",
        "period_slot.*",
        "classroom.*",
        "substitution.*",
        "hostel.*",
        "events.*",
        "staff_leave.*",
        "ai.*",
        "transport.*",
        "library.*",
        "admissions.*",
        "inventory.*",
        "teacher_cockpit.view",
    ],
    "Vice Principal": [
        "academic_term.view",
        "student.*",
        "teacher.*",
        "attendance.*",
        "subject.*",
        "class.*",
        "section.*",
        "grading.view",
        "evaluation_config.view",
        "report_card.view",
        "report_card.generate",
        "report_card.finalize",
        "reports.*",
        "homework.view",
        "homework.create",
        "homework.update",
        "homework.publish",
        "homework.grade",
        "documents.view",
        "documents.upload",
        "documents.download",
        "documents.update",
        "documents.verify",
        "staff_leave.*",
        "substitution.*",
        "ai.*",
        "transport.*",
        "library.*",
        "admissions.*",
        "inventory.*",
        "teacher_cockpit.view",
    ],
    "Teacher": [
        "teacher_cockpit.view",
        "attendance.create",
        "attendance.view",
        "attendance.update",
        "student.view",
        "subject.view",
        "class.view",
        "section.view",
        "marks.create",
        "marks.update",
        "marks.view",
        "grading.view",
        "homework.view",
        "homework.create",
        "homework.update",
        "homework.publish",
        "homework.grade",
        "documents.view",
        "documents.upload",
        "documents.download",
        "documents.update",
        "staff_leave.view",
        "staff_leave.create",
        "staff_leave.cancel",
        "staff_leave.balance.view",
        "ai.assistant",
        "ai.risk.view",
        "ai.communication.draft",
        "transport.view",
        "library.view",
        "library.circulate",
        "inventory.view",
    ],
    "Class Teacher": [
        "teacher_cockpit.view",
        "attendance.create",
        "attendance.view",
        "attendance.update",
        "student.view",
        "subject.view",
        "marks.create",
        "marks.update",
        "marks.view",
        "class.view",
        "section.view",
        "grading.view",
        "homework.view",
        "homework.create",
        "homework.update",
        "homework.publish",
        "homework.grade",
        "documents.view",
        "documents.upload",
        "documents.download",
        "documents.update",
        "staff_leave.view",
        "staff_leave.create",
        "staff_leave.cancel",
        "staff_leave.balance.view",
        "ai.assistant",
        "ai.risk.view",
        "ai.communication.draft",
        "transport.view",
        "library.view",
        "library.circulate",
        "inventory.view",
    ],
    "Receptionist": [
        "student.create",
        "student.view",
        "parent.create",
        "parent.view",
        "documents.view",
        "documents.upload",
        "documents.download",
        "staff_leave.view",
        "staff_leave.create",
        "staff_leave.cancel",
        "staff_leave.balance.view",
        "transport.view",
        "library.view",
        "admissions.view",
        "admissions.create",
        "admissions.update",
        "inventory.view",
    ],
    "Accountant": [
        "fees.*",
        "student.view",
        "staff_leave.view",
        "staff_leave.create",
        "staff_leave.cancel",
        "staff_leave.balance.view",
        "transport.view",
        "library.view",
        "inventory.view",
    ],
    "Parent": [
        "student.view",
        "attendance.view",
        "fees.view",
        "marks.view",
        "homework.view",
        "timetable.view",
        "report_card.view",
        "documents.view",
        "documents.upload",
        "documents.download",
        "notification.view",
        "ai.risk.view",
        "transport.view",
        "library.view",
    ],
    "Student": [
        "attendance.view",
        "fees.view",
        "marks.view",
        "homework.view",
        "homework.submit",
        "timetable.view",
        "report_card.view",
        "documents.view",
        "documents.upload",
        "documents.download",
        "notification.view",
        "ai.risk.view",
        "transport.view",
        "library.view",
    ],
}


class RolePermissionSeeder:
    """
    Idempotent seeder for role ↔ permission matrix assignments.
    """

    def _resolve_permissions_for_patterns(
        self,
        patterns: list[str],
        all_permissions: list[IdentityPermission],
    ) -> list[IdentityPermission]:
        matched: set[IdentityPermission] = set()

        for pattern in patterns:
            pattern_str = pattern.strip().lower()

            if pattern_str == "*":
                matched.update(all_permissions)
            elif pattern_str.endswith(".*"):
                module_name = pattern_str[:-2]
                for perm in all_permissions:
                    if (
                        perm.module.lower() == module_name
                        or perm.name.lower().startswith(f"{module_name}.")
                    ):
                        matched.add(perm)
            else:
                for perm in all_permissions:
                    if perm.name.lower() == pattern_str:
                        matched.add(perm)

        return sorted(matched, key=lambda p: p.name)

    def seed(self, db: Session) -> dict[str, int]:
        created = 0
        skipped = 0

        all_permissions = permission_repository.get_all(db)

        for role_name, patterns in ROLE_PERMISSIONS_MATRIX.items():
            role = role_repository.get_by_name(
                db=db,
                school_id=None,
                name=role_name,
            )

            if role is None:
                logger.warning(
                    f"Role '{role_name}' not found when seeding permissions."
                )
                continue

            target_permissions = self._resolve_permissions_for_patterns(
                patterns,
                all_permissions,
            )

            for perm in target_permissions:
                if role_permission_repository.permission_exists(
                    db=db,
                    role_id=role.id,
                    permission_id=perm.id,
                ):
                    skipped += 1
                else:
                    role_permission_repository.assign_permission(
                        db=db,
                        role_id=role.id,
                        permission_id=perm.id,
                    )
                    created += 1

        return {
            "created": created,
            "skipped": skipped,
            "total": created + skipped,
        }


role_permission_seeder = RolePermissionSeeder()
