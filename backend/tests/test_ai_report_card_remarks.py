"""
Phase 12.6 AI Report Card Narrative Remarks & Qualitative Student Summary Tests
"""

import pytest
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.models.school import School
from app.models.academic_year import AcademicYear
from app.models.academic_term import AcademicTerm
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.common.enums.student import Gender
from app.models.grading import (
    GradeScale,
    EvaluationConfig,
    ReportCard,
    ReportCardItemSnapshot,
)
from app.common.enums.report_card import ReportCardStatus
from app.identity.models import IdentityUser, IdentityRole, IdentityPermission
from app.identity.security.jwt_manager import jwt_manager
from app.ai.report_card.engine import (
    AIReportCardRemarksEngine,
    ReportCardRemarksInput,
    SubjectMarkItem,
)

client = TestClient(app)


def test_01_remarks_engine_generation():
    engine = AIReportCardRemarksEngine()
    input_data = ReportCardRemarksInput(
        student_name="Aarav Sharma",
        gender="MALE",
        percentage=82.5,
        overall_grade="A",
        is_passed=True,
        attendance_percentage=94.0,
        subject_marks=[
            SubjectMarkItem(subject_name="Mathematics", percentage=95.0, grade="A+", is_passed=True),
            SubjectMarkItem(subject_name="Physics", percentage=88.0, grade="A", is_passed=True),
            SubjectMarkItem(subject_name="Chemistry", percentage=45.0, grade="F", is_passed=False),
            SubjectMarkItem(subject_name="English", percentage=80.0, grade="A", is_passed=True),
        ],
        risk_level="MEDIUM",
        tone="ENCOURAGING",
        detail_level="DETAILED",
    )

    output = engine.generate(input_data)

    assert "Aarav Sharma" in output.teacher_remarks
    assert "Mathematics" in output.strength_subjects
    assert "Chemistry" in output.focus_subjects
    assert len(output.action_items) >= 2
    assert output.token_count > 0
    assert len(output.principal_remarks) > 0


def test_02_pii_sanitization_in_remarks():
    from app.ai.security.data_minimizer import AIDataMinimizer
    sanitized, log = AIDataMinimizer.sanitize_text("Student Aarav Sharma (email: aarav@school.com, phone: 9876543210)")

    assert "aarav@school.com" not in sanitized
    assert "9876543210" not in sanitized
    assert len(log) >= 2


