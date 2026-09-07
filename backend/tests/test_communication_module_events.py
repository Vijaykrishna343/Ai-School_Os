"""
Phase 8 Communication Integration Tests Across Business Modules
Verifies Event, Hostel, Staff Leave, Fee, and Attendance Notification Dispatches.
"""
import pytest
from uuid import uuid4
from app.database.session import SessionLocal
from app.models.school import School
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus
from app.services.notification_service import notification_service


def test_business_modules_notification_dispatches():
    db = SessionLocal()
    school = School(name=f"Module Test School {uuid4().hex[:4]}", code=f"MTS-{uuid4().hex[:4]}", address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db.add(school)
    db.commit()

    # 1. Absence Alert
    abs_n = notification_service.send_absence_alert(
        db=db,
        school_id=school.id,
        student_name="Rahul Kumar",
        parent_name="Suresh Kumar",
        parent_contact="suresh@test.com",
        date_str="2026-08-25",
    )
    assert abs_n.status == NotificationStatus.SENT
    assert "Rahul Kumar" in abs_n.body

    # 2. Fee Receipt
    fee_n = notification_service.send_fee_receipt(
        db=db,
        school_id=school.id,
        student_name="Rahul Kumar",
        parent_name="Suresh Kumar",
        parent_contact="suresh@test.com",
        amount="15000",
        date_str="2026-08-25",
        receipt_number="REC-998811",
    )
    assert fee_n.status == NotificationStatus.SENT
    assert "15000" in fee_n.body

    # 3. Staff Leave Notification
    leave_n = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.TEACHER,
        recipient_name="Anita Sharma",
        recipient_contact="anita@school.com",
        channel=NotificationChannel.EMAIL,
        template_key="staff_leave_approved",
        template_variables={"start_date": "2026-09-01", "end_date": "2026-09-02"},
    )
    assert leave_n.status == NotificationStatus.SENT
    assert "APPROVED" in leave_n.body

    # 4. Hostel Outpass Status
    hostel_n = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STUDENT,
        recipient_name="Vikram Singh",
        recipient_contact="vikram@school.com",
        channel=NotificationChannel.IN_APP,
        template_key="hostel_outpass_status",
        template_variables={
            "student_name": "Vikram Singh",
            "start_date": "2026-09-05",
            "end_date": "2026-09-06",
            "status": "APPROVED",
        },
    )
    assert hostel_n.status == NotificationStatus.SENT
    assert "APPROVED" in hostel_n.body

    db.close()
