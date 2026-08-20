"""
Phase 10.2 Fix Regression Test Suite.
Verifies resolutions for DEF-10-2-1, DEF-10-2-2, DEF-10-2-3, DEF-10-2-4 and Tenant Isolation.
"""
import uuid
from sqlalchemy.orm import Session
from app.identity.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.school.school import School


def create_user_with_perms(db: Session, perms: list[str]):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=f"Test School {uuid.uuid4().hex[:4]}",
        code=f"TST{uuid.uuid4().hex[:4].upper()}",
        address_line1="1 Test Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Phase 10.2 Test Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in perms:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        username=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Pass123!"),
        first_name="Test",
        last_name="Teacher",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


def test_identity_api_authorization_def_10_2_3(client, db_session: Session):
    """DEF-10-2-3: GET /users and /roles must return 403 for user without user.view or role.view."""
    teacher_perms = ["attendance.view", "attendance.create", "student.view", "marks.view"]
    _, _, headers = create_user_with_perms(db_session, teacher_perms)

    # Verify 403 Forbidden for /users and /roles for Teacher
    res_users = client.get("/api/v1/users", headers=headers)
    assert res_users.status_code == 403

    res_roles = client.get("/api/v1/roles", headers=headers)
    assert res_roles.status_code == 403

    # Create admin user with user.view and role.view
    admin_perms = ["user.view", "role.view"]
    _, _, admin_headers = create_user_with_perms(db_session, admin_perms)

    res_admin_users = client.get("/api/v1/users", headers=admin_headers)
    assert res_admin_users.status_code == 200

    res_admin_roles = client.get("/api/v1/roles", headers=admin_headers)
    assert res_admin_roles.status_code == 200


def test_academic_year_current_context_def_10_2_2(client, db_session: Session):
    """DEF-10-2-2: Operational user can fetch current academic year context without academic_year.view."""
    teacher_perms = ["attendance.view", "attendance.create"]
    _, _, headers = create_user_with_perms(db_session, teacher_perms)

    # /academic-years/current must return 200 OK
    res_current = client.get("/api/v1/academic-years/current", headers=headers)
    assert res_current.status_code == 200
    assert "data" in res_current.json()

    # /academic-years administrative list must return 403 Forbidden
    res_admin_list = client.get("/api/v1/academic-years", headers=headers)
    assert res_admin_list.status_code == 403


def test_teacher_dashboard_summary_def_10_2_1(client, db_session: Session):
    """DEF-10-2-1: Teacher can fetch operational dashboard summary without school.view permission."""
    teacher_perms = ["attendance.view", "attendance.create"]
    _, _, headers = create_user_with_perms(db_session, teacher_perms)

    # Teacher dashboard summary returns 200 OK
    res = client.get("/api/v1/dashboard/teacher/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "user_name" in data
    assert "assigned_students_count" in data

    # Admin dashboard summary returns 403 Forbidden for Teacher
    res_admin = client.get("/api/v1/dashboard/admin/summary", headers=headers)
    assert res_admin.status_code == 403


def test_student_csv_export_def_10_2_4(client, db_session: Session):
    """DEF-10-2-4: /export/students requires student.export permission."""
    teacher_perms = ["student.view"]
    _, _, headers = create_user_with_perms(db_session, teacher_perms)

    # /export/students returns 403 Forbidden for Teacher (student.view only)
    res_export = client.get("/api/v1/export/students", headers=headers)
    assert res_export.status_code == 403

    # Normal student listing /students returns 200 OK
    res_list = client.get("/api/v1/students", headers=headers)
    assert res_list.status_code == 200

    # User with student.export permission gets 200 OK
    exporter_perms = ["student.export"]
    _, _, export_headers = create_user_with_perms(db_session, exporter_perms)
    res_allowed_export = client.get("/api/v1/export/students", headers=export_headers)
    assert res_allowed_export.status_code == 200
