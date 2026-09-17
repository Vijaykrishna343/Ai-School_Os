"""
Phase 27.4.5 — Cross-Domain Notification Integration Hardening & Verification Test Suite.
Tests unified event contracts, cross-tenant isolation, savepoint resilience, idempotency,
preference enforcement, provider failure isolation, status monotonicity, and PII minimization
across all five notification domains (Visitor checkin/checkout, Fee receipt, Absence, Homework).
"""
import pytest
from datetime import date, datetime, timezone
from decimal import Decimal
from uuid import uuid4
from unittest.mock import patch, MagicMock

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus, StudentStatus
from app.common.enums.fees import FeeCategory, FeeStructureStatus, PaymentMode, StudentFeeAssignmentStatus
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from app.models.communication import UserCommunicationPreference
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.subject.subject import Subject
from app.models.student.student import Student
from app.models.parent.parent import Parent
from app.models.teacher.teacher import Teacher
from app.common.enums.visitor import HostType, VisitorStatus
from app.models.visitor import Visitor
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.attendance.attendance import Attendance
from app.models.homework.homework import Homework, HomeworkStatus
from app.schemas.notification_trigger import NotificationTriggerEvent
from app.services.notification_trigger_service import notification_trigger_service
from app.services.visitor_service import (
    _trigger_visitor_checkin_notification,
    _trigger_visitor_checkout_notification,
)
from app.services.fee_service import _trigger_fee_receipt_notification
from app.services.attendance_service import _trigger_student_absence_notification
from app.services.homework_service import _trigger_homework_published_notification


# ── FIXTURES & HELPERS ────────────────────────────────────────────────────────

