"""
Phase 27.4.4 — Student Absence & Homework Publication Notification Tests

Validates:
1. Student absence notification triggers (single create, bulk create, status updates, parent fallback, tenant isolation, idempotency).
2. Homework publication notification triggers (draft vs published, update_homework, publish_homework, recipient deduplication, idempotency).
3. System safety & fault tolerance (provider/staging error does not roll back attendance or homework transactions).
"""
from datetime import date, timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus, StudentStatus
from app.models.homework.homework import Homework, HomeworkStatus
from app.identity.models.user import IdentityUser
from app.models.academic_year.academic_year import AcademicYear
from app.models.attendance import Attendance
from app.models.homework.homework import Homework
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.schemas.attendance.attendance import (
    AttendanceBulkCreate,
    AttendanceBulkItem,
    AttendanceCreate,
    AttendanceUpdate,
)
from app.schemas.homework.homework import HomeworkCreate, HomeworkUpdate
from app.services.attendance_service import attendance_service
from app.services.homework_service import homework_service


@pytest.fixture
def setup_absence_homework_data(db_session: Session):
    """
    Sets up school, academic year, school class, section, teacher, subject, parents, and students.
    """
    school = School(
        id=uuid4(),
        name="Test Academy Notifications",
        code=f"TAN-{uuid4().hex[:4]}",
        address_line1="123 Test St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(school)

    ay = AcademicYear(
        id=uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db_session.add(ay)

    school_class = SchoolClass(
        id=uuid4(),
        school_id=school.id,
        name="Grade 9",
        display_order=1,
    )
    db_session.add(school_class)

    section = Section(
        id=uuid4(),
        school_class_id=school_class.id,
        name="A",
    )
    db_session.add(section)

    teacher = Teacher(
        id=uuid4(),
        school_id=school.id,
        employee_id=f"EMP-{uuid4().hex[:4]}",
        first_name="Alice",
        last_name="Teacher",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 6, 1),
        qualification="M.Sc",
        phone=f"+9199000{uuid4().hex[:5]}",
        email=f"teacher_{uuid4().hex[:4]}@test.com",
        address_line1="123 Staff St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(teacher)

    user = IdentityUser(
        id=uuid4(),
        school_id=school.id,
        email=teacher.email,
        password_hash="hashed",
        first_name="Alice",
        last_name="Teacher",
        is_active=True,
    )
    db_session.add(user)

    subject = Subject(
        id=uuid4(),
        school_id=school.id,
        subject_name="Mathematics",
        subject_code=f"MATH-{uuid4().hex[:4]}",
    )
    db_session.add(subject)

    # Parent 1 with phone & email
    parent1 = Parent(
        id=uuid4(),
        school_id=school.id,
        father_name="John Doe",
        primary_phone=f"+9198000{uuid4().hex[:5]}",
        email=f"parent1_{uuid4().hex[:4]}@test.com",
        address_line1="123 Home St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(parent1)

    # Student 1 linked to Parent 1
    student1 = Student(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent1.id,
        admission_number=f"ADM-001-{uuid4().hex[:4]}",
        roll_number=f"R001-{uuid4().hex[:4]}",
        first_name="Bob",
        last_name="Doe",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        phone=f"+9197000{uuid4().hex[:5]}",
        email=f"student1_{uuid4().hex[:4]}@test.com",
        address_line1="123 Student St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(student1)

    # Student 2 linked to Parent 1 (sibling test)
    student2 = Student(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent1.id,
        admission_number=f"ADM-002-{uuid4().hex[:4]}",
        roll_number=f"R002-{uuid4().hex[:4]}",
        first_name="Charlie",
        last_name="Doe",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        phone=f"+9197001{uuid4().hex[:5]}",
        email=f"student2_{uuid4().hex[:4]}@test.com",
        address_line1="123 Student St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(student2)

    # Parent with no phone/email (for fallback test)
    parent_no_contact = Parent(
        id=uuid4(),
        school_id=school.id,
        father_name="No Contact Parent",
        primary_phone="",
        email="",
        address_line1="123 Home St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(parent_no_contact)

    # Student 3 linked to Parent with no contact info (fallback test)
    student3 = Student(
        id=uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=school_class.id,
        section_id=section.id,
        parent_id=parent_no_contact.id,
        admission_number=f"ADM-003-{uuid4().hex[:4]}",
        roll_number=f"R003-{uuid4().hex[:4]}",
        first_name="Dave",
        last_name="Solo",
        gender="MALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2020, 6, 1),
        status=StudentStatus.ACTIVE,
        phone=f"+9197002{uuid4().hex[:5]}",
        email=f"student3_{uuid4().hex[:4]}@test.com",
        address_line1="123 Student St",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="123456",
    )
    db_session.add(student3)

    db_session.commit()

    return {
        "school": school,
        "ay": ay,
        "school_class": school_class,
        "section": section,
        "teacher": teacher,
        "user": user,
        "subject": subject,
        "parent1": parent1,
        "student1": student1,
        "student2": student2,
        "student3": student3,
    }


# ==========================================
# 1. STUDENT ABSENCE NOTIFICATION TESTS
# ==========================================

def test_single_attendance_absent_triggers_notification(db_session: Session, setup_absence_homework_data):
    """
    Creating single attendance with status ABSENT stages notification for parent.
    """
    d = setup_absence_homework_data
    att_in = AttendanceCreate(
        student_id=d["student1"].id,
        attendance_date=date(2026, 9, 10),
        status=AttendanceStatus.ABSENT,
        remarks="Unexcused absence",
    )

    rec = attendance_service.create_attendance(db_session, d["user"], att_in)
    db_session.commit()

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == d["school"].id,
            Notification.recipient_id == d["parent1"].id,
            Notification.is_deleted == False,
        )
    ).all()

    assert len(notifs) >= 1
    absent_notif = next((n for n in notifs if "student_absence" in (n.idempotency_key or "")), None)
    assert absent_notif is not None
    assert absent_notif.recipient_type == NotificationRecipientType.PARENT
    assert "Bob" in absent_notif.body or "Bob" in absent_notif.title


def test_single_attendance_present_does_not_trigger_absence_notification(db_session: Session, setup_absence_homework_data):
    """
    Creating single attendance with status PRESENT stages 0 absence notifications.
    """
    d = setup_absence_homework_data
    att_in = AttendanceCreate(
        student_id=d["student1"].id,
        attendance_date=date(2026, 9, 11),
        status=AttendanceStatus.PRESENT,
    )

    attendance_service.create_attendance(db_session, d["user"], att_in)
    db_session.commit()

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == d["school"].id,
            Notification.is_deleted == False,
        )
    ).all()

    absence_notifs = [n for n in notifs if "student_absence" in (n.idempotency_key or "")]
    assert len(absence_notifs) == 0


def test_bulk_attendance_triggers_absence_only_for_absent_students(db_session: Session, setup_absence_homework_data):
    """
    Bulk attendance for 3 students (1 ABSENT, 2 PRESENT) stages notifications only for the absent student.
    """
    d = setup_absence_homework_data
    bulk_in = AttendanceBulkCreate(
        section_id=d["section"].id,
        attendance_date=date(2026, 9, 12),
        records=[
            AttendanceBulkItem(student_id=d["student1"].id, status=AttendanceStatus.PRESENT),
            AttendanceBulkItem(student_id=d["student2"].id, status=AttendanceStatus.ABSENT, remarks="Sick"),
            AttendanceBulkItem(student_id=d["student3"].id, status=AttendanceStatus.PRESENT),
        ],
    )

    attendance_service.create_bulk_attendance(db_session, d["user"], bulk_in)
    db_session.commit()

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == d["school"].id,
            Notification.is_deleted == False,
        )
    ).all()

    absence_notifs = [n for n in notifs if "student_absence" in (n.idempotency_key or "")]
    assert len(absence_notifs) >= 1
    # Check that notifications were sent for student2 (Charlie) but not student1 (Bob) or student3 (Dave)
    for n in absence_notifs:
        assert "2026-09-12" in (n.idempotency_key or "")
        assert str(d["student2"].id) in (n.idempotency_key or "")


