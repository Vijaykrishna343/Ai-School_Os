import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.teacher.teacher import Teacher
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.services.staff_leave_service import staff_leave_service


def test_staff_leave_rbac_and_tenant_isolation(client: TestClient, db_session: Session):
    seed_identity(db_session)

    # Setup School A
    school_a = School(name="School A", code=f"SCHA-{uuid.uuid4().hex[:4]}", address_line1="A", city="A", district="A", state="A", postal_code="500001")
    db_session.add(school_a)
    # Setup School B
    school_b = School(name="School B", code=f"SCHB-{uuid.uuid4().hex[:4]}", address_line1="B", city="B", district="B", state="B", postal_code="500002")
    db_session.add(school_b)
    db_session.commit()

    ay_a = AcademicYear(school_id=school_a.id, name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_current=True)
    ay_b = AcademicYear(school_id=school_b.id, name="2026-2027", start_date=date(2026, 6, 1), end_date=date(2027, 5, 31), is_current=True)
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    teacher_role = db_session.query(IdentityRole).filter_by(name="Teacher", school_id=None).first()
    parent_role = db_session.query(IdentityRole).filter_by(name="Parent", school_id=None).first()
    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()

    # Teacher A in School A
    teacher_a_user = IdentityUser(school_id=school_a.id, email="teacher_a@schoola.com", password_hash="h", first_name="A", last_name="T", is_active=True, status="ACTIVE")
    db_session.add(teacher_a_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=teacher_a_user.id, role_id=teacher_role.id))
    db_session.commit()
    teacher_a = Teacher(
        id=teacher_a_user.id,
        school_id=school_a.id,
        first_name="A",
        last_name="T",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 6, 1),
        qualification="B.Ed",
        phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        email=f"teacher_a_{uuid.uuid4().hex[:6]}@schoola.com",
        address_line1="123 Staff St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(teacher_a)

    # Admin B in School B
    admin_b_user = IdentityUser(school_id=school_b.id, email="admin_b@schoolb.com", password_hash="h", first_name="B", last_name="A", is_active=True, status="ACTIVE")
    db_session.add(admin_b_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_b_user.id, role_id=admin_role.id))

    # Parent A in School A
    parent_a_user = IdentityUser(school_id=school_a.id, email="parent_a@schoola.com", password_hash="h", first_name="P", last_name="A", is_active=True, status="ACTIVE")
    db_session.add(parent_a_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=parent_a_user.id, role_id=parent_role.id))
    db_session.commit()

    token_ta = jwt_manager.create_access_token(user_id=teacher_a_user.id, school_id=school_a.id)
    token_ab = jwt_manager.create_access_token(user_id=admin_b_user.id, school_id=school_b.id)
    token_pa = jwt_manager.create_access_token(user_id=parent_a_user.id, school_id=school_a.id)

    headers_ta = {"Authorization": f"Bearer {token_ta}"}
    headers_ab = {"Authorization": f"Bearer {token_ab}"}
    headers_pa = {"Authorization": f"Bearer {token_pa}"}

    # 1. Parent cannot create or view staff leave -> 403 Forbidden
    res_parent = client.get("/api/v1/staff-leave/types", headers=headers_pa)
    assert res_parent.status_code == 403

    # 2. Teacher A seeds leave types and creates a request in School A
    types = staff_leave_service.get_leave_types(db_session, school_a.id)
    casual_type = types[0]

    res_create = client.post(
        "/api/v1/staff-leave",
        headers=headers_ta,
        json={
            "academic_year_id": str(ay_a.id),
            "leave_type_id": str(casual_type.id),
            "start_date": (date.today() + timedelta(days=10)).isoformat(),
            "end_date": (date.today() + timedelta(days=11)).isoformat(),
            "reason": "Family function",
        },
    )
    assert res_create.status_code == 201
    req_id = res_create.json()["data"]["id"]

    # 3. Admin B from School B tries to approve Teacher A's request in School A -> 404 (Tenant Isolation)
    res_cross_app = client.post(
        f"/api/v1/staff-leave/{req_id}/approve",
        headers=headers_ab,
        json={"remarks": "Cross school approval attempt"},
    )
    assert res_cross_app.status_code == 404
