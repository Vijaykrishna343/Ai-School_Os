import uuid
from datetime import date, time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.classroom import Classroom
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.models.timetable.teacher_substitution import TeacherSubstitution
from app.common.enums import AttendanceStatus, TeacherStatus, Gender
from app.common.enums.timetable import TimetableStatus, DayOfWeek, PeriodType, RoomType
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.database.common_model import CommonModel


@pytest.fixture
def setup_engine_test_data(db_session: Session):
    CommonModel.metadata.create_all(db_session.get_bind())
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # School A & B
    school_a = School(
        name=f"Engine School A {s}", code=f"ESA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    school_b = School(
        name=f"Engine School B {s}", code=f"ESB_{s}",
        address_line1="456 Other St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay = AcademicYear(school_id=school_a.id, name=f"2025-2026 {s}", start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True)
    db_session.add(ay)
    db_session.commit()

    sc = SchoolClass(school_id=school_a.id, name="Grade 9", display_order=9)
    db_session.add(sc)
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="A")
    db_session.add(sec)
    db_session.commit()

    subj_math = Subject(school_id=school_a.id, subject_name="Mathematics", subject_code=f"MATH_{s}")
    subj_phy = Subject(school_id=school_a.id, subject_name="Physics", subject_code=f"PHY_{s}")
    db_session.add_all([subj_math, subj_phy])
    db_session.commit()

    slot1 = PeriodSlot(school_id=school_a.id, name="Period 1", period_type=PeriodType.REGULAR, start_time=time(9, 0), end_time=time(9, 45), display_order=1)
    slot2 = PeriodSlot(school_id=school_a.id, name="Period 2", period_type=PeriodType.REGULAR, start_time=time(9, 45), end_time=time(10, 30), display_order=2)
    db_session.add_all([slot1, slot2])
    db_session.commit()

    room101 = Classroom(school_id=school_a.id, room_number=f"R101_{s}", capacity=40, room_type=RoomType.CLASSROOM)
    db_session.add(room101)
    db_session.commit()

    # Teachers A (Absent), B (Present & Math qualified), C (Present & Physics)
    t_a = Teacher(
        school_id=school_a.id, employee_id=f"TCH_A_{s}", first_name="Absent", last_name="Teacher",
        gender=Gender.MALE, date_of_birth=date(1985, 1, 1), joining_date=date(2015, 6, 1),
        qualification="M.Sc Math", phone=f"9881{s[:6]}", email=f"tcha_{s}@school.com",
        address_line1="Address 1", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    t_b = Teacher(
        school_id=school_a.id, employee_id=f"TCH_B_{s}", first_name="MathSub", last_name="Teacher",
        gender=Gender.FEMALE, date_of_birth=date(1988, 5, 5), joining_date=date(2018, 6, 1),
        qualification="M.Sc Mathematics", specialization="Mathematics", phone=f"9882{s[:6]}", email=f"tchb_{s}@school.com",
        address_line1="Address 2", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    t_c = Teacher(
        school_id=school_a.id, employee_id=f"TCH_C_{s}", first_name="PhySub", last_name="Teacher",
        gender=Gender.MALE, date_of_birth=date(1990, 8, 8), joining_date=date(2020, 6, 1),
        qualification="M.Sc Physics", specialization="Physics", phone=f"9883{s[:6]}", email=f"tchc_{s}@school.com",
        address_line1="Address 3", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([t_a, t_b, t_c])
    db_session.commit()

    sec_b = Section(school_class_id=sc.id, name="B")
    db_session.add(sec_b)
    db_session.commit()

    # Published Timetable for Section Grade 9-B
    tt_b = Timetable(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec_b.id, status=TimetableStatus.PUBLISHED)
    db_session.add(tt_b)
    db_session.commit()

    # Entry 3: Monday Period 2 -> Teacher B teaches Math in Section B
    entry3 = TimetableEntry(
        timetable_id=tt_b.id, period_slot_id=slot2.id, subject_id=subj_math.id, teacher_id=t_b.id,
        classroom_id=room101.id, day_of_week=DayOfWeek.MONDAY
    )

    # Published Timetable for Section Grade 9-A
    tt = Timetable(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, status=TimetableStatus.PUBLISHED)
    db_session.add(tt)
    db_session.commit()

    # Entry 1: Monday Period 1 -> Teacher A (Absent) teaches Math
    entry1 = TimetableEntry(
        timetable_id=tt.id, period_slot_id=slot1.id, subject_id=subj_math.id, teacher_id=t_a.id,
        classroom_id=room101.id, day_of_week=DayOfWeek.MONDAY
    )
    # Entry 2: Monday Period 2 -> Teacher C teaches Physics
    entry2 = TimetableEntry(
        timetable_id=tt.id, period_slot_id=slot2.id, subject_id=subj_phy.id, teacher_id=t_c.id,
        classroom_id=room101.id, day_of_week=DayOfWeek.MONDAY
    )
    db_session.add_all([entry1, entry2, entry3])
    db_session.commit()

    # Mark Teacher A ABSENT on 2026-08-24 (a Monday)
    sub_date = date(2026, 8, 24)  # Monday
    att_a = TeacherAttendance(school_id=school_a.id, teacher_id=t_a.id, attendance_date=sub_date, status=AttendanceStatus.ABSENT)
    att_b = TeacherAttendance(school_id=school_a.id, teacher_id=t_b.id, attendance_date=sub_date, status=AttendanceStatus.PRESENT)
    att_c = TeacherAttendance(school_id=school_a.id, teacher_id=t_c.id, attendance_date=sub_date, status=AttendanceStatus.PRESENT)
    db_session.add_all([att_a, att_b, att_c])
    db_session.commit()

    pwd = hash_password("Password@123")
    u_admin_a = IdentityUser(email=f"admin_engine_a_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="AdminA")
    u_admin_b = IdentityUser(email=f"admin_engine_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="AdminB")
    db_session.add_all([u_admin_a, u_admin_b])
    db_session.commit()

    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    db_session.add_all([
        IdentityUserRole(user_id=u_admin_a.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=r_admin.id),
    ])
    db_session.commit()

    tok_admin_a = jwt_manager.create_access_token(user_id=u_admin_a.id, school_id=school_a.id)
    tok_admin_b = jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b, "ay": ay, "sc": sc, "sec": sec,
        "entry1": entry1, "entry2": entry2, "sub_date": sub_date,
        "t_a": t_a, "t_b": t_b, "t_c": t_c,
        "tok_admin_a": tok_admin_a, "tok_admin_b": tok_admin_b,
    }


def test_01_affected_slots_detection(client: TestClient, setup_engine_test_data):
    d = setup_engine_test_data
    sub_date_str = d["sub_date"].isoformat()

    res = client.get(f"/api/v1/teacher-substitutions/affected-slots?substitution_date={sub_date_str}", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res.status_code == 200
    body = res.json()
    assert body["total_affected_slots"] == 1
    assert body["unassigned_count"] == 1
    assert body["assigned_count"] == 0
    assert body["items"][0]["timetable_entry_id"] == str(d["entry1"].id)
    assert body["items"][0]["status"] == "UNASSIGNED"


def test_02_recommendations_scoring_and_ranking(client: TestClient, setup_engine_test_data):
    d = setup_engine_test_data
    sub_date_str = d["sub_date"].isoformat()
    entry1_id = str(d["entry1"].id)

    res = client.get(f"/api/v1/teacher-substitutions/recommendations?timetable_entry_id={entry1_id}&substitution_date={sub_date_str}", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res.status_code == 200
    candidates = res.json()["candidates"]

    # Teacher B (Math qualified, present, free) should be top candidate
    assert len(candidates) >= 1
    top = candidates[0]
    assert top["teacher_id"] == str(d["t_b"].id)
    assert top["score"] > 50
    assert "Qualified in Mathematics" in top["match_reasons"] or "Teaches Mathematics" in top["match_reasons"]

    # Teacher A (absent) must NOT be in candidate list
    assert not any(c["teacher_id"] == str(d["t_a"].id) for c in candidates)


def test_03_auto_assign_substitutions(client: TestClient, setup_engine_test_data):
    d = setup_engine_test_data
    sub_date_str = d["sub_date"].isoformat()

    payload = {
        "substitution_date": sub_date_str,
        "school_class_id": str(d["sc"].id),
        "override_existing": False
    }
    res = client.post("/api/v1/teacher-substitutions/auto-assign", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res.status_code == 200
    body = res.json()
    assert body["assigned_count"] == 1
    assert len(body["created_substitutions"]) == 1
    created_sub = body["created_substitutions"][0]
    assert created_sub["substitute_teacher_id"] == str(d["t_b"].id)

    # Verify re-querying affected slots now shows status ASSIGNED
    res_aff = client.get(f"/api/v1/teacher-substitutions/affected-slots?substitution_date={sub_date_str}", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res_aff.status_code == 200
    assert res_aff.json()["unassigned_count"] == 0
    assert res_aff.json()["assigned_count"] == 1


def test_04_multi_tenant_substitution_isolation(client: TestClient, setup_engine_test_data):
    d = setup_engine_test_data
    sub_date_str = d["sub_date"].isoformat()
    entry1_id = str(d["entry1"].id)

    # Tenant B admin calls recommendations for Tenant A timetable entry -> 404
    res = client.get(f"/api/v1/teacher-substitutions/recommendations?timetable_entry_id={entry1_id}&substitution_date={sub_date_str}", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code == 404