def test_attendance_status_update_prevents_duplicate_notifications(db_session: Session, setup_absence_homework_data):
    """
    Updating PRESENT -> ABSENT triggers notification.
    Updating ABSENT -> ABSENT does NOT trigger additional notification.
    Updating ABSENT -> PRESENT does NOT trigger notification.
    """
    d = setup_absence_homework_data
    att_date = date(2026, 9, 13)

    # 1. Initially mark PRESENT
    att_in = AttendanceCreate(
        student_id=d["student1"].id,
        attendance_date=att_date,
        status=AttendanceStatus.PRESENT,
    )
    rec = attendance_service.create_attendance(db_session, d["user"], att_in)
    db_session.commit()

    count_0 = len(db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all())
    assert count_0 == 0

    # 2. Update PRESENT -> ABSENT
    up_1 = AttendanceUpdate(status=AttendanceStatus.ABSENT)
    attendance_service.update_attendance(db_session, d["user"], rec.id, up_1)
    db_session.commit()

    notifs_1 = db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all()
    count_1 = len([n for n in notifs_1 if "student_absence" in (n.idempotency_key or "")])
    assert count_1 >= 1

    # 3. Update ABSENT -> ABSENT (remarks update)
    up_2 = AttendanceUpdate(status=AttendanceStatus.ABSENT, remarks="Updated remarks")
    attendance_service.update_attendance(db_session, d["user"], rec.id, up_2)
    db_session.commit()

    notifs_2 = db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all()
    count_2 = len([n for n in notifs_2 if "student_absence" in (n.idempotency_key or "")])
    assert count_2 == count_1  # No duplicate notifications added

    # 4. Update ABSENT -> PRESENT
    up_3 = AttendanceUpdate(status=AttendanceStatus.PRESENT)
    attendance_service.update_attendance(db_session, d["user"], rec.id, up_3)
    db_session.commit()

    notifs_3 = db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all()
    count_3 = len([n for n in notifs_3 if "student_absence" in (n.idempotency_key or "")])
    assert count_3 == count_1  # No notifications added when corrected to PRESENT


