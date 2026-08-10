import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.parent import ParentRelationship
from app.identity.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.academic_year.academic_year import AcademicYear
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student


def create_school_and_user(db, school_name, school_code, permissions_list):
    """
    Helper to seed identity, create school, role, user, and return auth headers.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Fee Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Test Fees Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(
                role_id=role.id,
                permission_id=perm.id,
            )
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"user_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Pass123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


def setup_fee_fixture_data(db, school):
    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"AY-{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay)

    sc = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Class-{uuid.uuid4().hex[:4]}",
        display_order=1,
    )
    db.add(sc)
    db.commit()

    sec = Section(
        id=uuid.uuid4(),
        school_class_id=sc.id,
        name="Section A",
    )
    db.add(sec)

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Parent User",
        primary_phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        relationship=ParentRelationship.FATHER,
        address_line1="100 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()

    student = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        parent_id=parent.id,
        admission_number=f"ADM_{uuid.uuid4().hex[:6]}",
        roll_number=f"R_{uuid.uuid4().hex[:4]}",
        first_name="Alice",
        last_name="Smith",
        gender=Gender.FEMALE,
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2026, 4, 1),
        address_line1="100 Student St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    db.add(student)
    db.commit()
    db.refresh(ay)
    db.refresh(sc)
    db.refresh(student)

    return ay, sc, student


# ------------------------------------------------------------------
# 1. Authentication & RBAC Tests
# ------------------------------------------------------------------


def test_fees_api_anonymous_rejected(client: TestClient):
    response = client.get("/api/v1/fees/structures")
    assert response.status_code == 401


def test_fees_api_rbac_permissions(client: TestClient, db_session):
    school, user, headers_view_only = create_school_and_user(
        db_session, "RBAC School", "RBC1", ["fees.view"]
    )
    ay, sc, student = setup_fee_fixture_data(db_session, school)

    # Missing fees.create -> 403 Forbidden
    payload = {
        "academic_year_id": str(ay.id),
        "name": "Fee Structure 1",
        "items": [],
    }
    response = client.post("/api/v1/fees/structures", json=payload, headers=headers_view_only)
    assert response.status_code == 403

    # User with full fees permissions
    school_full, _, headers_full = create_school_and_user(
        db_session, "Full Perm School", "FPS1",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )
    ay_full, _, _ = setup_fee_fixture_data(db_session, school_full)

    payload_full = {
        "academic_year_id": str(ay_full.id),
        "name": "Fee Structure Full",
        "items": [],
    }
    res_create = client.post("/api/v1/fees/structures", json=payload_full, headers=headers_full)
    assert res_create.status_code == 201


# ------------------------------------------------------------------
# 2. Tenant Isolation Tests
# ------------------------------------------------------------------


def test_fees_api_tenant_isolation(client: TestClient, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "School A", "SCHA",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "School B", "SCHB",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )

    ay_a, _, _ = setup_fee_fixture_data(db_session, school_a)
    ay_b, _, _ = setup_fee_fixture_data(db_session, school_b)

    # Create structure in School A
    res_a = client.post(
        "/api/v1/fees/structures",
        json={
            "academic_year_id": str(ay_a.id),
            "name": "School A Fees",
            "items": [],
        },
        headers=headers_a,
    )
    assert res_a.status_code == 201
    struct_a_id = res_a.json()["id"]

    # User B attempting to access School A's structure -> 404 Not Found (scoped by user's school)
    res_get_b = client.get(f"/api/v1/fees/structures/{struct_a_id}", headers=headers_b)
    assert res_get_b.status_code == 404

    # User B attempting to override school_id query parameter cannot see School A's structures
    res_list_b = client.get(
        f"/api/v1/fees/structures?school_id={school_a.id}",
        headers=headers_b,
    )
    assert res_list_b.status_code == 200
    b_items = res_list_b.json()["items"]
    assert len(b_items) == 0  # Strictly isolated to User B's school!


# ------------------------------------------------------------------
# 3. Fee Structure CRUD & Validations
# ------------------------------------------------------------------


def test_fees_structure_crud_and_validations(client: TestClient, db_session):
    school, user, headers = create_school_and_user(
        db_session, "CRUD School", "CRD1",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )
    ay, sc, _ = setup_fee_fixture_data(db_session, school)

    # 1. Create Structure with items
    create_payload = {
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "name": "Class 1 Annual Fees",
        "description": "Tuition and Books",
        "status": "ACTIVE",
        "items": [
            {
                "category": "TUITION",
                "name": "Tuition Fee",
                "amount": 15000.00,
                "is_optional": False,
                "order": 1,
            },
            {
                "category": "BOOKS",
                "name": "Books & Notebooks",
                "amount": 3000.00,
                "is_optional": True,
                "order": 2,
            },
        ],
    }
    res_create = client.post("/api/v1/fees/structures", json=create_payload, headers=headers)
    assert res_create.status_code == 201
    struct_data = res_create.json()
    struct_id = struct_data["id"]
    assert struct_data["name"] == "Class 1 Annual Fees"
    assert len(struct_data["items"]) == 2

    # Duplicate active name rejection
    res_dup = client.post("/api/v1/fees/structures", json=create_payload, headers=headers)
    assert res_dup.status_code in (400, 409, 422)

    # 2. Get Structure
    res_get = client.get(f"/api/v1/fees/structures/{struct_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == struct_id

    # 3. List Structures (Pagination)
    res_list = client.get("/api/v1/fees/structures?page=1&page_size=10", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] == 1

    # 4. Update Structure
    update_payload = {
        "name": "Class 1 Annual Fees Updated",
        "description": "Updated description",
    }
    res_update = client.put(f"/api/v1/fees/structures/{struct_id}", json=update_payload, headers=headers)
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Class 1 Annual Fees Updated"

    # 5. Soft Delete Structure
    res_delete = client.delete(f"/api/v1/fees/structures/{struct_id}", headers=headers)
    assert res_delete.status_code == 204

    # Deleted structure not returned in GET
    res_get_deleted = client.get(f"/api/v1/fees/structures/{struct_id}", headers=headers)
    assert res_get_deleted.status_code == 404


# ------------------------------------------------------------------
# 4. Student Assignment & Financial Calculations API
# ------------------------------------------------------------------


def test_student_assignment_and_payments_flow(client: TestClient, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Payment Flow School", "PFS1",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )
    ay, sc, student = setup_fee_fixture_data(db_session, school)

    # Create Fee Structure
    res_struct = client.post(
        "/api/v1/fees/structures",
        json={
            "academic_year_id": str(ay.id),
            "school_class_id": str(sc.id),
            "name": "Standard Fee Structure",
            "status": "ACTIVE",
            "items": [
                {
                    "category": "TUITION",
                    "name": "Tuition",
                    "amount": 20000.00,
                    "is_optional": False,
                },
                {
                    "category": "EXAMINATION",
                    "name": "Exam Fee",
                    "amount": 2000.00,
                    "is_optional": False,
                },
            ],
        },
        headers=headers,
    )
    struct_id = res_struct.json()["id"]

    # 1. Assign to Student
    res_assign = client.post(
        "/api/v1/fees/assignments",
        json={
            "academic_year_id": str(ay.id),
            "student_id": str(student.id),
            "fee_structure_id": struct_id,
            "due_date": "2026-07-31",
        },
        headers=headers,
    )
    assert res_assign.status_code == 201
    assign_data = res_assign.json()
    assign_id = assign_data["id"]
    assert float(assign_data["gross_amount"]) == 22000.00
    assert float(assign_data["net_payable"]) == 22000.00
    assert float(assign_data["outstanding_due"]) == 22000.00
    assert assign_data["status"] == "PENDING"

    # 2. Add Custom Student Item (Transportation)
    res_custom_item = client.post(
        f"/api/v1/fees/assignments/{assign_id}/items",
        json={
            "category": "TRANSPORTATION",
            "name": "Route 1 Bus Fee",
            "amount": 5000.00,
            "is_optional": True,
            "is_applicable": True,
        },
        headers=headers,
    )
    assert res_custom_item.status_code == 201
    updated_assign_1 = res_custom_item.json()
    assert float(updated_assign_1["gross_amount"]) == 27000.00

    # 3. Apply Concession/Discount
    res_discount = client.post(
        f"/api/v1/fees/assignments/{assign_id}/discounts",
        json={
            "discount_type": "SCHOLARSHIP",
            "name": "Merit Scholarship",
            "amount": 7000.00,
        },
        headers=headers,
    )
    assert res_discount.status_code == 201
    updated_assign_2 = res_discount.json()
    assert float(updated_assign_2["total_discounts"]) == 7000.00
    assert float(updated_assign_2["net_payable"]) == 20000.00
    assert float(updated_assign_2["outstanding_due"]) == 20000.00

    # Discount greater than gross amount rejected
    res_huge_discount = client.post(
        f"/api/v1/fees/assignments/{assign_id}/discounts",
        json={
            "discount_type": "SPECIAL_DISCOUNT",
            "name": "Huge Concession",
            "amount": 30000.00,
        },
        headers=headers,
    )
    assert res_huge_discount.status_code in (400, 422)

    # 4. Record Partial Payment
    res_pay1 = client.post(
        "/api/v1/fees/payments",
        json={
            "student_fee_assignment_id": assign_id,
            "amount": 8000.00,
            "payment_date": "2026-06-15",
            "payment_mode": "UPI",
            "reference_number": "TXN_UPI_999",
        },
        headers=headers,
    )
    assert res_pay1.status_code == 201
    pay1_data = res_pay1.json()
    pay1_id = pay1_data["id"]
    assert pay1_data["receipt_number"].startswith("REC-")

    # Verify assignment status updated to PARTIALLY_PAID
    res_get_assign1 = client.get(f"/api/v1/fees/assignments/{assign_id}", headers=headers)
    assert res_get_assign1.status_code == 200
    assert res_get_assign1.json()["status"] == "PARTIALLY_PAID"
    assert float(res_get_assign1.json()["outstanding_due"]) == 12000.00

    # Excessive payment rejection
    res_pay_excessive = client.post(
        "/api/v1/fees/payments",
        json={
            "student_fee_assignment_id": assign_id,
            "amount": 15000.00,
            "payment_date": "2026-06-16",
            "payment_mode": "CASH",
        },
        headers=headers,
    )
    assert res_pay_excessive.status_code in (400, 422)

    # 5. Final Payment to complete outstanding due
    res_pay2 = client.post(
        "/api/v1/fees/payments",
        json={
            "student_fee_assignment_id": assign_id,
            "amount": 12000.00,
            "payment_date": "2026-06-20",
            "payment_mode": "BANK_TRANSFER",
            "reference_number": "TXN_NEFT_888",
        },
        headers=headers,
    )
    assert res_pay2.status_code == 201

    # Verify status is now PAID and outstanding due is 0.00
    res_get_assign2 = client.get(f"/api/v1/fees/assignments/{assign_id}", headers=headers)
    assert res_get_assign2.status_code == 200
    assert res_get_assign2.json()["status"] == "PAID"
    assert float(res_get_assign2.json()["outstanding_due"]) == 0.00

    # 6. Fetch Receipt
    res_receipt = client.get(f"/api/v1/fees/payments/{pay1_id}/receipt", headers=headers)
    assert res_receipt.status_code == 200
    receipt_data = res_receipt.json()
    assert receipt_data["receipt_number"] == pay1_data["receipt_number"]
    assert float(receipt_data["amount"]) == 8000.00
    assert float(receipt_data["net_payable"]) == 20000.00
    assert float(receipt_data["outstanding_due"]) == 0.00


def test_fees_api_discount_removal_and_cancellation(client: TestClient, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Discount Cancel API School", "DCAS1",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "Other School B", "OSB1",
        ["fees.create", "fees.view", "fees.update", "fees.delete"]
    )
    school_view, _, headers_view = create_school_and_user(
        db_session, "View Only School", "VOS1",
        ["fees.view"]
    )

    ay, sclass, student = setup_fee_fixture_data(db_session, school)

    # 1. Create Structure & Assign
    res_struct = client.post(
        "/api/v1/fees/structures",
        json={
            "academic_year_id": str(ay.id),
            "name": "API Test Structure",
            "items": [
                {"category": "TUITION", "name": "Tuition", "amount": 10000.00}
            ],
        },
        headers=headers,
    )
    assert res_struct.status_code == 201
    struct_id = res_struct.json()["id"]

    res_assign = client.post(
        "/api/v1/fees/assignments",
        json={
            "academic_year_id": str(ay.id),
            "student_id": str(student.id),
            "fee_structure_id": struct_id,
        },
        headers=headers,
    )
    assert res_assign.status_code == 201
    assign_id = res_assign.json()["id"]

    # 2. Add Discount
    res_disc = client.post(
        f"/api/v1/fees/assignments/{assign_id}/discounts",
        json={
            "discount_type": "SCHOLARSHIP",
            "name": "Merit Waiver",
            "amount": 3000.00,
        },
        headers=headers,
    )
    assert res_disc.status_code == 201
    discount_id = res_disc.json()["discounts"][0]["id"]

    # 3. RBAC Check on DELETE discount (View-only user fails with 403)
    res_del_no_perm = client.delete(
        f"/api/v1/fees/assignments/{assign_id}/discounts/{discount_id}",
        headers=headers_view,
    )
    assert res_del_no_perm.status_code == 403

    # 4. Cross-tenant access on DELETE discount (User B fails with 404)
    res_del_cross = client.delete(
        f"/api/v1/fees/assignments/{assign_id}/discounts/{discount_id}",
        headers=headers_b,
    )
    assert res_del_cross.status_code == 404

    # 5. Successful discount removal
    res_del_ok = client.delete(
        f"/api/v1/fees/assignments/{assign_id}/discounts/{discount_id}",
        headers=headers,
    )
    assert res_del_ok.status_code == 200
    assert len(res_del_ok.json()["discounts"]) == 0
    assert float(res_del_ok.json()["net_payable"]) == 10000.00

    # 6. RBAC Check on cancel assignment (View-only user fails with 403)
    res_cancel_no_perm = client.post(
        f"/api/v1/fees/assignments/{assign_id}/cancel",
        headers=headers_view,
    )
    assert res_cancel_no_perm.status_code == 403

    # 7. Cross-tenant access on cancel assignment (User B fails with 404)
    res_cancel_cross = client.post(
        f"/api/v1/fees/assignments/{assign_id}/cancel",
        headers=headers_b,
    )
    assert res_cancel_cross.status_code == 404

    # 8. Successful assignment cancellation
    res_cancel_ok = client.post(
        f"/api/v1/fees/assignments/{assign_id}/cancel",
        headers=headers,
    )
    assert res_cancel_ok.status_code == 200
    assert res_cancel_ok.json()["status"] == "CANCELLED"