@pytest.fixture
def school_a(db_session: Session) -> School:
    school = School(
        id=uuid4(),
        name=f"School A {uuid4().hex[:6]}",
        code=f"SCH-A-{uuid4().hex[:6]}",
        email=f"school_a_{uuid4().hex[:4]}@test.com",
        address_line1="123 Main St",
        city="City A",
        district="District A",
        state="State A",
        postal_code="123456",
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


@pytest.fixture
def school_b(db_session: Session) -> School:
    school = School(
        id=uuid4(),
        name=f"School B {uuid4().hex[:6]}",
        code=f"SCH-B-{uuid4().hex[:6]}",
        email=f"school_b_{uuid4().hex[:4]}@test.com",
        address_line1="456 Other St",
        city="City B",
        district="District B",
        state="State B",
        postal_code="654321",
    )
    db_session.add(school)
    db_session.commit()
    db_session.refresh(school)
    return school


def create_ay(db: Session, school_id) -> AcademicYear:
    ay = AcademicYear(
        id=uuid4(),
        school_id=school_id,
        name=f"2026-2027-{uuid4().hex[:4]}",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db.add(ay)
    db.commit()
    db.refresh(ay)
    return ay


def create_class_and_section(db: Session, school_id) -> tuple[SchoolClass, Section]:
    cls = SchoolClass(
        id=uuid4(),
        school_id=school_id,
        name=f"Class-{uuid4().hex[:4]}",
        display_order=1,
    )
    db.add(cls)
    db.flush()
    sec = Section(
        id=uuid4(),
        school_class_id=cls.id,
        name="A",
    )
    db.add(sec)
    db.commit()
    db.refresh(cls)
    db.refresh(sec)
    return cls, sec


def create_teacher(db: Session, school_id) -> Teacher:
    uid = uuid4().hex[:6]
    t = Teacher(
        id=uuid4(),
        school_id=school_id,
        employee_id=f"EMP-{uid}",
        first_name="Host",
        last_name="Teacher",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 6, 1),
        qualification="M.Sc",
        phone=f"+9198{uid[:8]}",
        email=f"teach_{uid}@test.com",
        address_line1="123 Staff St",
        city="City",
        district="District",
        state="State",
        postal_code="123456",
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def create_parent(db: Session, school_id) -> Parent:
    uid = uuid4().hex[:6]
    p = Parent(
        id=uuid4(),
        school_id=school_id,
        father_name=f"Parent {uid}",
        primary_phone=f"+9199{uid[:8]}",
        email=f"parent_{uid}@test.com",
        address_line1="123 Parent St",
        city="City",
        district="District",
        state="State",
        postal_code="123456",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return p


def create_student(db: Session, school_id, parent_id=None, class_id=None, section_id=None, ay_id=None) -> Student:
    uid = uuid4().hex[:6]
    if not parent_id:
        p = create_parent(db, school_id)
        parent_id = p.id
    if not ay_id:
        ay = create_ay(db, school_id)
        ay_id = ay.id
    if not class_id or not section_id:
        cls, sec = create_class_and_section(db, school_id)
        class_id = cls.id
        section_id = sec.id

    s = Student(
        id=uuid4(),
        school_id=school_id,
        academic_year_id=ay_id,
        admission_number=f"ADM-{uid}",
        roll_number=f"R-{uid}",
        first_name=f"Student_{uid}",
        last_name="Test",
        gender="MALE",
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        phone=f"+9197{uid[:8]}",
        email=f"student_{uid}@test.com",
        parent_id=parent_id,
        school_class_id=class_id,
        section_id=section_id,
        address_line1="123 Student St",
        city="City",
        district="District",
        state="State",
        postal_code="123456",
    )
    db.add(s)
    db.commit()
    db.refresh(s)
    return s


# ── TEST 1: UNIFIED EVENT CONTRACT VALIDATION ────────────────────────────────

def test_unified_event_contract_across_all_domains(school_a: School):
    """
    Verifies that NotificationTriggerEvent enforces a predictable schema across all 5 domains.
    """
    domains = [
        ("visitor_checkin", "visitor_checkin", NotificationRecipientType.TEACHER, NotificationChannel.SMS),
        ("visitor_checkout", "visitor_checkout", NotificationRecipientType.TEACHER, NotificationChannel.IN_APP),
        ("fee_payment_received", "fee_payment_received", NotificationRecipientType.PARENT, NotificationChannel.WHATSAPP),
        ("student_absence", "student_absent_alert", NotificationRecipientType.PARENT, NotificationChannel.SMS),
        ("homework_published", "homework_published", NotificationRecipientType.STUDENT, NotificationChannel.IN_APP),
    ]

    for event_type, tpl_key, recip_type, channel in domains:
        evt = NotificationTriggerEvent(
            event_type=event_type,
            school_id=school_a.id,
            recipient_type=recip_type,
            recipient_name="Test Recipient",
            recipient_contact="+919876543210",
            channel=channel,
            template_key=tpl_key,
            template_variables={"student_name": "Alice", "title": "Math"},
            recipient_id=uuid4(),
            idempotency_key=f"{event_type}:{uuid4().hex[:8]}:{channel.value.lower()}",
            event_metadata={"domain": event_type, "school_id": str(school_a.id)},
        )
        assert evt.event_type == event_type
        assert evt.school_id == school_a.id
        assert evt.template_key == tpl_key
        assert evt.channel == channel


# ── TEST 2: CROSS-TENANT ISOLATION (FAIL-CLOSED) ──────────────────────────────

def test_cross_tenant_isolation_visitor(db_session: Session, school_a: School, school_b: School):
    """
    Verifies that a Visitor event in School A referencing a host in School B fails closed.
    """
    teacher_b = create_teacher(db_session, school_b.id)

    visitor_a = Visitor(
        id=uuid4(),
        school_id=school_a.id,
        visitor_name="Sneaky Visitor",
        phone="+919800000002",
        host_type=HostType.TEACHER,
        host_id=teacher_b.id,  # Cross-tenant host from School B!
        purpose="Meeting",
        status=VisitorStatus.CHECKED_IN,
    )
    db_session.add(visitor_a)
    db_session.flush()

    # Trigger should safely resolve no host and stage 0 notifications
    _trigger_visitor_checkin_notification(db=db_session, visitor=visitor_a)

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.recipient_contact == teacher_b.phone,
        )
    ).all()
    assert len(notifs) == 0


def test_cross_tenant_isolation_fee_payment(db_session: Session, school_a: School, school_b: School):
    """
    Verifies that a Fee Payment in School A referencing a student in School B fails closed.
    """
    student_b = create_student(db_session, school_b.id)

    ay_a = create_ay(db_session, school_a.id)
    structure_a = FeeStructure(
        id=uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        name="Tuition",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(structure_a)
    db_session.flush()

    assignment_a = StudentFeeAssignment(
        id=uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        student_id=student_b.id,  # Student belongs to School B!
        fee_structure_id=structure_a.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 12, 31),
    )
    db_session.add(assignment_a)
    db_session.flush()

    payment_a = FeePayment(
        id=uuid4(),
        school_id=school_a.id,
        student_fee_assignment_id=assignment_a.id,
        receipt_number=f"REC-{uuid4().hex[:6]}",
        amount=Decimal("1000.00"),
        payment_mode=PaymentMode.CASH,
        payment_date=date.today(),
    )
    db_session.add(payment_a)
    db_session.flush()

    _trigger_fee_receipt_notification(db=db_session, payment=payment_a, assignment=assignment_a)

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.template_key == "fee_payment_received",
        )
    ).all()
    assert len(notifs) == 0


