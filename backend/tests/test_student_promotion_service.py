from datetime import date, timedelta
from uuid import uuid4

import pytest

from app.common.enums import (
    EnrollmentStatus,
    PromotionDecision,
    StudentStatus,
    TransferCertificateStatus,
)
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.academic_year import AcademicYear
from app.models.parent import Parent
from app.models.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.schemas.student.promotion_schema import (
    AcademicYearTransitionRequest,
    BulkStudentPromotionItem,
    BulkStudentPromotionRequest,
    BulkStudentRetentionItem,
    BulkStudentRetentionRequest,
    StudentPromotionRequest,
    StudentRetentionRequest,
    TransferCertificateCreate,
)
from app.services.student.student_promotion_service import student_promotion_service


@pytest.fixture
def test_data(db_session):
    """
    Setup standard test environment with School, Academic Years, Classes, Sections, Parent, and Student.
    """
    school = School(
        name="Promotion Test Academy",
        code=f"PTA-{uuid4().hex[:6]}",
        address_line1="123 Education Lane",
        city="Testville",
        district="TestDistrict",
        state="TestState",
        postal_code="123456",
        phone="+1234567890",
        email=f"admin-{uuid4().hex[:6]}@pta.com",
    )
    db_session.add(school)
    db_session.commit()

    ay_source = AcademicYear(
        school_id=school.id,
        name="2024-2025",
        start_date=date(2024, 6, 1),
        end_date=date(2025, 4, 30),
        is_current=True,
    )
    ay_target = AcademicYear(
        school_id=school.id,
        name="2025-2026",
        start_date=date(2025, 6, 1),
        end_date=date(2026, 4, 30),
        is_current=False,
    )
    db_session.add_all([ay_source, ay_target])
    db_session.commit()

    class_1 = SchoolClass(
        school_id=school.id,
        name="Class 1",
        display_order=1,
    )
    class_2 = SchoolClass(
        school_id=school.id,
        name="Class 2",
        display_order=2,
    )
    db_session.add_all([class_1, class_2])
    db_session.commit()

    sec_1a = Section(
        school_class_id=class_1.id,
        name="A",
        capacity=30,
    )
    sec_2a = Section(
        school_class_id=class_2.id,
        name="A",
        capacity=30,
    )
    db_session.add_all([sec_1a, sec_2a])
    db_session.commit()

    parent = Parent(
        school_id=school.id,
        father_name="John Doe",
        mother_name="Jane Doe",
        primary_phone="+1987654321",
        email=f"parent-{uuid4().hex[:6]}@gmail.com",
        address_line1="456 Home Street",
        city="Testville",
        district="TestDistrict",
        state="TestState",
        postal_code="123456",
    )
    db_session.add(parent)
    db_session.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=ay_source.id,
        school_class_id=class_1.id,
        section_id=sec_1a.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid4().hex[:6]}",
        roll_number="001",
        first_name="Alice",
        last_name="Smith",
        gender="FEMALE",
        date_of_birth=date(2015, 5, 15),
        admission_date=date(2024, 6, 1),
        address_line1="456 Home Street",
        city="Testville",
        district="TestDistrict",
        state="TestState",
        postal_code="123456",
        status=StudentStatus.ACTIVE,
    )
    db_session.add(student)
    db_session.commit()

    return {
        "school": school,
        "ay_source": ay_source,
        "ay_target": ay_target,
        "class_1": class_1,
        "class_2": class_2,
        "sec_1a": sec_1a,
        "sec_2a": sec_2a,
        "parent": parent,
        "student": student,
    }


