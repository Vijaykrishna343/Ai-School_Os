import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.common.enums import StudentStatus
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
from app.models.academic_year import AcademicYear
from app.models.parent import Parent
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student


def create_school_user_and_student_env(db, permissions_list):
    """
    Creates a complete test environment with School, User, Role, Academic Years, Classes, Sections, Parent, and Student.
    """
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
            rp = IdentityRolePermission(
                role_id=role.id,
                permission_id=perm.id,
            )
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"user_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Pass123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db.add(ur)
    db.commit()

    ay_source = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2024-2025",
        start_date=date(2024, 6, 1),
        end_date=date(2025, 4, 30),
        is_current=True,
    )
    ay_target = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2025-2026",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 4, 30),
        is_current=False,
    )
    db.add_all([ay_source, ay_target])
    db.commit()

    class_1 = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 1",
        display_order=1,
    )
    class_2 = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 2",
        display_order=2,
    )
    db.add_all([class_1, class_2])
    db.commit()

    sec_1a = Section(
        id=uuid.uuid4(),
        school_class_id=class_1.id,
        name="A",
        capacity=30,
    )
    sec_2a = Section(
        id=uuid.uuid4(),
        school_class_id=class_2.id,
        name="A",
        capacity=30,
    )
    db.add_all([sec_1a, sec_2a])
    db.commit()

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Father John",
        mother_name="Mother Mary",
        primary_phone=f"+1{uuid.uuid4().int % 1000000000:09d}",
        email=f"parent_{uuid.uuid4().hex[:6]}@mail.com",
        address_line1="123 Street",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()

    student = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay_source.id,
        school_class_id=class_1.id,
        section_id=sec_1a.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="001",
        first_name="StudentOne",
        last_name="Test",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2024, 6, 1),
        address_line1="123 Street",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}

    return {
        "school": school,
        "user": user,
        "headers": headers,
        "ay_source": ay_source,
        "ay_target": ay_target,
        "class_1": class_1,
        "class_2": class_2,
        "sec_1a": sec_1a,
        "sec_2a": sec_2a,
        "student": student,
    }