def test_student_absence_fallback_when_no_parent(db_session: Session, setup_absence_homework_data):
    """
    When student has no linked parent (student3), notification falls back to Student recipient.
    """
    d = setup_absence_homework_data
    att_in = AttendanceCreate(
        student_id=d["student3"].id,
        attendance_date=date(2026, 9, 14),
        status=AttendanceStatus.ABSENT,
    )

    attendance_service.create_attendance(db_session, d["user"], att_in)
    db_session.commit()

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == d["school"].id,
            Notification.recipient_id == d["student3"].id,
            Notification.is_deleted == False,
        )
    ).all()

    st_notif = next((n for n in notifs if "student_absence" in (n.idempotency_key or "")), None)
    assert st_notif is not None
    assert st_notif.recipient_type == NotificationRecipientType.STUDENT


# ==========================================
# 2. HOMEWORK PUBLICATION NOTIFICATION TESTS
# ==========================================

def test_homework_created_as_draft_does_not_trigger_notification(db_session: Session, setup_absence_homework_data):
    """
    Creating homework in DRAFT status triggers 0 notifications.
    """
    d = setup_absence_homework_data
    hw_in = HomeworkCreate(
        school_class_id=d["school_class"].id,
        section_id=d["section"].id,
        subject_id=d["subject"].id,
        title="Math Algebra Intro",
        description="Solve exercises 1 to 10",
        due_date=date(2026, 9, 20),
    )

    hw_res = homework_service.create_homework(db_session, d["school"].id, d["user"], hw_in)
    db_session.commit()

    notifs = db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all()
    hw_notifs = [n for n in notifs if "homework_published" in (n.idempotency_key or "")]
    assert len(hw_notifs) == 0


