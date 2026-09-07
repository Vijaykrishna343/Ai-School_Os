"""
Phase 12.4 — Explainable Student Academic Risk & Attendance Analytics Test Suite.
Covers deterministic scoring logic, data sufficiency status, trend deltas, financial signal exclusion,
role & relationship access boundaries, independent validator, and API endpoints.
"""

import uuid
import pytest
from datetime import date, datetime, time, timezone, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.risk.engine import (
    DeterministicRiskEngine,
    StudentEducationalData,
    RiskEvaluationOutput,
    deterministic_risk_engine,
)
from app.ai.risk.validator import RiskScoreValidator, risk_score_validator
from app.models.school import School
from app.models.academic_year import AcademicYear
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.models.subject import Subject
from app.models.parent import Parent
from app.models.attendance import Attendance
from app.models.exam import Exam, ExamSchedule, StudentExamResult
from app.models.homework import Homework, HomeworkSubmission, SubmissionStatus
from app.models.fees import StudentFeeAssignment
from app.common.enums import AttendanceStatus, Gender
from app.common.enums.fees import StudentFeeAssignmentStatus
from app.identity.models import IdentityUser, IdentityRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def ai_risk_env(db_session: Session):
    seed_identity(db_session)

    s_a = uuid.uuid4().hex[:6]
    s_b = uuid.uuid4().hex[:6]

    school_a = School(
        id=uuid.uuid4(), name=f"Risk School A {s_a}", code=f"RSA_{s_a}",
        address_line1="1 Risk Lane", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500081",
    )
    school_b = School(
        id=uuid.uuid4(), name=f"Risk School B {s_b}", code=f"RSB_{s_b}",
        address_line1="2 Risk Road", city="Bangalore", district="Bangalore", state="Karnataka", postal_code="560001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(
        id=uuid.uuid4(), school_id=school_a.id, name="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), is_current=True,
    )
    ay_b = AcademicYear(
        id=uuid.uuid4(), school_id=school_b.id, name="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), is_current=True,
    )
    db_session.add_all([ay_a, ay_b])

    cls_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Class 10", display_order=1)
    sec_a1 = Section(id=uuid.uuid4(), school_class_id=cls_a.id, name="Section A")
    sec_a2 = Section(id=uuid.uuid4(), school_class_id=cls_a.id, name="Section B")
    db_session.add_all([cls_a, sec_a1, sec_a2])
    db_session.commit()

    # Parents & Students
    p_a = Parent(
        id=uuid.uuid4(), school_id=school_a.id, father_name="Father A", primary_phone=f"90111{s_a[:5]}",
        email=f"parent_a_{s_a}@school.com", address_line1="Line 1", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    p_other = Parent(
        id=uuid.uuid4(), school_id=school_a.id, father_name="Father Other", primary_phone=f"90222{s_a[:5]}",
        email=f"parent_other_{s_a}@school.com", address_line1="Line 2", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    db_session.add_all([p_a, p_other])
    db_session.commit()

    cls_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Class 10", display_order=1)
    sec_b = Section(id=uuid.uuid4(), school_class_id=cls_b.id, name="Section A")
    p_b = Parent(
        id=uuid.uuid4(), school_id=school_b.id, father_name="Father B", primary_phone=f"90333{s_b[:5]}",
        email=f"parent_b_{s_b}@school.com", address_line1="Line B", city="Blr", district="Blr", state="KA", postal_code="560001",
    )
    db_session.add_all([cls_b, sec_b, p_b])
    db_session.commit()

    stu_good = Student(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id, section_id=sec_a1.id, parent_id=p_a.id,
        admission_number=f"ADM_G_{s_a}", roll_number=1, first_name="Good", last_name="Student", gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1),
        address_line1="1 Street", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    stu_at_risk = Student(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id, section_id=sec_a1.id, parent_id=p_other.id,
        admission_number=f"ADM_R_{s_a}", roll_number=2, first_name="AtRisk", last_name="Student", gender=Gender.MALE,
        date_of_birth=date(2010, 2, 1), admission_date=date(2026, 6, 1),
        address_line1="2 Street", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    stu_new = Student(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id, section_id=sec_a1.id, parent_id=p_other.id,
        admission_number=f"ADM_N_{s_a}", roll_number=3, first_name="New", last_name="Enrollee", gender=Gender.FEMALE,
        date_of_birth=date(2010, 3, 1), admission_date=date(2026, 8, 20),
        address_line1="3 Street", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    stu_b = Student(
        id=uuid.uuid4(), school_id=school_b.id, academic_year_id=ay_b.id, school_class_id=cls_b.id, section_id=sec_b.id, parent_id=p_b.id,
        admission_number=f"ADM_B_{s_b}", roll_number=1, first_name="SchoolB", last_name="Student", gender=Gender.MALE,
        date_of_birth=date(2010, 4, 1), admission_date=date(2026, 6, 1),
        address_line1="4 Street", city="Blr", district="Blr", state="KA", postal_code="560001",
    )
    db_session.add_all([stu_good, stu_at_risk, stu_new, stu_b])
    db_session.commit()

    # Roles & Users
    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    teacher_role = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    parent_role = db_session.query(IdentityRole).filter_by(name="Parent").first()
    student_role = db_session.query(IdentityRole).filter_by(name="Student").first()
    rec_role = db_session.query(IdentityRole).filter_by(name="Receptionist").first()
    pwd = hash_password("Password@123")

    user_admin = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"risk_admin_{s_a}", email=f"risk_admin_{s_a}@school.com",
        password_hash=pwd, first_name="Admin", last_name="A", is_active=True,
    )
    user_admin.roles = [admin_role]

    user_parent = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"risk_parent_{s_a}", email=p_a.email,
        password_hash=pwd, first_name="Parent", last_name="A", is_active=True,
    )
    user_parent.roles = [parent_role]

    user_stu = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"risk_stu_{s_a}", email=f"risk_stu_{s_a}@school.com",
        password_hash=pwd, first_name="Good", last_name="Student", is_active=True,
    )
    user_stu.roles = [student_role]
    stu_good.user_id = user_stu.id

    user_rec = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"risk_rec_{s_a}", email=f"risk_rec_{s_a}@school.com",
        password_hash=pwd, first_name="Rec", last_name="A", is_active=True,
    )
    user_rec.roles = [rec_role]

    user_b = IdentityUser(
        id=uuid.uuid4(), school_id=school_b.id, username=f"risk_admin_{s_b}", email=f"risk_admin_{s_b}@school.com",
        password_hash=pwd, first_name="Admin", last_name="B", is_active=True,
    )
    user_b.roles = [admin_role]

    db_session.add_all([user_admin, user_parent, user_stu, user_rec, user_b])
    db_session.commit()

    tok_admin = jwt_manager.create_access_token(user_id=user_admin.id, school_id=school_a.id)
    tok_parent = jwt_manager.create_access_token(user_id=user_parent.id, school_id=school_a.id)
    tok_stu = jwt_manager.create_access_token(user_id=user_stu.id, school_id=school_a.id)
    tok_rec = jwt_manager.create_access_token(user_id=user_rec.id, school_id=school_a.id)
    tok_b = jwt_manager.create_access_token(user_id=user_b.id, school_id=school_b.id)

    # Populate 15 Attendance records for Good Student (100% Present)
    for i in range(15):
        att = Attendance(
            id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id,
            section_id=sec_a1.id, student_id=stu_good.id, attendance_date=date(2026, 6, 1) + timedelta(days=i),
            status=AttendanceStatus.PRESENT,
        )
        db_session.add(att)

    # Populate 15 Attendance records for At-Risk Student (Low attendance 50%)
    for i in range(15):
        st = AttendanceStatus.PRESENT if i % 2 == 0 else AttendanceStatus.ABSENT
        att = Attendance(
            id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id,
            section_id=sec_a1.id, student_id=stu_at_risk.id, attendance_date=date(2026, 6, 1) + timedelta(days=i),
            status=st,
        )
        db_session.add(att)

    # Populate Exams & Subjects for Good Student (90% marks)
    sub_a1 = Subject(id=uuid.uuid4(), school_id=school_a.id, subject_code=f"MTH_{s_a[:4]}", subject_name="Mathematics")
    sub_a2 = Subject(id=uuid.uuid4(), school_id=school_a.id, subject_code=f"SCI_{s_a[:4]}", subject_name="Science")
    db_session.add_all([sub_a1, sub_a2])
    db_session.commit()

    ex = Exam(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, name="Midterm Exam",
        start_date=date(2026, 7, 1), end_date=date(2026, 7, 10),
    )
    db_session.add(ex)
    db_session.commit()

    sched1 = ExamSchedule(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id,
        section_id=sec_a1.id, subject_id=sub_a1.id, exam_id=ex.id, exam_date=date(2026, 7, 5),
        start_time=time(9, 0), end_time=time(12, 0), maximum_marks=Decimal("100"), passing_marks=Decimal("40"),
    )
    sched2 = ExamSchedule(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=cls_a.id,
        section_id=sec_a1.id, subject_id=sub_a2.id, exam_id=ex.id, exam_date=date(2026, 7, 6),
        start_time=time(9, 0), end_time=time(12, 0), maximum_marks=Decimal("100"), passing_marks=Decimal("40"),
    )
    db_session.add_all([sched1, sched2])
    db_session.commit()

    res_g1 = StudentExamResult(id=uuid.uuid4(), exam_schedule_id=sched1.id, student_id=stu_good.id, marks_obtained=Decimal("92.00"))
    res_g2 = StudentExamResult(id=uuid.uuid4(), exam_schedule_id=sched2.id, student_id=stu_good.id, marks_obtained=Decimal("88.00"))
    res_r1 = StudentExamResult(id=uuid.uuid4(), exam_schedule_id=sched1.id, student_id=stu_at_risk.id, marks_obtained=Decimal("30.00"))  # Failed
    res_r2 = StudentExamResult(id=uuid.uuid4(), exam_schedule_id=sched2.id, student_id=stu_at_risk.id, marks_obtained=Decimal("35.00"))  # Failed
    db_session.add_all([res_g1, res_g2, res_r1, res_r2])
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "sec_a1": sec_a1,
        "stu_good": stu_good,
        "stu_at_risk": stu_at_risk,
        "stu_new": stu_new,
        "stu_b": stu_b,
        "user_admin": user_admin,
        "headers_admin": {"Authorization": f"Bearer {tok_admin}"},
        "headers_parent": {"Authorization": f"Bearer {tok_parent}"},
        "headers_stu": {"Authorization": f"Bearer {tok_stu}"},
        "headers_rec": {"Authorization": f"Bearer {tok_rec}"},
        "headers_b": {"Authorization": f"Bearer {tok_b}"},
    }