def test_api_promote_student_success(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.promote", "student.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_target = env["ay_target"]
    class_2 = env["class_2"]
    sec_2a = env["sec_2a"]

    payload = {
        "target_academic_year_id": str(ay_target.id),
        "target_class_id": str(class_2.id),
        "target_section_id": str(sec_2a.id),
        "remarks": "API Promoted",
    }

    response = client.post(
        f"/api/v1/students/{student.id}/promote",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["student_id"] == str(student.id)
    assert res_data["data"]["school_class_id"] == str(class_2.id)


def test_api_retain_student_success(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.retain", "student.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_target = env["ay_target"]

    payload = {
        "target_academic_year_id": str(ay_target.id),
        "remarks": "API Retained",
    }

    response = client.post(
        f"/api/v1/students/{student.id}/retain",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["student_id"] == str(student.id)


def test_api_get_enrollment_history(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.promote", "student.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_target = env["ay_target"]
    class_2 = env["class_2"]
    sec_2a = env["sec_2a"]

    # Perform promotion
    payload = {
        "target_academic_year_id": str(ay_target.id),
        "target_class_id": str(class_2.id),
        "target_section_id": str(sec_2a.id),
    }
    client.post(f"/api/v1/students/{student.id}/promote", json=payload, headers=headers)

    response = client.get(
        f"/api/v1/students/{student.id}/enrollments",
        headers=headers,
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["total"] == 2


def test_api_issue_transfer_certificate(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.tc.create", "student.tc.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_source = env["ay_source"]

    payload = {
        "academic_year_id": str(ay_source.id),
        "issue_date": "2026-08-10",
        "leaving_date": "2026-08-08",
        "reason": "Relocation",
    }

    response = client.post(
        f"/api/v1/students/{student.id}/transfer-certificate",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["student_id"] == str(student.id)

    # Get TCs
    get_res = client.get(
        f"/api/v1/students/{student.id}/transfer-certificates",
        headers=headers,
    )
    assert get_res.status_code == 200
    assert get_res.json()["data"]["total"] == 1


def test_api_unauthorized_and_forbidden(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_target = env["ay_target"]
    class_2 = env["class_2"]
    sec_2a = env["sec_2a"]

    payload = {
        "target_academic_year_id": str(ay_target.id),
        "target_class_id": str(class_2.id),
        "target_section_id": str(sec_2a.id),
    }

    # 1. Unauthenticated -> 401
    unauth_res = client.post(f"/api/v1/students/{student.id}/promote", json=payload)
    assert unauth_res.status_code == 401

    # 2. Missing student.promote permission -> 403
    forb_res = client.post(f"/api/v1/students/{student.id}/promote", json=payload, headers=headers)
    assert forb_res.status_code == 403


def test_api_tenant_isolation_cross_school(client, db_session):
    env_school1 = create_school_user_and_student_env(db_session, ["student.promote", "student.view"])
    env_school2 = create_school_user_and_student_env(db_session, ["student.promote", "student.view"])

    # School 1 user tries to promote School 2 student
    student_school2 = env_school2["student"]
    ay_target1 = env_school1["ay_target"]
    class_2_s1 = env_school1["class_2"]
    sec_2a_s1 = env_school1["sec_2a"]

    payload = {
        "target_academic_year_id": str(ay_target1.id),
        "target_class_id": str(class_2_s1.id),
        "target_section_id": str(sec_2a_s1.id),
    }

    response = client.post(
        f"/api/v1/students/{student_school2.id}/promote",
        json=payload,
        headers=env_school1["headers"],
    )

    assert response.status_code in [400, 404, 422]


def test_api_bulk_promote_students(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.promote", "student.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_source = env["ay_source"]
    ay_target = env["ay_target"]
    class_2 = env["class_2"]
    sec_2a = env["sec_2a"]

    payload = {
        "source_academic_year_id": str(ay_source.id),
        "target_academic_year_id": str(ay_target.id),
        "promotions": [
            {
                "student_id": str(student.id),
                "target_class_id": str(class_2.id),
                "target_section_id": str(sec_2a.id),
                "remarks": "API Bulk Promoted",
            }
        ],
    }

    response = client.post(
        "/api/v1/students/promote/bulk",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["promoted_count"] == 1
    assert res_data["data"]["total_processed"] == 1


def test_api_bulk_retain_students(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.retain", "student.view"],
    )
    headers = env["headers"]
    student = env["student"]
    ay_source = env["ay_source"]
    ay_target = env["ay_target"]
    class_1 = env["class_1"]
    sec_1a = env["sec_1a"]

    payload = {
        "source_academic_year_id": str(ay_source.id),
        "target_academic_year_id": str(ay_target.id),
        "retentions": [
            {
                "student_id": str(student.id),
                "target_class_id": str(class_1.id),
                "target_section_id": str(sec_1a.id),
                "remarks": "API Bulk Retained",
            }
        ],
    }

    response = client.post(
        "/api/v1/students/retain/bulk",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["retained_count"] == 1


def test_api_transition_academic_year(client, db_session):
    env = create_school_user_and_student_env(
        db_session,
        ["student.transition", "student.view"],
    )
    headers = env["headers"]
    ay_source = env["ay_source"]
    ay_target = env["ay_target"]

    payload = {
        "target_academic_year_id": str(ay_target.id),
        "remarks": "API Year Transition",
    }

    response = client.post(
        f"/api/v1/academic-years/{ay_source.id}/transition",
        json=payload,
        headers=headers,
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["success"] is True
    assert res_data["data"]["source_academic_year_id"] == str(ay_source.id)
    assert res_data["data"]["target_academic_year_id"] == str(ay_target.id)
