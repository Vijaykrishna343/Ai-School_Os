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
from app.schemas.timetable.timetable import TimetableCreate
from app.schemas.timetable.timetable_entry import TimetableEntryCreate
from app.services.timetable_entry_service import TimetableEntryService
from app.services.timetable_service import TimetableService


def create_school_and_user(db, school_name, school_code, permissions_list):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Substitution Way",
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
        name=f"ROLE_SUB_{uuid.uuid4().hex[:6]}",
        description="Substitution Role",
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
        first_name="Sub",
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


def test_teacher_substitution_api_flow(client, db_session):
    school, user, headers = create_school_and_user(
        db_session,
        "Sub API School",
        "SAS1",
        [
            "timetable.create", "timetable.view", "timetable.update", "timetable.delete",
            "timetable.publish", "timetable.archive",
            "substitution.create", "substitution.view", "substitution.update", "substitution.delete",
        ],
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
    t2 = Teacher(
        school_id=school.id,
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        first_name="Bob",
        last_name="Jones",
        gender=Gender.MALE,
        qualification="M.Ed",
        blood_group=BloodGroup.B_POSITIVE,
        date_of_birth=date(1988, 5, 5),
        joining_date=date(2019, 1, 1),
        email=f"bob_{uuid.uuid4().hex[:6]}@example.com",
        phone="9876543211",
        address_line1="101 St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([sec, p1, r1, sub, t1, t2])
    db_session.commit()

    tt_service = TimetableService()
    entry_service = TimetableEntryService()

    tt = tt_service.create_timetable(
        db_session,
        TimetableCreate(school_id=school.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id),
        current_school_id=school.id,
    )
    entry = entry_service.create_entry(
        db_session,
        tt.id,
        TimetableEntryCreate(
            day_of_week=DayOfWeek.MONDAY,
            period_slot_id=p1.id,
            subject_id=sub.id,
            teacher_id=t1.id,
            classroom_id=r1.id,
        ),
        current_school_id=school.id,
    )

    # 1. Publish Timetable via API
    pub_res = client.post(f"/api/v1/timetables/{tt.id}/publish", headers=headers)
    assert pub_res.status_code == status.HTTP_200_OK
    assert pub_res.json()["status"] == "PUBLISHED"

    # 2. Create TeacherSubstitution via API
    # 2026-08-10 is a MONDAY
    sub_payload = {
        "school_id": str(school.id),
        "timetable_entry_id": str(entry.id),
        "substitution_date": "2026-08-10",
        "substitute_teacher_id": str(t2.id),
        "remarks": "Alice on leave",
    }
    sub_res = client.post("/api/v1/teacher-substitutions", json=sub_payload, headers=headers)
    assert sub_res.status_code == status.HTTP_201_CREATED, sub_res.text
    sub_data = sub_res.json()
    sub_id = sub_data["id"]
    assert sub_data["substitute_teacher"]["first_name"] == "Bob"

    # 3. Get Substitution by ID
    get_sub_res = client.get(f"/api/v1/teacher-substitutions/{sub_id}", headers=headers)
    assert get_sub_res.status_code == status.HTTP_200_OK
    assert get_sub_res.json()["remarks"] == "Alice on leave"

    # 4. List Substitutions
    list_res = client.get("/api/v1/teacher-substitutions", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 1

    # 5. Update Substitution
    update_res = client.put(f"/api/v1/teacher-substitutions/{sub_id}", json={"remarks": "Updated remarks"}, headers=headers)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["remarks"] == "Updated remarks"

    # 6. Delete Substitution
    del_res = client.delete(f"/api/v1/teacher-substitutions/{sub_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 7. Archive Timetable via API
    arch_res = client.post(f"/api/v1/timetables/{tt.id}/archive", headers=headers)
    assert arch_res.status_code == status.HTTP_200_OK
    assert arch_res.json()["status"] == "ARCHIVED"