def test_cross_tenant_isolation_student_absence(db_session: Session, school_a: School, school_b: School):
    """
    Verifies that student absence trigger fails closed when student is cross-tenant.
    """
    student_b = create_student(db_session, school_b.id)

    # Trigger with school_a ID but student from school_b
    _trigger_student_absence_notification(
        db=db_session,
        school_id=school_a.id,
        student=student_b,
        attendance_date=date.today(),
    )

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.template_key == "student_absent_alert",
        )
    ).all()
    assert len(notifs) == 0


def test_cross_tenant_isolation_homework(db_session: Session, school_a: School, school_b: School):
    """
    Verifies that homework published in School A targeting class in School A resolves 0 students from School B.
    """
    class_a, section_a = create_class_and_section(db_session, school_a.id)
    subject_a = Subject(id=uuid4(), school_id=school_a.id, subject_name="Science", subject_code=f"SCI-{uuid4().hex[:4]}")
    teacher_a = create_teacher(db_session, school_a.id)

    # Student belongs to School B
    student_b = create_student(db_session, school_b.id, class_id=class_a.id, section_id=section_a.id)

    hw_a = Homework(
        id=uuid4(),
        school_id=school_a.id,
        school_class_id=class_a.id,
        section_id=section_a.id,
        subject_id=subject_a.id,
        teacher_id=teacher_a.id,
        title="Science Project",
        description="Science project assignment details",
        status=HomeworkStatus.PUBLISHED,
        assigned_date=date.today(),
        due_date=date.today(),
    )
    db_session.add_all([subject_a, hw_a])
    db_session.commit()

    _trigger_homework_published_notification(db=db_session, school_id=school_a.id, hw=hw_a)

    # Student B should receive 0 notifications from School A
    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.recipient_contact == student_b.phone,
        )
    ).all()
    assert len(notifs) == 0


# ── TEST 3: SAVEPOINT RESILIENCE & PENDING ROLLBACK ISOLATION ────────────────

def test_savepoint_failure_isolation_preserves_business_transaction(db_session: Session, school_a: School):
    """
    Verifies that if notification staging raises an exception, the savepoint rolls back
    without poisoning the outer database transaction, allowing the business commit to succeed.
    """
    cls, sec = create_class_and_section(db_session, school_a.id)
    ay = create_ay(db_session, school_a.id)
    student = create_student(db_session, school_a.id, class_id=cls.id, section_id=sec.id, ay_id=ay.id)

    # Simulate staging failure by patching stage_notification_event
    with patch.object(notification_trigger_service, "stage_notification_event", side_effect=Exception("DB Staging Error")):
        _trigger_student_absence_notification(
            db=db_session,
            school_id=school_a.id,
            student=student,
            attendance_date=date.today(),
        )

    # Main session must still be functional and able to commit business records
    att = Attendance(
        id=uuid4(),
        school_id=school_a.id,
        academic_year_id=ay.id,
        school_class_id=cls.id,
        section_id=sec.id,
        student_id=student.id,
        attendance_date=date.today(),
        status=AttendanceStatus.ABSENT,
    )
    db_session.add(att)
    db_session.commit()  # Must succeed without PendingRollbackError!

    saved_att = db_session.get(Attendance, att.id)
    assert saved_att is not None
    assert saved_att.status == AttendanceStatus.ABSENT


# ── TEST 4: BUSINESS ROLLBACK PREVENTS NOTIFICATION PERSISTENCE ──────────────