def test_promote_student_success(db_session, test_data):
    """
    Test successful promotion of a student from Class 1 to Class 2.
    """
    school = test_data["school"]
    student = test_data["student"]
    ay_target = test_data["ay_target"]
    class_2 = test_data["class_2"]
    sec_2a = test_data["sec_2a"]

    req = StudentPromotionRequest(
        target_academic_year_id=ay_target.id,
        target_class_id=class_2.id,
        target_section_id=sec_2a.id,
        remarks="Promoted with distinction",
    )

    history = student_promotion_service.promote_student(
        db=db_session,
        student_id=student.id,
        data=req,
        current_school_id=school.id,
    )

    assert history is not None
    assert history.student_id == student.id
    assert history.academic_year_id == ay_target.id
    assert history.school_class_id == class_2.id
    assert history.section_id == sec_2a.id
    assert history.enrollment_status == EnrollmentStatus.ENROLLED
    assert history.promotion_decision == PromotionDecision.PENDING

    # Verify student current placement updated
    db_session.refresh(student)
    assert student.academic_year_id == ay_target.id
    assert student.school_class_id == class_2.id
    assert student.section_id == sec_2a.id

    # Verify historical records
    all_history = student_promotion_service.get_student_enrollments(
        db=db_session,
        student_id=student.id,
        current_school_id=school.id,
    )
    assert len(all_history) == 2
    source_hist = next(h for h in all_history if h.academic_year_id == test_data["ay_source"].id)
    assert source_hist.promotion_decision == PromotionDecision.PROMOTED
    assert source_hist.enrollment_status == EnrollmentStatus.PROMOTED


def test_promote_student_duplicate_rejection(db_session, test_data):
    """
    Test that repeating promotion for the same student and target academic year fails.
    """
    school = test_data["school"]
    student = test_data["student"]
    ay_target = test_data["ay_target"]
    class_2 = test_data["class_2"]
    sec_2a = test_data["sec_2a"]

    req = StudentPromotionRequest(
        target_academic_year_id=ay_target.id,
        target_class_id=class_2.id,
        target_section_id=sec_2a.id,
    )

    # First promotion succeeds
    student_promotion_service.promote_student(
        db=db_session,
        student_id=student.id,
        data=req,
        current_school_id=school.id,
    )

    # Second promotion fails
    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.promote_student(
            db=db_session,
            student_id=student.id,
            data=req,
            current_school_id=school.id,
        )
    assert "already enrolled" in str(exc_info.value).lower()


def test_promote_student_cross_school_rejection(db_session, test_data):
    """
    Test tenant boundary enforcement: promoting student using another school's ID fails.
    """
    student = test_data["student"]
    ay_target = test_data["ay_target"]
    class_2 = test_data["class_2"]
    sec_2a = test_data["sec_2a"]
    other_school_id = uuid4()

    req = StudentPromotionRequest(
        target_academic_year_id=ay_target.id,
        target_class_id=class_2.id,
        target_section_id=sec_2a.id,
    )

    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.promote_student(
            db=db_session,
            student_id=student.id,
            data=req,
            current_school_id=other_school_id,
        )
    assert "must belong to the user's school" in str(exc_info.value)


def test_retain_student_success(db_session, test_data):
    """
    Test retaining a student in the same class.
    """
    school = test_data["school"]
    student = test_data["student"]
    ay_target = test_data["ay_target"]

    req = StudentRetentionRequest(
        target_academic_year_id=ay_target.id,
        remarks="Retained due to low attendance",
    )

    history = student_promotion_service.retain_student(
        db=db_session,
        student_id=student.id,
        data=req,
        current_school_id=school.id,
    )

    assert history is not None
    assert history.academic_year_id == ay_target.id
    assert history.school_class_id == test_data["class_1"].id
    assert history.enrollment_status == EnrollmentStatus.RETAINED

    all_history = student_promotion_service.get_student_enrollments(
        db=db_session,
        student_id=student.id,
        current_school_id=school.id,
    )
    source_hist = next(h for h in all_history if h.academic_year_id == test_data["ay_source"].id)
    assert source_hist.promotion_decision == PromotionDecision.RETAINED


