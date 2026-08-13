from __future__ import annotations

from sqlalchemy.orm import Session

from app.common.logger.logger import get_logger
from app.identity.models.permission import IdentityPermission
from app.identity.repositories import permission_repository

logger = get_logger(__name__)

DEFAULT_PERMISSIONS: list[dict[str, str]] = [
    # School Management
    {"name": "school.create", "module": "school", "action": "create", "description": "Create school"},
    {"name": "school.view", "module": "school", "action": "view", "description": "View school"},
    {"name": "school.update", "module": "school", "action": "update", "description": "Update school"},
    {"name": "school.delete", "module": "school", "action": "delete", "description": "Delete school"},

    # Academic Year
    {"name": "academic_year.create", "module": "academic_year", "action": "create", "description": "Create academic year"},
    {"name": "academic_year.view", "module": "academic_year", "action": "view", "description": "View academic year"},
    {"name": "academic_year.update", "module": "academic_year", "action": "update", "description": "Update academic year"},
    {"name": "academic_year.delete", "module": "academic_year", "action": "delete", "description": "Delete academic year"},

    # Academic Term
    {"name": "academic_term.create", "module": "academic_term", "action": "create", "description": "Create academic term"},
    {"name": "academic_term.view", "module": "academic_term", "action": "view", "description": "View academic term"},
    {"name": "academic_term.update", "module": "academic_term", "action": "update", "description": "Update academic term"},
    {"name": "academic_term.delete", "module": "academic_term", "action": "delete", "description": "Delete academic term"},

    # Class
    {"name": "class.create", "module": "class", "action": "create", "description": "Create class"},
    {"name": "class.view", "module": "class", "action": "view", "description": "View class"},
    {"name": "class.update", "module": "class", "action": "update", "description": "Update class"},
    {"name": "class.delete", "module": "class", "action": "delete", "description": "Delete class"},

    # Section
    {"name": "section.create", "module": "section", "action": "create", "description": "Create section"},
    {"name": "section.view", "module": "section", "action": "view", "description": "View section"},
    {"name": "section.update", "module": "section", "action": "update", "description": "Update section"},
    {"name": "section.delete", "module": "section", "action": "delete", "description": "Delete section"},

    # Student
    {"name": "student.create", "module": "student", "action": "create", "description": "Create student"},
    {"name": "student.view", "module": "student", "action": "view", "description": "View student"},
    {"name": "student.update", "module": "student", "action": "update", "description": "Update student"},
    {"name": "student.delete", "module": "student", "action": "delete", "description": "Delete student"},
    {"name": "student.promote", "module": "student", "action": "promote", "description": "Promote student"},
    {"name": "student.retain", "module": "student", "action": "retain", "description": "Retain student"},
    {"name": "student.transition", "module": "student", "action": "transition", "description": "Transition academic year"},
    {"name": "student.tc.create", "module": "student", "action": "tc.create", "description": "Create transfer certificate"},
    {"name": "student.tc.view", "module": "student", "action": "tc.view", "description": "View transfer certificate"},

    # Academic Progression Matrix & Preview & Execution
    {"name": "progression_matrix.view", "module": "progression_matrix", "action": "view", "description": "View class progression rules"},
    {"name": "progression_matrix.manage", "module": "progression_matrix", "action": "manage", "description": "Manage class progression rules"},
    {"name": "progression.preview", "module": "progression", "action": "preview", "description": "Preview academic year progression"},
    {"name": "progression.execute", "module": "progression", "action": "execute", "description": "Execute academic year progression rollover"},


    # Teacher
    {"name": "teacher.create", "module": "teacher", "action": "create", "description": "Create teacher"},
    {"name": "teacher.view", "module": "teacher", "action": "view", "description": "View teacher"},
    {"name": "teacher.update", "module": "teacher", "action": "update", "description": "Update teacher"},
    {"name": "teacher.delete", "module": "teacher", "action": "delete", "description": "Delete teacher"},

    # Parent
    {"name": "parent.create", "module": "parent", "action": "create", "description": "Create parent"},
    {"name": "parent.view", "module": "parent", "action": "view", "description": "View parent"},
    {"name": "parent.update", "module": "parent", "action": "update", "description": "Update parent"},
    {"name": "parent.delete", "module": "parent", "action": "delete", "description": "Delete parent"},

    # Subject
    {"name": "subject.create", "module": "subject", "action": "create", "description": "Create subject"},
    {"name": "subject.view", "module": "subject", "action": "view", "description": "View subject"},
    {"name": "subject.update", "module": "subject", "action": "update", "description": "Update subject"},
    {"name": "subject.delete", "module": "subject", "action": "delete", "description": "Delete subject"},

    # Attendance
    {"name": "attendance.create", "module": "attendance", "action": "create", "description": "Create attendance"},
    {"name": "attendance.view", "module": "attendance", "action": "view", "description": "View attendance"},
    {"name": "attendance.update", "module": "attendance", "action": "update", "description": "Update attendance"},
    {"name": "attendance.delete", "module": "attendance", "action": "delete", "description": "Delete attendance"},

    # Fees
    {"name": "fees.create", "module": "fees", "action": "create", "description": "Create fees"},
    {"name": "fees.view", "module": "fees", "action": "view", "description": "View fees"},
    {"name": "fees.update", "module": "fees", "action": "update", "description": "Update fees"},
    {"name": "fees.delete", "module": "fees", "action": "delete", "description": "Delete fees"},

    # Exam
    {"name": "exam.create", "module": "exam", "action": "create", "description": "Create exam"},
    {"name": "exam.view", "module": "exam", "action": "view", "description": "View exam"},
    {"name": "exam.update", "module": "exam", "action": "update", "description": "Update exam"},
    {"name": "exam.delete", "module": "exam", "action": "delete", "description": "Delete exam"},

    # Grading & Evaluation Config
    {"name": "grading.manage", "module": "grading", "action": "manage", "description": "Manage grading configuration"},
    {"name": "grading.view", "module": "grading", "action": "view", "description": "View grading configuration"},
    {"name": "evaluation_config.create", "module": "evaluation_config", "action": "create", "description": "Create evaluation config"},
    {"name": "evaluation_config.view", "module": "evaluation_config", "action": "view", "description": "View evaluation config"},
    {"name": "evaluation_config.update", "module": "evaluation_config", "action": "update", "description": "Update evaluation config"},
    {"name": "evaluation_config.delete", "module": "evaluation_config", "action": "delete", "description": "Delete evaluation config"},

    # Report Cards
    {"name": "report_card.generate", "module": "report_card", "action": "generate", "description": "Generate report cards"},
    {"name": "report_card.view", "module": "report_card", "action": "view", "description": "View report cards"},
    {"name": "report_card.edit_remarks", "module": "report_card", "action": "edit_remarks", "description": "Edit report card remarks"},
    {"name": "report_card.finalize", "module": "report_card", "action": "finalize", "description": "Finalize report cards"},
    {"name": "report_card.publish", "module": "report_card", "action": "publish", "description": "Publish report cards"},
    {"name": "report_card.reopen", "module": "report_card", "action": "reopen", "description": "Reopen finalized report cards"},


    # Marks
    {"name": "marks.create", "module": "marks", "action": "create", "description": "Create marks"},
    {"name": "marks.view", "module": "marks", "action": "view", "description": "View marks"},
    {"name": "marks.update", "module": "marks", "action": "update", "description": "Update marks"},
    {"name": "marks.delete", "module": "marks", "action": "delete", "description": "Delete marks"},

    # Timetable
    {"name": "timetable.create", "module": "timetable", "action": "create", "description": "Create timetable"},
    {"name": "timetable.view", "module": "timetable", "action": "view", "description": "View timetable"},
    {"name": "timetable.update", "module": "timetable", "action": "update", "description": "Update timetable"},
    {"name": "timetable.delete", "module": "timetable", "action": "delete", "description": "Delete timetable"},
    {"name": "timetable.publish", "module": "timetable", "action": "publish", "description": "Publish timetable"},
    {"name": "timetable.archive", "module": "timetable", "action": "archive", "description": "Archive timetable"},

    # Teacher Substitution
    {"name": "substitution.create", "module": "substitution", "action": "create", "description": "Create teacher substitution"},
    {"name": "substitution.view", "module": "substitution", "action": "view", "description": "View teacher substitution"},
    {"name": "substitution.update", "module": "substitution", "action": "update", "description": "Update teacher substitution"},
    {"name": "substitution.delete", "module": "substitution", "action": "delete", "description": "Delete teacher substitution"},

    # User
    {"name": "user.create", "module": "user", "action": "create", "description": "Create user"},
    {"name": "user.view", "module": "user", "action": "view", "description": "View user"},
    {"name": "user.update", "module": "user", "action": "update", "description": "Update user"},
    {"name": "user.delete", "module": "user", "action": "delete", "description": "Delete user"},

    # Role
    {"name": "role.create", "module": "role", "action": "create", "description": "Create role"},
    {"name": "role.view", "module": "role", "action": "view", "description": "View role"},
    {"name": "role.update", "module": "role", "action": "update", "description": "Update role"},
    {"name": "role.delete", "module": "role", "action": "delete", "description": "Delete role"},

    # Permission
    {"name": "permission.create", "module": "permission", "action": "create", "description": "Create permission"},
    {"name": "permission.view", "module": "permission", "action": "view", "description": "View permission"},
    {"name": "permission.update", "module": "permission", "action": "update", "description": "Update permission"},
    {"name": "permission.delete", "module": "permission", "action": "delete", "description": "Delete permission"},

    # Reports
    {"name": "reports.create", "module": "reports", "action": "create", "description": "Create reports"},
    {"name": "reports.view", "module": "reports", "action": "view", "description": "View reports"},
    {"name": "reports.update", "module": "reports", "action": "update", "description": "Update reports"},
    {"name": "reports.delete", "module": "reports", "action": "delete", "description": "Delete reports"},

    # User Role Assignments
    {"name": "user_role.assign", "module": "user_role", "action": "assign", "description": "Assign user role"},
    {"name": "user_role.remove", "module": "user_role", "action": "remove", "description": "Remove user role"},
    {"name": "user_role.view", "module": "user_role", "action": "view", "description": "View user role"},

    # Role Permission Assignments
    {"name": "role_permission.assign", "module": "role_permission", "action": "assign", "description": "Assign role permission"},
    {"name": "role_permission.remove", "module": "role_permission", "action": "remove", "description": "Remove role permission"},
    {"name": "role_permission.view", "module": "role_permission", "action": "view", "description": "View role permission"},
]


class PermissionSeeder:
    """
    Idempotent seeder for system permissions grouped by module.
    """

    def seed(self, db: Session) -> dict[str, int]:
        created = 0
        skipped = 0

        for perm_data in DEFAULT_PERMISSIONS:
            existing = permission_repository.get_by_name(
                db,
                perm_data["name"],
            )

            if existing is not None:
                skipped += 1
            else:
                permission = IdentityPermission(
                    name=perm_data["name"],
                    description=perm_data["description"],
                    module=perm_data["module"],
                    action=perm_data["action"],
                )
                permission_repository.create(db, permission)
                created += 1

        return {
            "created": created,
            "skipped": skipped,
            "total": created + skipped,
        }


permission_seeder = PermissionSeeder()
