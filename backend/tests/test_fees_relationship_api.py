"""
Relationship Security Tests for Fees & Financial Data API Endpoints (SEC-005B).
Tests HTTP route authorization for:
- GET /api/v1/fees/assignments
- GET /api/v1/fees/assignments/{assignment_id}
- GET /api/v1/fees/payments/{payment_id}
- GET /api/v1/fees/payments/{payment_id}/receipt
- GET /api/v1/export/fees
"""
import uuid
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.fees import FeeCategory, FeeStructureStatus, PaymentMode, StudentFeeAssignmentStatus
from app.common.enums.parent import ParentRelationship
from app.identity.models import IdentityRole, IdentityRolePermission, IdentityUser, IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import StudentFeeAssignment, StudentFeeItem
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.main import app


def create_role_with_permissions(db, school_id, role_name, permission_names):
    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_id,
        name=role_name,
        description=f"{role_name} test role",
        is_system=True,
    )
    db.add(role)
    db.commit()

    for perm_name in permission_names:
        from app.identity.repositories import permission_repository
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()
    return role


def create_user_and_auth_headers(db, school_id, email, role, username=None, phone=None):
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_id,
        email=email,
        username=username,
        phone=phone,
        password_hash="hash123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school_id)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def fees_fixture(db_session):
    db = db_session
    from app.identity.seeders import seed_identity
    seed_identity(db)
    school = School(
        id=uuid.uuid4(),
        name=f"School_{uuid.uuid4().hex[:6]}",
        code=f"SCH_{uuid.uuid4().hex[:4]}",
        address_line1="100 Fee St",
        city="City",
        district="Dist",
        state="State",
        country="India",
        postal_code="110001",
    )
    school2 = School(
        id=uuid.uuid4(),
        name=f"School2_{uuid.uuid4().hex[:6]}",
        code=f"SCH2_{uuid.uuid4().hex[:4]}",
        address_line1="200 Fee St",
        city="City2",
        district="Dist2",
        state="State2",
        country="India",
        postal_code="110002",
    )
    db.add_all([school, school2])
    db.commit()

    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="AY 2026",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    sclass = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 10",
        display_order=1,
    )
    section = Section(
        id=uuid.uuid4(),
        school_class_id=sclass.id,
        name="A",
    )
    db.add_all([ay, sclass, section])
    db.commit()

    # Parents
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Father A",
        email=f"parent_a_{uuid.uuid4().hex[:6]}@example.com",
        primary_phone=f"999{uuid.uuid4().hex[:7]}",
        address_line1="123 Main St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Father B",
        email=f"parent_b_{uuid.uuid4().hex[:6]}@example.com",
        primary_phone=f"888{uuid.uuid4().hex[:7]}",
        address_line1="123 Main St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    parent_zero = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Father Zero",
        email=f"parent_zero_{uuid.uuid4().hex[:6]}@example.com",
        primary_phone=f"777{uuid.uuid4().hex[:7]}",
        address_line1="123 Main St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    db.add_all([parent_a, parent_b, parent_zero])
    db.commit()

    # Students
    stu_1 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        parent_id=parent_a.id,
        school_class_id=sclass.id,
        section_id=section.id,
        first_name="Child1",
        last_name="A",
        admission_number=f"ADM1_{uuid.uuid4().hex[:4]}",
        admission_date=date(2025, 4, 1),
        roll_number="101",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        status=StudentStatus.ACTIVE,
        email=f"stu1_{uuid.uuid4().hex[:6]}@school.com",
        address_line1="123 Main St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    stu_2 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        parent_id=parent_a.id,
        school_class_id=sclass.id,
        section_id=section.id,
        first_name="Child2",
        last_name="A",
        admission_number=f"ADM2_{uuid.uuid4().hex[:4]}",
        admission_date=date(2025, 4, 1),
        roll_number="102",
        gender=Gender.FEMALE,
        date_of_birth=date(2011, 2, 2),
        status=StudentStatus.ACTIVE,
        email=f"stu2_{uuid.uuid4().hex[:6]}@school.com",
        address_line1="123 Main St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    stu_b = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        parent_id=parent_b.id,
        school_class_id=sclass.id,
        section_id=section.id,
        first_name="Child",
        last_name="B",
        admission_number=f"ADMB_{uuid.uuid4().hex[:4]}",
        admission_date=date(2025, 4, 1),
        roll_number="103",
        gender=Gender.MALE,
        date_of_birth=date(2010, 5, 5),
        status=StudentStatus.ACTIVE,
        email=f"stub_{uuid.uuid4().hex[:6]}@school.com",
        address_line1="123 Main St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    db.add_all([stu_1, stu_2, stu_b])
    db.commit()

    # Fee Structure
    structure = FeeStructure(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        name="Tuition Fee Structure",
        description="Standard Fee Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    fee_item = FeeItem(
        id=uuid.uuid4(),
        fee_structure_id=structure.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("5000.00"),
        is_optional=False,
    )
    structure.items.append(fee_item)
    db.add(structure)
    db.commit()

    # Fee Assignments
    assign_1 = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=stu_1.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 6, 1),
    )
    assign_1_item = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assign_1.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("5000.00"),
    )
    assign_1.student_fee_items.append(assign_1_item)

    assign_2 = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=stu_2.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 6, 1),
    )
    assign_2_item = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assign_2.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("5000.00"),
    )
    assign_2.student_fee_items.append(assign_2_item)

    assign_b = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=stu_b.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 6, 1),
    )
    assign_b_item = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assign_b.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("5000.00"),
    )
    assign_b.student_fee_items.append(assign_b_item)

    db.add_all([assign_1, assign_2, assign_b])
    db.commit()

    # Fee Payments
    pay_1 = FeePayment(
        id=uuid.uuid4(),
        school_id=school.id,
        student_fee_assignment_id=assign_1.id,
        receipt_number="REC-1001",
        amount=Decimal("2500.00"),
        payment_date=date(2026, 5, 10),
        payment_mode=PaymentMode.CASH,
        reference_number="REF1001",
    )
    pay_b = FeePayment(
        id=uuid.uuid4(),
        school_id=school.id,
        student_fee_assignment_id=assign_b.id,
        receipt_number="REC-1002",
        amount=Decimal("5000.00"),
        payment_date=date(2026, 5, 12),
        payment_mode=PaymentMode.UPI,
        reference_number="REF1002",
    )
    db.add_all([pay_1, pay_b])
    db.commit()

    # Roles
    parent_role = create_role_with_permissions(db, school.id, "Parent", ["fees.view", "fees.export"])
    student_role = create_role_with_permissions(db, school.id, "Student", ["fees.view", "fees.export"])
    accountant_role = create_role_with_permissions(db, school.id, "Accountant", ["fees.view", "fees.create", "fees.update", "fees.delete", "fees.export"])
    admin_role = create_role_with_permissions(db, school.id, "School Admin", ["fees.view", "fees.create", "fees.update", "fees.delete", "fees.export"])
    principal_role = create_role_with_permissions(db, school.id, "Principal", ["fees.view", "fees.create", "fees.update", "fees.delete", "fees.export"])

    # Users
    user_parent_a, headers_parent_a = create_user_and_auth_headers(db, school.id, parent_a.email, parent_role)
    user_parent_b, headers_parent_b = create_user_and_auth_headers(db, school.id, parent_b.email, parent_role)
    user_parent_zero, headers_parent_zero = create_user_and_auth_headers(db, school.id, parent_zero.email, parent_role)

    user_stu_1, headers_stu_1 = create_user_and_auth_headers(db, school.id, stu_1.email, student_role, username=stu_1.admission_number)
    user_stu_b, headers_stu_b = create_user_and_auth_headers(db, school.id, stu_b.email, student_role, username=stu_b.admission_number)

    user_acct, headers_acct = create_user_and_auth_headers(db, school.id, f"acct_{uuid.uuid4().hex[:6]}@school.com", accountant_role)
    user_admin, headers_admin = create_user_and_auth_headers(db, school.id, f"admin_{uuid.uuid4().hex[:6]}@school.com", admin_role)
    user_princ, headers_princ = create_user_and_auth_headers(db, school.id, f"princ_{uuid.uuid4().hex[:6]}@school.com", principal_role)

    super_admin_role = create_role_with_permissions(db, school.id, "Super Admin", ["fees.view", "fees.create", "fees.update", "fees.delete", "fees.export"])
    super_admin_user, headers_super = create_user_and_auth_headers(db, school.id, f"super_{uuid.uuid4().hex[:6]}@system.com", super_admin_role)

    return {
        "school": school,
        "school2": school2,
        "parent_a": parent_a,
        "parent_b": parent_b,
        "stu_1": stu_1,
        "stu_2": stu_2,
        "stu_b": stu_b,
        "assign_1": assign_1,
        "assign_2": assign_2,
        "assign_b": assign_b,
        "pay_1": pay_1,
        "pay_b": pay_b,
        "headers_parent_a": headers_parent_a,
        "headers_parent_b": headers_parent_b,
        "headers_parent_zero": headers_parent_zero,
        "headers_stu_1": headers_stu_1,
        "headers_stu_b": headers_stu_b,
        "headers_acct": headers_acct,
        "headers_admin": headers_admin,
        "headers_princ": headers_princ,
        "headers_super": headers_super,
    }