def test_issue_transfer_certificate_success(db_session, test_data):
    """
    Test issuing a Transfer Certificate to a student.
    """
    school = test_data["school"]
    student = test_data["student"]
    ay_source = test_data["ay_source"]

    tc_req = TransferCertificateCreate(
        academic_year_id=ay_source.id,
        issue_date=date.today(),
        leaving_date=date.today() - timedelta(days=2),
        reason="Family relocation",
        destination_school="St. Xavier High School",
        remarks="Good conduct",
    )

    tc = student_promotion_service.issue_transfer_certificate(
        db=db_session,
        student_id=student.id,
        data=tc_req,
        current_school_id=school.id,
    )

    assert tc is not None
    assert tc.student_id == student.id
    assert tc.status == TransferCertificateStatus.ISSUED
    assert tc.tc_number.startswith("TC-")

    db_session.refresh(student)
    assert student.status == StudentStatus.TRANSFERRED

    tcs = student_promotion_service.get_student_transfer_certificates(
        db=db_session,
        student_id=student.id,
        current_school_id=school.id,
    )
    assert len(tcs) == 1
    assert tcs[0].id == tc.id


def test_issue_transfer_certificate_duplicate_rejection(db_session, test_data):
    """
    Test that issuing a second active TC for the same student fails.
    """
    school = test_data["school"]
    student = test_data["student"]
    ay_source = test_data["ay_source"]

    tc_req = TransferCertificateCreate(
        academic_year_id=ay_source.id,
        issue_date=date.today(),
        leaving_date=date.today(),
    )

    # First TC
    student_promotion_service.issue_transfer_certificate(
        db=db_session,
        student_id=student.id,
        data=tc_req,
        current_school_id=school.id,
    )

    # Reset student status back to ACTIVE for test case check
    student.status = StudentStatus.ACTIVE
    db_session.commit()

    # Second TC fails
    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.issue_transfer_certificate(
            db=db_session,
            student_id=student.id,
            data=tc_req,
            current_school_id=school.id,
        )
    assert "already has an active transfer certificate" in str(exc_info.value).lower()


def test_transition_academic_year(db_session, test_data):
    """
    Test controlled academic year transition.
    """
    school = test_data["school"]
    ay_source = test_data["ay_source"]
    ay_target = test_data["ay_target"]

    req = AcademicYearTransitionRequest(
        target_academic_year_id=ay_target.id,
        remarks="End of 2024-2025 academic session",
    )

    result = student_promotion_service.transition_academic_year(
        db=db_session,
        source_academic_year_id=ay_source.id,
        data=req,
        current_school_id=school.id,
    )

    assert result.source_academic_year_id == ay_source.id
    assert result.target_academic_year_id == ay_target.id
    assert result.total_students_preserved >= 1

    db_session.refresh(ay_source)
    db_session.refresh(ay_target)

    assert ay_source.is_current is False
    assert ay_target.is_current is True


def test_transition_academic_year_large_student_count(db_session, test_data):
    """
    F01 Regression Test: Verify academic year transition preserves history for >1,000 active students.
    """
    from sqlalchemy.exc import IntegrityError
    school = test_data["school"]
    ay_source = test_data["ay_source"]
    ay_target = test_data["ay_target"]
    class_1 = test_data["class_1"]
    sec_1a = test_data["sec_1a"]
    parent = test_data["parent"]

    # Bulk insert 1005 students
    batch_students = []
    for i in range(2, 1007):
        s = Student(
            school_id=school.id,
            academic_year_id=ay_source.id,
            school_class_id=class_1.id,
            section_id=sec_1a.id,
            parent_id=parent.id,
            admission_number=f"ADM-L-{i}",
            roll_number=f"{i:04d}",
            first_name=f"LargeStudent{i}",
            last_name="Test",
            gender="MALE",
            date_of_birth=date(2015, 1, 1),
            admission_date=date(2024, 6, 1),
            address_line1="123 Street",
            city="TestCity",
            district="Central",
            state="TestState",
            postal_code="110001",
            status=StudentStatus.ACTIVE,
        )
        batch_students.append(s)

    db_session.add_all(batch_students)
    db_session.commit()

    req = AcademicYearTransitionRequest(
        target_academic_year_id=ay_target.id,
        remarks="Transition with large student count",
    )

    result = student_promotion_service.transition_academic_year(
        db=db_session,
        source_academic_year_id=ay_source.id,
        data=req,
        current_school_id=school.id,
    )

    assert result.total_students_preserved == 1006

    # Genuinely verify 1006 enrollment history records exist in database
    from app.models.student.student_enrollment_history import StudentEnrollmentHistory
    histories_count = db_session.query(StudentEnrollmentHistory).filter(
        StudentEnrollmentHistory.school_id == school.id,
        StudentEnrollmentHistory.academic_year_id == ay_source.id,
    ).count()
    assert histories_count == 1006




