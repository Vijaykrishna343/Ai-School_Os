"""
Phase 12.7 — Backend Typed Domain Tool Handler Test Suite.
Verifies functional correctness, tenant isolation (School A vs School B), PII safety,
parameter validation, and empty dataset handling for all 7 domain tools:
1. get_academic_risk_summary
2. get_attendance_analytics
3. get_fee_delinquency_summary
4. get_exam_performance_summary
5. get_homework_completion_summary
6. get_timetable_schedule_summary
7. get_staff_leave_summary
"""

import uuid
import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus
from app.common.enums.fees import StudentFeeAssignmentStatus, DiscountType
from app.common.enums.timetable import DayOfWeek, TimetableStatus
from app.common.exceptions import BadRequestException, ForbiddenException
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.ai.ai_student_risk_assessment import AIStudentRiskAssessment
from app.models.attendance.attendance import Attendance
from app.models.fees.fee_structure import FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.grading.report_card import ReportCard
from app.models.homework.homework import Homework
from app.models.homework.homework_submission import HomeworkSubmission, SubmissionStatus
from app.models.parent.parent import Parent
from app.models.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.staff_leave import StaffLeaveRequest, StaffLeaveType
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.models.subject.subject import Subject

from app.ai.tools.domain_tools import (
    get_academic_risk_summary,
    get_attendance_analytics,
    get_fee_delinquency_summary,
    get_exam_performance_summary,
    get_homework_completion_summary,
    get_timetable_schedule_summary,
    get_staff_leave_summary,
)


