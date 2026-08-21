"""
Relationship Authorization & IDOR Protection Module.

Provides standard helper functions to enforce Parent -> Linked Children,
Student -> Self, and Teacher -> Assigned Resources scoping.
"""
from __future__ import annotations

from uuid import UUID
from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException
from app.identity.models.user import IdentityUser
from app.models.parent.parent import Parent
from app.models.student.student import Student


def get_user_role_names(user: IdentityUser) -> list[str]:
    """Returns a list of role names associated with the user."""
    return [r.name for r in getattr(user, "roles", []) if not getattr(r, "is_deleted", False)]


def resolve_parent_linked_student_ids(db: Session, school_id: UUID, current_user: IdentityUser) -> list[UUID]:
    """Returns list of Student IDs linked to the current parent user."""
    parent = db.scalar(
        select(Parent).where(Parent.email == current_user.email, Parent.school_id == school_id)
    )
    if not parent and current_user.phone:
        parent = db.scalar(
            select(Parent).where(Parent.primary_phone == current_user.phone, Parent.school_id == school_id)
        )
    if not parent:
        return []

    students = db.scalars(
        select(Student.id).where(
            Student.parent_id == parent.id,
            Student.school_id == school_id,
            Student.is_deleted == False,
        )
    ).all()
    return list(students)


def resolve_student_id_for_user(db: Session, school_id: UUID, current_user: IdentityUser) -> UUID | None:
    """Returns Student ID for the current student user."""
    student = db.scalar(
        select(Student).where(
            Student.school_id == school_id,
            Student.is_deleted == False,
            (Student.admission_number == current_user.username) | (Student.email == current_user.email),
        )
    )
    return student.id if student else None


def enforce_relationship_access(
    db: Session,
    school_id: UUID,
    current_user: IdentityUser,
    target_student_id: UUID | None = None,
) -> UUID | list[UUID] | None:
    """
    Enforces Parent -> Child and Student -> Self access control.

    Returns:
        - For Super Admin / School Admin / Principal / Teacher: returns target_student_id as requested.
        - For Parent: ensures target_student_id belongs to parent's children. Returns allowed student ID(s).
        - For Student: forces target_student_id = authenticated student ID.
    """
    if getattr(current_user, "is_super_admin", False):
        return target_student_id

    role_names = get_user_role_names(current_user)

    # Operational staff roles have school-level access
    if any(r in ("School Admin", "Principal", "Vice Principal", "Teacher", "Class Teacher", "Accountant") for r in role_names):
        return target_student_id

    # Parent Role: Must be linked to the child
    if "Parent" in role_names:
        linked_student_ids = resolve_parent_linked_student_ids(db, school_id, current_user)
        if not linked_student_ids:
            raise ForbiddenException("No linked children found for current parent profile.")

        if target_student_id is not None:
            if target_student_id not in linked_student_ids:
                raise ForbiddenException("Access denied. Student does not belong to this parent.")
            return target_student_id
        return linked_student_ids

    # Student Role: Must be self
    if "Student" in role_names:
        authenticated_student_id = resolve_student_id_for_user(db, school_id, current_user)
        if not authenticated_student_id:
            raise ForbiddenException("Student profile not found for current user.")

        if target_student_id is not None and target_student_id != authenticated_student_id:
            raise ForbiddenException("Access denied. Students can only access their own records.")
        return authenticated_student_id

    return target_student_id
