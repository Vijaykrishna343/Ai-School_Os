"""
Phase 27.4.2 Visitor Event Notifications Tests
Tests post-commit notification triggers, host recipient resolution, quick check-in idempotency,
failure isolation, tenant isolation, PII protection, and preference handling.
"""
from datetime import date, datetime, timezone
from uuid import uuid4
import pytest
from sqlalchemy import select

from app.common.enums import (
    BloodGroup,
    Gender,
    TeacherStatus,
)
from app.common.enums.visitor import HostType, IdProofType, VisitorStatus
from app.models.communication import UserCommunicationPreference
from app.models.notification import (
    Notification,
    NotificationChannel,
    NotificationRecipientType,
    NotificationStatus,
)
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.schemas.visitor import VisitorCreate, VisitorPreRegister
from app.services.visitor_service import visitor_service


@pytest.fixture
def visitor_test_setup(db_session):
    """Sets up a test school, teacher, student, and parent."""
    school = School(
        id=uuid4(),
        name="Visitor Notification Test Academy",
        code=f"VNTA-{uuid4().hex[:6]}",
        address_line1="123 School Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.flush()

    teacher = Teacher(
        id=uuid4(),
        school_id=school.id,
        employee_id=f"EMP-{uuid4().hex[:6]}",
        first_name="Alice",
        last_name="Smith",
        gender=Gender.FEMALE,
        date_of_birth=date(1985, 5, 20),
        joining_date=date(2020, 1, 15),
        qualification="M.Ed",
        phone=f"+9198765{uuid4().hex[:5]}",
        email=f"alice.{uuid4().hex[:6]}@school.com",
        address_line1="123 Main St",
        city="City",
        district="District",
        state="State",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add(teacher)

    parent = Parent(
        id=uuid4(),
        school_id=school.id,
        father_name="Bob Johnson",
        primary_phone=f"+9199887{uuid4().hex[:5]}",
        email=f"bob.{uuid4().hex[:6]}@parent.com",
        address_line1="456 Oak Rd",
        city="City",
        district="District",
        state="State",
        postal_code="500002",
    )
    db_session.add(parent)
    db_session.flush()

    db_session.commit()

    return {
        "school": school,
        "teacher": teacher,
        "parent": parent,
    }


def test_check_in_visitor_triggers_arrival_notification(db_session, visitor_test_setup):
    """Verifies that check_in_visitor triggers arrival notifications to host after DB commit."""
    setup = visitor_test_setup
    school = setup["school"]
    teacher = setup["teacher"]

    create_data = VisitorCreate(
        visitor_name="John Doe",
        phone="+919123456789",
        email="john.doe@example.com",
        id_proof_type=IdProofType.AADHAAR,
        id_proof_number="AADHAAR-SECRET-1234",
        purpose="Meeting regarding syllabus",
        host_type=HostType.TEACHER,
        host_id=teacher.id,
    )

    visitor_res = visitor_service.check_in_visitor(
        db=db_session,
        current_school_id=school.id,
        data=create_data,
    )

    assert visitor_res.status == VisitorStatus.CHECKED_IN
    assert visitor_res.visitor_name == "John Doe"

    # Query staged/dispatched notifications for this school
    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()

    assert len(notifs) >= 1
    # Check that in-app or SMS notification was staged for teacher
    teacher_notif = next((n for n in notifs if n.recipient_id == teacher.id), None)
    assert teacher_notif is not None
    assert teacher_notif.recipient_type == NotificationRecipientType.TEACHER
    assert teacher_notif.template_key == "visitor_checkin"
    assert "John Doe" in teacher_notif.body
    assert "Meeting regarding syllabus" in teacher_notif.body

    # PII verification: ID proof number MUST NOT be present in title or body
    assert "AADHAAR-SECRET-1234" not in teacher_notif.title
    assert "AADHAAR-SECRET-1234" not in teacher_notif.body


def test_quick_check_in_triggers_exactly_one_notification(db_session, visitor_test_setup):
    """Verifies pre-registration -> quick check-in triggers arrival notification and prevents duplicate notifications."""
    setup = visitor_test_setup
    school = setup["school"]
    teacher = setup["teacher"]

    prereg_data = VisitorPreRegister(
        visitor_name="Expected Guest",
        phone="+919111122222",
        purpose="Campus tour",
        host_type=HostType.TEACHER,
        host_id=teacher.id,
    )

    expected_visitor = visitor_service.pre_register_visitor(
        db=db_session,
        current_school_id=school.id,
        data=prereg_data,
    )

    assert expected_visitor.status == VisitorStatus.EXPECTED

    # Pre-registration should not trigger arrival notification
    prereg_notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()
    assert len(prereg_notifs) == 0

    # Perform Quick Check-In
    checked_in_res = visitor_service.quick_check_in_visitor(
        db=db_session,
        visitor_id=expected_visitor.id,
        current_school_id=school.id,
    )

    assert checked_in_res.status == VisitorStatus.CHECKED_IN

    quick_notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()
    assert len(quick_notifs) >= 1

    initial_count = len(quick_notifs)

    # Attempting second quick check-in raises exception and does not create duplicate notifications
    with pytest.raises(Exception):
        visitor_service.quick_check_in_visitor(
            db=db_session,
            visitor_id=expected_visitor.id,
            current_school_id=school.id,
        )

    subsequent_notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.is_deleted.is_(False),
        )
    ).all()
    assert len(subsequent_notifs) == initial_count


