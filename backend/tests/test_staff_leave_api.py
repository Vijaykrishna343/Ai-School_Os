import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.teacher.teacher import Teacher
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.services.staff_leave_service import staff_leave_service


def test_staff_leave_lifecycle_api(client: TestClient, db_session: Session):
    seed_identity(db_session)

    # 1. Setup School, Academic Year, Admin User and Teacher User
    school = School(
        name="Staff Leave Test School",
        code=f"SLS-{uuid.uuid4().hex[:4]}",
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

    # Teacher user & model
    teacher_user = IdentityUser(
        school_id=school.id,
        email="teacher_leave@school.com",
        password_hash="hash",
        first_name="Jane",
        last_name="Doe",
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
        first_name="Jane",
        last_name="Doe",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 6, 1),
        qualification="M.Ed",
        phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        email=f"teacher_leave_{uuid.uuid4().hex[:6]}@school.com",
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        address_line1="123 Staff St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(teacher)
    db_session.commit()

    # Admin user
    admin_user = IdentityUser(
        school_id=school.id,
        email="admin_leave@school.com",
        password_hash="hash",
        first_name="Principal",
        last_name="Admin",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_user)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.commit()

    t_token = jwt_manager.create_access_token(user_id=teacher_user.id, school_id=school.id)
    t_headers = {"Authorization": f"Bearer {t_token}"}

    a_token = jwt_manager.create_access_token(user_id=admin_user.id, school_id=school.id)
    a_headers = {"Authorization": f"Bearer {a_token}"}

    # 2. Get Leave Types (seeds default)
    res_types = client.get("/api/v1/staff-leave/types", headers=t_headers)
    assert res_types.status_code == 200
    types = res_types.json()["data"]
    assert len(types) >= 5
    casual_type = next(t for t in types if t["code"] == "CASUAL")

    # 3. Get Teacher Balances
    res_bal = client.get(f"/api/v1/staff-leave/balance?academic_year_id={ay.id}", headers=t_headers)
    assert res_bal.status_code == 200
    balances = res_bal.json()["data"]
    casual_bal = next(b for b in balances if b["leave_type_code"] == "CASUAL")
    assert float(casual_bal["remaining_days"]) == 12.0

    # 4. Submit Leave Request (2 days)
    start_d = date.today() + timedelta(days=5)
    end_d = start_d + timedelta(days=1)
    res_sub = client.post(
        "/api/v1/staff-leave",
        headers=t_headers,
        json={
            "academic_year_id": str(ay.id),
            "leave_type_id": casual_type["id"],
            "start_date": start_d.isoformat(),
            "end_date": end_d.isoformat(),
            "half_day_type": "FULL_DAY",
            "reason": "Personal medical appointment",
        },
    )
    assert res_sub.status_code == 201
    req_data = res_sub.json()["data"]
    req_id = req_data["id"]
    assert req_data["status"] == "PENDING"
    assert float(req_data["requested_days"]) == 2.0

    # 5. Admin Approves Request
    res_app = client.post(
        f"/api/v1/staff-leave/{req_id}/approve",
        headers=a_headers,
        json={"remarks": "Approved by Principal"},
    )
    assert res_app.status_code == 200
    app_data = res_app.json()["data"]
    assert app_data["status"] == "APPROVED"

    # 6. Verify Updated Balance
    res_bal2 = client.get(f"/api/v1/staff-leave/balance?academic_year_id={ay.id}", headers=t_headers)
    casual_bal2 = next(b for b in res_bal2.json()["data"] if b["leave_type_code"] == "CASUAL")
    assert float(casual_bal2["used_days"]) == 2.0
    assert float(casual_bal2["remaining_days"]) == 10.0

    # 7. Summary Report Verification
    res_rep = client.get(f"/api/v1/staff-leave/reports/summary?academic_year_id={ay.id}", headers=a_headers)
    assert res_rep.status_code == 200
    rep = res_rep.json()["data"]
    assert rep["total_requests"] >= 1