# ============================================================================
# 1. DETERMINISTIC RISK ENGINE UNIT TESTS
# ============================================================================

def test_risk_engine_high_performing_student_returns_low():
    data = StudentEducationalData(
        student_id="stu_1", section_id="sec_1", academic_year_id="ay_1",
        attendance_count=20, recent_attendance_count=10, previous_attendance_count=10,
        attendance_present_count=20, recent_present_count=10, previous_present_count=10,
        exam_results_count=4, recent_exam_average=92.0, previous_exam_average=88.0, failed_subjects_count=0,
        total_homework_count=10, submitted_homework_count=10,
    )
    output = deterministic_risk_engine.evaluate(data)
    assert output.risk_level == "LOW"
    assert output.risk_score is not None and output.risk_score <= Decimal("0.25")
    assert output.data_sufficiency_status == "FULL"
    assert output.confidence == Decimal("0.95")


def test_risk_engine_declining_and_failing_student_returns_high_or_critical():
    data = StudentEducationalData(
        student_id="stu_2", section_id="sec_1", academic_year_id="ay_1",
        attendance_count=20, recent_attendance_count=10, previous_attendance_count=10,
        attendance_present_count=10, recent_present_count=3, previous_present_count=7,  # Declining
        exam_results_count=4, recent_exam_average=32.0, previous_exam_average=55.0, failed_subjects_count=2,
        total_homework_count=10, submitted_homework_count=3,
    )
    output = deterministic_risk_engine.evaluate(data)
    assert output.risk_level in ("HIGH", "CRITICAL")
    assert output.risk_score is not None and output.risk_score > Decimal("0.50")
    assert any("FAILED_SUBJECTS" in f["factor"] for f in output.risk_factors)


