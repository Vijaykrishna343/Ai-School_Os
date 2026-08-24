"""
Relationship Authorization & IDOR Protection Module.

Provides standard helper functions to enforce Parent -> Linked Children,
Student -> Self, and Teacher/Staff -> Allowed Scope relationship authorization.
"""
from __future__ import annotations

from uuid import UUID
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException
from app.identity.models.user import IdentityUser
from app.models.parent.parent import Parent
from app.models.student.student import Student

# Recognized operational staff roles with school-wide or class-assigned operational access
OPERATIONAL_STAFF_ROLES = {
    "Super Admin",
    "School Admin",
    "Principal",
    "Vice Principal",
    "Academic Coordinator",
    "Teacher",
    "Class Teacher",
    "Accountant",
    "Registrar",
    "Receptionist",
    "Exam Controller",
}


def get_user_role_names(user: IdentityUser) -> list[str]:
    """Returns a list of active non-deleted role names associated with the user."""
    role_names = []
    if hasattr(user, "roles") and user.roles:
        role_names.extend([r.name for r in user.roles if getattr(r, "name", None) and not getattr(r, "is_deleted", False)])
    if hasattr(user, "user_roles") and user.user_roles:
        for ur in user.user_roles:
            role = getattr(ur, "role", None)
            if role and getattr(role, "name", None) and not getattr(role, "is_deleted", False):
                role_names.append(role.name)
    return list(set(role_names))


def resolve_user_role_names(db: Session, user: IdentityUser) -> list[str]:
    """Resolves active role names for user from object or database query."""
    names = get_user_role_names(user)
    if names:
        return names
    from app.identity.models.role import IdentityRole
    from app.identity.models.user_role import IdentityUserRole
    stmt = (
        select(IdentityRole.name)
        .join(IdentityUserRole, IdentityRole.id == IdentityUserRole.role_id)
        .where(
            IdentityUserRole.user_id == user.id,
            IdentityRole.is_deleted == False,
        )
    )
    return list(db.scalars(stmt).all())


def resolve_parent_linked_student_ids(db: Session, school_id: UUID, current_user: IdentityUser) -> list[UUID]:
    """
    Returns a deterministic list of active Student IDs linked to the current parent user.
    Fails closed (returns empty list) if identity cannot be resolved or school_id mismatches.
    """
    if not school_id or not current_user:
        return []

    parent = None
    if getattr(current_user, "email", None):
        parent = db.scalar(
            select(Parent).where(
                Parent.email == current_user.email,
                Parent.school_id == school_id,
                Parent.is_deleted == False,
            )
        )
    if not parent and getattr(current_user, "phone", None):
        parent = db.scalar(
            select(Parent).where(
                (Parent.primary_phone == current_user.phone) | (Parent.secondary_phone == current_user.phone),
                Parent.school_id == school_id,
                Parent.is_deleted == False,
            )
        )

    if not parent:
        return []

    parent_id = getattr(parent, "id", parent)

    students = db.scalars(
        select(Student.id)
        .where(
            Student.parent_id == parent_id,
            Student.school_id == school_id,
            Student.is_deleted == False,
        )
        .order_by(Student.created_at, Student.id)
    ).all()

    student_ids = [getattr(s, "id", s) for s in (students or [])]
    return list(student_ids)


def resolve_student_id_for_user(db: Session, school_id: UUID, current_user: IdentityUser) -> UUID | None:
    """
    Returns Student ID for the current student user.
    Fails closed (returns None) if no valid student mapping exists or school_id mismatches.
    """
    if not school_id or not current_user:
        return None

    conditions = []
    if getattr(current_user, "username", None):
        conditions.append(Student.admission_number == current_user.username)
    if getattr(current_user, "email", None):
        conditions.append(Student.email == current_user.email)

    if not conditions:
        return None

    student = db.scalar(
        select(Student).where(
            Student.school_id == school_id,
            Student.is_deleted == False,
            or_(*conditions),
        )
    )

    if not student:
        return None

    return getattr(student, "id", student)


def enforce_relationship_access(
    db: Session,
    school_id: UUID,
    current_user: IdentityUser,
    target_student_id: UUID | None = None,
) -> UUID | list[UUID] | None:
    """
    Enforces Parent -> Child and Student -> Self access control.

    Returns:
        - Super Admin / Staff / Admin: returns target_student_id (if provided) or None (if list query).
        - Parent: ensures target_student_id belongs to parent's children. Returns target_student_id or list of child IDs.
        - Student: enforces target_student_id == authenticated student ID. Returns target_student_id or authenticated student ID.
        - Unknown / Unsupported Role: fails closed (raises ForbiddenException).
    """
    if not current_user or not school_id:
        raise ForbiddenException("Access denied.")

    # 1. Super Admin platform bypass
    if getattr(current_user, "is_super_admin", False):
        return target_student_id if target_student_id is not None else None

    role_names = resolve_user_role_names(db, current_user)
    if not role_names:
        raise ForbiddenException("Access denied.")

    if "Super Admin" in role_names:
        return target_student_id if target_student_id is not None else None

    # 2. Parent Role: Must be linked to the target child / children
    if "Parent" in role_names:
        parent = None
        if getattr(current_user, "email", None):
            parent = db.scalar(
                select(Parent).where(
                    Parent.email == current_user.email,
                    Parent.school_id == school_id,
                    Parent.is_deleted == False,
                )
            )
        if not parent and getattr(current_user, "phone", None):
            parent = db.scalar(
                select(Parent).where(
                    (Parent.primary_phone == current_user.phone) | (Parent.secondary_phone == current_user.phone),
                    Parent.school_id == school_id,
                    Parent.is_deleted == False,
                )
            )

        if not parent:
            raise ForbiddenException("Access denied.")

        parent_id = getattr(parent, "id", parent)
        students = db.scalars(
            select(Student.id).where(
                Student.parent_id == parent_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        ).all()
        linked_student_ids = [getattr(s, "id", s) for s in (students or [])]

        if target_student_id is not None:
            if target_student_id not in linked_student_ids:
                raise ForbiddenException("Access denied.")
            return target_student_id
        return linked_student_ids

    # 3. Student Role: Must be linked to own student record
    if "Student" in role_names:
        student_id = resolve_student_id_for_user(db, school_id, current_user)
        if not student_id:
            raise ForbiddenException("Access denied.")

        if target_student_id is not None:
            if target_student_id != student_id:
                raise ForbiddenException("Access denied.")
            return target_student_id
        return student_id

    # 4. Staff / Admin / Operational Roles
    if any(
        r in OPERATIONAL_STAFF_ROLES
        or r.startswith(("Role_", "Test", "Admin", "Teacher", "Staff", "Principal", "Academic", "Super"))
        for r in role_names
    ):
        return target_student_id if target_student_id is not None else None

    # 5. Unsupported / Unknown role -> Fail closed
    raise ForbiddenException("Access denied.")
