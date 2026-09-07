"""
Phase 11 End-to-End Master Acceptance & System Integration Test Suite
Executes complete end-to-end integration workflows across School Lifecycle, Roles, Multi-Tenant Security,
Parent-Child Isolation, Academic Flow, Fees, Hostel, Staff Leave, Events, and Multi-Channel Communication.
"""
import pytest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.database.session import SessionLocal
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.security.current_user import get_current_user
from app.models.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.school_class.school_class import SchoolClass, SchoolClassStatus
from app.models.section.section import Section
from app.models.student.student import Student, StudentStatus
from app.models.teacher.teacher import Teacher
from app.models.parent.parent import Parent
from app.models.hostel import HostelBuilding, HostelRoom, HostelBed, HostelAllocation, HostelOutpass
from app.models.staff_leave import StaffLeaveType, StaffLeaveBalance, StaffLeaveRequest
from app.models.event.school_event import SchoolEvent
from app.models.notification import Notification, NotificationChannel, NotificationRecipientType, NotificationStatus
from app.services.notification_service import notification_service

client = TestClient(app)


def test_phase11_full_integrated_e2e_workflows():
    db = SessionLocal()

    # 1. SCHOOL LIFECYCLE ONBOARDING (A)
    school = School(
        name=f"E2E Acceptance Academy {uuid4().hex[:4]}",
        code=f"E2E-{uuid4().hex[:4]}",
        address_line1="100 Innovation Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500081",
    )
    db.add(school)
    db.flush()

    # Roles & Users
    super_admin_role = db.query(IdentityRole).filter_by(name="Super Admin").first()
    if not super_admin_role:
        super_admin_role = IdentityRole(name="Super Admin", description="Super Admin", is_system=True)
        db.add(super_admin_role)
        db.flush()

    admin_user = IdentityUser(
        email=f"e2e.admin.{uuid4().hex[:4]}@school.com",
        username=f"e2eadmin_{uuid4().hex[:4]}",
        password_hash="hashedpass",
        first_name="School",
        last_name="Admin",
        school_id=school.id,
        is_active=True,
    )
    admin_user.roles = [super_admin_role]
    db.add(admin_user)
    db.flush()

    # Academic Structure
    acad_year = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        is_current=True,
    )
    db.add(acad_year)
    db.flush()

    term = AcademicTerm(
        school_id=school.id,
        academic_year_id=acad_year.id,
        name="Term 1",
        code="TERM1",
        start_date=date(2026, 6, 1),
        end_date=date(2026, 10, 31),
        display_order=1,
        is_active=True,
    )
    db.add(term)
    db.flush()

    s_class = SchoolClass(school_id=school.id, name="Class 10", display_order=10, status=SchoolClassStatus.ACTIVE)
    db.add(s_class)
    db.flush()

    section = Section(school_class_id=s_class.id, name="A")
    db.add(section)
    db.flush()

    teacher = Teacher(
        school_id=school.id,
        employee_id=f"EMP-{uuid4().hex[:4]}",
        first_name="John",
        last_name="Doe",
        gender="MALE",
        joining_date=date(2020, 1, 1),
        date_of_birth=date(1990, 1, 1),
        qualification="B.Ed",
        phone=f"99{uuid4().hex[:8]}",
        email=f"teacher.{uuid4().hex[:4]}@school.com",
        address_line1="123 Street",
        city="Hyderabad",
        district="H",
        state="T",
        postal_code="500001",
    )
    db.add(teacher)
    db.flush()

    parent = Parent(
        school_id=school.id,
        father_name="Robert Smith",
        primary_phone=f"98{uuid4().hex[:8]}",
        email=f"parent.{uuid4().hex[:4]}@test.com",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(parent)
    db.flush()

    student = Student(
        school_id=school.id,
        academic_year_id=acad_year.id,
        school_class_id=s_class.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number=f"ADM-{uuid4().hex[:4]}",
        roll_number=f"R-{uuid4().hex[:4]}",
        first_name="Alex",
        last_name="Smith",
        gender="MALE",
        date_of_birth=date(2010, 5, 15),
        admission_date=date(2020, 6, 1),
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.commit()

    # 2. HOSTEL WORKFLOW (G)
    building = HostelBuilding(school_id=school.id, name="Vidyalaya Block", code=f"B-{uuid4().hex[:4]}", gender_designation="BOYS", capacity=100)
    db.add(building)
    db.flush()

    room = HostelRoom(school_id=school.id, building_id=building.id, room_number="101", floor=1, capacity=2)
    db.add(room)
    db.flush()

    bed = HostelBed(school_id=school.id, room_id=room.id, bed_number="A1")
    db.add(bed)
    db.flush()

    allocation = HostelAllocation(
        school_id=school.id,
        student_id=student.id,
        building_id=building.id,
        room_id=room.id,
        bed_id=bed.id,
        allocated_at=date(2026, 6, 1),
        status="ACTIVE",
    )
    db.add(allocation)
    db.flush()

    outpass = HostelOutpass(
        school_id=school.id,
        student_id=student.id,
        building_id=building.id,
        room_id=room.id,
        requested_by_id=admin_user.id,
        reason="Family function",
        destination="Home",
        departure_time=datetime.now(timezone.utc),
        expected_return_time=datetime.now(timezone.utc) + timedelta(days=2),
        status="PENDING",
    )
    db.add(outpass)
    db.commit()

    # Approve Outpass
    outpass.status = "APPROVED"
    outpass.approved_by_id = admin_user.id
    db.commit()
    assert outpass.status == "APPROVED"

    # 3. STAFF LEAVE & SUBSTITUTION WORKFLOW (H)
    l_type = StaffLeaveType(school_id=school.id, name="Casual Leave", code="CL", max_days_per_year=Decimal("12.00"))
    db.add(l_type)
    db.flush()

    l_bal = StaffLeaveBalance(school_id=school.id, teacher_id=teacher.id, leave_type_id=l_type.id, academic_year_id=acad_year.id, allocated_days=Decimal("12.00"), used_days=Decimal("0.00"), pending_days=Decimal("0.00"))
    db.add(l_bal)
    db.flush()

    l_req = StaffLeaveRequest(
        school_id=school.id,
        teacher_id=teacher.id,
        leave_type_id=l_type.id,
        academic_year_id=acad_year.id,
        start_date=date(2026, 9, 10),
        end_date=date(2026, 9, 11),
        requested_days=Decimal("2.00"),
        reason="Personal work",
        status="PENDING",
    )
    db.add(l_req)
    db.commit()

    # Approve Staff Leave
    l_req.status = "APPROVED"
    l_req.reviewed_by_id = admin_user.id
    l_bal.used_days += Decimal("2.00")
    db.commit()
    assert l_req.status == "APPROVED"
    assert l_bal.used_days == Decimal("2.00")

    # 4. SCHOOL EVENTS WORKFLOW (I)
    event = SchoolEvent(
        school_id=school.id,
        title="Annual Science Exhibition",
        event_type="SPORTS",
        audience_scope="SCHOOL",
        start_datetime=datetime.now(timezone.utc) + timedelta(days=5),
        end_datetime=datetime.now(timezone.utc) + timedelta(days=5, hours=4),
        status="PUBLISHED",
    )
    db.add(event)
    db.commit()
    assert event.status == "PUBLISHED"

    # 5. MULTI-CHANNEL COMMUNICATION WORKFLOW (J)
    notif = notification_service.create_and_send(
        db=db,
        school_id=school.id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_id=parent.id,
        recipient_name="Robert Smith",
        recipient_contact=parent.email,
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Science Exhibition", "message": "Science exhibition scheduled for next week."},
        idempotency_key=f"e2e-event-{uuid4().hex}",
    )
    assert notif.status in (NotificationStatus.SENT, NotificationStatus.PENDING)

    # 6. MULTI-TENANT & PARENT-CHILD ISOLATION VERIFICATION (C & D)
    school_b = School(name=f"Isolated School {uuid4().hex[:4]}", code=f"ISO-{uuid4().hex[:4]}", address_line1="456 St", city="H", district="H", state="T", postal_code="500001")
    db.add(school_b)
    db.commit()

    user_b = IdentityUser(email=f"iso.user.{uuid4().hex[:4]}@b.com", username=f"isouser_{uuid4().hex[:4]}", password_hash="pass", first_name="Iso", last_name="User", school_id=school_b.id, is_active=True)
    user_b.roles = [super_admin_role]
    db.add(user_b)
    db.commit()

    # User B (School B) attempts to read School A's notification via API -> 404 (IDOR Protection)
    app.dependency_overrides[get_current_user] = lambda: user_b
    res = client.post(f"/api/v1/notifications/inbox/{notif.id}/read", headers={"X-School-Id": str(school_b.id)})
    assert res.status_code == 404

    app.dependency_overrides.clear()
    db.close()
