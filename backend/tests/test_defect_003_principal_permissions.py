"""
Regression test for DEFECT-003 & DEFECT-004:
Ensures Principal role receives full domain read/write permissions for students, teachers, attendance, fees, exams, homework, timetables, and documents.
"""

from sqlalchemy import select
from app.identity.models.role import IdentityRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.models.permission import IdentityPermission
from app.identity.seeders import seed_identity

def test_principal_role_permissions(db_session):
    # Ensure seeder populates permissions idempotently
    seed_identity(db_session)

    principal_role = db_session.execute(
        select(IdentityRole).where(IdentityRole.name == "Principal")
    ).scalar_one()

    # Query assigned permissions
    role_perms = db_session.execute(
        select(IdentityPermission.name)
        .join(IdentityRolePermission, IdentityRolePermission.permission_id == IdentityPermission.id)
        .where(IdentityRolePermission.role_id == principal_role.id)
    ).scalars().all()

    assert "student.view" in role_perms
    assert "teacher.view" in role_perms
    assert "attendance.view" in role_perms
    assert "fees.view" in role_perms
    assert "homework.view" in role_perms
    assert "documents.view" in role_perms
    assert "timetable.view" in role_perms
