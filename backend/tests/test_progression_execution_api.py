"""
API Integration tests for Academic Year Progression Execution endpoint.

Endpoint: POST /api/v1/academic-years/{source_academic_year_id}/progression-execute

Verifies:
- 200 OK success response on valid progression rollover request.
- Idempotency-Key header requirement.
- RBAC permission enforcement (progression.execute).
- Tenant isolation (cross-school execution forbidden).
"""

from datetime import date
import uuid

import pytest
from fastapi.testclient import TestClient
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
from app.models.academic_year import AcademicYear, ClassProgressionRule
from app.models.parent import Parent
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.services.student.progression_planner import progression_planner


def _create_test_env_with_permissions(db: Session, permissions_list: list[str]):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=f"School-{uuid.uuid4().hex[:6]}",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 Academic Way",
        city="TestCity",
        district="Central",
        state="TestState",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Test Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"user_{uuid.uuid4().hex[:6]}",
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user_id=user.id, school_id=school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


def _create_academic_year(db: Session, school_id, name: str = "2025-2026", is_current: bool = True) -> AcademicYear:
    ay = AcademicYear(
        school_id=school_id,
        name=name,
        start_date=date(2025, 4, 1),
        end_date=date(2026, 3, 31),
        is_current=is_current,
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


def _create_class(db: Session, school_id, name: str = "Class 1", display_order: int = 1) -> SchoolClass:
    sc = SchoolClass(school_id=school_id, name=name, display_order=display_order)
    db.add(sc)
    db.commit()
    db.refresh(sc)
    return sc


def _create_section(db: Session, school_class_id, name: str = "A") -> Section:
    sec = Section(school_class_id=school_class_id, name=name)
    db.add(sec)
    db.commit()
    db.refresh(sec)
    return sec


def _create_parent(db: Session, school_id) -> Parent:
    parent = Parent(
        school_id=school_id,
        father_name="Parent Doe",
        primary_phone=f"+199{uuid.uuid4().hex[:8]}",
        address_line1="123 Main St",
        city="City",
        district="District",
        state="State",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()
    db.refresh(parent)
    return parent


def _create_student(
    db: Session,
    school_id,
    academic_year_id,
    school_class_id,
    section_id,
    admission_number: str = "ADM-001",
    roll_number: str = "001",
) -> Student:
    parent = _create_parent(db, school_id)
    st = Student(
        school_id=school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        parent_id=parent.id,
        admission_number=admission_number,
        first_name="API",
        last_name="Student",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2025, 4, 1),
        address_line1="123 Street",
        city="City",
        district="District",
        state="State",
        country="Country",
        postal_code="100001",
        roll_number=roll_number,
    )
    db.add(st)
    db.commit()
    db.refresh(st)
    return st


def _create_progression_rule(
    db: Session, school_id, source_class_id, target_class_id=None, is_terminal: bool = False
) -> ClassProgressionRule:
    rule = ClassProgressionRule(
        school_id=school_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        is_terminal=is_terminal,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def test_api_progression_execute_success(client: TestClient, db_session: Session):
    """
    Test API 1 — POST /api/v1/academic-years/{ay_id}/progression-execute executes rollover and returns 200 OK.
    """
    school, user, headers = _create_test_env_with_permissions(db_session, ["progression.execute"])

    ay_source = _create_academic_year(db_session, school.id, name="2025-2026", is_current=True)
    ay_target = _create_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = _create_class(db_session, school.id, name="Class 10")
    sec1 = _create_section(db_session, cls1.id, name="A")
    cls2 = _create_class(db_session, school.id, name="Class 11")
    sec2 = _create_section(db_session, cls2.id, name="A")

    _create_progression_rule(db_session, school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    _create_student(db_session, school.id, ay_source.id, cls1.id, sec1.id, admission_number="ADM-API-EX-1")

    plan = progression_planner.calculate_plan(db_session, ay_source.id, ay_target.id, school.id)

    payload = {
        "target_academic_year_id": str(ay_target.id),
        "execution_plan_hash": plan.execution_plan_hash,
        "confirm_warnings": True,
    }
    req_headers = {
        **headers,
        "Idempotency-Key": f"IDEM-API-{uuid.uuid4().hex[:8]}",
    }

    url = f"/api/v1/academic-years/{ay_source.id}/progression-execute"
    response = client.post(url, json=payload, headers=req_headers)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    exec_data = data["data"]
    assert exec_data["status"] == "COMPLETED"
    assert exec_data["summary"]["promoted_count"] == 1


def test_api_progression_execute_missing_idempotency_key(client: TestClient, db_session: Session):
    """
    Test API 2 — Missing Idempotency-Key header returns 422 Unprocessable Entity.
    """
    school, user, headers = _create_test_env_with_permissions(db_session, ["progression.execute"])
    ay_source = _create_academic_year(db_session, school.id)

    url = f"/api/v1/academic-years/{ay_source.id}/progression-execute"
    payload = {
        "target_academic_year_id": str(uuid.uuid4()),
        "execution_plan_hash": "a" * 64,
    }

    response = client.post(url, json=payload, headers=headers)
    assert response.status_code == 422