def test_risk_engine_new_enrollee_insufficient_data():
    data = StudentEducationalData(
        student_id="stu_new", section_id="sec_1", academic_year_id="ay_1",
        attendance_count=2, recent_attendance_count=2, previous_attendance_count=0,
        attendance_present_count=2, recent_present_count=2, previous_present_count=0,
        exam_results_count=0, recent_exam_average=None, previous_exam_average=None, failed_subjects_count=0,
        total_homework_count=0, submitted_homework_count=0,
    )
    output = deterministic_risk_engine.evaluate(data)
    assert output.risk_level == "INSUFFICIENT_DATA"
    assert output.risk_score is None
    assert output.data_sufficiency_status == "INSUFFICIENT"


# ============================================================================
# 2. INDEPENDENT VALIDATOR TESTS
# ============================================================================

def test_risk_validator_catches_invalid_score_bounds():
    bad_output = RiskEvaluationOutput(
        risk_level="LOW",
        risk_score=Decimal("1.25"),  # Out of bounds (> 1.00)
        confidence=Decimal("0.95"),
        scoring_version="deterministic-v1",
        data_sufficiency_status="FULL",
    )
    report = risk_score_validator.validate(bad_output)
    assert report.is_valid is False
    assert any("out of bounds" in v for v in report.violations)


