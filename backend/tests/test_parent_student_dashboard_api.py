import uuid
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.parent.parent import Parent
from app.models.attendance.attendance import Attendance
from app.models.fees.fee_structure import FeeStructure, FeeItem
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.common.enums.fees import FeeCategory, StudentFeeAssignmentStatus
from app.common.enums.attendance import AttendanceStatus
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_dashboard_test_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # School A
    school_a = School(
        name=f"Dashboard School A {s}", code=f"DSA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    # School B (for cross-tenant test)
    school_b = School(
        name=f"Dashboard School B {s}", code=f"DSB_{s}",
        address_line1="456 Other St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay = AcademicYear(school_id=school_a.id, name=f"2025-2026 {s}", start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True)
    db_session.add(ay)
    db_session.commit()

    term = AcademicTerm(school_id=school_a.id, academic_year_id=ay.id, name="Term 1", code=f"T1_{s}", start_date=date(2025, 6, 1), end_date=date(2025, 10, 31))
    db_session.add(term)
    db_session.commit()

    sc = SchoolClass(school_id=school_a.id, name="Grade 5", display_order=5)
    db_session.add(sc)
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="A")
    db_session.add(sec)
    db_session.commit()

    # Parent 1: Multi-child parent with 2 children (Child 1 & Child 2)
    p_multi = Parent(
        school_id=school_a.id, father_name="Multi Parent", primary_phone=f"9666{s[:6]}", email=f"multiparent_{s}@school.com",
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    # Parent 2: Unrelated parent with Child 3
    p_unrelated = Parent(
        school_id=school_a.id, father_name="Unrelated Parent", primary_phone=f"9555{s[:6]}", email=f"unrelated_{s}@school.com",
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    # Parent 3: Zero-child parent (no children linked)
    p_zero = Parent(
        school_id=school_a.id, father_name="Zero Parent", primary_phone=f"9444{s[:6]}", email=f"zero_{s}@school.com",
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([p_multi, p_unrelated, p_zero])
    db_session.commit()

    # Children
    c1 = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=p_multi.id,
        first_name="ChildOne", last_name="Multi", admission_number=f"ADM_C1_{s}", roll_number="101",
        gender="MALE", date_of_birth=date(2015, 1, 1), admission_date=date(2020, 6, 1),
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    c2 = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=p_multi.id,
        first_name="ChildTwo", last_name="Multi", admission_number=f"ADM_C2_{s}", roll_number="102",
        gender="FEMALE", date_of_birth=date(2016, 2, 1), admission_date=date(2021, 6, 1),
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    c3 = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=p_unrelated.id,
        first_name="ChildThree", last_name="Unrelated", admission_number=f"ADM_C3_{s}", roll_number="103",
        gender="MALE", date_of_birth=date(2015, 3, 1), admission_date=date(2020, 6, 1),
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([c1, c2, c3])
    db_session.commit()

    # Attendance for c1 (Present 2, Absent 1)
    att1 = Attendance(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, student_id=c1.id, attendance_date=date(2025, 9, 1), status=AttendanceStatus.PRESENT)
    att2 = Attendance(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, student_id=c1.id, attendance_date=date(2025, 9, 2), status=AttendanceStatus.PRESENT)
    att3 = Attendance(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, student_id=c1.id, attendance_date=date(2025, 9, 3), status=AttendanceStatus.ABSENT)
    db_session.add_all([att1, att2, att3])

    # Fee Assignment for c1
    fs = FeeStructure(school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, name="Term Fee")
    db_session.add(fs)
    db_session.commit()

    sfa = StudentFeeAssignment(
        school_id=school_a.id, academic_year_id=ay.id, student_id=c1.id, fee_structure_id=fs.id,
        status=StudentFeeAssignmentStatus.PENDING
    )
    db_session.add(sfa)
    db_session.commit()

    pwd = hash_password("Password@123")
    u_multi_parent = IdentityUser(email=p_multi.email, password_hash=pwd, school_id=school_a.id, first_name="Multi", last_name="Parent", phone=p_multi.primary_phone)
    u_zero_parent = IdentityUser(email=p_zero.email, password_hash=pwd, school_id=school_a.id, first_name="Zero", last_name="Parent", phone=p_zero.primary_phone)
    u_student1 = IdentityUser(email=f"c1_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="ChildOne", username=c1.admission_number)
    u_tenant_b = IdentityUser(email=f"tenant_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="TenantBUser")

    db_session.add_all([u_multi_parent, u_zero_parent, u_student1, u_tenant_b])
    db_session.commit()

    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()

    db_session.add_all([
        IdentityUserRole(user_id=u_multi_parent.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_zero_parent.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_student1.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_tenant_b.id, role_id=r_parent.id),
    ])
    db_session.commit()

    tok_multi_parent = jwt_manager.create_access_token(user_id=u_multi_parent.id, school_id=school_a.id)
    tok_zero_parent = jwt_manager.create_access_token(user_id=u_zero_parent.id, school_id=school_a.id)
    tok_student1 = jwt_manager.create_access_token(user_id=u_student1.id, school_id=school_a.id)
    tok_tenant_b = jwt_manager.create_access_token(user_id=u_tenant_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "c1": c1, "c2": c2, "c3": c3,
        "tok_multi_parent": tok_multi_parent, "tok_zero_parent": tok_zero_parent,
        "tok_student1": tok_student1, "tok_tenant_b": tok_tenant_b,
    }


def test_01_parent_dashboard_multi_child_default(client: TestClient, setup_dashboard_test_data):
    d = setup_dashboard_test_data
    res = client.get("/api/v1/dashboard/parent/summary", headers={"Authorization": f"Bearer {d['tok_multi_parent']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["zero_child_state"] is False
    assert len(data["children"]) == 2
    assert data["selected_child_id"] == str(d["c1"].id)
    assert data["attendance_summary"]["total_days"] == 3
    assert data["attendance_summary"]["present_days"] == 2
    assert data["attendance_summary"]["absent_days"] == 1


def test_02_parent_dashboard_multi_child_switching(client: TestClient, setup_dashboard_test_data):
    d = setup_dashboard_test_data
    # Request child 2 specifically
    res = client.get(f"/api/v1/dashboard/parent/summary?student_id={d['c2'].id}", headers={"Authorization": f"Bearer {d['tok_multi_parent']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["selected_child_id"] == str(d["c2"].id)
    assert data["attendance_summary"]["total_days"] == 0  # c2 has 0 attendance records


def test_03_parent_dashboard_idor_blocked(client: TestClient, setup_dashboard_test_data):
    d = setup_dashboard_test_data
    # Parent tries to pass c3 (unrelated child belonging to Parent 2)
    res = client.get(f"/api/v1/dashboard/parent/summary?student_id={d['c3'].id}", headers={"Authorization": f"Bearer {d['tok_multi_parent']}"})
    assert res.status_code == 403


def test_04_parent_dashboard_zero_child(client: TestClient, setup_dashboard_test_data):
    d = setup_dashboard_test_data
    res = client.get("/api/v1/dashboard/parent/summary", headers={"Authorization": f"Bearer {d['tok_zero_parent']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["zero_child_state"] is True
    assert data["children"] == []
    assert data["selected_child_id"] is None


def test_05_student_dashboard_self_access(client: TestClient, setup_dashboard_test_data):
    d = setup_dashboard_test_data
    res = client.get("/api/v1/dashboard/student/summary", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["student_info"]["id"] == str(d["c1"].id)
    assert data["attendance_summary"]["total_days"] == 3


def test_06_cross_tenant_dashboard_isolation(client: TestClient, setup_dashboard_test_data):
    d = setup_dashboard_test_data
    # Tenant B parent tries to pass Tenant A child ID
    res = client.get(f"/api/v1/dashboard/parent/summary?student_id={d['c1'].id}", headers={"Authorization": f"Bearer {d['tok_tenant_b']}"})
    assert res.status_code == 403
