import uuid
from decimal import Decimal
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums.fees import FeeCategory, PaymentMode, StudentFeeAssignmentStatus
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.parent.parent import Parent
from app.models.fees.fee_structure import FeeStructure, FeeItem
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.fees.fee_payment import FeePayment
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_cash_reconciliation_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    school_a = School(
        name=f"Cash School A {s}", code=f"CSA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(school_a)
    db_session.commit()

    ay = AcademicYear(school_id=school_a.id, name=f"2025-2026 {s}", start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True)
    sc = SchoolClass(school_id=school_a.id, name="Grade 1", display_order=1)
    db_session.add(sc)
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="A")
    db_session.add_all([ay, sec])
    db_session.commit()

    p = Parent(
        school_id=school_a.id, father_name="Father Cash", primary_phone=f"9777{s[:6]}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(p)
    db_session.commit()

    st = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=p.id,
        first_name="CashStudent", last_name="User", admission_number=f"ADM_C_{s}", roll_number="101",
        gender="MALE", date_of_birth=date(2015, 1, 1), admission_date=date(2020, 6, 1),
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(st)
    db_session.commit()

    fs = FeeStructure(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, name="Term Fee")
    db_session.add(fs)
    db_session.commit()

    item = FeeItem(fee_structure_id=fs.id, category=FeeCategory.TUITION, name="Tuition", amount=Decimal("5000.00"))
    db_session.add(item)
    db_session.commit()

    sfa = StudentFeeAssignment(
        school_id=school_a.id, academic_year_id=ay.id, student_id=st.id, fee_structure_id=fs.id,
        status=StudentFeeAssignmentStatus.PARTIALLY_PAID
    )
    db_session.add(sfa)
    db_session.commit()

    # Payments: 2000 CASH, 1000 UPI
    p_cash = FeePayment(
        school_id=school_a.id, student_fee_assignment_id=sfa.id, receipt_number=f"REC_CASH_{s}",
        amount=Decimal("2000.00"), payment_date=date.today(), payment_mode=PaymentMode.CASH
    )
    p_upi = FeePayment(
        school_id=school_a.id, student_fee_assignment_id=sfa.id, receipt_number=f"REC_UPI_{s}",
        amount=Decimal("1000.00"), payment_date=date.today(), payment_mode=PaymentMode.UPI
    )
    db_session.add_all([p_cash, p_upi])
    db_session.commit()

    pwd = hash_password("Password@123")
    u_acc = IdentityUser(email=f"accountant_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Accountant")
    u_teacher = IdentityUser(email=f"teacher_cash_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Teacher")
    u_parent = IdentityUser(email=f"parent_cash_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent")

    db_session.add_all([u_acc, u_teacher, u_parent])
    db_session.commit()

    r_acc = db_session.query(IdentityRole).filter_by(name="Accountant").first()
    r_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()

    db_session.add_all([
        IdentityUserRole(user_id=u_acc.id, role_id=r_acc.id),
        IdentityUserRole(user_id=u_teacher.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_parent.id, role_id=r_parent.id),
    ])
    db_session.commit()

    tok_acc = jwt_manager.create_access_token(user_id=u_acc.id, school_id=school_a.id)
    tok_teacher = jwt_manager.create_access_token(user_id=u_teacher.id, school_id=school_a.id)
    tok_parent = jwt_manager.create_access_token(user_id=u_parent.id, school_id=school_a.id)

    return {
        "school_a": school_a, "sfa": sfa,
        "tok_acc": tok_acc, "tok_teacher": tok_teacher, "tok_parent": tok_parent,
    }


def test_01_open_and_get_active_cash_session(client: TestClient, setup_cash_reconciliation_data):
    d = setup_cash_reconciliation_data
    payload = {"opening_balance": "500.00"}
    res_open = client.post("/api/v1/fees/cash-drawer/open", json=payload, headers={"Authorization": f"Bearer {d['tok_acc']}"})
    assert res_open.status_code == 201
    data = res_open.json()
    assert data["status"] == "OPEN"
    assert float(data["opening_balance"]) == 500.0
    assert float(data["expected_cash_collected"]) == 2000.0
    assert float(data["expected_non_cash_collected"]) == 1000.0
    assert float(data["expected_total_cash"]) == 2500.0  # 500 + 2000

    res_active = client.get("/api/v1/fees/cash-drawer/active", headers={"Authorization": f"Bearer {d['tok_acc']}"})
    assert res_active.status_code == 200
    assert res_active.json()["status"] == "OPEN"


def test_02_close_cash_session_and_compute_variance(client: TestClient, setup_cash_reconciliation_data):
    d = setup_cash_reconciliation_data
    client.post("/api/v1/fees/cash-drawer/open", json={"opening_balance": "500.00"}, headers={"Authorization": f"Bearer {d['tok_acc']}"})
    active_res = client.get("/api/v1/fees/cash-drawer/active", headers={"Authorization": f"Bearer {d['tok_acc']}"})
    session_id = active_res.json()["id"]

    # Close with counted cash = 2500 (zero variance)
    res_close = client.post(f"/api/v1/fees/cash-drawer/{session_id}/close", json={"actual_counted_cash": "2500.00", "notes": "Balanced"}, headers={"Authorization": f"Bearer {d['tok_acc']}"})
    assert res_close.status_code == 200
    data = res_close.json()
    assert data["status"] == "CLOSED"
    assert float(data["variance"]) == 0.0

    # Repeat close fails
    res_reclose = client.post(f"/api/v1/fees/cash-drawer/{session_id}/close", json={"actual_counted_cash": "2500.00"}, headers={"Authorization": f"Bearer {d['tok_acc']}"})
    assert res_reclose.status_code == 422


def test_03_unauthorized_users_cannot_access_cash_drawer(client: TestClient, setup_cash_reconciliation_data):
    d = setup_cash_reconciliation_data
    res_t = client.post("/api/v1/fees/cash-drawer/open", json={"opening_balance": "100.00"}, headers={"Authorization": f"Bearer {d['tok_teacher']}"})
    assert res_t.status_code == 403

    res_p = client.get("/api/v1/fees/cash-drawer/active", headers={"Authorization": f"Bearer {d['tok_parent']}"})
    assert res_p.status_code == 403