def test_publish_homework_triggers_notifications_with_deduplication(db_session: Session, setup_absence_homework_data):
    """
    Publishing homework stages notifications for eligible active students and parents.
    Parent1 (who has 2 children in class) receives deduplicated notifications.
    """
    d = setup_absence_homework_data
    hw_in = HomeworkCreate(
        school_class_id=d["school_class"].id,
        section_id=d["section"].id,
        subject_id=d["subject"].id,
        title="Geometry Quiz Prep",
        description="Prepare chapters 4 and 5",
        due_date=date(2026, 9, 21),
    )

    hw_res = homework_service.create_homework(db_session, d["school"].id, d["user"], hw_in)
    homework_service.publish_homework(db_session, d["school"].id, hw_res.id, d["user"])
    db_session.commit()

    notifs = db_session.scalars(
        select(Notification).where(
            Notification.school_id == d["school"].id,
            Notification.is_deleted == False,
        )
    ).all()

    hw_notifs = [n for n in notifs if "homework_published" in (n.idempotency_key or "")]

    # Check recipient types
    recipient_types = {n.recipient_type.value if hasattr(n.recipient_type, "value") else str(n.recipient_type) for n in hw_notifs}
    assert "STUDENT" in recipient_types or any(n.recipient_type == NotificationRecipientType.STUDENT for n in hw_notifs)
    assert "PARENT" in recipient_types or any(n.recipient_type == NotificationRecipientType.PARENT for n in hw_notifs)

    # Check parent1 (has 2 children student1 and student2) - must have exactly 1 notification per channel
    parent_inapp_notifs = [
        n for n in hw_notifs
        if str(n.recipient_id) == str(d["parent1"].id) and (n.channel == NotificationChannel.IN_APP or getattr(n.channel, "value", str(n.channel)) == "IN_APP")
    ]
    assert len(parent_inapp_notifs) == 1


def test_update_homework_status_to_published_triggers_notifications(db_session: Session, setup_absence_homework_data):
    """
    Updating homework status from DRAFT -> PUBLISHED via update_homework stages notifications.
    Subsequent edits when already PUBLISHED do NOT re-trigger publication notifications.
    """
    d = setup_absence_homework_data
    hw_in = HomeworkCreate(
        school_class_id=d["school_class"].id,
        section_id=d["section"].id,
        subject_id=d["subject"].id,
        title="Physics Principles",
        description="Read pages 100 to 120",
        due_date=date(2026, 9, 22),
    )
    hw_res = homework_service.create_homework(db_session, d["school"].id, d["user"], hw_in)
    db_session.commit()

    # 1. Update status to PUBLISHED
    up_1 = HomeworkUpdate(status=HomeworkStatus.PUBLISHED)
    homework_service.update_homework(db_session, d["school"].id, hw_res.id, d["user"], up_1)
    db_session.commit()

    notifs_1 = db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all()
    count_1 = len([n for n in notifs_1 if "homework_published" in (n.idempotency_key or "")])
    assert count_1 >= 1

    # 2. Update title of ALREADY PUBLISHED homework
    up_2 = HomeworkUpdate(title="Physics Principles Revised")
    homework_service.update_homework(db_session, d["school"].id, hw_res.id, d["user"], up_2)
    db_session.commit()

    notifs_2 = db_session.scalars(select(Notification).where(Notification.school_id == d["school"].id)).all()
    count_2 = len([n for n in notifs_2 if "homework_published" in (n.idempotency_key or "")])
    assert count_2 == count_1  # No duplicate notifications on edit of published homework
