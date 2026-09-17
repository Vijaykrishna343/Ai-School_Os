"""
Integration & Unit Test Suite: Teacher Classroom Command Cockpit — Phase 30.3
Tests authentication, RBAC, tenant isolation, schedule aggregation, substitutions,
attendance status, homework, exams, alerts, and empty states.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, time, timedelta
from typing import Any, Dict

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus, Gender, TeacherStatus
from app.common.enums.exam import ExamStatus
from app.models.homework.homework import HomeworkStatus
from app.common.enums.timetable import DayOfWeek, PeriodType, TimetableStatus
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.models.academic_year.academic_year import AcademicYear
from app.models.attendance.attendance import Attendance
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.homework.homework import Homework
from app.models.homework.homework_submission import HomeworkSubmission
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.teacher_substitution import TeacherSubstitution
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.services.teacher_cockpit_service import TeacherCockpitService


@pytest.fixture
def cockpit_test_env(db_session: Session):
    db = db_session
    suffix = uuid.uuid4().hex[:6]

    # --- School Alpha ---
    school_a = School(
        name=f"Alpha Academy {suffix}",
        code=f"ALP_{suffix}",
        address_line1="100 Cockpit Way",
        city="AlphaCity",
        district="Central",
        state="AlphaState",
        country="India",
        postal_code="500001",
        status="ACTIVE",
    )
    db.add(school_a)

    # --- School Beta ---
    school_b = School(
        name=f"Beta International {suffix}",
        code=f"BET_{suffix}",
        address_line1="200 Cockpit Way",
        city="BetaCity",
        district="North",
        state="BetaState",
        country="India",
        postal_code="500002",
        status="ACTIVE",
    )
    db.add(school_b)
    db.flush()

    # Academic Year
    ay_a = AcademicYear(
        school_id=school_a.id,
        name=f"2026-2027-{suffix}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay_a)
    db.flush()

    # Teachers in School Alpha
    teacher_a1 = Teacher(
        school_id=school_a.id,
        first_name="Alan",
        last_name="Turing",
        employee_id=f"T_ALP1_{suffix}",
        email=f"alan_{suffix}@alpha.edu",
        phone=f"98765{suffix[:5]}",
        date_of_birth=date(1985, 6, 23),
        joining_date=date(2020, 1, 1),
        gender=Gender.MALE,
        qualification="M.Sc. Mathematics",
        specialization="Calculus",
        address_line1="123 Alpha St",
        city="AlphaCity",
        district="AlphaDist",
        state="AlphaState",
        country="India",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    teacher_a2 = Teacher(
        school_id=school_a.id,
        first_name="Ada",
        last_name="Lovelace",
        employee_id=f"T_ALP2_{suffix}",
        email=f"ada_{suffix}@alpha.edu",
        phone=f"98766{suffix[:5]}",
        date_of_birth=date(1988, 12, 10),
        joining_date=date(2021, 2, 1),
        gender=Gender.FEMALE,
        qualification="M.Tech Computer Science",
        specialization="Algorithms",
        address_line1="456 Alpha Ave",
        city="AlphaCity",
        district="AlphaDist",
        state="AlphaState",
        country="India",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db.add_all([teacher_a1, teacher_a2])

    # Teacher in School Beta
    teacher_b = Teacher(
        school_id=school_b.id,
        first_name="Isaac",
        last_name="Newton",
        employee_id=f"T_BET_{suffix}",
        email=f"isaac_{suffix}@beta.edu",
        phone=f"98767{suffix[:5]}",
        date_of_birth=date(1980, 1, 4),
        joining_date=date(2019, 1, 1),
        gender=Gender.MALE,
        qualification="Ph.D. Physics",
        specialization="Optics",
        address_line1="789 Beta Rd",
        city="BetaCity",
        district="BetaDist",
        state="BetaState",
        country="India",
        postal_code="500002",
        status=TeacherStatus.ACTIVE,
    )
    db.add(teacher_b)
    db.flush()

    # Classes & Sections in School Alpha
    class_10 = SchoolClass(
        school_id=school_a.id,
        name="Grade 10",
        display_order=10,
    )
    db.add(class_10)
    db.flush()

    section_10a = Section(
        school_class_id=class_10.id,
        name="A",
        capacity=40,
    )
    db.add(section_10a)
    db.flush()

    # Subject
    subj_math = Subject(
        school_id=school_a.id,
        subject_name="Advanced Mathematics",
        subject_code=f"MTH_{suffix}",
    )
    db.add(subj_math)

    from app.models.parent.parent import Parent
    from app.common.enums.parent import ParentRelationship

    parent_a = Parent(
        school_id=school_a.id,
        father_name="Gauss Father",
        relationship=ParentRelationship.FATHER,
        primary_phone=f"9871{suffix[:5]}",
        address_line1="Math Street",
        city="AlphaCity",
        district="AlphaDist",
        state="AlphaState",
        postal_code="500001",
    )
    db.add(parent_a)
    db.flush()

    # Students in 10-A
    student1 = Student(
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        roll_number="1",
        first_name="Carl",
        last_name="Gauss",
        admission_number=f"ADM_G_{suffix}",
        admission_date=date(2024, 6, 1),
        date_of_birth=date(2010, 4, 30),
        gender=Gender.MALE,
        emergency_contact="9870000001",
        address_line1="Math Street",
        city="AlphaCity",
        district="AlphaDist",
        state="AlphaState",
        postal_code="500001",
    )
    student2 = Student(
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        roll_number="2",
        first_name="Leonhard",
        last_name="Euler",
        admission_number=f"ADM_E_{suffix}",
        admission_date=date(2024, 6, 1),
        date_of_birth=date(2010, 4, 15),
        gender=Gender.MALE,
        emergency_contact="9870000002",
        address_line1="Analysis Way",
        city="AlphaCity",
        district="AlphaDist",
        state="AlphaState",
        postal_code="500001",
    )
    db.add_all([student1, student2])
    db.flush()

    # Period Slots
    slot1 = PeriodSlot(
        school_id=school_a.id,
        display_order=1,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 30),
        period_type=PeriodType.REGULAR,
    )
    slot2 = PeriodSlot(
        school_id=school_a.id,
        display_order=2,
        name="Period 2",
        start_time=time(9, 35),
        end_time=time(10, 35),
        period_type=PeriodType.REGULAR,
    )
    db.add_all([slot1, slot2])
    db.flush()

    # Classroom
    room101 = Classroom(
        school_id=school_a.id,
        room_number="101",
        building_name="Main Wing",
        capacity=40,
    )
    db.add(room101)
    db.flush()

    # Timetable for 10-A
    tt_10a = Timetable(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        status=TimetableStatus.PUBLISHED,
    )
    db.add(tt_10a)
    db.flush()

    today_dow = TeacherCockpitService.WEEKDAY_MAP.get(date.today().weekday(), DayOfWeek.MONDAY)

    # Slot 1: Alan Turing teaches Math in 10-A on today's DOW
    entry1 = TimetableEntry(
        timetable_id=tt_10a.id,
        period_slot_id=slot1.id,
        subject_id=subj_math.id,
        teacher_id=teacher_a1.id,
        classroom_id=room101.id,
        day_of_week=today_dow,
    )
    # Slot 2: Ada Lovelace teaches Math in 10-A on today's DOW
    entry2 = TimetableEntry(
        timetable_id=tt_10a.id,
        period_slot_id=slot2.id,
        subject_id=subj_math.id,
        teacher_id=teacher_a2.id,
        classroom_id=room101.id,
        day_of_week=today_dow,
    )
    db.add_all([entry1, entry2])
    db.flush()

    # Substitution: Alan Turing substitutes for Ada Lovelace on Slot 2 today!
    sub1 = TeacherSubstitution(
        school_id=school_a.id,
        timetable_entry_id=entry2.id,
        substitution_date=date.today(),
        original_teacher_id=teacher_a2.id,
        substitute_teacher_id=teacher_a1.id,
        remarks="Covering for Ada on leave",
    )
    db.add(sub1)

    # Attendance today for 10-A
    att1 = Attendance(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        student_id=student1.id,
        attendance_date=date.today(),
        status=AttendanceStatus.PRESENT,
    )
    att2 = Attendance(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        student_id=student2.id,
        attendance_date=date.today(),
        status=AttendanceStatus.ABSENT,
    )
    db.add_all([att1, att2])

    # Homework created by Alan
    hw1 = Homework(
        school_id=school_a.id,
        teacher_id=teacher_a1.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        subject_id=subj_math.id,
        title="Calculus Problem Set 1",
        description="Solve problems 1-10",
        assigned_date=date.today(),
        due_date=date.today() + timedelta(days=2),
        status=HomeworkStatus.PUBLISHED,
    )
    db.add(hw1)
    db.flush()

    # Submission for student 1
    subm1 = HomeworkSubmission(
        school_id=school_a.id,
        homework_id=hw1.id,
        student_id=student1.id,
        content_text="Completed problems 1-10",
    )
    db.add(subm1)

    # Exam in 5 days
    exam1 = Exam(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        name=f"Mid-Term Exam {suffix}",
        status=ExamStatus.SCHEDULED,
        start_date=date.today() + timedelta(days=5),
        end_date=date.today() + timedelta(days=10),
    )
    db.add(exam1)
    db.flush()

    sched1 = ExamSchedule(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        exam_id=exam1.id,
        school_class_id=class_10.id,
        section_id=section_10a.id,
        subject_id=subj_math.id,
        exam_date=date.today() + timedelta(days=5),
        start_time=time(10, 0),
        end_time=time(12, 0),
        maximum_marks=100.0,
        passing_marks=40.0,
    )
    db.add(sched1)

    # Permissions
    perm_cockpit = db.execute(
        select(IdentityPermission).where(IdentityPermission.name == "teacher_cockpit.view")
    ).scalars().first()
    if not perm_cockpit:
        perm_cockpit = IdentityPermission(
            name="teacher_cockpit.view",
            module="teacher_cockpit",
            action="view",
            description="View teacher cockpit",
        )
        db.add(perm_cockpit)
        db.flush()

    # Role in School Alpha with teacher_cockpit.view
    role_teacher = IdentityRole(
        school_id=school_a.id,
        name=f"Teacher Role {suffix}",
        is_system=False,
    )
    db.add(role_teacher)
    db.flush()

    rp1 = IdentityRolePermission(
        role_id=role_teacher.id,
        permission_id=perm_cockpit.id,
    )
    db.add(rp1)

    # Role in School Beta with teacher_cockpit.view
    role_beta = IdentityRole(
        school_id=school_b.id,
        name=f"Beta Teacher {suffix}",
        is_system=False,
    )
    db.add(role_beta)
    db.flush()

    rp2 = IdentityRolePermission(
        role_id=role_beta.id,
        permission_id=perm_cockpit.id,
    )
    db.add(rp2)

    # Identity Users
    # User 1: Alan Turing (Teacher in School Alpha)
    user_alan = IdentityUser(
        school_id=school_a.id,
        email=teacher_a1.email,
        first_name="Alan",
        last_name="Turing",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.add(user_alan)
    db.flush()

    ur_alan = IdentityUserRole(
        user_id=user_alan.id,
        role_id=role_teacher.id,
    )
    db.add(ur_alan)

    # User 2: Isaac Newton (Teacher in School Beta)
    user_isaac = IdentityUser(
        school_id=school_b.id,
        email=teacher_b.email,
        first_name="Isaac",
        last_name="Newton",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.add(user_isaac)
    db.flush()

    ur_isaac = IdentityUserRole(
        user_id=user_isaac.id,
        role_id=role_beta.id,
    )
    db.add(ur_isaac)

    # User 3: Unauthorized user (No roles/permissions)
    user_unauth = IdentityUser(
        school_id=school_a.id,
        email=f"unauth_{suffix}@alpha.edu",
        first_name="Unauth",
        last_name="User",
        password_hash=hash_password("Password123!"),
        is_active=True,
    )
    db.add(user_unauth)
    db.flush()

    # Pre-generate JWT tokens
    token_alan = jwt_manager.create_access_token(user_id=user_alan.id, school_id=school_a.id)
    token_isaac = jwt_manager.create_access_token(user_id=user_isaac.id, school_id=school_b.id)
    token_unauth = jwt_manager.create_access_token(user_id=user_unauth.id, school_id=school_a.id)

    db.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "teacher_alan": teacher_a1,
        "teacher_isaac": teacher_b,
        "user_alan": user_alan,
        "user_isaac": user_isaac,
        "user_unauth": user_unauth,
        "headers_alan": {"Authorization": f"Bearer {token_alan}"},
        "headers_isaac": {"Authorization": f"Bearer {token_isaac}"},
        "headers_unauth": {"Authorization": f"Bearer {token_unauth}"},
    }


def test_teacher_cockpit_authentication(client):
    """Unauthenticated requests must be rejected with HTTP 401."""
    res = client.get("/api/v1/teacher-cockpit")
    assert res.status_code == 401


def test_teacher_cockpit_authorization(client, cockpit_test_env):
    """Authorized teacher gets 200 OK, unauthorized user gets 403 Forbidden."""
    res_unauth = client.get("/api/v1/teacher-cockpit", headers=cockpit_test_env["headers_unauth"])
    assert res_unauth.status_code == 403

    res_alan = client.get("/api/v1/teacher-cockpit", headers=cockpit_test_env["headers_alan"])
    assert res_alan.status_code == 200
    data = res_alan.json()["data"]
    assert data["teacher"]["full_name"] == "Alan Turing"
    assert data["teacher"]["employee_id"] == cockpit_test_env["teacher_alan"].employee_id


def test_teacher_cockpit_strict_tenant_isolation(client, cockpit_test_env):
    """School Beta teacher receives only Beta data, never School Alpha data."""
    res_isaac = client.get("/api/v1/teacher-cockpit", headers=cockpit_test_env["headers_isaac"])
    assert res_isaac.status_code == 200
    data = res_isaac.json()["data"]
    assert data["teacher"]["full_name"] == "Isaac Newton"
    assert data["teacher"]["school_name"] == cockpit_test_env["school_b"].name
    assert str(data["teacher"]["school_id"]) == str(cockpit_test_env["school_b"].id)
    # Isaac has no schedule in School Alpha
    assert len(data["today_schedule"]) == 0
    assert len(data["homework_overview"]) == 0


def test_teacher_cockpit_aggregation_and_substitutions(client, cockpit_test_env):
    """
    Validates that today's schedule includes both regular classes and assigned substitutions,
    attendance marked flag is computed correctly, and homework reviews pending are counted.
    """
    res = client.get("/api/v1/teacher-cockpit", headers=cockpit_test_env["headers_alan"])
    assert res.status_code == 200
    data = res.json()["data"]

    # 1. Schedule should have 2 slots: Period 1 (Regular) and Period 2 (Substitution for Ada)
    schedule = data["today_schedule"]
    assert len(schedule) == 2

    regular_slot = next(s for s in schedule if s["slot_number"] == 1)
    assert regular_slot["is_substitution"] is False
    assert regular_slot["class_name"] == "Grade 10"
    assert regular_slot["section_name"] == "A"
    assert regular_slot["subject_name"] == "Advanced Mathematics"
    assert regular_slot["attendance_marked"] is True
    assert regular_slot["attendance_stats"] == {"present": 1, "absent": 1, "late": 0}

    sub_slot = next(s for s in schedule if s["slot_number"] == 2)
    assert sub_slot["is_substitution"] is True
    assert sub_slot["original_teacher_name"] == "Ada Lovelace"

    # 2. Attendance Roster
    roster = data["attendance_roster"]
    assert len(roster) == 1
    assert roster[0]["class_name"] == "Grade 10"
    assert roster[0]["section_name"] == "A"
    assert roster[0]["is_marked"] is True
    assert roster[0]["present_count"] == 1
    assert roster[0]["absent_count"] == 1
    assert roster[0]["attendance_pct"] == 50.0

    # 3. Homework Overview
    hw = data["homework_overview"]
    assert len(hw) >= 1
    assert hw[0]["title"] == "Calculus Problem Set 1"
    assert hw[0]["total_submissions"] == 1
    assert hw[0]["pending_review_count"] == 1

    # 4. Summary KPIs
    summary = data["summary"]
    assert summary["total_classes_today"] == 2
    assert summary["pending_homework_reviews_count"] == 1
    assert summary["active_homework_count"] == 1

    # 5. Summary Endpoint
    res_sum = client.get("/api/v1/teacher-cockpit/summary", headers=cockpit_test_env["headers_alan"])
    assert res_sum.status_code == 200
    sum_data = res_sum.json()["data"]
    assert sum_data["teacher"]["full_name"] == "Alan Turing"
    assert sum_data["summary"]["total_classes_today"] == 2

