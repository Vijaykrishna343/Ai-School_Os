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


def _create_test_academic_year(db: Session, school_id, name="2025-2026", is_current=True) -> AcademicYear:
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


def test_api_progression_preview_success(client: TestClient, db_session: Session):
    school, user, headers = _create_test_env_with_permissions(db_session, ["progression.preview"])
    ay_source = _create_test_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_test_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    cls1 = SchoolClass(school_id=school.id, name="Class 1", display_order=1)
    db_session.add(cls1)
    db_session.commit()
    db_session.refresh(cls1)
    sec1 = Section(school_class_id=cls1.id, name="A")
    db_session.add(sec1)

    cls2 = SchoolClass(school_id=school.id, name="Class 2", display_order=2)
    db_session.add(cls2)
    db_session.commit()
    db_session.refresh(cls2)
    sec2 = Section(school_class_id=cls2.id, name="A")
    db_session.add(sec2)

    rule = ClassProgressionRule(school_id=school.id, source_class_id=cls1.id, target_class_id=cls2.id)
    db_session.add(rule)

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        primary_phone="+1234567890",
        address_line1="123 Main St",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
    )
    db_session.add(parent)
    db_session.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=ay_source.id,
        school_class_id=cls1.id,
        section_id=sec1.id,
        parent_id=parent.id,
        admission_number="ADM-API-001",
        first_name="API",
        last_name="Test",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2025, 4, 1),
        address_line1="123 Student St",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
        roll_number="001",
    )
    db_session.add(student)
    db_session.commit()

    response = client.post(
        f"/api/v1/academic-years/{ay_source.id}/progression-preview",
        headers=headers,
        json={
            "target_academic_year_id": str(ay_target.id),
            "page": 1,
            "page_size": 10,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    preview_data = data["data"]
    assert "execution_plan_hash" in preview_data
    assert isinstance(preview_data["execution_plan_hash"], str)
    assert len(preview_data["execution_plan_hash"]) == 64
    assert preview_data["summary"]["promoted_count"] == 1
    assert preview_data["total"] == 1
    assert len(preview_data["items"]) == 1
    item = preview_data["items"][0]
    assert item["decision"] == "PROMOTED"
    assert item["target_class_name"] == "Class 2"
    assert item["proposed_roll_number"] == "001"


def test_api_progression_preview_rbac_forbidden(client: TestClient, db_session: Session):
    school, user, headers = _create_test_env_with_permissions(db_session, ["student.view"])
    ay_source = _create_test_academic_year(db_session, school.id, name="2025-2026")
    ay_target = _create_test_academic_year(db_session, school.id, name="2026-2027", is_current=False)

    response = client.post(
        f"/api/v1/academic-years/{ay_source.id}/progression-preview",
        headers=headers,
        json={"target_academic_year_id": str(ay_target.id)},
    )

    assert response.status_code == 403


def test_api_progression_preview_cross_tenant_not_found(client: TestClient, db_session: Session):
    school_a, user_a, headers_a = _create_test_env_with_permissions(db_session, ["progression.preview"])
    school_b = _create_test_school(db_session, "School B")

    ay_source_a = _create_test_academic_year(db_session, school_a.id, name="2025-2026")
    ay_target_b = _create_test_academic_year(db_session, school_b.id, name="2026-2027")

    response = client.post(
        f"/api/v1/academic-years/{ay_source_a.id}/progression-preview",
        headers=headers_a,
        json={"target_academic_year_id": str(ay_target_b.id)},
    )

    assert response.status_code == 404


def test_api_progression_preview_same_source_target_year_rejected(client: TestClient, db_session: Session):
    school, user, headers = _create_test_env_with_permissions(db_session, ["progression.preview"])
    ay = _create_test_academic_year(db_session, school.id, name="2025-2026")

    response = client.post(
        f"/api/v1/academic-years/{ay.id}/progression-preview",
        headers=headers,
        json={"target_academic_year_id": str(ay.id)},
    )

    assert response.status_code == 422


def _create_test_school(db: Session, name="School") -> School:
    school = School(
        id=uuid.uuid4(),
        name=name,
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
    return school