def test_historical_enrollment_fk_restrict(db_session, test_data):
    """
    F02 Regression Test: Deleting a SchoolClass or Section with historical enrollments is rejected (RESTRICT).
    """
    from sqlalchemy import text
    from sqlalchemy.exc import IntegrityError

    try:
        db_session.execute(text("PRAGMA foreign_keys = ON;"))
    except Exception:
        pass

    school = test_data["school"]
    student = test_data["student"]
    ay_target = test_data["ay_target"]
    class_1 = test_data["class_1"]
    class_2 = test_data["class_2"]
    sec_2a = test_data["sec_2a"]

    req = StudentPromotionRequest(
        target_academic_year_id=ay_target.id,
        target_class_id=class_2.id,
        target_section_id=sec_2a.id,
    )

    # Promote student to create history referencing class_1
    student_promotion_service.promote_student(
        db=db_session,
        student_id=student.id,
        data=req,
        current_school_id=school.id,
    )

    # Attempting DB delete on class_1 must fail due to FK RESTRICT constraint on student_enrollment_histories
    with pytest.raises(IntegrityError):
        db_session.delete(class_1)
        db_session.commit()
    db_session.rollback()


def test_bulk_promotion_partial_success_semantics(db_session, test_data):
    """
    F05 Regression Test: Verify partial success semantics in bulk promotion.
    Valid students are promoted, invalid students are recorded as errors, session remains valid.
    """
    school = test_data["school"]
    student1 = test_data["student"]
    ay_source = test_data["ay_source"]
    ay_target = test_data["ay_target"]
    class_1 = test_data["class_1"]
    class_2 = test_data["class_2"]
    sec_1a = test_data["sec_1a"]
    sec_2a = test_data["sec_2a"]
    parent = test_data["parent"]

    # Create student2
    student2 = Student(
        school_id=school.id,
        academic_year_id=ay_source.id,
        school_class_id=class_1.id,
        section_id=sec_1a.id,
        parent_id=parent.id,
        admission_number=f"ADM-B2-{uuid4().hex[:4]}",
        roll_number="002",
        first_name="Bob",
        last_name="Test",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2024, 6, 1),
        address_line1="123 Street",
        city="TestCity",
        district="Central",
        state="TestState",
        postal_code="110001",
        status=StudentStatus.INACTIVE,  # Inactive status causes ValidationException
    )
    db_session.add(student2)
    db_session.commit()

    bulk_req = BulkStudentPromotionRequest(
        source_academic_year_id=ay_source.id,
        target_academic_year_id=ay_target.id,
        promotions=[
            BulkStudentPromotionItem(
                student_id=student1.id,
                target_class_id=class_2.id,
                target_section_id=sec_2a.id,
            ),
            BulkStudentPromotionItem(
                student_id=student2.id,
                target_class_id=class_2.id,
                target_section_id=sec_2a.id,
            ),
        ],
    )

    result = student_promotion_service.bulk_promote_students(
        db=db_session,
        data=bulk_req,
        current_school_id=school.id,
    )

    assert result.total_processed == 2
    assert result.promoted_count == 1
    assert result.skipped_count == 1
    assert len(result.errors) == 1
    assert result.errors[0]["student_id"] == str(student2.id)

    # Student 1 is promoted
    db_session.refresh(student1)
    assert student1.academic_year_id == ay_target.id