# ============================================================================
# Fee Assignments Tests
# ============================================================================

def test_parent_list_linked_child_fee_assignments(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    data = res.json()
    returned_ids = [item["student_id"] for item in data["items"]]
    assert str(fees_fixture["stu_1"].id) in returned_ids
    assert str(fees_fixture["stu_2"].id) in returned_ids
    assert str(fees_fixture["stu_b"].id) not in returned_ids


def test_parent_cannot_list_other_parent_fee_assignments(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_parent_b"])
    assert res.status_code == 200
    data = res.json()
    returned_ids = [item["student_id"] for item in data["items"]]
    assert str(fees_fixture["stu_b"].id) in returned_ids
    assert str(fees_fixture["stu_1"].id) not in returned_ids
    assert str(fees_fixture["stu_2"].id) not in returned_ids


def test_parent_cannot_tamper_student_id_query(client, fees_fixture):
    # Parent A requests Student B's ID via query param
    res = client.get(f"/api/v1/fees/assignments?student_id={fees_fixture['stu_b'].id}", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 403


def test_parent_access_own_child_assignment_detail(client, fees_fixture):
    res = client.get(f"/api/v1/fees/assignments/{fees_fixture['assign_1'].id}", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    assert res.json()["id"] == str(fees_fixture["assign_1"].id)


def test_parent_cannot_access_other_child_assignment_detail(client, fees_fixture):
    res = client.get(f"/api/v1/fees/assignments/{fees_fixture['assign_b'].id}", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 403


def test_student_list_own_fee_assignment(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 200
    data = res.json()
    returned_ids = [item["student_id"] for item in data["items"]]
    assert returned_ids == [str(fees_fixture["stu_1"].id)]


def test_student_cannot_list_other_student_assignment(client, fees_fixture):
    res = client.get(f"/api/v1/fees/assignments?student_id={fees_fixture['stu_b'].id}", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 403


def test_student_access_own_assignment_detail(client, fees_fixture):
    res = client.get(f"/api/v1/fees/assignments/{fees_fixture['assign_1'].id}", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 200
    assert res.json()["id"] == str(fees_fixture["assign_1"].id)


def test_student_cannot_access_other_student_assignment_detail(client, fees_fixture):
    res = client.get(f"/api/v1/fees/assignments/{fees_fixture['assign_b'].id}", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 403


def test_cross_tenant_assignment_access_denied(client, db_session, fees_fixture):
    db = db_session
    # Create user in School 2
    role2 = create_role_with_permissions(db, fees_fixture["school2"].id, "Parent", ["fees.view"])
    _, headers2 = create_user_and_auth_headers(db, fees_fixture["school2"].id, "parent2@school2.com", role2)

    res = client.get(f"/api/v1/fees/assignments/{fees_fixture['assign_1'].id}", headers=headers2)
    assert res.status_code == 404


def test_parent_with_multiple_children_sees_all_linked_children(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    assert res.json()["total"] == 2


def test_parent_with_zero_children_receives_empty_assignment_list(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_parent_zero"])
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert res.json()["items"] == []


# ============================================================================
# Fee Payments Tests
# ============================================================================

def test_parent_access_linked_child_payment(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_1'].id}", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    assert res.json()["id"] == str(fees_fixture["pay_1"].id)


def test_parent_cannot_access_other_child_payment(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_b'].id}", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 403


def test_student_access_own_payment(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_1'].id}", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 200
    assert res.json()["id"] == str(fees_fixture["pay_1"].id)


def test_student_cannot_access_other_student_payment(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_b'].id}", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 403


def test_cross_tenant_payment_access_denied(client, db_session, fees_fixture):
    db = db_session
    role2 = create_role_with_permissions(db, fees_fixture["school2"].id, "Parent", ["fees.view"])
    _, headers2 = create_user_and_auth_headers(db, fees_fixture["school2"].id, "parent2_pay@school2.com", role2)

    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_1'].id}", headers=headers2)
    assert res.status_code == 404


# ============================================================================
# Receipts Tests
# ============================================================================

def test_parent_retrieve_linked_child_receipt(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_1'].id}/receipt", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    assert res.json()["receipt_number"] == "REC-1001"


def test_parent_cannot_retrieve_other_child_receipt(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_b'].id}/receipt", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 403


def test_student_retrieve_own_receipt(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_1'].id}/receipt", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 200
    assert res.json()["receipt_number"] == "REC-1001"


def test_student_cannot_retrieve_other_student_receipt(client, fees_fixture):
    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_b'].id}/receipt", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 403


def test_cross_tenant_receipt_access_denied(client, db_session, fees_fixture):
    db = db_session
    role2 = create_role_with_permissions(db, fees_fixture["school2"].id, "Parent", ["fees.view"])
    _, headers2 = create_user_and_auth_headers(db, fees_fixture["school2"].id, "parent2_rec@school2.com", role2)

    res = client.get(f"/api/v1/fees/payments/{fees_fixture['pay_1'].id}/receipt", headers=headers2)
    assert res.status_code == 404


# ============================================================================
# Export Tests
# ============================================================================

def test_parent_fee_export_contains_only_linked_children(client, fees_fixture):
    res = client.get("/api/v1/export/fees", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    content = res.text
    assert "REC-1001" in content
    assert "REC-1002" not in content


def test_student_fee_export_contains_only_self(client, fees_fixture):
    res = client.get("/api/v1/export/fees", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 200
    content = res.text
    assert "REC-1001" in content
    assert "REC-1002" not in content


def test_parent_export_query_tampering_prevented(client, fees_fixture):
    res = client.get(f"/api/v1/export/fees?student_id={fees_fixture['stu_b'].id}", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    content = res.text
    assert "REC-1002" not in content


def test_student_export_query_tampering_prevented(client, fees_fixture):
    res = client.get(f"/api/v1/export/fees?student_id={fees_fixture['stu_b'].id}", headers=fees_fixture["headers_stu_1"])
    assert res.status_code == 200
    content = res.text
    assert "REC-1002" not in content


def test_parent_zero_children_gets_empty_export(client, fees_fixture):
    res = client.get("/api/v1/export/fees", headers=fees_fixture["headers_parent_zero"])
    assert res.status_code == 200
    lines = [line for line in res.text.strip().split("\n") if line]
    # Should only contain header line or empty content
    assert len(lines) <= 1


def test_multi_child_parent_export_contains_all_linked_children(client, fees_fixture):
    res = client.get("/api/v1/export/fees", headers=fees_fixture["headers_parent_a"])
    assert res.status_code == 200
    assert "REC-1001" in res.text


# ============================================================================
# Staff & Regression Tests
# ============================================================================

def test_accountant_fee_access_remains_functional(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_acct"])
    assert res.status_code == 200
    assert res.json()["total"] == 3


def test_admin_fee_access_remains_functional(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_admin"])
    assert res.status_code == 200
    assert res.json()["total"] == 3


def test_principal_fee_access_remains_functional(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_princ"])
    assert res.status_code == 200
    assert res.json()["total"] == 3


def test_super_admin_behavior_remains_functional(client, fees_fixture):
    res = client.get("/api/v1/fees/assignments", headers=fees_fixture["headers_super"])
    assert res.status_code == 200
    assert res.json()["total"] == 3
