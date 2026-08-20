import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import AttendanceStatus, TeacherStatus, Gender
from app.main import app
from app.models.school.school import School
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager


@pytest.fixture
def setup_teacher_attendance_data(db_session: Session):
    suffix = uuid.uuid4().hex[:6]

    # Create School A & B
    school_a = School(name=f"TA School A {suffix}", code=f"TASA_{suffix}", address_line1="123 Campus St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    school_b = School(name=f"TA School B {suffix}", code=f"TASB_{suffix}", address_line1="456 Campus St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db_session.add_all([school_a, school_b])
    db_session.commit()

    # Create Teachers in School A
    teacher_a1 = Teacher(
        school_id=school_a.id,
        employee_id=f"EMP_A1_{suffix}",
        first_name="Alice",
        last_name="Staff",
        gender=Gender.FEMALE,
        phone=f"9000{suffix[:6]}",
        email=f"alice_{suffix}@school.edu",
        status=TeacherStatus.ACTIVE,
    )
    teacher_a2 = Teacher(
        school_id=school_a.id,
        employee_id=f"EMP_A2_{suffix}",
        first_name="Bob",
        last_name="Staff",
        gender=Gender.MALE,
        phone=f"9001{suffix[:6]}",
        email=f"bob_{suffix}@school.edu",
        status=TeacherStatus.ACTIVE,
    )

    # Create Teacher in School B
    teacher_b1 = Teacher(
        school_id=school_b.id,
        employee_id=f"EMP_B1_{suffix}",
        first_name="Charlie",
        last_name="Staff",
        gender=Gender.MALE,
        phone=f"9002{suffix[:6]}",
        email=f"charlie_{suffix}@school.edu",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([teacher_a1, teacher_a2, teacher_b1])
    db_session.commit()

    # Get School Admin Role
    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    teacher_role = db_session.query(IdentityRole).filter_by(name="Teacher").first()

    # User Admin School A
    admin_a = IdentityUser(
        school_id=school_a.id,
        email=f"admin_a_{suffix}@school.edu",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    db_session.add(admin_a)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_a.id, role_id=admin_role.id))

    # User Teacher Alice School A
    teacher_user_a = IdentityUser(
        school_id=school_a.id,
        email=f"alice_{suffix}@school.edu",
        password_hash=hash_password("TeacherPass123!"),
        is_active=True,
    )
    db_session.add(teacher_user_a)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=teacher_user_a.id, role_id=teacher_role.id))

    # User Admin School B
    admin_b = IdentityUser(
        school_id=school_b.id,
        email=f"admin_b_{suffix}@school.edu",
        password_hash=hash_password("AdminPass123!"),
        is_active=True,
    )
    db_session.add(admin_b)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_b.id, role_id=admin_role.id))

    db_session.commit()

    token_admin_a = jwt_manager.create_access_token(user_id=admin_a.id, school_id=school_a.id)
    token_teacher_a = jwt_manager.create_access_token(user_id=teacher_user_a.id, school_id=school_a.id)
    token_admin_b = jwt_manager.create_access_token(user_id=admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a,
        "school_b": school_b,
        "teacher_a1": teacher_a1,
        "teacher_a2": teacher_a2,
        "teacher_b1": teacher_b1,
        "token_admin_a": token_admin_a,
        "token_teacher_a": token_teacher_a,
        "token_admin_b": token_admin_b,
    }


def test_01_teacher_attendance_list_and_summary(setup_teacher_attendance_data):
    data = setup_teacher_attendance_data
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {data['token_admin_a']}"}

    today_str = date.today().isoformat()

    # Get summary
    res_sum = client.get(f"/api/v1/teachers/attendance/summary?attendance_date={today_str}", headers=headers)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()["data"]
    assert sum_data["total_teachers"] >= 2
    assert sum_data["present_count"] >= 2

    # Get list
    res_list = client.get(f"/api/v1/teachers/attendance?attendance_date={today_str}", headers=headers)
    assert res_list.status_code == 200
    list_items = res_list.json()["data"]
    assert len(list_items) >= 2


def test_02_bulk_mark_teacher_attendance(setup_teacher_attendance_data):
    data = setup_teacher_attendance_data
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {data['token_admin_a']}"}

    today_str = date.today().isoformat()
    payload = {
        "attendance_date": today_str,
        "items": [
            {
                "teacher_id": str(data["teacher_a1"].id),
                "status": "PRESENT",
                "check_in_time": "08:15 AM",
                "check_out_time": "04:00 PM",
                "remarks": "On time",
            },
            {
                "teacher_id": str(data["teacher_a2"].id),
                "status": "ABSENT",
                "remarks": "Sick leave",
            },
        ],
    }

    res = client.post("/api/v1/teachers/attendance/bulk", json=payload, headers=headers)
    assert res.status_code == 200
    items = res.json()["data"]
    assert len(items) == 2

    # Check updated summary
    res_sum = client.get(f"/api/v1/teachers/attendance/summary?attendance_date={today_str}", headers=headers)
    assert res_sum.status_code == 200
    sum_data = res_sum.json()["data"]
    assert sum_data["absent_count"] >= 1


def test_03_teacher_self_checkin_checkout(setup_teacher_attendance_data):
    data = setup_teacher_attendance_data
    client = TestClient(app)
    headers = {"Authorization": f"Bearer {data['token_teacher_a']}"}

    # Self Check In
    res_in = client.post("/api/v1/teachers/attendance/check-in", headers=headers)
    assert res_in.status_code == 200
    assert res_in.json()["data"]["check_in_time"] is not None
    assert res_in.json()["data"]["status"] == "PRESENT"

    # Self Check Out
    res_out = client.post("/api/v1/teachers/attendance/check-out", headers=headers)
    assert res_out.status_code == 200
    assert res_out.json()["data"]["check_out_time"] is not None


def test_04_teacher_attendance_tenant_isolation(setup_teacher_attendance_data):
    data = setup_teacher_attendance_data
    client = TestClient(app)
    headers_b = {"Authorization": f"Bearer {data['token_admin_b']}"}

    today_str = date.today().isoformat()
    res_b = client.get(f"/api/v1/teachers/attendance?attendance_date={today_str}", headers=headers_b)
    assert res_b.status_code == 200
    items_b = res_b.json()["data"]

    # Ensure School B admin does NOT see School A teachers
    teacher_a1_id = str(data["teacher_a1"].id)
    assert not any(item["teacher_id"] == teacher_a1_id for item in items_b)