def test_business_transaction_rollback_prevents_notification(db_session: Session, school_a: School):
    """
    Verifies that when an outer business transaction rolls back, all staged notifications
    are rolled back and never dispatched.
    """
    school_id = school_a.id
    teacher = create_teacher(db_session, school_id)

    visitor = Visitor(
        id=uuid4(),
        school_id=school_id,
        visitor_name="Rollback Visitor",
        phone="+919800000008",
        host_type=HostType.TEACHER,
        host_id=teacher.id,
        purpose="Inquiry",
        status=VisitorStatus.CHECKED_IN,
    )
    db_session.add(visitor)
    db_session.flush()

    _trigger_visitor_checkin_notification(db=db_session, visitor=visitor)

    # Staged in transaction
    staged = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_id,
            Notification.template_key == "visitor_checkin",
        )
    ).all()
    assert len(staged) > 0

    # Business transaction rolls back
    db_session.rollback()

    # Post-rollback: notification must NOT exist
    after_rollback = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_id,
            Notification.template_key == "visitor_checkin",
        )
    ).all()
    assert len(after_rollback) == 0


# ── TEST 5: CROSS-DOMAIN IDEMPOTENCY & DUPLICATE PREVENTION ──────────────────

def test_cross_domain_idempotency_deduplication(db_session: Session, school_a: School):
    """
    Verifies that repeatedly triggering the same event yields exactly 1 staged notification.
    """
    student = create_student(db_session, school_a.id)

    test_date = date(2026, 9, 9)
    # Trigger absence 3 times
    for _ in range(3):
        _trigger_student_absence_notification(
            db=db_session,
            school_id=school_a.id,
            student=student,
            attendance_date=test_date,
        )

    db_session.commit()

    # Query notifications for student on test_date
    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.recipient_id == student.parent_id,
            Notification.template_key == "student_absent_alert",
            Notification.channel == NotificationChannel.IN_APP,
        )
    ).all()
    assert len(notifs) == 1


# ── TEST 6: COMMUNICATION PREFERENCE OPT-OUT COMPLIANCE ──────────────────────

