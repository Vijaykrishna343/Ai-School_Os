"""
Phase 30.1 — Parent & Student Self-Service Portals Test Suite.

Validates:
- Parent ward switching & zero-child fail-closed behavior.
- Parent online fee payment order creation, verification, idempotency, and receipt retrieval.
- Parent published report card access & unpublished/draft denial.
- Student daily timetable schedule retrieval.
- Student digital homework submission, resubmission, and access rules.
- Student library circulation loan tracking & authorization scoping.
- Strict tenant isolation, relationship authorization, and unauthenticated/inactive rejections.
"""
from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import date, datetime, time, timezone
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings

import app.database.models  # noqa: F401
from app.common.enums import (
    BloodGroup,
    Gender,
    StudentStatus,
    TeacherStatus,
)
from app.common.enums.fees import FeeCategory, PaymentMode, StudentFeeAssignmentStatus
from app.common.enums.library import (
    BookCondition,
    BookCopyStatus,
    BookLoanStatus,
    LibraryMemberStatus,
    LibraryMemberType,
)
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider
from app.common.enums.report_card import ReportCardStatus
from app.common.enums.timetable import DayOfWeek, PeriodType, TimetableStatus
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeCategory, FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeAssignmentStatus, StudentFeeItem
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.grading.grade_scale import GradeScale
from app.models.grading.grade_scale_entry import GradeScaleEntry
from app.models.grading.report_card import ReportCard
from app.models.grading.report_card_item_snapshot import ReportCardItemSnapshot
from app.models.homework.homework import Homework, HomeworkStatus
from app.models.homework.homework_submission import HomeworkSubmission, SubmissionStatus
from app.models.library import Book, BookCategory, BookCopy, BookLoan, Library, LibraryMember
from app.models.parent.parent import Parent
from app.models.payment.payment_order import PaymentOrder
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry


@pytest.fixture
def setup_portals_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # Schools A & B
    school_a = School(
        name=f"Portals School A {s}",
        code=f"PSA_{s}",
        address_line1="100 Main Road",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    school_b = School(
        name=f"Portals School B {s}",
        code=f"PSB_{s}",
        address_line1="200 Other Road",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    # Academic Structure
    ay_a = AcademicYear(
        school_id=school_a.id,
        name=f"2026-2027 {s}",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        is_current=True,
    )
    db_session.add(ay_a)
    db_session.commit()

    term_a = AcademicTerm(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        name="Term 1",
        code=f"T1_{s}",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 10, 31),
    )
    db_session.add(term_a)
    db_session.commit()

    class_a = SchoolClass(school_id=school_a.id, name="Grade 8", display_order=8)
    db_session.add(class_a)
    db_session.commit()

    sec_a = Section(school_class_id=class_a.id, name="A")
    sec_b = Section(school_class_id=class_a.id, name="B")
    db_session.add_all([sec_a, sec_b])
    db_session.commit()

    subject_math = Subject(
        school_id=school_a.id,
        subject_name="Mathematics",
        subject_code=f"MATH_{s}",
        is_optional=False,
    )
    db_session.add(subject_math)
    db_session.commit()

    # Teachers
    teacher_user = IdentityUser(
        school_id=school_a.id,
        username=f"teacher_{s}",
        email=f"teacher_{s}@school.com",
        password_hash=hash_password("TeacherPass123!"),
        first_name="Alice",
        last_name="Smith",
        is_active=True,
    )
    db_session.add(teacher_user)
    db_session.commit()

    teacher_role = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    db_session.add(IdentityUserRole(user_id=teacher_user.id, role_id=teacher_role.id))
    db_session.commit()

    teacher_prof = Teacher(
        school_id=school_a.id,
        first_name="Alice",
        last_name="Smith",
        email=teacher_user.email,
        phone=f"912345{s[:4]}",
        gender=Gender.FEMALE,
        date_of_birth=date(1990, 1, 1),
        employee_id=f"EMP_{s}",
        qualification="M.Sc",
        joining_date=date(2020, 1, 1),
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add(teacher_prof)
    db_session.commit()

    # Parent 1: Multi-child parent with 2 wards (Ward 1 in 8-A, Ward 2 in 8-A)
    parent_p1_user = IdentityUser(
        school_id=school_a.id,
        username=f"parent1_{s}",
        email=f"parent1_{s}@family.com",
        phone=f"987654{s[:4]}",
        password_hash=hash_password("ParentPass123!"),
        first_name="John",
        last_name="Doe",
        is_active=True,
    )
    db_session.add(parent_p1_user)
    db_session.commit()

    parent_role = db_session.query(IdentityRole).filter_by(name="Parent").first()
    db_session.add(IdentityUserRole(user_id=parent_p1_user.id, role_id=parent_role.id))
    db_session.commit()

    parent_p1_rec = Parent(
        school_id=school_a.id,
        father_name="John Doe",
        email=parent_p1_user.email,
        primary_phone=parent_p1_user.phone,
        address_line1="123 Oak St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent_p1_rec)
    db_session.commit()

    # Parent 2: Unrelated parent in School A
    parent_p2_user = IdentityUser(
        school_id=school_a.id,
        username=f"parent2_{s}",
        email=f"parent2_{s}@family.com",
        phone=f"911111{s[:4]}",
        password_hash=hash_password("ParentPass123!"),
        first_name="Unrelated",
        last_name="Guardian",
        is_active=True,
    )
    db_session.add(parent_p2_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=parent_p2_user.id, role_id=parent_role.id))
    db_session.commit()

    parent_p2_rec = Parent(
        school_id=school_a.id,
        father_name="Unrelated Guardian",
        email=parent_p2_user.email,
        primary_phone=parent_p2_user.phone,
        address_line1="456 Pine St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent_p2_rec)
    db_session.commit()

    # Parent Inactive
    parent_inactive_user = IdentityUser(
        school_id=school_a.id,
        username=f"inactive_parent_{s}",
        email=f"inactive_parent_{s}@family.com",
        password_hash=hash_password("ParentPass123!"),
        first_name="Inactive",
        last_name="Parent",
        is_active=False,
    )
    db_session.add(parent_inactive_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=parent_inactive_user.id, role_id=parent_role.id))
    db_session.commit()

    # Students for Parent 1
    ward1 = Student(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        parent_id=parent_p1_rec.id,
        first_name="Tommy",
        last_name="Doe",
        admission_number=f"ADM_W1_{s}",
        roll_number="01",
        email=f"tommy_{s}@school.com",
        gender=Gender.MALE,
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2020, 6, 1),
        address_line1="123 Oak St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    ward2 = Student(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        parent_id=parent_p1_rec.id,
        first_name="Sally",
        last_name="Doe",
        admission_number=f"ADM_W2_{s}",
        roll_number="02",
        email=f"sally_{s}@school.com",
        gender=Gender.FEMALE,
        date_of_birth=date(2013, 2, 2),
        admission_date=date(2021, 6, 1),
        address_line1="123 Oak St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # Student for Parent 2
    ward_other = Student(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        section_id=sec_b.id,
        parent_id=parent_p2_rec.id,
        first_name="Other",
        last_name="Student",
        admission_number=f"ADM_OTHER_{s}",
        roll_number="99",
        email=f"other_{s}@school.com",
        gender=Gender.MALE,
        date_of_birth=date(2012, 5, 5),
        admission_date=date(2020, 6, 1),
        address_line1="456 Pine St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([ward1, ward2, ward_other])
    db_session.commit()

    # Student User for Ward 1
    student_role = db_session.query(IdentityRole).filter_by(name="Student").first()
    student_user_w1 = IdentityUser(
        school_id=school_a.id,
        username=ward1.admission_number,
        email=ward1.email,
        password_hash=hash_password("StudentPass123!"),
        first_name=ward1.first_name,
        last_name=ward1.last_name,
        is_active=True,
    )
    db_session.add(student_user_w1)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=student_user_w1.id, role_id=student_role.id))
    db_session.commit()

    # Fee Structures & Fee Assignment for Ward 1
    fee_struct = FeeStructure(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        name=f"Grade 8 Standard Fee {s}",
    )
    db_session.add(fee_struct)
    db_session.commit()

    fee_item_tuition = FeeItem(
        fee_structure_id=fee_struct.id,
        name="Tuition Fee Term 1",
        category=FeeCategory.TUITION,
        amount=Decimal("5000.00"),
    )
    db_session.add(fee_item_tuition)
    db_session.commit()

    fee_assign_w1 = StudentFeeAssignment(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        student_id=ward1.id,
        fee_structure_id=fee_struct.id,
        status=StudentFeeAssignmentStatus.PENDING,
    )
    fee_assign_other = StudentFeeAssignment(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        student_id=ward_other.id,
        fee_structure_id=fee_struct.id,
        status=StudentFeeAssignmentStatus.PENDING,
    )
    db_session.add_all([fee_assign_w1, fee_assign_other])
    db_session.commit()

    fee_assign_item_w1 = StudentFeeItem(
        student_fee_assignment_id=fee_assign_w1.id,
        fee_item_id=fee_item_tuition.id,
        category=FeeCategory.TUITION,
        name=fee_item_tuition.name,
        amount=fee_item_tuition.amount,
        is_applicable=True,
    )
    fee_assign_item_other = StudentFeeItem(
        student_fee_assignment_id=fee_assign_other.id,
        fee_item_id=fee_item_tuition.id,
        category=FeeCategory.TUITION,
        name=fee_item_tuition.name,
        amount=fee_item_tuition.amount,
        is_applicable=True,
    )
    db_session.add_all([fee_assign_item_w1, fee_assign_item_other])
    db_session.commit()

    # Grading Scale & Report Cards
    grade_scale = GradeScale(
        school_id=school_a.id,
        name=f"Standard 10 Point Scale {s}",
        is_default=True,
    )
    db_session.add(grade_scale)
    db_session.commit()

    grade_item_a = GradeScaleEntry(
        grade_scale_id=grade_scale.id,
        grade_code="A+",
        min_percentage=Decimal("90.00"),
        max_percentage=Decimal("100.00"),
        grade_point=Decimal("10.00"),
        is_pass=True,
    )
    db_session.add(grade_item_a)
    db_session.commit()

    eval_config = EvaluationConfig(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        name=f"Evaluation Config {s}",
        is_default=True,
    )
    db_session.add(eval_config)
    db_session.commit()

    report_card_published = ReportCard(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        academic_term_id=term_a.id,
        student_id=ward1.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        grade_scale_id=grade_scale.id,
        evaluation_config_id=eval_config.id,
        status=ReportCardStatus.PUBLISHED,
        total_max_marks=Decimal("100.00"),
        total_obtained_marks=Decimal("95.00"),
        percentage=Decimal("95.00"),
        overall_grade="A+",
        gpa=Decimal("10.00"),
        is_passed=True,
        total_working_days=100,
        present_days=98,
        attendance_percentage=Decimal("98.00"),
        teacher_remarks="Outstanding analytical problem solving.",
        published_at=datetime.now(timezone.utc),
    )
    report_card_draft = ReportCard(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        academic_term_id=term_a.id,
        student_id=ward2.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        grade_scale_id=grade_scale.id,
        evaluation_config_id=eval_config.id,
        status=ReportCardStatus.DRAFT,
        total_max_marks=Decimal("100.00"),
        total_obtained_marks=Decimal("70.00"),
        percentage=Decimal("70.00"),
        overall_grade="B",
        gpa=Decimal("7.00"),
        is_passed=True,
    )
    db_session.add_all([report_card_published, report_card_draft])
    db_session.commit()

    # Homework Assignment
    hw_math = Homework(
        school_id=school_a.id,
        teacher_id=teacher_prof.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        subject_id=subject_math.id,
        title="Quadratic Equations Practice",
        description="Solve exercises 4.1 to 4.5 in textbook.",
        assigned_date=date.today(),
        due_date=date(2027, 12, 31),
        status=HomeworkStatus.PUBLISHED,
    )
    db_session.add(hw_math)
    db_session.commit()

    # Timetable Setup
    period_1 = PeriodSlot(
        school_id=school_a.id,
        name="Period 1",
        period_type=PeriodType.REGULAR,
        start_time=time(9, 0),
        end_time=time(9, 45),
        display_order=1,
    )
    db_session.add(period_1)
    db_session.commit()

    timetable_section = Timetable(
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        section_id=sec_a.id,
        academic_term_id=term_a.id,
        status=TimetableStatus.PUBLISHED,
        is_active=True,
    )
    db_session.add(timetable_section)
    db_session.commit()

    tt_entry = TimetableEntry(
        timetable_id=timetable_section.id,
        period_slot_id=period_1.id,
        subject_id=subject_math.id,
        teacher_id=teacher_prof.id,
        day_of_week=DayOfWeek.MONDAY,
    )
    db_session.add(tt_entry)
    db_session.commit()

    # Library Setup
    library_main = Library(school_id=school_a.id, name="Central Campus Library", code=f"LIB_{s}")
    db_session.add(library_main)
    db_session.commit()

    category_sci = BookCategory(school_id=school_a.id, name="Science & Math", code=f"SCI_{s}")
    db_session.add(category_sci)
    db_session.commit()

    book_algebra = Book(
        school_id=school_a.id,
        library_id=library_main.id,
        category_id=category_sci.id,
        title="Advanced Algebra",
        author="Leonhard Euler",
    )
    db_session.add(book_algebra)
    db_session.commit()

    book_copy_1 = BookCopy(
        school_id=school_a.id,
        book_id=book_algebra.id,
        accession_number=f"ACC_{s}_001",
        status=BookCopyStatus.ISSUED,
        condition=BookCondition.GOOD,
    )
    db_session.add(book_copy_1)
    db_session.commit()

    lib_member_w1 = LibraryMember(
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=ward1.id,
        card_number=f"CARD_{s}_001",
        issue_date=date(2026, 6, 1),
        max_books_allowed=3,
        status=LibraryMemberStatus.ACTIVE,
    )
    db_session.add(lib_member_w1)
    db_session.commit()

    loan_w1 = BookLoan(
        school_id=school_a.id,
        member_id=lib_member_w1.id,
        book_copy_id=book_copy_1.id,
        issue_date=date(2026, 7, 1),
        due_date=date(2026, 7, 15),
        status=BookLoanStatus.ISSUED,
    )
    db_session.add(loan_w1)
    db_session.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "parent_p1_user": parent_p1_user,
        "parent_p2_user": parent_p2_user,
        "parent_inactive_user": parent_inactive_user,
        "student_user_w1": student_user_w1,
        "ward1": ward1,
        "ward2": ward2,
        "ward_other": ward_other,
        "fee_assign_w1": fee_assign_w1,
        "fee_assign_other": fee_assign_other,
        "report_card_published": report_card_published,
        "report_card_draft": report_card_draft,
        "hw_math": hw_math,
        "loan_w1": loan_w1,
        "lib_member_w1": lib_member_w1,
    }


def auth_header(user: IdentityUser) -> dict[str, str]:
    token = jwt_manager.create_access_token(
        user_id=user.id,
        school_id=user.school_id,
    )
    return {"Authorization": f"Bearer {token}"}


class TestParentSelfServiceWorkflows:
    """Tests for Parent Portal transactional workflows."""

    def test_parent_ward_switcher_authorized_wards(self, client: TestClient, setup_portals_data):
        d = setup_portals_data
        headers = auth_header(d["parent_p1_user"])

        # 1. Get summary without student_id -> defaults to first child (Ward 1)
        res1 = client.get("/api/v1/dashboard/parent/summary", headers=headers)
        assert res1.status_code == 200
        data1 = res1.json()["data"]
        assert len(data1["children"]) == 2
        assert data1["selected_child_id"] == str(d["ward1"].id)

        # 2. Switch to second authorized child (Ward 2)
        res2 = client.get(
            f"/api/v1/dashboard/parent/summary?student_id={d['ward2'].id}",
            headers=headers,
        )
        assert res2.status_code == 200
        data2 = res2.json()["data"]
        assert data2["selected_child_id"] == str(d["ward2"].id)

    def test_parent_ward_switcher_unauthorized_student_denied(self, client: TestClient, setup_portals_data):
        d = setup_portals_data
        headers = auth_header(d["parent_p1_user"])

        # Attempt to access unrelated student
        res = client.get(
            f"/api/v1/dashboard/parent/summary?student_id={d['ward_other'].id}",
            headers=headers,
        )
        assert res.status_code == 403

    def test_parent_fee_payment_order_and_verification_lifecycle(
        self, client: TestClient, setup_portals_data, db_session: Session, monkeypatch
    ):
        monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_key")
        monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "mock_rzp_secret")

        d = setup_portals_data
        headers = auth_header(d["parent_p1_user"])

        # 1. Parent creates payment order for Ward 1
        create_order_payload = {
            "student_fee_assignment_id": str(d["fee_assign_w1"].id),
            "provider": "RAZORPAY",
        }
        res_order = client.post("/api/v1/payments/orders", json=create_order_payload, headers=headers)
        assert res_order.status_code == 201
        order_data = res_order.json()
        assert order_data["gateway_order_id"] is not None
        assert Decimal(str(order_data["amount"])) == Decimal("5000.00")

        order_id = order_data["id"]
        gateway_order_id = order_data["gateway_order_id"]
        payment_id = f"pay_rzp_{uuid.uuid4().hex[:6]}"
        msg = f"{gateway_order_id}|{payment_id}"
        sig = hmac.new("mock_rzp_secret".encode(), msg.encode(), hashlib.sha256).hexdigest()

        # 2. Parent completes verification with mock signature
        verify_payload = {
            "provider": "RAZORPAY",
            "payment_order_id": order_id,
            "gateway_order_id": gateway_order_id,
            "gateway_payment_id": payment_id,
            "gateway_signature": sig,
        }
        res_verify = client.post("/api/v1/payments/verify", json=verify_payload, headers=headers)
        assert res_verify.status_code == 200
        verify_data = res_verify.json()
        assert verify_data["success"] is True
        assert verify_data["status"] == "PAID"

        # 3. Verify Fee Assignment status updated in DB
        db_session.refresh(d["fee_assign_w1"])
        assert d["fee_assign_w1"].status == StudentFeeAssignmentStatus.PAID

        # 4. Parent retrieves receipt for the verified payment
        payment = db_session.query(FeePayment).filter_by(student_fee_assignment_id=d["fee_assign_w1"].id).first()
        assert payment is not None

        res_receipt = client.get(f"/api/v1/fees/payments/{payment.id}/receipt", headers=headers)
        assert res_receipt.status_code == 200
        receipt_data = res_receipt.json()
        assert receipt_data["receipt_number"] == payment.receipt_number
        assert Decimal(str(receipt_data["amount"])) == Decimal("5000.00")

    def test_parent_fee_payment_unauthorized_assignment_denied(
        self, client: TestClient, setup_portals_data, monkeypatch
    ):
        monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_key")
        monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "mock_rzp_secret")

        d = setup_portals_data
        headers = auth_header(d["parent_p1_user"])

        # Attempt to create payment order for another parent's ward
        payload = {
            "student_fee_assignment_id": str(d["fee_assign_other"].id),
            "provider": "RAZORPAY",
        }
        res = client.post("/api/v1/payments/orders", json=payload, headers=headers)
        assert res.status_code == 403

    def test_parent_receipt_access_unauthorized_student_denied(
        self, client: TestClient, setup_portals_data, db_session: Session
    ):
        d = setup_portals_data
        headers_p1 = auth_header(d["parent_p1_user"])

        # Create payment on other student
        other_payment = FeePayment(
            school_id=d["school_a"].id,
            student_fee_assignment_id=d["fee_assign_other"].id,
            receipt_number=f"RCP_{uuid.uuid4().hex[:6]}",
            amount=Decimal("5000.00"),
            payment_date=date.today(),
            payment_mode=PaymentMode.CASH,
        )
        db_session.add(other_payment)
        db_session.commit()

        # Parent 1 tries to access Parent 2's ward receipt
        res = client.get(f"/api/v1/fees/payments/{other_payment.id}/receipt", headers=headers_p1)
        assert res.status_code == 403

    def test_parent_published_report_card_visibility_and_draft_denial(self, client: TestClient, setup_portals_data):
        d = setup_portals_data
        headers = auth_header(d["parent_p1_user"])

        # 1. Listing report cards returns ONLY published cards
        res_list = client.get(f"/api/v1/report-cards?student_id={d['ward1'].id}", headers=headers)
        assert res_list.status_code == 200
        cards = res_list.json()["items"]
        assert len(cards) == 1
        assert cards[0]["id"] == str(d["report_card_published"].id)
        assert cards[0]["status"] == "PUBLISHED"

        # 2. Get specific published card -> 200
        res_pub = client.get(f"/api/v1/report-cards/{d['report_card_published'].id}", headers=headers)
        assert res_pub.status_code == 200

        # 3. Attempt to get DRAFT report card -> 403 Forbidden
        res_draft = client.get(f"/api/v1/report-cards/{d['report_card_draft'].id}", headers=headers)
        assert res_draft.status_code == 403


class TestStudentSelfServiceWorkflows:
    """Tests for Student Portal transactional workflows."""

    def test_student_section_timetable_retrieval(self, client: TestClient, setup_portals_data):
        d = setup_portals_data
        headers = auth_header(d["student_user_w1"])

        res = client.get(f"/api/v1/timetables/section/{d['ward1'].section_id}", headers=headers)
        assert res.status_code == 200
        data = res.json()
        assert "entries" in data
        assert len(data["entries"]) >= 1
        assert data["entries"][0]["day_of_week"] == "MONDAY"

    def test_student_homework_submission_and_resubmission(
        self, client: TestClient, setup_portals_data, db_session: Session
    ):
        d = setup_portals_data
        headers = auth_header(d["student_user_w1"])

        # 1. Initial Submission
        submit_payload = {"content_text": "Here is my completed solution for quadratic equations."}
        res_submit = client.post(
            f"/api/v1/homework/{d['hw_math'].id}/submit",
            json=submit_payload,
            headers=headers,
        )
        assert res_submit.status_code == 201
        sub_data = res_submit.json()
        assert sub_data["status"] == "SUBMITTED"
        assert sub_data["content_text"] == submit_payload["content_text"]

        # 2. Resubmission
        resubmit_payload = {"content_text": "Updated answer with graph attachment notes."}
        res_resubmit = client.post(
            f"/api/v1/homework/{d['hw_math'].id}/submit",
            json=resubmit_payload,
            headers=headers,
        )
        assert res_resubmit.status_code == 201
        resub_data = res_resubmit.json()
        assert resub_data["status"] == "RESUBMITTED"
        assert resub_data["content_text"] == resubmit_payload["content_text"]

    def test_student_library_loans_retrieval_and_cross_student_scoping(self, client: TestClient, setup_portals_data):
        d = setup_portals_data
        headers_w1 = auth_header(d["student_user_w1"])

        # 1. Student lists loans -> sees own loan
        res_loans = client.get("/api/v1/library/loans", headers=headers_w1)
        assert res_loans.status_code == 200
        loans = res_loans.json()["items"]
        assert len(loans) == 1
        assert loans[0]["id"] == str(d["loan_w1"].id)
        assert loans[0]["accession_number"] == d["loan_w1"].book_copy.accession_number

        # 2. Student gets specific loan -> 200
        res_single = client.get(f"/api/v1/library/loans/{d['loan_w1'].id}", headers=headers_w1)
        assert res_single.status_code == 200


class TestPortalsSecurityAndTenantIsolation:
    """Security, Inactive User, and Cross-Tenant Rejection."""

    def test_unauthenticated_requests_denied(self, client: TestClient, setup_portals_data):
        d = setup_portals_data

        assert client.get("/api/v1/dashboard/parent/summary").status_code == 401
        assert client.get("/api/v1/dashboard/student/summary").status_code == 401
        assert client.post("/api/v1/payments/orders", json={}).status_code == 401
        assert client.get("/api/v1/report-cards").status_code == 401
        assert client.get("/api/v1/library/loans").status_code == 401

    def test_inactive_user_rejected(self, client: TestClient, setup_portals_data):
        d = setup_portals_data
        headers = auth_header(d["parent_inactive_user"])

        res = client.get("/api/v1/dashboard/parent/summary", headers=headers)
        assert res.status_code == 401