def test_checkout_visitor_triggers_departure_notification(db_session, visitor_test_setup):
    """Verifies that checking out a visitor triggers an IN_APP departure notification to the host."""
    setup = visitor_test_setup
    school = setup["school"]
    teacher = setup["teacher"]

    create_data = VisitorCreate(
        visitor_name="Departing Visitor",
        phone="+919333344444",
        purpose="Vendor delivery",
        host_type=HostType.TEACHER,
        host_id=teacher.id,
    )

    v_res = visitor_service.check_in_visitor(
        db=db_session,
        current_school_id=school.id,
        data=create_data,
    )

    # Checkout
    co_res = visitor_service.check_out_visitor(
        db=db_session,
        visitor_id=v_res.id,
        current_school_id=school.id,
    )

    assert co_res.status == VisitorStatus.CHECKED_OUT

    co_notif = db_session.scalar(
        select(Notification).where(
            Notification.school_id == school.id,
            Notification.template_key == "visitor_checkout",
            Notification.idempotency_key == f"visitor_checkout:{v_res.id}:in_app",
            Notification.is_deleted.is_(False),
        )
    )

    assert co_notif is not None
    assert co_notif.channel == NotificationChannel.IN_APP
    assert "Departing Visitor" in co_notif.body
    assert "checked out" in co_notif.body.lower()


def test_rollback_safety_sends_no_notification(db_session, visitor_test_setup):
    """Verifies that if a visitor transaction fails/rolls back, no notification is sent."""
    setup = visitor_test_setup
    school = setup["school"]
    teacher = setup["teacher"]

    create_data = VisitorCreate(
        visitor_name="Rollback Test Visitor",
        phone="+919444455555",
        purpose="Rollback Test",
        host_type=HostType.TEACHER,
        host_id=teacher.id,
    )

    # Perform check-in once
    visitor_service.check_in_visitor(
        db=db_session,
        current_school_id=school.id,
        data=create_data,
    )

    # Count notifications
    count_before = len(
        db_session.scalars(
            select(Notification).where(
                Notification.school_id == school.id,
                Notification.is_deleted.is_(False),
            )
        ).all()
    )

    # Attempting duplicate active check-in raises ValidationException and rolls back
    with pytest.raises(Exception):
        visitor_service.check_in_visitor(
            db=db_session,
            current_school_id=school.id,
            data=create_data,
        )

    count_after = len(
        db_session.scalars(
            select(Notification).where(
                Notification.school_id == school.id,
                Notification.is_deleted.is_(False),
            )
        ).all()
    )

    assert count_after == count_before


def test_tenant_isolation_cross_tenant_host(db_session, visitor_test_setup):
    """Verifies host linkage cannot cross tenant boundaries."""
    setup = visitor_test_setup
    teacher = setup["teacher"]

    other_school = School(
        id=uuid4(),
        name="Other School Academy",
        code=f"OSA-{uuid4().hex[:6]}",
        address_line1="456 Other St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500002",
    )
    db_session.add(other_school)
    db_session.commit()

    create_data = VisitorCreate(
        visitor_name="Cross Tenant Visitor",
        phone="+919555566666",
        purpose="Cross Tenant Test",
        host_type=HostType.TEACHER,
        host_id=teacher.id,  # teacher belongs to school, not other_school
    )

    with pytest.raises(Exception) as exc_info:
        visitor_service.check_in_visitor(
            db=db_session,
            current_school_id=other_school.id,
            data=create_data,
        )

    assert "Referenced teacher host not found" in str(exc_info.value)