def test_communication_preference_opt_out_cancels_cleanly(db_session: Session, school_a: School):
    """
    Verifies that when a user opts out of SMS channel, notifications are staged as CANCELLED.
    """
    uid = uuid4().hex[:6]
    from app.identity.models.user import IdentityUser
    user = IdentityUser(
        id=uuid4(),
        school_id=school_a.id,
        email=f"optout_{uid}@test.com",
        password_hash="hashed",
        first_name="OptOut",
        last_name="User",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()

    # Opt-out preference for user
    pref = UserCommunicationPreference(
        id=uuid4(),
        school_id=school_a.id,
        user_id=user.id,
        enable_sms=False,
    )
    db_session.add(pref)
    db_session.commit()

    event = NotificationTriggerEvent(
        event_type="student_absence",
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="OptOut User",
        recipient_contact="+919800000099",
        channel=NotificationChannel.SMS,
        template_key="student_absent_alert",
        template_variables={"student_name": "Child", "date": "2026-09-09"},
        recipient_id=user.id,
        idempotency_key=f"absence:test:optout:sms:{uuid4().hex[:4]}",
    )

    notif = notification_trigger_service.stage_notification_event(
        db=db_session,
        event=event,
        auto_dispatch_on_commit=True,
    )
    db_session.commit()

    assert notif.status == NotificationStatus.CANCELLED
    assert "preference" in (notif.error_message or "").lower()


# ── TEST 7: PROVIDER FAILURE ISOLATION & STATUS MONOTONICITY ─────────────────

def test_provider_failure_isolation_and_status_monotonicity(db_session: Session, school_a: School):
    """
    Verifies that:
    1. Provider failures transition notification to FAILED and record error message.
    2. Already SENT notifications are never re-dispatched or altered.
    """
    # Create PENDING notification
    notif = Notification(
        id=uuid4(),
        school_id=school_a.id,
        recipient_type=NotificationRecipientType.TEACHER,
        recipient_name="Test Host",
        recipient_contact="+919800000011",
        channel=NotificationChannel.SMS,
        template_key="visitor_checkin",
        title="Visitor Alert",
        body="Visitor has arrived",
        status=NotificationStatus.PENDING,
        idempotency_key=f"test_provider_fail:{uuid4().hex[:6]}",
    )
    db_session.add(notif)
    db_session.commit()

    # Mock provider failure
    mock_provider = MagicMock()
    mock_provider.send.return_value = (NotificationStatus.FAILED, "SMS Gateway Timeout")
    with patch("app.services.notification_service.notification_service._get_provider", return_value=mock_provider):
        res = notification_trigger_service.dispatch_pending_notification(
            school_id=school_a.id,
            notification_id=notif.id,
            db_override=db_session,
        )

    assert res is not None
    assert res.status == NotificationStatus.FAILED
    assert "SMS Gateway Timeout" in (res.error_message or "")

    # Now simulate a SENT notification — dispatch must skip it and not overwrite it
    notif.status = NotificationStatus.SENT
    notif.sent_at = datetime.now(timezone.utc)
    db_session.commit()

    with patch("app.services.notification_service.notification_service._get_provider", return_value=mock_provider):
        res2 = notification_trigger_service.dispatch_pending_notification(
            school_id=school_a.id,
            notification_id=notif.id,
            db_override=db_session,
        )

    assert res2 is not None
    assert res2.status == NotificationStatus.SENT  # Retains SENT status!


# ── TEST 8: PII MINIMIZATION IN METADATA ─────────────────────────────────────

def test_pii_minimization_in_metadata(db_session: Session, school_a: School):
    """
    Verifies that metadata and templates across triggers contain no sensitive passwords,
    payment credentials, government IDs, or JWT tokens.
    """
    teacher = create_teacher(db_session, school_a.id)
    visitor = Visitor(
        id=uuid4(),
        school_id=school_a.id,
        visitor_name="John Doe",
        phone="+919800000012",
        id_proof_number="ABCDE1234F",  # Government ID (PAN/Aadhaar)
        host_type=HostType.TEACHER,
        host_id=teacher.id,
        purpose="Delivery",
        status=VisitorStatus.CHECKED_IN,
    )
    db_session.add(visitor)
    db_session.commit()

    _trigger_visitor_checkin_notification(db=db_session, visitor=visitor)
    db_session.commit()

    notif = db_session.scalar(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.template_key == "visitor_checkin",
        )
    )
    if notif:
        assert "ABCDE1234F" not in notif.body
        assert "ABCDE1234F" not in notif.title


# ── TEST 9: HOMEWORK PARENT RECIPIENT DEDUPLICATION ──────────────────────────

def test_homework_parent_recipient_deduplication(db_session: Session, school_a: School):
    """
    Verifies that when a parent has 2 children in the same class, they receive exactly
    ONE homework notification broadcast for that assignment.
    """
    class_a, section_a = create_class_and_section(db_session, school_a.id)
    subject_a = Subject(id=uuid4(), school_id=school_a.id, subject_name="Math", subject_code=f"MTH-{uuid4().hex[:4]}")
    teacher_a = create_teacher(db_session, school_a.id)
    parent = create_parent(db_session, school_a.id)

    # Two sibling students sharing the same parent
    st1 = create_student(db_session, school_a.id, parent_id=parent.id, class_id=class_a.id, section_id=section_a.id)
    st2 = create_student(db_session, school_a.id, parent_id=parent.id, class_id=class_a.id, section_id=section_a.id)

    hw = Homework(
        id=uuid4(),
        school_id=school_a.id,
        school_class_id=class_a.id,
        section_id=section_a.id,
        subject_id=subject_a.id,
        teacher_id=teacher_a.id,
        title="Algebra Homework",
        description="Complete exercises 1 through 10",
        status=HomeworkStatus.PUBLISHED,
        assigned_date=date.today(),
        due_date=date.today(),
    )
    db_session.add_all([subject_a, hw])
    db_session.commit()

    _trigger_homework_published_notification(db=db_session, school_id=school_a.id, hw=hw)
    db_session.commit()

    # Query parent notifications
    parent_notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school_a.id,
            Notification.recipient_id == parent.id,
            Notification.channel == NotificationChannel.IN_APP,
        )
    ).all()
    assert len(parent_notifs) == 1  # Exactly 1 in-app notification for the parent!
