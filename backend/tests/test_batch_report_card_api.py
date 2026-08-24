import uuid
from decimal import Decimal
from datetime import date, time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums.report_card import ReportCardStatus
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.parent.parent import Parent
from app.models.subject.subject import Subject
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading.grade_scale import GradeScale
from app.models.grading.grade_scale_entry import GradeScaleEntry
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.grading.report_card import ReportCard
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_batch_report_card_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    school_a = School(
        name=f"Batch RC School A {s}", code=f"BRCA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    school_b = School(
        name=f"Batch RC School B {s}", code=f"BRCB_{s}",
        address_line1="456 Other St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay = AcademicYear(school_id=school_a.id, name=f"2025-2026 {s}", start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True)
    db_session.add(ay)
    db_session.commit()

    term = AcademicTerm(school_id=school_a.id, academic_year_id=ay.id, name="Term 1", code=f"T1_{s}", start_date=date(2025, 6, 1), end_date=date(2025, 10, 31))
    db_session.add(term)
    db_session.commit()

    sc = SchoolClass(school_id=school_a.id, name="Grade 10", display_order=10)
    db_session.add(sc)
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="A")
    db_session.add(sec)
    db_session.commit()

    p = Parent(
        school_id=school_a.id, father_name="Father One", primary_phone=f"9888{s[:6]}",
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(p)
    db_session.commit()

    s1 = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=p.id,
        first_name="Alice", last_name="Student", admission_number=f"ADM_S1_{s}", roll_number="101",
        gender="FEMALE", date_of_birth=date(2010, 1, 1), admission_date=date(2020, 6, 1),
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    s2 = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=p.id,
        first_name="Bob", last_name="Student", admission_number=f"ADM_S2_{s}", roll_number="102",
        gender="MALE", date_of_birth=date(2010, 2, 1), admission_date=date(2020, 6, 1),
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([s1, s2])
    db_session.commit()

    sub = Subject(school_id=school_a.id, subject_name="Physics", subject_code=f"PHY_{s}")
    db_session.add(sub)
    db_session.commit()

    exam = Exam(school_id=school_a.id, academic_year_id=ay.id, academic_term_id=term.id, name="Midterm Exam", start_date=date(2025, 9, 1), end_date=date(2025, 9, 10))
    db_session.add(exam)
    db_session.commit()

    sch = ExamSchedule(
        school_id=school_a.id, academic_year_id=ay.id, exam_id=exam.id, subject_id=sub.id,
        school_class_id=sc.id, section_id=sec.id, exam_date=date(2025, 9, 5),
        start_time=time(9, 0), end_time=time(12, 0),
        maximum_marks=Decimal("100.00"), passing_marks=Decimal("35.00")
    )
    db_session.add(sch)
    db_session.commit()

    # Results for s1 only (s2 missing)
    res1 = StudentExamResult(
        exam_schedule_id=sch.id, student_id=s1.id, marks_obtained=Decimal("85.00")
    )
    db_session.add(res1)
    db_session.commit()

    # Grade scale & eval config
    gs = GradeScale(school_id=school_a.id, name="Default 10-Point Scale", is_default=True)
    db_session.add(gs)
    db_session.commit()
    gse = GradeScaleEntry(grade_scale_id=gs.id, grade_code="A", min_percentage=Decimal("80.00"), max_percentage=Decimal("100.00"), grade_point=Decimal("9.00"))
    db_session.add(gse)

    ec = EvaluationConfig(school_id=school_a.id, academic_year_id=ay.id, name="Default Eval Config", is_default=True)
    db_session.add(ec)
    db_session.commit()

    # Users
    pwd = hash_password("Password@123")
    u_admin = IdentityUser(email=f"admin_brc_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin")
    u_parent = IdentityUser(email=f"parent_brc_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent")
    u_student = IdentityUser(email=s1.email or f"s1_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", username=s1.admission_number)

    db_session.add_all([u_admin, u_parent, u_student])
    db_session.commit()

    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_parent.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_student.id, role_id=r_student.id),
    ])
    db_session.commit()

    tok_admin = jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id)
    tok_parent = jwt_manager.create_access_token(user_id=u_parent.id, school_id=school_a.id)
    tok_student = jwt_manager.create_access_token(user_id=u_student.id, school_id=school_a.id)

    return {
        "school_a": school_a, "ay": ay, "term": term, "sc": sc, "sec": sec,
        "s1": s1, "s2": s2, "tok_admin": tok_admin, "tok_parent": tok_parent, "tok_student": tok_student,
    }


def test_01_preview_batch_report_cards(client: TestClient, setup_batch_report_card_data):
    d = setup_batch_report_card_data
    payload = {
        "school_class_id": str(d["sc"].id),
        "section_id": str(d["sec"].id),
        "academic_year_id": str(d["ay"].id),
        "academic_term_id": str(d["term"].id),
    }
    res = client.post("/api/v1/report-cards/batch-preview", json=payload, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()
    assert data["total_students"] == 2
    assert data["eligible_count"] == 1
    assert data["missing_data_count"] == 1


def test_02_batch_generate_report_cards(client: TestClient, setup_batch_report_card_data):
    d = setup_batch_report_card_data
    payload = {
        "school_class_id": str(d["sc"].id),
        "section_id": str(d["sec"].id),
        "academic_year_id": str(d["ay"].id),
        "academic_term_id": str(d["term"].id),
    }
    res = client.post("/api/v1/report-cards/batch-generate", json=payload, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()
    assert data["generated_count"] == 2  # Generates for s1 (eligible) and s2 (default calculations)


def test_03_batch_finalize_report_cards(client: TestClient, setup_batch_report_card_data):
    d = setup_batch_report_card_data
    # First generate
    payload_gen = {
        "school_class_id": str(d["sc"].id),
        "section_id": str(d["sec"].id),
        "academic_year_id": str(d["ay"].id),
        "academic_term_id": str(d["term"].id),
    }
    client.post("/api/v1/report-cards/batch-generate", json=payload_gen, headers={"Authorization": f"Bearer {d['tok_admin']}"})

    # Finalize
    payload_fin = {
        "school_class_id": str(d["sc"].id),
        "section_id": str(d["sec"].id),
        "academic_year_id": str(d["ay"].id),
        "academic_term_id": str(d["term"].id),
    }
    res = client.post("/api/v1/report-cards/batch-finalize", json=payload_fin, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()
    assert data["finalized_count"] == 2

    # Repeated finalization is idempotent
    res_repeat = client.post("/api/v1/report-cards/batch-finalize", json=payload_fin, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res_repeat.status_code == 200
    assert res_repeat.json()["already_finalized_count"] == 2


def test_04_parent_and_student_batch_operations_denied(client: TestClient, setup_batch_report_card_data):
    d = setup_batch_report_card_data
    payload = {
        "school_class_id": str(d["sc"].id),
        "section_id": str(d["sec"].id),
        "academic_year_id": str(d["ay"].id),
        "academic_term_id": str(d["term"].id),
    }
    res_p = client.post("/api/v1/report-cards/batch-generate", json=payload, headers={"Authorization": f"Bearer {d['tok_parent']}"})
    assert res_p.status_code == 403

    res_s = client.post("/api/v1/report-cards/batch-finalize", json=payload, headers={"Authorization": f"Bearer {d['tok_student']}"})
    assert res_s.status_code == 403