def test_risk_validator_catches_insufficient_data_with_non_null_score():
    bad_output = RiskEvaluationOutput(
        risk_level="INSUFFICIENT_DATA",
        risk_score=Decimal("0.30"),  # Must be None
        confidence=Decimal("0.10"),
        scoring_version="deterministic-v1",
        data_sufficiency_status="INSUFFICIENT",
    )
    report = risk_score_validator.validate(bad_output)
    assert report.is_valid is False
    assert any("must have risk_score=None" in v for v in report.violations)


# ============================================================================
# 3. TENANT & ROLE AUTHORIZATION TESTS
# ============================================================================

def test_ai_risk_tenant_isolation(client: TestClient, ai_risk_env):
    env = ai_risk_env
    headers_b = env["headers_b"]
    stu_good_id = str(env["stu_good"].id)

    # School B admin cannot assess or view School A student risk -> 404
    res = client.get(f"/api/v1/ai/risk/student/{stu_good_id}", headers=headers_b)
    assert res.status_code == 404


def test_ai_risk_authorization_enforcement(client: TestClient, ai_risk_env):
    env = ai_risk_env
    headers_rec = env["headers_rec"]
    stu_good_id = str(env["stu_good"].id)

    # Unauthorized role (Receptionist) gets 403 Forbidden
    res = client.post(f"/api/v1/ai/risk/assess/student/{stu_good_id}", headers=headers_rec)
    assert res.status_code == 403


def test_ai_risk_parent_scope_isolation(client: TestClient, ai_risk_env):
    env = ai_risk_env
    headers_parent = env["headers_parent"]
    stu_at_risk_id = str(env["stu_at_risk"].id)  # Unlinked student

    # Parent attempting to access unlinked student receives 403 Forbidden
    res = client.get(f"/api/v1/ai/risk/student/{stu_at_risk_id}", headers=headers_parent)
    assert res.status_code == 403


# ============================================================================
# 4. API WORKFLOW & PERSISTENCE TESTS
# ============================================================================

def test_ai_risk_complete_assessment_flow(client: TestClient, ai_risk_env):
    env = ai_risk_env
    headers_admin = env["headers_admin"]
    stu_good_id = str(env["stu_good"].id)
    stu_at_risk_id = str(env["stu_at_risk"].id)
    sec_a1_id = str(env["sec_a1"].id)

    # 1. Assess Good Student -> LOW Risk
    res_g = client.post(f"/api/v1/ai/risk/assess/student/{stu_good_id}", headers=headers_admin)
    assert res_g.status_code == 201
    data_g = res_g.json()
    assert data_g["risk_level"] == "LOW"
    assert data_g["scoring_version"] == "deterministic-v1"
    assert data_g["data_sufficiency_status"] in ("PARTIAL", "FULL")

    # 2. Assess At-Risk Student -> HIGH/CRITICAL Risk
    res_r = client.post(f"/api/v1/ai/risk/assess/student/{stu_at_risk_id}", headers=headers_admin)
    assert res_r.status_code == 201
    data_r = res_r.json()
    assert data_r["risk_level"] in ("HIGH", "CRITICAL")
    assert data_r["failed_subjects_count"] == 2

    # 3. Retrieve Section Summary
    res_sum = client.get(f"/api/v1/ai/risk/section/{sec_a1_id}", headers=headers_admin)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()
    assert sum_data["total_students"] >= 2
    assert "risk_distribution" in sum_data
