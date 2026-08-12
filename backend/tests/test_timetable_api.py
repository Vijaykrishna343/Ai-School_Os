from datetime import date, time
import uuid

from fastapi import status

from app.common.enums.teacher import BloodGroup, Gender, TeacherStatus
from app.common.enums.timetable import DayOfWeek, PeriodType, RoomType
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
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.models.timetable.period_slot import PeriodSlot


def create_school_and_user(db, school_name, school_code, permissions_list):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Timetable Way",
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
        name=f"ROLE_TT_{uuid.uuid4().hex[:6]}",
        description="Timetable Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            db.add(
                IdentityRolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                )
            )
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"user_{uuid.uuid4().hex[:6]}",
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Password@123"),
        first_name="Timetable",
        last_name="Admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    db.add(IdentityUserRole(user_id=user.id, role_id=role.id))
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


def test_timetable_api_flow(client, db_session):
    school, user, headers = create_school_and_user(
        db_session,
        "Timetable API School",
        "TAS1",
        ["timetable.create", "timetable.view", "timetable.update", "timetable.delete"],
    )

    ay = AcademicYear(school_id=school.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True)
    sc = SchoolClass(school_id=school.id, name="Class 5", display_order=1)
    db_session.add_all([ay, sc])
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="Section A")
    p1 = PeriodSlot(school_id=school.id, name="Period 1", period_type=PeriodType.REGULAR, start_time=time(8, 30), end_time=time(9, 15), display_order=1)
    r1 = Classroom(school_id=school.id, room_number="101", capacity=40, room_type=RoomType.CLASSROOM)
    sub = Subject(school_id=school.id, subject_name="Mathematics", subject_code="MATH5")
    t1 = Teacher(
        school_id=school.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        first_name="Alice",
        last_name="Smith",
        gender=Gender.FEMALE,
        qualification="B.Ed",
        blood_group=BloodGroup.A_POSITIVE,
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 1, 1),
        email=f"alice_{uuid.uuid4().hex[:6]}@example.com",
        phone="9876543210",
        address_line1="100 St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([sec, p1, r1, sub, t1])
    db_session.commit()

    # 1. Create Timetable
    create_payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
    }
    response = client.post("/api/v1/timetables", json=create_payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    timetable_id = data["id"]
    assert data["status"] == "DRAFT"

    # 2. Get Timetable Detail
    get_res = client.get(f"/api/v1/timetables/{timetable_id}", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["id"] == timetable_id

    # 3. Create TimetableEntry
    entry_payload = {
        "day_of_week": "MONDAY",
        "period_slot_id": str(p1.id),
        "subject_id": str(sub.id),
        "teacher_id": str(t1.id),
        "classroom_id": str(r1.id),
    }
    entry_res = client.post(f"/api/v1/timetables/{timetable_id}/entries", json=entry_payload, headers=headers)
    assert entry_res.status_code == status.HTTP_201_CREATED, entry_res.text
    entry_id = entry_res.json()["id"]

    # 4. Get Section Timetable View
    sec_res = client.get(f"/api/v1/timetables/section/{sec.id}", headers=headers)
    assert sec_res.status_code == status.HTTP_200_OK
    assert len(sec_res.json()["entries"]) == 1

    # 5. Get Teacher Schedule View
    teacher_res = client.get(f"/api/v1/timetables/teacher/{t1.id}", headers=headers)
    assert teacher_res.status_code == status.HTTP_200_OK
    assert len(teacher_res.json()) == 1
    assert teacher_res.json()[0]["school_class_name"] == "Class 5"

    # 6. Update TimetableEntry
    update_res = client.put(f"/api/v1/timetable-entries/{entry_id}", json={"day_of_week": "TUESDAY"}, headers=headers)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["day_of_week"] == "TUESDAY"

    # 7. Delete TimetableEntry
    del_res = client.delete(f"/api/v1/timetable-entries/{entry_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT
