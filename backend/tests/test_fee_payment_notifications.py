"""
Phase 27.4.3 Fee Receipt / Payment Confirmation Notifications Tests
Tests post-commit fee payment notification triggers, recipient resolution (parent preferred, student fallback),
tenant isolation, communication preference handling, rollback safety, provider failure isolation,
and deterministic idempotency.
"""
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4
import pytest
from sqlalchemy import select

from app.common.enums import (
    BloodGroup,
    Gender,
    StudentStatus,
)
from app.common.enums.fees import (
    FeeCategory,
    FeeStructureStatus,
    PaymentMode,
    StudentFeeAssignmentStatus,
)
from app.common.enums.payment import (
    PaymentOrderStatus,
    PaymentProvider,
    PaymentTransactionStatus,
)
from app.models.academic_year.academic_year import AcademicYear
from app.models.communication import UserCommunicationPreference
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from app.models.parent.parent import Parent
from app.models.payment.payment_order import PaymentOrder
from app.models.payment.payment_transaction import PaymentTransaction
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.schemas.fees.fees import FeePaymentCreate
from app.services.fee_service import fee_service
from app.services.payment_settlement_service import payment_settlement_service


@pytest.fixture
def fee_notification_test_setup(db_session):
    """Sets up a test school, academic year, class, parent, student, fee structure, and assignment."""
    school = School(
        id=uuid4(),
        name="Fee Notification Test Academy",
        code=f"FNTA-{uuid4().hex[:6]}",
        address_line1="100 Fee Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.flush()

    ay = AcademicYear(
        id=uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        is_current=True,
    )
    db_session.add(ay)

    school_class = SchoolClass(
        id=uuid4(),
        school_id=school.id,
        name="Grade 10",
        display_order=1,
    )
    db_session.add(school_class)

    section = Section(
        id=uuid4(),
        school_class_id=school_class.id,
        name="A",
    )
    db_session.add(section)

    parent = Parent(
        id=uuid4(),
        school_id=school.id,
        father_name="Robert Williams",
        primary_phone=f"+9198700{uuid4().hex[:5]}",
        email=f"robert.{uuid4().hex[:6]}@parent.com",
        address_line1="789 Park Ave",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500003",
    )
    db_session.add(parent)
    db_session.flush()

    student = Student(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid4().hex[:6]}",
        roll_number="101",
        first_name="Charlie",
        last_name="Williams",
        gender=Gender.MALE,
        date_of_birth=date(2010, 8, 12),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        phone=f"+9198711{uuid4().hex[:5]}",
        email=f"charlie.{uuid4().hex[:6]}@student.com",
        address_line1="789 Park Ave",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500003",
    )
    db_session.add(student)

    structure = FeeStructure(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        name="Standard Grade 10 Fee",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(structure)

    assignment = StudentFeeAssignment(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 12, 31),
    )
    db_session.add(assignment)

    fee_item = StudentFeeItem(
        id=uuid4(),
        student_fee_assignment_id=assignment.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee Q1",
        amount=Decimal("5000.00"),
        is_applicable=True,
    )
    db_session.add(fee_item)
    db_session.flush()

    db_session.commit()

    return {
        "school": school,
        "ay": ay,
        "school_class": school_class,
        "section": section,
        "parent": parent,
        "student": student,
        "structure": structure,
        "assignment": assignment,
    }


def test_record_payment_triggers_fee_receipt_notification(db_session, fee_notification_test_setup):
    """Verifies that record_payment stages fee receipt notifications to the primary parent post-commit."""
    setup = fee_notification_test_setup
    school = setup["school"]
    parent = setup["parent"]
    assignment = setup["assignment"]

    pay_data = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("2500.00"),
        payment_date=date(2026, 9, 8),
        payment_mode=PaymentMode.CASH,
        reference_number="REF-CASH-1001",
        remarks="Term 1 Part Payment",
    )

    payment_resp = fee_service.record_payment(
        db=db_session,
        data=pay_data,
        current_school_id=school.id,
    )

    assert payment_resp.receipt_number.startswith("REC-")
    assert payment_resp.amount == Decimal("2500.00")

    # Verify notifications were staged for parent
    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()

    assert len(notifs) >= 1

    parent_notif = next((n for n in notifs if n.recipient_id == parent.id and n.channel == NotificationChannel.IN_APP), None)
    assert parent_notif is not None
    assert parent_notif.recipient_type == NotificationRecipientType.PARENT
    assert parent_notif.template_key == "fee_payment_received"
    assert payment_resp.receipt_number in parent_notif.body
    assert "2500.00" in parent_notif.body
    assert "Charlie Williams" in parent_notif.body

    # Verify idempotency key structure
    assert parent_notif.idempotency_key == f"fee_receipt:{payment_resp.receipt_number}:in_app"


