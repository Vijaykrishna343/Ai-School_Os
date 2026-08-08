import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.parent import ParentRelationship
from app.identity.models import (
    IdentityPermission,
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.models.academic_year.academic_year import AcademicYear
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.academic_year import AcademicYearCreate
from app.services.academic_year_service import academic_year_service


def create_school_user_and_students(db, school_name, school_code, permissions_list):
    """
    Helper function to seed identity, create school, user with specified permissions,
    school class, section, parent, and active students.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=school_code,
        address_line1="100 Academic Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
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

    ay_in = AcademicYearCreate(
        school_id=school.id,
        name=f"2026-2027-{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    academic_year = academic_year_service.create_academic_year(db, ay_in)

    sclass = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 10",
        display_order=1,
    )
    db.add(sclass)

    section = Section(
        id=uuid.uuid4(),
        school_class_id=sclass.id,
        name="Section A",
    )
    db.add(section)

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Ramesh Kumar",
        primary_phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        relationship=ParentRelationship.FATHER,
        address_line1="12 Park St",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()

    student1 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=academic_year.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="101",
        first_name="Aarav",
        last_name="Kumar",
        gender=Gender.MALE,
        date_of_birth=date(2010, 5, 15),
        admission_date=date(2026, 4, 1),
        address_line1="12 Park St",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    student2 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=academic_year.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="102",
        first_name="Ananya",
        last_name="Kumar",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 6, 20),
        admission_date=date(2026, 4, 1),
        address_line1="12 Park St",
        city="Delhi",
        district="Delhi",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    db.add_all([student1, student2])
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers, academic_year, sclass, section, student1, student2


def test_01_authenticated_user_can_create_individual_attendance(client, db_session):
    school, user, headers, ay, sclass, section, s1, s2 = create_school_user_and_students(
        db_session, "API Att School 1", "APIAT1", ["attendance.create"]
    )
    payload = {
        "student_id": str(s1.id),
        "attendance_date": "2026-08-10",
        "status": "PRESENT",
        "remarks": "On time",
    }
    response = client.post("/api/v1/attendance/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["student_id"] == str(s1.id)
    assert data["status"] == "PRESENT"


def test_02_anonymous_request_is_rejected(client):
    payload = {
        "student_id": str(uuid.uuid4()),
        "attendance_date": "2026-08-10",
        "status": "PRESENT",
    }
    response = client.post("/api/v1/attendance/", json=payload)
    assert response.status_code == 401


def test_03_user_without_permission_is_rejected(client, db_session):
    school, user, headers, ay, sclass, section, s1, s2 = create_school_user_and_students(
        db_session, "API Att School 3", "APIAT3", []
    )
    payload = {
        "student_id": str(s1.id),
        "attendance_date": "2026-08-10",
        "status": "PRESENT",
    }
    response = client.post("/api/v1/attendance/", json=payload, headers=headers)
    assert response.status_code == 403


def test_04_bulk_attendance_create(client, db_session):
    school, user, headers, ay, sclass, section, s1, s2 = create_school_user_and_students(
        db_session, "API Att School 4", "APIAT4", ["attendance.create"]
    )
    payload = {
        "section_id": str(section.id),
        "attendance_date": "2026-08-11",
        "records": [
            {"student_id": str(s1.id), "status": "PRESENT"},
            {"student_id": str(s2.id), "status": "ABSENT", "remarks": "Sick"},
        ],
    }
    response = client.post("/api/v1/attendance/bulk", json=payload, headers=headers)
    assert response.status_code == 201
    items = response.json()["data"]["items"]
    assert len(items) == 2


def test_05_duplicate_attendance_rejected(client, db_session):
    school, user, headers, ay, sclass, section, s1, s2 = create_school_user_and_students(
        db_session, "API Att School 5", "APIAT5", ["attendance.create"]
    )
    payload = {
        "student_id": str(s1.id),
        "attendance_date": "2026-08-12",
        "status": "PRESENT",
    }
    res1 = client.post("/api/v1/attendance/", json=payload, headers=headers)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/attendance/", json=payload, headers=headers)
    assert res2.status_code == 409


def test_06_list_attendance_with_filters(client, db_session):
    school, user, headers, ay, sclass, section, s1, s2 = create_school_user_and_students(
        db_session, "API Att School 6", "APIAT6", ["attendance.create", "attendance.view"]
    )

    client.post(
        "/api/v1/attendance/",
        json={"student_id": str(s1.id), "attendance_date": "2026-08-13", "status": "PRESENT"},
        headers=headers,
    )
    client.post(
        "/api/v1/attendance/",
        json={"student_id": str(s2.id), "attendance_date": "2026-08-13", "status": "ABSENT"},
        headers=headers,
    )

    # Filter by section and date
    res = client.get(
        f"/api/v1/attendance/?section_id={section.id}&attendance_date=2026-08-13",
        headers=headers,
    )
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 2

    # Filter by status
    res_status = client.get(
        f"/api/v1/attendance/?status=ABSENT",
        headers=headers,
    )
    assert res_status.status_code == 200
    items_absent = res_status.json()["data"]["items"]
    assert len(items_absent) == 1
    assert items_absent[0]["student_id"] == str(s2.id)


def test_07_get_update_delete_attendance(client, db_session):
    school, user, headers, ay, sclass, section, s1, s2 = create_school_user_and_students(
        db_session,
        "API Att School 7",
        "APIAT7",
        ["attendance.create", "attendance.view", "attendance.update", "attendance.delete"],
    )

    create_res = client.post(
        "/api/v1/attendance/",
        json={"student_id": str(s1.id), "attendance_date": "2026-08-14", "status": "LATE"},
        headers=headers,
    )
    att_id = create_res.json()["data"]["id"]

    # GET detail
    get_res = client.get(f"/api/v1/attendance/{att_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["data"]["status"] == "LATE"

    # PUT update
    put_res = client.put(
        f"/api/v1/attendance/{att_id}",
        json={"status": "EXCUSED", "remarks": "Traffic delay excused"},
        headers=headers,
    )
    assert put_res.status_code == 200
    assert put_res.json()["data"]["status"] == "EXCUSED"

    # DELETE soft-delete
    del_res = client.delete(f"/api/v1/attendance/{att_id}", headers=headers)
    assert del_res.status_code == 200

    # Verify 404 after deletion
    get_after_del = client.get(f"/api/v1/attendance/{att_id}", headers=headers)
    assert get_after_del.status_code == 404


def test_08_tenant_isolation(client, db_session):
    s1, u1, h1, ay1, sc1, sec1, st1_1, st1_2 = create_school_user_and_students(
        db_session, "API Att School 8A", "APIAT8A", ["attendance.create", "attendance.view"]
    )
    s2, u2, h2, ay2, sc2, sec2, st2_1, st2_2 = create_school_user_and_students(
        db_session, "API Att School 8B", "APIAT8B", ["attendance.create", "attendance.view"]
    )

    res_1 = client.post(
        "/api/v1/attendance/",
        json={"student_id": str(st1_1.id), "attendance_date": "2026-08-15", "status": "PRESENT"},
        headers=h1,
    )
    att1_id = res_1.json()["data"]["id"]

    # User 2 attempting to view User 1's attendance -> 404
    cross_res = client.get(f"/api/v1/attendance/{att1_id}", headers=h2)
    assert cross_res.status_code == 404
