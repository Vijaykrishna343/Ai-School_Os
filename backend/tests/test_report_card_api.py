import uuid
from datetime import date, time
from decimal import Decimal

from app.common.enums import (
    AcademicYearStatus,
    AssessmentType,
    AttendanceStatus,
    Gender,
    ReportCardStatus,
)
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
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.attendance.attendance import Attendance
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading.grade_scale import GradeScale
from app.models.grading.grade_scale_entry import GradeScaleEntry
from app.models.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject


def create_school_and_user(db, school_name, school_code, permissions_list):
    seed_identity(db)
    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 RC Way",
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
        name=f"ROLE_RC_{uuid.uuid4().hex[:6]}",
        description="RC Role",
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
        first_name="Report",
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


def test_report_card_api_flow(db_session, client):
    perms = [
        "report_card.generate",
        "report_card.view",
        "report_card.edit_remarks",
        "report_card.finalize",
        "report_card.publish",
    ]
    school, user, headers = create_school_and_user(
        db_session, "API RC School", "RCAPI", perms
    )

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    db_session.flush()

    term = AcademicTerm(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1",
        code="T1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 10, 31),
    )
    db_session.add(term)

    school_class = SchoolClass(school_id=school.id, name="Class 10", display_order=1)
    db_session.add(school_class)
    db_session.flush()

    section = Section(school_class_id=school_class.id, name="Section A")
    db_session.add(section)
    db_session.flush()

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        primary_phone="9999999999",
        email=f"parent_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Parent St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(parent)
    db_session.flush()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:6]}",
        roll_number="1",
        first_name="Jane",
        last_name="Doe",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2026, 6, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db_session.add(student)

    subject = Subject(
        school_id=school.id,
        subject_name="Physics",
        subject_code="PHY10",
    )
    db_session.add(subject)
    db_session.flush()

    # Grade scale
    gs = GradeScale(school_id=school.id, name="Standard Scale", is_default=True)
    db_session.add(gs)
    db_session.flush()

    g1 = GradeScaleEntry(
        grade_scale_id=gs.id,
        grade_code="A",
        min_percentage=Decimal("80.00"),
        max_percentage=Decimal("100.00"),
        grade_point=Decimal("10.00"),
        is_pass=True,
    )
    db_session.add(g1)

    # Exam & Schedule
    exam = Exam(
        school_id=school.id,
        academic_year_id=ay.id,
        academic_term_id=term.id,
        name="Term Exam",
        assessment_type=AssessmentType.TERM,
        start_date=date(2026, 8, 1),
        end_date=date(2026, 8, 10),
    )
    db_session.add(exam)
    db_session.flush()

    sch = ExamSchedule(
        exam_id=exam.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        subject_id=subject.id,
        exam_date=date(2026, 8, 5),
        start_time=time(9, 0),
        end_time=time(12, 0),
        maximum_marks=Decimal("100.00"),
        passing_marks=Decimal("40.00"),
    )
    db_session.add(sch)
    db_session.flush()

    res = StudentExamResult(
        exam_schedule_id=sch.id,
        student_id=student.id,
        marks_obtained=Decimal("92.00"),
    )
    db_session.add(res)
    db_session.commit()

    # 1. Generate Report Card via API
    gen_payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "academic_term_id": str(term.id),
        "student_id": str(student.id),
    }
    response = client.post("/api/v1/report-cards/generate", json=gen_payload, headers=headers)
    assert response.status_code == 201
    cards = response.json()
    assert len(cards) == 1
    card_id = cards[0]["id"]
    assert cards[0]["total_obtained_marks"] == "92.00"
    assert cards[0]["status"] == "DRAFT"

    # 2. List Report Cards via API
    response = client.get(f"/api/v1/report-cards?academic_year_id={ay.id}", headers=headers)
    assert response.status_code == 200
    list_data = response.json()
    assert list_data["total"] == 1

    # 3. Finalize Report Card via API
    response = client.put(f"/api/v1/report-cards/{card_id}/finalize", headers=headers)
    assert response.status_code == 200
    finalized = response.json()
    assert finalized["status"] == "FINALIZED"

    # 4. Publish Report Card via API
    response = client.put(f"/api/v1/report-cards/{card_id}/publish", headers=headers)
    assert response.status_code == 200
    published = response.json()
    assert published["status"] == "PUBLISHED"