def test_transition_academic_year_multiple_orphan_active_years(db_session, test_data):
    """
    F06 Regression Test: Transitioning academic year deactivates all active current years for the school.
    """
    school = test_data["school"]
    ay_source = test_data["ay_source"]
    ay_target = test_data["ay_target"]

    # Create an orphan academic year also marked is_current=True
    orphan_ay = AcademicYear(
        school_id=school.id,
        name="2023-2024-ORPHAN",
        start_date=date(2023, 6, 1),
        end_date=date(2024, 4, 30),
        is_current=True,
    )
    db_session.add(orphan_ay)
    db_session.commit()

    req = AcademicYearTransitionRequest(
        target_academic_year_id=ay_target.id,
    )

    student_promotion_service.transition_academic_year(
        db=db_session,
        source_academic_year_id=ay_source.id,
        data=req,
        current_school_id=school.id,
    )

    db_session.refresh(ay_source)
    db_session.refresh(ay_target)
    db_session.refresh(orphan_ay)

    assert ay_source.is_current is False
    assert orphan_ay.is_current is False
    assert ay_target.is_current is True


# ===========================================================================
# SEC-02 Tenant Isolation Regression Tests
# ===========================================================================

def test_cross_tenant_class_assignment_rejected(db_session, test_data):
    """
    SEC-02: Promoting student into a class belonging to another school/tenant must be rejected.
    """
    school = test_data["school"]
    student = test_data["student"]
    ay_target = test_data["ay_target"]

    # Create another school and a class under that other school
    other_school = School(
        name="Other School",
        code=f"OTH-{uuid4().hex[:6]}",
        address_line1="456 Other St",
        city="OtherCity",
        district="OtherDistrict",
        state="OtherState",
        postal_code="654321",
        phone="+9876543210",
        email=f"admin-{uuid4().hex[:6]}@other.com",
    )
    db_session.add(other_school)
    db_session.commit()

    other_class = SchoolClass(
        school_id=other_school.id,
        name="Class 3 Other",
        display_order=3,
    )
    db_session.add(other_class)
    db_session.commit()

    other_section = Section(
        school_class_id=other_class.id,
        name="A",
        capacity=30,
    )
    db_session.add(other_section)
    db_session.commit()

    req = StudentPromotionRequest(
        target_academic_year_id=ay_target.id,
        target_class_id=other_class.id,
        target_section_id=other_section.id,
    )

    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.promote_student(
            db=db_session,
            student_id=student.id,
            data=req,
            current_school_id=school.id,
        )
    assert "School class must belong to the user's school." in str(exc_info.value)


def test_cross_tenant_section_assignment_rejected(db_session, test_data):
    """
    SEC-02: Promoting student into a section belonging to a class of another school must be rejected.
    """
    school = test_data["school"]
    student = test_data["student"]
    class_2 = test_data["class_2"]
    ay_target = test_data["ay_target"]

    # Create another school, a class under that school, and a section under that class
    other_school = School(
        name="Other School Sec",
        code=f"OTHSEC-{uuid4().hex[:6]}",
        address_line1="789 Sec St",
        city="SecCity",
        district="SecDistrict",
        state="SecState",
        postal_code="654322",
        phone="+9876543211",
        email=f"admin-{uuid4().hex[:6]}@othersec.com",
    )
    db_session.add(other_school)
    db_session.commit()

    other_class = SchoolClass(
        school_id=other_school.id,
        name="Class Other Sec",
        display_order=5,
    )
    db_session.add(other_class)
    db_session.commit()

    other_section = Section(
        school_class_id=other_class.id,
        name="B",
        capacity=30,
    )
    db_session.add(other_section)
    db_session.commit()

    # Pass class_2 (which belongs to school) but target_section_id=other_section.id (which belongs to other_school's class)
    req = StudentPromotionRequest(
        target_academic_year_id=ay_target.id,
        target_class_id=class_2.id,
        target_section_id=other_section.id,
    )

    with pytest.raises(ValidationException) as exc_info:
        student_promotion_service.promote_student(
            db=db_session,
            student_id=student.id,
            data=req,
            current_school_id=school.id,
        )
    assert "Target section does not belong to target class." in str(exc_info.value)