def test_03_ai_report_card_api_generate_and_apply():
    db = SessionLocal()

    # 1. Setup Domain Entities
    school = School(
        name=f"Report Card Test School {uuid4().hex[:8]}",
        code=f"RCS-{uuid4().hex[:8]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(school)
    db.commit()

    from datetime import date
    from app.common.enums import AcademicYearStatus

    year = AcademicYear(school_id=school.id, name=f"2026-2027 {uuid4().hex[:6]}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db.add(year)
    db.commit()

    term = AcademicTerm(school_id=school.id, academic_year_id=year.id, name=f"Term 1 {uuid4().hex[:6]}", code=f"T1-{uuid4().hex[:6]}", start_date=date(2026, 6, 1), end_date=date(2026, 10, 31))
    s_class = SchoolClass(school_id=school.id, name=f"Class 10 {uuid4().hex[:6]}", display_order=1)
    db.add_all([term, s_class])
    db.commit()

    section = Section(school_class_id=s_class.id, name=f"A-{uuid4().hex[:2]}")
    g_scale = GradeScale(school_id=school.id, name=f"Standard Scale {uuid4().hex[:6]}", is_default=False)
    eval_cfg = EvaluationConfig(school_id=school.id, academic_year_id=year.id, name=f"Default Eval Config {uuid4().hex[:6]}")
    db.add_all([section, g_scale, eval_cfg])
    db.commit()

    from app.models.parent import Parent

    parent = Parent(school_id=school.id, father_name="Father Verma", primary_phone=f"987{uuid4().hex[:7]}", address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db.add(parent)
    db.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=year.id,
        school_class_id=s_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid4().hex[:6]}",
        roll_number=101,
        first_name="Rohan",
        last_name="Verma",
        gender=Gender.MALE,
        date_of_birth=date(2010, 5, 15),
        admission_date=date(2026, 6, 1),
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(student)
    db.commit()

    report_card = ReportCard(
        school_id=school.id,
        academic_year_id=year.id,
        academic_term_id=term.id,
        student_id=student.id,
        school_class_id=s_class.id,
        section_id=section.id,
        grade_scale_id=g_scale.id,
        evaluation_config_id=eval_cfg.id,
        status=ReportCardStatus.DRAFT,
        total_max_marks=Decimal("400.00"),
        total_obtained_marks=Decimal("330.00"),
        percentage=Decimal("82.50"),
        overall_grade="A",
        is_passed=True,
        attendance_percentage=Decimal("92.00"),
    )
    db.add(report_card)
    db.commit()

    from app.models.subject import Subject

    sub1 = Subject(school_id=school.id, subject_name="Mathematics", subject_code=f"MTH-{uuid4().hex[:4]}")
    sub2 = Subject(school_id=school.id, subject_name="Science", subject_code=f"SCI-{uuid4().hex[:4]}")
    db.add_all([sub1, sub2])
    db.commit()

    item1 = ReportCardItemSnapshot(
        report_card_id=report_card.id,
        subject_id=sub1.id,
        subject_name=sub1.subject_name,
        subject_code=sub1.subject_code,
        max_marks=Decimal("100.00"),
        obtained_marks=Decimal("95.00"),
        percentage=Decimal("95.00"),
        grade_code="A+",
        is_pass=True,
    )
    item2 = ReportCardItemSnapshot(
        report_card_id=report_card.id,
        subject_id=sub2.id,
        subject_name=sub2.subject_name,
        subject_code=sub2.subject_code,
        max_marks=Decimal("100.00"),
        obtained_marks=Decimal("45.00"),
        percentage=Decimal("45.00"),
        grade_code="F",
        is_pass=False,
    )
    db.add_all([item1, item2])
    db.commit()

    # 2. Setup Authorized User & Token
    perm = db.query(IdentityPermission).filter_by(name="report_card.edit_remarks").first()
    if not perm:
        perm = IdentityPermission(name="report_card.edit_remarks", module="report_card", action="edit_remarks", description="Edit report card remarks")
        db.add(perm)
        db.commit()

    role = IdentityRole(name=f"Teacher_{uuid4().hex[:6]}", school_id=school.id)
    role.permissions.append(perm)
    db.add(role)
    db.commit()

    user = IdentityUser(
        email=f"teacher.{uuid4().hex[:6]}@school.com",
        username=f"teacher_{uuid4().hex[:6]}",
        password_hash="hashed_secret",
        first_name="Test",
        last_name="Teacher",
        school_id=school.id,
        is_active=True,
    )
    user.roles.append(role)
    db.add(user)
    db.commit()

    token = jwt_manager.create_access_token(
        user_id=user.id,
        school_id=school.id,
    )
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Call Generate API
    resp_gen = client.post(
        "/api/v1/ai/report-card/remarks/generate",
        json={
            "report_card_id": str(report_card.id),
            "tone": "ENCOURAGING",
            "detail_level": "DETAILED",
        },
        headers=headers,
    )

    assert resp_gen.status_code == 200
    gen_data = resp_gen.json()
    assert "Rohan" in gen_data["teacher_remarks_draft"]
    assert "Mathematics" in gen_data["strength_subjects"]
    assert "Science" in gen_data["focus_subjects"]

    # 4. Call Get API
    resp_get = client.get(
        f"/api/v1/ai/report-card/remarks/{report_card.id}",
        headers=headers,
    )
    assert resp_get.status_code == 200
    assert resp_get.json()["id"] == gen_data["id"]

    # 5. Call Apply API
    resp_apply = client.post(
        "/api/v1/ai/report-card/remarks/apply",
        json={
            "report_card_id": str(report_card.id),
            "teacher_remarks": gen_data["teacher_remarks_draft"],
            "principal_remarks": gen_data["principal_remarks_draft"],
        },
        headers=headers,
    )

    assert resp_apply.status_code == 200
    rc_data = resp_apply.json()
    assert rc_data["teacher_remarks"] == gen_data["teacher_remarks_draft"]
    assert rc_data["principal_remarks"] == gen_data["principal_remarks_draft"]

    db.close()


def test_04_ai_report_card_rbac_unauthorized():
    db = SessionLocal()

    school = School(
        name=f"Report Card RBAC School {uuid4().hex[:8]}",
        code=f"RCR-{uuid4().hex[:8]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(school)
    db.commit()

    # User without report_card.edit_remarks
    unauth_user = IdentityUser(
        email=f"parent.{uuid4().hex[:6]}@school.com",
        username=f"parent_{uuid4().hex[:6]}",
        password_hash="hashed_secret",
        first_name="Parent",
        last_name="User",
        school_id=school.id,
        is_active=True,
    )
    db.add(unauth_user)
    db.commit()

    token = jwt_manager.create_access_token(
        user_id=unauth_user.id,
        school_id=school.id,
    )
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.post(
        "/api/v1/ai/report-card/remarks/generate",
        json={"report_card_id": str(uuid4())},
        headers=headers,
    )

    assert resp.status_code == 403

    db.close()
