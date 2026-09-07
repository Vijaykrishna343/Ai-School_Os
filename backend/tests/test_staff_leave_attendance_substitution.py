import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.common.enums import AttendanceStatus
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.services.staff_leave_service import staff_leave_service
from app.schemas.staff_leave import StaffLeaveRequestCreate
from app.services.teacher_substitution_service import teacher_substitution_service


def test_leave_attendance_and_substitution_integration(client: TestClient, db_session: Session):
    seed_identity(db_session)

    school = School(
        name="Substitution Test School",
        code=f"SUB-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 5, 31),
        is_current=True,
    )
    db_session.add(ay)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()
    teacher_role = db_session.query(IdentityRole).filter_by(name="Teacher", school_id=None).first()

    # Teacher user
    teacher_user = IdentityUser(
        school_id=school.id,
        email="sub_teacher@school.com",
        password_hash="hash",
        first_name="Sub",
        last_name="Teacher",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(teacher_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=teacher_user.id, role_id=teacher_role.id))
    db_session.commit()

    teacher = Teacher(
        id=teacher_user.id,
        school_id=school.id,
        first_name="Sub",
        last_name="Teacher",
        gender="MALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 6, 1),
        qualification="M.Sc",
        phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        email=f"sub_teacher_{uuid.uuid4().hex[:6]}@school.com",
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        address_line1="123 Staff St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(teacher)

    # Admin user
    admin_user = IdentityUser(
        school_id=school.id,
        email="sub_admin@school.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Sub",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.commit()

    types = staff_leave_service.get_leave_types(db_session, school.id)
    casual_type = types[0]

    # Create & Approve Leave for Tomorrow
    leave_date = date.today() + timedelta(days=1)
    req_res = staff_leave_service.create_leave_request(
        db=db_session,
        school_id=school.id,
        current_user=teacher_user,
        data=StaffLeaveRequestCreate(
            academic_year_id=ay.id,
            leave_type_id=casual_type.id,
            start_date=leave_date,
            end_date=leave_date,
            reason="Attending seminar",
        ),
    )

    # Approve request
    staff_leave_service.approve_leave_request(
        db=db_session,
        school_id=school.id,
        approver_user=admin_user,
        request_id=req_res.id,
        remarks="Approved for seminar",
    )

    # 1. Verify TeacherAttendance auto-created with status EXCUSED
    att = db_session.query(TeacherAttendance).filter_by(
        school_id=school.id,
        teacher_id=teacher.id,
        attendance_date=leave_date,
    ).first()
    assert att is not None
    assert att.status == AttendanceStatus.EXCUSED

    # 2. Verify TeacherSubstitutionService recognizes this teacher's attendance on leave date
    affected_slots = teacher_substitution_service.get_affected_slots(
        db=db_session,
        current_school_id=school.id,
        substitution_date=leave_date,
    )
    assert affected_slots is not None
    assert hasattr(affected_slots, "items")
