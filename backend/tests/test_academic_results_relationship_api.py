"""
Relationship Security Tests for Academic Results & Report Card API Endpoints (SEC-004B).
Tests HTTP route authorization for:
- GET /api/v1/student-exam-results
- GET /api/v1/student-exam-results/{result_id}
- GET /api/v1/report-cards
- GET /api/v1/report-cards/{report_card_id}
- GET /api/v1/export/exam-results
"""
import uuid
from datetime import date, time
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.exam import AssessmentType, AttemptType, ExamStatus
from app.common.enums.report_card import ReportCardStatus
from app.identity.models import IdentityPermission, IdentityRole, IdentityRolePermission, IdentityUser, IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.models.academic_year.academic_year import AcademicYear
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading.grade_scale import GradeScale
from app.models.grading.report_card import ReportCard
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.models.grading.evaluation_config import EvaluationConfig
from app.main import app

client = TestClient(app)


def create_role_with_permissions(db, school_id, role_name, permission_names):
    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_id,
        name=role_name,
        description=f"{role_name} test role",
        is_system=True,
    )
    db.add(role)
    db.commit()

    for perm_name in permission_names:
        from app.identity.repositories import permission_repository
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()
    return role


def create_user_and_auth_headers(db, school_id, email, role, username=None, phone=None):
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_id,
        email=email,
        username=username,
        phone=phone,
        password_hash="hash123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school_id)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def academic_results_fixture(db_session):
    """
    Sets up School A & School B, Parent A (with Child A1 & Child A2), Parent B (with Child B1),
    Parent C (no children), Student A1, Student B1, Teacher, SuperAdmin, cross-tenant entities,
    exam results, and report card records.
    """
    db = db_session

    from app.identity.seeders import seed_identity
    seed_identity(db)

    # 1. School A & School B
    school_a = School(
        id=uuid.uuid4(),
        name="School Alpha",
        code=f"SCHA_{uuid.uuid4().hex[:4]}",
        address_line1="100 Alpha St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    school_b = School(
        id=uuid.uuid4(),
        name="School Beta",
        code=f"SCHB_{uuid.uuid4().hex[:4]}",
        address_line1="200 Beta St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110002",
    )
    db.add_all([school_a, school_b])
    db.commit()

    # 2. Roles with academic permissions
    perms = ["exam.view", "marks.view", "report_card.view", "student.view"]
    parent_role = create_role_with_permissions(db, school_a.id, "Parent", perms)
    student_role = create_role_with_permissions(db, school_a.id, "Student", perms)
    teacher_role = create_role_with_permissions(db, school_a.id, "Teacher", perms)
    superadmin_role = create_role_with_permissions(db, school_a.id, "Super Admin", perms)

    # 3. Parents
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Alpha",
        primary_phone="+919876543240",
        email="parenta_res@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Beta",
        primary_phone="+919876543241",
        email="parentb_res@schoola.com",
        address_line1="456 Park Ave",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent_no_children = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Childless",
        primary_phone="+919876543242",
        email="parent_no_child_res@schoola.com",
        address_line1="789 Lonely Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent_b_school = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Father School B",
        primary_phone="+919876543249",
        email="parent_b_school_res@schoolb.com",
        address_line1="100 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
    )
    db.add_all([parent_a, parent_b, parent_no_children, parent_b_school])
    db.commit()

    # 4. Academic Year, Class, Section, Subject
    ay_a = AcademicYear(id=uuid.uuid4(), school_id=school_a.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Class 10", display_order=1)
    db.add_all([ay_a, sc_a])
    db.commit()
    sec_a = Section(id=uuid.uuid4(), school_class_id=sc_a.id, name="Section A")
    subj_a = Subject(id=uuid.uuid4(), school_id=school_a.id, subject_code="MATH10", subject_name="Mathematics")
    db.add_all([sec_a, subj_a])
    db.commit()

    # Students for Parent A (2 children)
    child_a1 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-RES-A1",
        roll_number="01",
        first_name="ChildA1",
        last_name="Alpha",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2025, 4, 1),
        email="child_a1_res@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    child_a2 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-RES-A2",
        roll_number="02",
        first_name="ChildA2",
        last_name="Alpha",
        gender=Gender.FEMALE,
        date_of_birth=date(2012, 2, 2),
        admission_date=date(2025, 4, 1),
        email="child_a2_res@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    # Student for Parent B (1 child)
    child_b1 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_b.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-RES-B1",
        roll_number="03",
        first_name="ChildB1",
        last_name="Beta",
        gender=Gender.MALE,
        date_of_birth=date(2011, 3, 3),
        admission_date=date(2025, 4, 1),
        email="child_b1_res@schoola.com",
        address_line1="456 Park Ave",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )

    # Student in School B
    ay_b = AcademicYear(id=uuid.uuid4(), school_id=school_b.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Class 10", display_order=1)
    db.add_all([ay_b, sc_b])
    db.commit()
    sec_b = Section(id=uuid.uuid4(), school_class_id=sc_b.id, name="Section B")
    subj_b = Subject(id=uuid.uuid4(), school_id=school_b.id, subject_code="MATH10B", subject_name="Mathematics B")
    eval_a = EvaluationConfig(id=uuid.uuid4(), school_id=school_a.id, academic_year_id=ay_a.id, name=f"Config_A_{uuid.uuid4().hex[:6]}", is_default=False)
    eval_b = EvaluationConfig(id=uuid.uuid4(), school_id=school_b.id, academic_year_id=ay_b.id, name=f"Config_B_{uuid.uuid4().hex[:6]}", is_default=False)
    db.add_all([sec_b, subj_b, eval_a, eval_b])
    db.commit()

    student_school_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        parent_id=parent_b_school.id,
        academic_year_id=ay_b.id,
        school_class_id=sc_b.id,
        section_id=sec_b.id,
        admission_number="ADM-RES-SCHB",
        roll_number="01",
        first_name="ChildB",
        last_name="SchoolB",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 5, 5),
        admission_date=date(2025, 4, 1),
        email="student_b_res@schoolb.com",
        address_line1="100 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
        status=StudentStatus.ACTIVE,
    )
    db.add_all([child_a1, child_a2, child_b1, student_school_b])
    db.commit()

    # 5. Exam, ExamSchedule
    exam_a = Exam(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        name="Midterm 2026",
        assessment_type=AssessmentType.SUMMATIVE_ASSESSMENT,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
        status=ExamStatus.COMPLETED,
    )
    exam_b = Exam(
        id=uuid.uuid4(),
        school_id=school_b.id,
        academic_year_id=ay_b.id,
        name="Midterm 2026 B",
        assessment_type=AssessmentType.SUMMATIVE_ASSESSMENT,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 15),
        status=ExamStatus.COMPLETED,
    )
    db.add_all([exam_a, exam_b])
    db.commit()

    sched_a = ExamSchedule(
        id=uuid.uuid4(),
        school_id=school_a.id,
        exam_id=exam_a.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        subject_id=subj_a.id,
        exam_date=date(2026, 10, 5),
        start_time=time(9, 0),
        end_time=time(12, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("35.00"),
    )
    sched_b = ExamSchedule(
        id=uuid.uuid4(),
        school_id=school_b.id,
        exam_id=exam_b.id,
        academic_year_id=ay_b.id,
        school_class_id=sc_b.id,
        section_id=sec_b.id,
        subject_id=subj_b.id,
        exam_date=date(2026, 10, 5),
        start_time=time(9, 0),
        end_time=time(12, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("35.00"),
    )
    db.add_all([sched_a, sched_b])
    db.commit()

    # 6. Student Exam Results
    res_a1 = StudentExamResult(
        id=uuid.uuid4(),
        exam_schedule_id=sched_a.id,
        student_id=child_a1.id,
        marks_obtained=Decimal("95.00"),
        remarks="Excellent A1",
    )
    res_a2 = StudentExamResult(
        id=uuid.uuid4(),
        exam_schedule_id=sched_a.id,
        student_id=child_a2.id,
        marks_obtained=Decimal("88.00"),
        remarks="Great A2",
    )
    res_b1 = StudentExamResult(
        id=uuid.uuid4(),
        exam_schedule_id=sched_a.id,
        student_id=child_b1.id,
        marks_obtained=Decimal("72.00"),
        remarks="Good B1",
    )
    res_sch_b = StudentExamResult(
        id=uuid.uuid4(),
        exam_schedule_id=sched_b.id,
        student_id=student_school_b.id,
        marks_obtained=Decimal("90.00"),
        remarks="Good B",
    )
    db.add_all([res_a1, res_a2, res_b1, res_sch_b])
    db.commit()

    # 7. Grade Scales & Report Cards
    gs_a = GradeScale(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Standard 10-Point Scale",
        is_default=True,
    )
    gs_b = GradeScale(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="Standard 10-Point Scale B",
        is_default=True,
    )
    db.add_all([gs_a, gs_b])
    db.commit()

    rc_a1 = ReportCard(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        student_id=child_a1.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        grade_scale_id=gs_a.id,
        evaluation_config_id=eval_a.id,
        status=ReportCardStatus.PUBLISHED,
        total_max_marks=Decimal("100.00"),
        total_obtained_marks=Decimal("95.00"),
        percentage=Decimal("95.00"),
        overall_grade="A+",
        overall_grade_point=Decimal("10.00"),
        is_passed=True,
        total_working_days=100,
        present_days=95,
        attendance_percentage=Decimal("95.00"),
    )
    rc_a2 = ReportCard(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        student_id=child_a2.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        grade_scale_id=gs_a.id,
        evaluation_config_id=eval_a.id,
        status=ReportCardStatus.PUBLISHED,
        total_max_marks=Decimal("100.00"),
        total_obtained_marks=Decimal("88.00"),
        percentage=Decimal("88.00"),
        overall_grade="A",
        overall_grade_point=Decimal("9.00"),
        is_passed=True,
        total_working_days=100,
        present_days=90,
        attendance_percentage=Decimal("90.00"),
    )
    rc_b1 = ReportCard(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        student_id=child_b1.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        grade_scale_id=gs_a.id,
        evaluation_config_id=eval_a.id,
        status=ReportCardStatus.PUBLISHED,
        total_max_marks=Decimal("100.00"),
        total_obtained_marks=Decimal("72.00"),
        percentage=Decimal("72.00"),
        overall_grade="B",
        overall_grade_point=Decimal("7.00"),
        is_passed=True,
        total_working_days=100,
        present_days=85,
        attendance_percentage=Decimal("85.00"),
    )
    rc_sch_b = ReportCard(
        id=uuid.uuid4(),
        school_id=school_b.id,
        academic_year_id=ay_b.id,
        student_id=student_school_b.id,
        school_class_id=sc_b.id,
        section_id=sec_b.id,
        grade_scale_id=gs_b.id,
        evaluation_config_id=eval_b.id,
        status=ReportCardStatus.PUBLISHED,
        total_max_marks=Decimal("100.00"),
        total_obtained_marks=Decimal("90.00"),
        percentage=Decimal("90.00"),
        overall_grade="A",
        overall_grade_point=Decimal("9.00"),
        is_passed=True,
        total_working_days=100,
        present_days=95,
        attendance_percentage=Decimal("95.00"),
    )
    db.add_all([rc_a1, rc_a2, rc_b1, rc_sch_b])
    db.commit()

    # 8. Identity Users & Auth Headers
    user_parent_a, headers_parent_a = create_user_and_auth_headers(
        db, school_a.id, "parenta_res@schoola.com", parent_role, phone="+919876543240"
    )
    user_parent_b, headers_parent_b = create_user_and_auth_headers(
        db, school_a.id, "parentb_res@schoola.com", parent_role, phone="+919876543241"
    )
    user_parent_no_child, headers_parent_no_child = create_user_and_auth_headers(
        db, school_a.id, "parent_no_child_res@schoola.com", parent_role, phone="+919876543242"
    )
    user_student_a1, headers_student_a1 = create_user_and_auth_headers(
        db, school_a.id, "child_a1_res@schoola.com", student_role, username="ADM-RES-A1"
    )
    user_student_b1, headers_student_b1 = create_user_and_auth_headers(
        db, school_a.id, "child_b1_res@schoola.com", student_role, username="ADM-RES-B1"
    )
    user_teacher, headers_teacher = create_user_and_auth_headers(
        db, school_a.id, "teacher_res@schoola.com", teacher_role
    )
    user_superadmin, headers_superadmin = create_user_and_auth_headers(
        db, school_a.id, "superadmin_res@schoola.com", superadmin_role
    )

    return {
        "school_a": school_a,
        "school_b": school_b,
        "parent_a": parent_a,
        "child_a1": child_a1,
        "child_a2": child_a2,
        "child_b1": child_b1,
        "student_school_b": student_school_b,
        "res_a1": res_a1,
        "res_a2": res_a2,
        "res_b1": res_b1,
        "res_sch_b": res_sch_b,
        "rc_a1": rc_a1,
        "rc_a2": rc_a2,
        "rc_b1": rc_b1,
        "rc_sch_b": rc_sch_b,
        "headers_parent_a": headers_parent_a,
        "headers_parent_b": headers_parent_b,
        "headers_parent_no_child": headers_parent_no_child,
        "headers_student_a1": headers_student_a1,
        "headers_student_b1": headers_student_b1,
        "headers_teacher": headers_teacher,
        "headers_superadmin": headers_superadmin,
    }


# ============================================================================
# STUDENT EXAM RESULTS TESTS
# ============================================================================

def test_parent_list_exam_results_returns_only_linked_children(client, academic_results_fixture):
    fx = academic_results_fixture
    response = client.get("/api/v1/student-exam-results", headers=fx["headers_parent_a"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    retrieved_student_ids = {item["student_id"] for item in data["items"]}
    assert retrieved_student_ids == {str(fx["child_a1"].id), str(fx["child_a2"].id)}


def test_parent_get_own_child_exam_result_detail_success(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results/{fx['res_a1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 200
    assert response.json()["id"] == str(fx["res_a1"].id)


def test_parent_get_other_parent_child_exam_result_detail_denied(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results/{fx['res_b1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 403


def test_parent_cannot_get_unrelated_student_exam_result_via_filter(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results?student_id={fx['child_b1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


def test_parent_cannot_access_cross_tenant_exam_result(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results/{fx['res_sch_b'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code in (403, 404)


def test_student_list_exam_results_returns_only_self(client, academic_results_fixture):
    fx = academic_results_fixture
    response = client.get("/api/v1/student-exam-results", headers=fx["headers_student_a1"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["student_id"] == str(fx["child_a1"].id)


def test_student_get_own_exam_result_detail_success(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results/{fx['res_a1'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 200
    assert response.json()["id"] == str(fx["res_a1"].id)


def test_student_get_other_student_exam_result_detail_denied(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results/{fx['res_a2'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 403


def test_student_exam_result_query_tampering_cannot_expose_others(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/student-exam-results?student_id={fx['child_b1'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    assert data["items"] == []


# ============================================================================
# REPORT CARD TESTS
# ============================================================================

def test_parent_list_report_cards_returns_only_linked_children(client, academic_results_fixture):
    fx = academic_results_fixture
    response = client.get("/api/v1/report-cards", headers=fx["headers_parent_a"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    retrieved_student_ids = {item["student_id"] for item in data["items"]}
    assert retrieved_student_ids == {str(fx["child_a1"].id), str(fx["child_a2"].id)}


def test_parent_get_own_child_report_card_detail_success(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/report-cards/{fx['rc_a1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 200
    assert response.json()["id"] == str(fx["rc_a1"].id)


def test_parent_get_other_parent_child_report_card_detail_denied(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/report-cards/{fx['rc_b1'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code == 403


def test_student_list_report_cards_returns_only_self(client, academic_results_fixture):
    fx = academic_results_fixture
    response = client.get("/api/v1/report-cards", headers=fx["headers_student_a1"])
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["student_id"] == str(fx["child_a1"].id)


def test_student_get_own_report_card_detail_success(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/report-cards/{fx['rc_a1'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 200
    assert response.json()["id"] == str(fx["rc_a1"].id)


def test_student_get_other_student_report_card_detail_denied(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/report-cards/{fx['rc_a2'].id}"
    response = client.get(url, headers=fx["headers_student_a1"])
    assert response.status_code == 403


def test_cross_tenant_report_card_access_denied(client, academic_results_fixture):
    fx = academic_results_fixture
    url = f"/api/v1/report-cards/{fx['rc_sch_b'].id}"
    response = client.get(url, headers=fx["headers_parent_a"])
    assert response.status_code in (403, 404)


# ============================================================================
# EXPORT EXAM RESULTS TESTS
# ============================================================================

def test_parent_exam_results_export_contains_only_linked_children(client, academic_results_fixture):
    fx = academic_results_fixture
    response = client.get("/api/v1/export/exam-results", headers=fx["headers_parent_a"])
    assert response.status_code == 200
    content = response.text
    assert "ADM-RES-A1" in content or "ChildA1 Alpha" in content
    assert "ADM-RES-B1" not in content and "ChildB1 Beta" not in content


def test_student_exam_results_export_contains_only_self(client, academic_results_fixture):
    fx = academic_results_fixture
    response = client.get("/api/v1/export/exam-results", headers=fx["headers_student_a1"])
    assert response.status_code == 200
    content = response.text
    assert "ADM-RES-A1" in content
    assert "ADM-RES-A2" not in content
    assert "ADM-RES-B1" not in content


# ============================================================================
# STAFF & SUPER ADMIN TESTS
# ============================================================================

def test_teacher_unrestricted_academic_results_list_and_detail_success(client, academic_results_fixture):
    fx = academic_results_fixture
    res_list = client.get("/api/v1/student-exam-results", headers=fx["headers_teacher"])
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 3

    res_detail = client.get(f"/api/v1/student-exam-results/{fx['res_b1'].id}", headers=fx["headers_teacher"])
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == str(fx["res_b1"].id)


def test_superadmin_unrestricted_academic_results_access_success(client, academic_results_fixture):
    fx = academic_results_fixture
    res_list = client.get("/api/v1/student-exam-results", headers=fx["headers_superadmin"])
    assert res_list.status_code == 200

    res_detail = client.get(f"/api/v1/student-exam-results/{fx['res_a1'].id}", headers=fx["headers_superadmin"])
    assert res_detail.status_code == 200