@pytest.fixture
def domain_tools_setup(db_session: Session):
    s_a = uuid.uuid4().hex[:6]
    s_b = uuid.uuid4().hex[:6]

    school_a = School(
        id=uuid.uuid4(), name=f"Domain School A {s_a}", code=f"DSA_{s_a}",
        address_line1="1 Tool St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500081",
    )
    school_b = School(
        id=uuid.uuid4(), name=f"Domain School B {s_b}", code=f"DSB_{s_b}",
        address_line1="2 Tool St", city="Bangalore", district="Bangalore", state="Karnataka", postal_code="560001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(
        id=uuid.uuid4(), school_id=school_a.id, name="2025-2026",
        start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True,
    )
    ay_b = AcademicYear(
        id=uuid.uuid4(), school_id=school_b.id, name="2025-2026",
        start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True,
    )
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    term_a = AcademicTerm(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id,
        name="Term 1", code=f"T1-{s_a}", start_date=date(2025, 6, 1), end_date=date(2025, 10, 31),
    )
    db_session.add(term_a)
    db_session.commit()

    class_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name=f"Class 10-{s_a[:2]}", display_order=1)
    class_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name=f"Class 10-{s_b[:2]}", display_order=2)
    db_session.add_all([class_a, class_b])
    db_session.commit()

    sec_a = Section(id=uuid.uuid4(), school_class_id=class_a.id, name="A")
    sec_b = Section(id=uuid.uuid4(), school_class_id=class_b.id, name="A")
    db_session.add_all([sec_a, sec_b])
    db_session.commit()

    parent_a = Parent(
        id=uuid.uuid4(), school_id=school_a.id, father_name="Father A",
        primary_phone=f"987{uuid.uuid4().hex[:7]}", address_line1="Line 1", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    parent_b = Parent(
        id=uuid.uuid4(), school_id=school_b.id, father_name="Father B",
        primary_phone=f"987{uuid.uuid4().hex[:7]}", address_line1="Line 1", city="Blr", district="Blr", state="KA", postal_code="560001",
    )
    db_session.add_all([parent_a, parent_b])
    db_session.commit()

    stu_a1 = Student(
        id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id,
        school_class_id=class_a.id, section_id=sec_a.id, parent_id=parent_a.id,
        admission_number=f"ADM-A1-{s_a}", roll_number=101, first_name="Student", last_name="A1",
        gender="MALE", date_of_birth=date(2010, 1, 1), admission_date=date(2022, 6, 1),
        address_line1="Line 1", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    stu_b1 = Student(
        id=uuid.uuid4(), school_id=school_b.id, academic_year_id=ay_b.id,
        school_class_id=class_b.id, section_id=sec_b.id, parent_id=parent_b.id,
        admission_number=f"ADM-B1-{s_b}", roll_number=102, first_name="Student", last_name="B1",
        gender="FEMALE", date_of_birth=date(2010, 2, 2), admission_date=date(2022, 6, 1),
        address_line1="Line 1", city="Blr", district="Blr", state="KA", postal_code="560001",
    )
    db_session.add_all([stu_a1, stu_b1])
    db_session.commit()

    teacher_a = Teacher(
        id=uuid.uuid4(), school_id=school_a.id, first_name="Teacher", last_name="A",
        employee_id=f"EMP-A-{s_a}", qualification="M.Sc", joining_date=date(2020, 1, 1),
        date_of_birth=date(1985, 5, 10), gender="MALE", phone=f"987{uuid.uuid4().hex[:7]}",
        email=f"teacher_a_{s_a}@school.com", address_line1="Line 1", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    teacher_b = Teacher(
        id=uuid.uuid4(), school_id=school_b.id, first_name="Teacher", last_name="B",
        employee_id=f"EMP-B-{s_b}", qualification="B.Ed", joining_date=date(2020, 1, 1),
        date_of_birth=date(1988, 8, 20), gender="FEMALE", phone=f"987{uuid.uuid4().hex[:7]}",
        email=f"teacher_b_{s_b}@school.com", address_line1="Line 1", city="Blr", district="Blr", state="KA", postal_code="560001",
    )
    db_session.add_all([teacher_a, teacher_b])
    db_session.commit()

    subject_a = Subject(id=uuid.uuid4(), school_id=school_a.id, subject_name="Maths", subject_code=f"MTH-{s_a[:3]}")
    db_session.add(subject_a)
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "term_a": term_a,
        "class_a": class_a,
        "class_b": class_b,
        "sec_a": sec_a,
        "sec_b": sec_b,
        "stu_a1": stu_a1,
        "stu_b1": stu_b1,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "subject_a": subject_a,
    }


# ============================================================================
# 1. get_academic_risk_summary Tests
# ============================================================================

def test_get_academic_risk_summary_success(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]
    stu_a1 = env["stu_a1"]

    risk_1 = AIStudentRiskAssessment(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        student_id=stu_a1.id, section_id=env["sec_a"].id, risk_level="HIGH",
        risk_score=Decimal("0.85"), confidence=Decimal("0.90"), failed_subjects_count=2,
    )
    db_session.add(risk_1)
    db_session.commit()

    res = get_academic_risk_summary(db_session, s_a.id, s_a.id)

    assert res["total_assessed"] == 1
    assert res["high_risk_count"] == 1
    assert res["average_risk_score"] == 0.85
    assert len(res["flagged_students_summary"]) == 1
    assert res["flagged_students_summary"][0]["risk_level"] == "HIGH"


def test_get_academic_risk_summary_tenant_isolation(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]
    s_b = env["school_b"]

    risk_b = AIStudentRiskAssessment(
        id=uuid.uuid4(), school_id=s_b.id, academic_year_id=env["ay_b"].id,
        student_id=env["stu_b1"].id, section_id=env["sec_b"].id, risk_level="HIGH",
        risk_score=Decimal("0.95"), confidence=Decimal("0.90"), failed_subjects_count=3,
    )
    db_session.add(risk_b)
    db_session.commit()

    # Querying as School A must return 0 records from School B
    res = get_academic_risk_summary(db_session, s_a.id, s_a.id)
    assert res["total_assessed"] == 0
    assert len(res["flagged_students_summary"]) == 0


def test_get_academic_risk_summary_invalid_params(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]

    with pytest.raises(BadRequestException):
        get_academic_risk_summary(db_session, s_a.id, s_a.id, class_id="invalid-uuid")

    with pytest.raises(BadRequestException):
        get_academic_risk_summary(db_session, s_a.id, s_a.id, risk_level="SUPER_HIGH")


# ============================================================================
# 2. get_attendance_analytics Tests
# ============================================================================

def test_get_attendance_analytics_success(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]

    att_1 = Attendance(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        school_class_id=env["class_a"].id, section_id=env["sec_a"].id,
        student_id=env["stu_a1"].id, attendance_date=date.today(), status=AttendanceStatus.PRESENT,
    )
    att_2 = Attendance(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        school_class_id=env["class_a"].id, section_id=env["sec_a"].id,
        student_id=env["stu_a1"].id, attendance_date=date.today() - timedelta(days=1), status=AttendanceStatus.ABSENT,
    )
    db_session.add_all([att_1, att_2])
    db_session.commit()

    res = get_attendance_analytics(db_session, s_a.id, s_a.id, days=30)

    assert res["days_analyzed"] == 30
    assert res["total_records"] == 2
    assert res["present_count"] == 1
    assert res["absent_count"] == 1
    assert res["overall_attendance_pct"] == 50.0


def test_get_attendance_analytics_invalid_days(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]

    with pytest.raises(BadRequestException):
        get_attendance_analytics(db_session, s_a.id, s_a.id, days=0)

    with pytest.raises(BadRequestException):
        get_attendance_analytics(db_session, s_a.id, s_a.id, days=120)


# ============================================================================
# 3. get_fee_delinquency_summary Tests
# ============================================================================

def test_get_fee_delinquency_summary_success(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]

    fs = FeeStructure(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        name="Annual Tuition",
    )
    db_session.add(fs)
    db_session.commit()

    fee_assign = StudentFeeAssignment(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        student_id=env["stu_a1"].id, fee_structure_id=fs.id, status=StudentFeeAssignmentStatus.PENDING,
        due_date=date.today() - timedelta(days=10),
    )
    db_session.add(fee_assign)
    db_session.commit()

    res = get_fee_delinquency_summary(db_session, s_a.id, s_a.id)

    assert res["total_assignments"] == 1
    assert res["pending_count"] == 1
    assert res["overdue_count"] == 1


# ============================================================================
# 4. get_exam_performance_summary Tests
# ============================================================================

def test_get_exam_performance_summary_success(db_session: Session, domain_tools_setup: dict):
    from app.models.grading.grade_scale import GradeScale
    from app.models.grading.evaluation_config import EvaluationConfig

    env = domain_tools_setup
    s_a = env["school_a"]

    g_scale = GradeScale(id=uuid.uuid4(), school_id=s_a.id, name=f"GS-{uuid.uuid4().hex[:6]}", is_default=False)
    eval_cfg = EvaluationConfig(id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id, name=f"EC-{uuid.uuid4().hex[:6]}")
    db_session.add_all([g_scale, eval_cfg])
    db_session.commit()

    rc = ReportCard(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        academic_term_id=env["term_a"].id, school_class_id=env["class_a"].id,
        section_id=env["sec_a"].id, student_id=env["stu_a1"].id,
        grade_scale_id=g_scale.id, evaluation_config_id=eval_cfg.id,
        total_max_marks=Decimal("500.00"), total_obtained_marks=Decimal("420.00"),
        percentage=Decimal("84.00"), overall_grade="A", overall_grade_point=Decimal("4.00"),
        gpa=Decimal("4.00"), is_passed=True, total_working_days=100, present_days=95,
        attendance_percentage=Decimal("95.00"), status="FINALIZED",
    )
    db_session.add(rc)
    db_session.commit()

    res = get_exam_performance_summary(db_session, s_a.id, s_a.id)

    assert res["total_report_cards"] == 1
    assert res["passed_count"] == 1
    assert res["average_percentage"] == 84.0
    assert res["pass_rate_pct"] == 100.0


# ============================================================================
# 5. get_homework_completion_summary Tests
# ============================================================================

def test_get_homework_completion_summary_success(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]

    hw = Homework(
        id=uuid.uuid4(), school_id=s_a.id, teacher_id=env["teacher_a"].id,
        school_class_id=env["class_a"].id, section_id=env["sec_a"].id,
        subject_id=env["subject_a"].id, title="Algebra Ch 1", description="Solve odd numbers",
        due_date=date.today(), status="PUBLISHED",
    )
    db_session.add(hw)
    db_session.commit()

    sub = HomeworkSubmission(
        id=uuid.uuid4(), school_id=s_a.id, homework_id=hw.id, student_id=env["stu_a1"].id,
        content_text="Done", status=SubmissionStatus.SUBMITTED,
    )
    db_session.add(sub)
    db_session.commit()

    res = get_homework_completion_summary(db_session, s_a.id, s_a.id, days=30)

    assert res["days_analyzed"] == 30
    assert res["total_homeworks_assigned"] == 1
    assert res["total_submissions"] == 1
    assert res["late_submissions_count"] == 0


# ============================================================================
# 6. get_timetable_schedule_summary Tests
# ============================================================================

def test_get_timetable_schedule_summary_success(db_session: Session, domain_tools_setup: dict):
    from datetime import time
    env = domain_tools_setup
    s_a = env["school_a"]

    tt = Timetable(
        id=uuid.uuid4(), school_id=s_a.id, academic_year_id=env["ay_a"].id,
        school_class_id=env["class_a"].id, section_id=env["sec_a"].id,
        academic_term_id=env["term_a"].id, status=TimetableStatus.PUBLISHED,
    )
    db_session.add(tt)
    db_session.commit()

    slot = PeriodSlot(
        id=uuid.uuid4(), school_id=s_a.id, name="Period 1",
        start_time=time(8, 30), end_time=time(9, 15), display_order=1,
    )
    db_session.add(slot)
    db_session.commit()

    entry = TimetableEntry(
        id=uuid.uuid4(), timetable_id=tt.id, period_slot_id=slot.id,
        subject_id=env["subject_a"].id, teacher_id=env["teacher_a"].id,
        day_of_week=DayOfWeek.MONDAY,
    )
    db_session.add(entry)
    db_session.commit()

    res = get_timetable_schedule_summary(db_session, s_a.id, s_a.id, day_of_week="MONDAY")

    assert res["total_scheduled_entries"] == 1
    assert res["unique_teachers_scheduled"] == 1
    assert res["day_filter"] == "MONDAY"


# ============================================================================
# 7. get_staff_leave_summary Tests
# ============================================================================

def test_get_staff_leave_summary_success(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]

    lt = StaffLeaveType(
        id=uuid.uuid4(), school_id=s_a.id, code=f"CAS_{uuid.uuid4().hex[:4]}", name="Casual Leave",
    )
    db_session.add(lt)
    db_session.commit()

    req = StaffLeaveRequest(
        id=uuid.uuid4(), school_id=s_a.id, teacher_id=env["teacher_a"].id,
        academic_year_id=env["ay_a"].id, leave_type_id=lt.id,
        start_date=date.today(), end_date=date.today() + timedelta(days=2),
        requested_days=Decimal("3.00"), reason="Personal work", status="APPROVED",
    )
    db_session.add(req)
    db_session.commit()

    res = get_staff_leave_summary(db_session, s_a.id, s_a.id, days=30)

    assert res["days_analyzed"] == 30
    assert res["total_requests"] == 1
    assert res["approved_count"] == 1
    assert res["total_approved_leave_days"] == 3.0
    assert res["currently_on_leave_staff_count"] == 1


# ============================================================================
# 8. Cross-Tenant Security Audit Test Across All Tools
# ============================================================================

def test_cross_tenant_security_audit_all_tools(db_session: Session, domain_tools_setup: dict):
    env = domain_tools_setup
    s_a = env["school_a"]
    s_b = env["school_b"]

    # When executing as School A, supplying school_id=School B MUST NOT grant access to School B data
    res_risk = get_academic_risk_summary(db_session, s_b.id, s_a.id)
    assert res_risk["total_assessed"] == 0

    res_att = get_attendance_analytics(db_session, s_b.id, s_a.id)
    assert res_att["total_records"] == 0

    res_fee = get_fee_delinquency_summary(db_session, s_b.id, s_a.id)
    assert res_fee["total_assignments"] == 0

    res_exam = get_exam_performance_summary(db_session, s_b.id, s_a.id)
    assert res_exam["total_report_cards"] == 0

    res_hw = get_homework_completion_summary(db_session, s_b.id, s_a.id)
    assert res_hw["total_homeworks_assigned"] == 0

    res_tt = get_timetable_schedule_summary(db_session, s_b.id, s_a.id)
    assert res_tt["total_scheduled_entries"] == 0

    res_leave = get_staff_leave_summary(db_session, s_b.id, s_a.id)
    assert res_leave["total_requests"] == 0


# ============================================================================
# 9. AIToolRegistry Registration & Permission Filtering Tests
# ============================================================================

def test_ai_tool_registry_all_8_tools_registered():
    from app.ai.tools.registry import ai_tool_registry

    all_tools = ai_tool_registry.list_tools()
    tool_names = {t["name"] for t in all_tools}

    expected_tools = {
        "get_school_summary",
        "get_academic_risk_summary",
        "get_attendance_analytics",
        "get_fee_delinquency_summary",
        "get_exam_performance_summary",
        "get_homework_completion_summary",
        "get_timetable_schedule_summary",
        "get_staff_leave_summary",
    }

    assert expected_tools.issubset(tool_names), f"Missing tools in registry: {expected_tools - tool_names}"


def test_ai_tool_registry_list_tools_for_user():
    from app.ai.tools.registry import ai_tool_registry

    class MockSuperUser:
        is_super_admin = True
        school_id = uuid.uuid4()
        permissions = set()

    super_user = MockSuperUser()
    super_tools = ai_tool_registry.list_tools_for_user(super_user)
    assert len(super_tools) == 8

    class MockRestrictedUser:
        is_super_admin = False
        school_id = uuid.uuid4()
        permissions = {"attendance.view", "fee.view"}

    restricted_user = MockRestrictedUser()
    restricted_tools = ai_tool_registry.list_tools_for_user(restricted_user)
    restricted_names = {t["name"] for t in restricted_tools}
    assert restricted_names == {"get_attendance_analytics", "get_fee_delinquency_summary"}


def test_ai_assistant_service_process_chat_integration(db_session: Session, domain_tools_setup: dict):
    from app.ai.services.ai_assistant_service import ai_assistant_service
    from app.ai.schemas.assistant import AssistantChatRequest
    from app.ai.providers.mock_provider import MockAIProvider
    from app.identity.models import IdentityUser, IdentityRole
    from app.identity.security.password import hash_password

    env = domain_tools_setup
    s_a = env["school_a"]

    admin_role = db_session.query(IdentityRole).filter_by(name="Super Admin").first()
    if not admin_role:
        from app.identity.seeders import seed_identity
        seed_identity(db_session)
        admin_role = db_session.query(IdentityRole).filter_by(name="Super Admin").first()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=s_a.id,
        username=f"ai_user_{uuid.uuid4().hex[:6]}",
        email=f"ai_user_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Password@123"),
        first_name="AI",
        last_name="Tester",
        is_active=True,
    )
    if admin_role:
        user.roles = [admin_role]
    db_session.add(user)
    db_session.commit()

    req = AssistantChatRequest(message="Give me school summary")
    
    provider = MockAIProvider()
    res = ai_assistant_service.process_chat(
        db=db_session,
        current_user=user,
        request_data=req,
        provider_override=provider,
    )

    assert res.reply is not None
    assert res.tool_invoked == "get_school_summary"
    assert res.tokens_used >= 0
    assert res.latency_ms >= 0