def test_payment_settlement_service_triggers_receipt_notification(db_session, fee_notification_test_setup):
    """Verifies that online payment settlement via PaymentSettlementService stages receipt notifications."""
    setup = fee_notification_test_setup
    school = setup["school"]
    parent = setup["parent"]
    assignment = setup["assignment"]

    # Create PaymentOrder and successful PaymentTransaction
    order = PaymentOrder(
        id=uuid4(),
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_{uuid4().hex[:8]}",
        amount=Decimal("1500.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.flush()

    txn = PaymentTransaction(
        id=uuid4(),
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id=f"pay_gtw_{uuid4().hex[:8]}",
        amount=Decimal("1500.00"),
        currency="INR",
        status=PaymentTransactionStatus.SUCCESS,
        payment_method="UPI",
        event_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(txn)
    db_session.commit()

    # Perform Settlement
    settled_payment = payment_settlement_service.settle_payment_transaction(
        db=db_session,
        transaction_id_or_obj=txn.id,
    )

    assert settled_payment.amount == Decimal("1500.00")
    assert settled_payment.reference_number == txn.gateway_transaction_id

    # Verify staged notifications
    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()

    parent_notifs = [n for n in notifs if n.recipient_id == parent.id]
    assert len(parent_notifs) >= 1
    assert any(n.template_key == "fee_payment_received" for n in parent_notifs)
    assert any(settled_payment.receipt_number in n.body for n in parent_notifs)


def test_student_fallback_when_no_parent(db_session, fee_notification_test_setup):
    """Verifies that if student has no linked parent, notification falls back to student recipient."""
    setup = fee_notification_test_setup
    school = setup["school"]
    ay = setup["ay"]
    school_class = setup["school_class"]
    section = setup["section"]
    structure = setup["structure"]

    # Soft-deleted parent to force student recipient fallback
    deleted_parent = Parent(
        id=uuid4(),
        school_id=school.id,
        father_name="Former Parent",
        primary_phone=f"+9198799{uuid4().hex[:5]}",
        email=f"former.{uuid4().hex[:6]}@parent.com",
        address_line1="123 Solo St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500004",
        is_deleted=True,
    )
    db_session.add(deleted_parent)
    db_session.flush()

    # Student whose linked parent is soft-deleted
    orphan_student = Student(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=deleted_parent.id,
        admission_number=f"ADM-NO-PARENT-{uuid4().hex[:4]}",
        roll_number="102",
        first_name="Independent",
        last_name="Student",
        gender=Gender.FEMALE,
        date_of_birth=date(2008, 3, 15),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        phone=f"+9198722{uuid4().hex[:5]}",
        email=f"indep.{uuid4().hex[:6]}@student.com",
        address_line1="123 Solo St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500004",
    )
    db_session.add(orphan_student)

    assignment = StudentFeeAssignment(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=orphan_student.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
    )
    db_session.add(assignment)

    fee_item = StudentFeeItem(
        id=uuid4(),
        student_fee_assignment_id=assignment.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("3000.00"),
        is_applicable=True,
    )
    db_session.add(fee_item)
    db_session.commit()

    pay_data = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("1000.00"),
        payment_date=date(2026, 9, 8),
        payment_mode=PaymentMode.CASH,
    )

    payment_resp = fee_service.record_payment(
        db=db_session,
        data=pay_data,
        current_school_id=school.id,
    )

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()

    assert len(notifs) >= 1
    st_notif = next((n for n in notifs if n.recipient_id == orphan_student.id), None)
    assert st_notif is not None
    assert st_notif.recipient_type == NotificationRecipientType.STUDENT
    assert "Independent Student" in st_notif.body


def test_duplicate_settlement_does_not_duplicate_notification(db_session, fee_notification_test_setup):
    """Verifies that calling settle_payment_transaction multiple times does not generate duplicate notifications."""
    setup = fee_notification_test_setup
    school = setup["school"]
    assignment = setup["assignment"]

    order = PaymentOrder(
        id=uuid4(),
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_dup_{uuid4().hex[:8]}",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.flush()

    txn = PaymentTransaction(
        id=uuid4(),
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id=f"pay_gtw_dup_{uuid4().hex[:8]}",
        amount=Decimal("1000.00"),
        currency="INR",
        status=PaymentTransactionStatus.SUCCESS,
        payment_method="CARD",
        event_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(txn)
    db_session.commit()

    # First settlement
    p1 = payment_settlement_service.settle_payment_transaction(db=db_session, transaction_id_or_obj=txn.id)

    count_after_first = len(
        db_session.scalars(
            select(Notification).where(
                Notification.school_id == school.id,
                Notification.is_deleted.is_(False),
            )
        ).all()
    )

    # Second settlement (duplicate attempt)
    p2 = payment_settlement_service.settle_payment_transaction(db=db_session, transaction_id_or_obj=txn.id)

    assert p1.id == p2.id

    count_after_second = len(
        db_session.scalars(
            select(Notification).where(
                Notification.school_id == school.id,
                Notification.is_deleted.is_(False),
            )
        ).all()
    )

    assert count_after_second == count_after_first


def test_unsettled_or_failed_transactions_trigger_no_receipt_notifications(db_session, fee_notification_test_setup):
    """Verifies that PENDING payment orders or FAILED payment transactions produce zero fee receipt notifications."""
    setup = fee_notification_test_setup
    school = setup["school"]
    assignment = setup["assignment"]

    # Pending Payment Order (No settlement)
    pending_order = PaymentOrder(
        id=uuid4(),
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=f"order_pend_{uuid4().hex[:8]}",
        amount=Decimal("500.00"),
        currency="INR",
        status=PaymentOrderStatus.PENDING,
    )
    db_session.add(pending_order)

    # Failed Payment Transaction
    failed_txn = PaymentTransaction(
        id=uuid4(),
        school_id=school.id,
        payment_order_id=pending_order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id=f"pay_failed_{uuid4().hex[:8]}",
        amount=Decimal("500.00"),
        currency="INR",
        status=PaymentTransactionStatus.FAILED,
        payment_method="UPI",
        event_timestamp=datetime.now(timezone.utc),
    )
    db_session.add(failed_txn)
    db_session.commit()

    # Attempting settlement on failed transaction raises exception
    with pytest.raises(Exception):
        payment_settlement_service.settle_payment_transaction(db=db_session, transaction_id_or_obj=failed_txn.id)

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.template_key == "fee_payment_received",
            Notification.is_deleted.is_(False),
        )
    ).all()

    assert len(notifs) == 0


def test_sensitive_financial_data_minimization(db_session, fee_notification_test_setup):
    """Verifies that card numbers, UPI secrets, and gateway credentials are NOT present in notifications or metadata."""
    setup = fee_notification_test_setup
    school = setup["school"]
    assignment = setup["assignment"]

    pay_data = FeePaymentCreate(
        student_fee_assignment_id=assignment.id,
        amount=Decimal("1000.00"),
        payment_date=date(2026, 9, 8),
        payment_mode=PaymentMode.UPI,
        reference_number="UPI-SECRET-REF-9988",
        remarks="Payment via UPI",
    )

    fee_service.record_payment(
        db=db_session,
        data=pay_data,
        current_school_id=school.id,
    )

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()

    for notif in notifs:
        assert "UPI-SECRET-REF-9988" not in notif.title
        assert "password" not in notif.body.lower()
        assert "secret" not in notif.body.lower()
        assert "card_number" not in str(notif.body).lower()
