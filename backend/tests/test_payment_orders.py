import uuid
from datetime import date
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.fees import FeeCategory, FeeStructureStatus, PaymentMode, StudentFeeAssignmentStatus
from app.common.enums.parent import ParentRelationship
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider
from app.core.config import settings
from app.dependencies.database import get_db
from app.identity.models import IdentityRole, IdentityRolePermission, IdentityUser, IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.main import app
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees.fee_payment import FeePayment
from app.models.fees.fee_structure import FeeItem, FeeStructure
from app.models.fees.student_fee_assignment import FeeDiscount, StudentFeeAssignment, StudentFeeItem
from app.models.parent.parent import Parent
from app.models.payment.payment_order import PaymentOrder
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student


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
        status="ACTIVE",
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school_id)
    return user, {"Authorization": f"Bearer {token}"}


@pytest.fixture
def payment_orders_fixture(db_session, monkeypatch):
    db = db_session
    from app.database.common_model import CommonModel
    CommonModel.metadata.create_all(db.get_bind())
    app.dependency_overrides[get_db] = lambda: db_session
    from app.identity.seeders import seed_identity
    seed_identity(db)

    # Configure dummy test gateway keys in settings so credential resolution succeeds by default
    monkeypatch.setenv("RAZORPAY_KEY_ID", "rzp_test_12345")
    monkeypatch.setenv("RAZORPAY_KEY_SECRET", "rzp_secret_67890")
    monkeypatch.setenv("RAZORPAY_WEBHOOK_SECRET", "rzp_whsec_112233")
    monkeypatch.setenv("STRIPE_PUBLISHABLE_KEY", "pk_test_12345")
    monkeypatch.setenv("STRIPE_SECRET_KEY", "sk_test_67890")
    monkeypatch.setenv("STRIPE_WEBHOOK_SECRET", "whsec_112233")

    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_12345")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "rzp_secret_67890")
    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "rzp_whsec_112233")
    monkeypatch.setattr(settings, "STRIPE_PUBLISHABLE_KEY", "pk_test_12345")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "sk_test_67890")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "whsec_112233")

    school = School(
        id=uuid.uuid4(),
        name=f"School_{uuid.uuid4().hex[:6]}",
        code=f"SCH_{uuid.uuid4().hex[:4]}",
        address_line1="100 Payment St",
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
        address_line1="200 Payment St",
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
        name="Section A",
    )
    db.add_all([ay, sclass, section])
    db.commit()

    structure = FeeStructure(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        name="Annual Tuition Structure",
        description="Standard Fee",
        status=FeeStructureStatus.ACTIVE,
    )
    db.add(structure)
    db.commit()

    # Create Parents
    p1 = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Father One",
        relationship=ParentRelationship.FATHER,
        primary_phone=f"999{uuid.uuid4().hex[:7]}",
        email=f"parent1_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Parent St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    p2 = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Father Two",
        relationship=ParentRelationship.FATHER,
        primary_phone=f"888{uuid.uuid4().hex[:7]}",
        email=f"parent2_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="200 Parent St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    db.add_all([p1, p2])
    db.commit()

    # Create Students
    student1 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        parent_id=p1.id,
        school_class_id=sclass.id,
        section_id=section.id,
        first_name="Child",
        last_name="One",
        admission_number=f"ADM1_{uuid.uuid4().hex[:4]}",
        admission_date=date(2025, 4, 1),
        roll_number="101",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        status=StudentStatus.ACTIVE,
        email=f"child1_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="100 Student St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    student2 = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        parent_id=p2.id,
        school_class_id=sclass.id,
        section_id=section.id,
        first_name="Child",
        last_name="Two",
        admission_number=f"ADM2_{uuid.uuid4().hex[:4]}",
        admission_date=date(2025, 4, 1),
        roll_number="102",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 2, 1),
        status=StudentStatus.ACTIVE,
        email=f"child2_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="200 Student St",
        city="City",
        district="Dist",
        state="State",
        postal_code="110001",
    )
    db.add_all([student1, student2])
    db.commit()

    # Create Fee Assignment 1 (Unpaid, 10000 gross)
    assign1 = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student1.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 12, 31),
    )
    db.add(assign1)
    db.commit()

    item1 = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assign1.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("10000.00"),
        is_applicable=True,
    )
    db.add(item1)
    db.commit()

    # Create Fee Assignment 2 for Student 2
    assign2 = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student2.id,
        fee_structure_id=structure.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 12, 31),
    )
    db.add(assign2)
    db.commit()

    item2 = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assign2.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("8000.00"),
        is_applicable=True,
    )
    db.add(item2)
    db.commit()

    # Roles & Users
    parent_role = create_role_with_permissions(db, school.id, "Parent", ["fees.view"])
    student_role = create_role_with_permissions(db, school.id, "Student", ["fees.view"])
    staff_role = create_role_with_permissions(db, school.id, "Finance Admin", ["fees.view", "fees.create"])
    unauthorized_role = create_role_with_permissions(db, school.id, "Guest", [])

    user_parent1, auth_parent1 = create_user_and_auth_headers(
        db, school.id, email=p1.email, role=parent_role
    )
    user_parent2, auth_parent2 = create_user_and_auth_headers(
        db, school.id, email=p2.email, role=parent_role
    )
    user_student1, auth_student1 = create_user_and_auth_headers(
        db, school.id, email=student1.email, role=student_role, username=student1.admission_number
    )
    user_staff, auth_staff = create_user_and_auth_headers(
        db, school.id, email=f"staff_{uuid.uuid4().hex[:6]}@example.com", role=staff_role
    )
    user_unauth, auth_unauth = create_user_and_auth_headers(
        db, school.id, email=f"unauth_{uuid.uuid4().hex[:6]}@example.com", role=unauthorized_role
    )

    # Tenant 2 User & Assignment (for cross-tenant testing)
    ay2 = AcademicYear(
        id=uuid.uuid4(),
        school_id=school2.id,
        name="AY 2026 T2",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    sclass2 = SchoolClass(
        id=uuid.uuid4(),
        school_id=school2.id,
        name="Class 10 T2",
        display_order=1,
    )
    section2 = Section(
        id=uuid.uuid4(),
        school_class_id=sclass2.id,
        name="Section T2",
    )
    db.add_all([ay2, sclass2, section2])
    db.commit()

    structure2 = FeeStructure(
        id=uuid.uuid4(),
        school_id=school2.id,
        academic_year_id=ay2.id,
        school_class_id=sclass2.id,
        name="T2 Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    db.add(structure2)
    db.commit()

    # Tenant 2 Parent, Student & Assignment (for cross-tenant testing)
    p_t2 = Parent(
        id=uuid.uuid4(),
        school_id=school2.id,
        father_name="Father T2",
        relationship=ParentRelationship.FATHER,
        primary_phone=f"777{uuid.uuid4().hex[:7]}",
        email=f"parent_t2_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="300 Parent St",
        city="City2",
        district="Dist2",
        state="State2",
        postal_code="110002",
    )
    db.add(p_t2)
    db.commit()

    student_t2 = Student(
        id=uuid.uuid4(),
        school_id=school2.id,
        academic_year_id=ay2.id,
        school_class_id=sclass2.id,
        section_id=section2.id,
        parent_id=p_t2.id,
        first_name="Child",
        last_name="T2",
        admission_number=f"ADM2_T2_{uuid.uuid4().hex[:4]}",
        admission_date=date(2025, 4, 1),
        roll_number="103",
        gender=Gender.MALE,
        date_of_birth=date(2010, 3, 1),
        status=StudentStatus.ACTIVE,
        email=f"child_t2_{uuid.uuid4().hex[:6]}@example.com",
        address_line1="300 Student St",
        city="City2",
        district="Dist2",
        state="State2",
        postal_code="110002",
    )
    db.add(student_t2)
    db.commit()

    assign_t2 = StudentFeeAssignment(
        id=uuid.uuid4(),
        school_id=school2.id,
        academic_year_id=ay2.id,
        student_id=student_t2.id,
        fee_structure_id=structure2.id,
        status=StudentFeeAssignmentStatus.PENDING,
    )
    db.add(assign_t2)
    db.commit()

    item_t2 = StudentFeeItem(
        id=uuid.uuid4(),
        student_fee_assignment_id=assign_t2.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("6000.00"),
        is_applicable=True,
    )
    db.add(item_t2)
    db.commit()

    yield {
        "school": school,
        "school2": school2,
        "ay": ay,
        "assign1": assign1,
        "assign2": assign2,
        "assign_t2": assign_t2,
        "student1": student1,
        "student2": student2,
        "p1": p1,
        "p2": p2,
        "auth_parent1": auth_parent1,
        "auth_parent2": auth_parent2,
        "auth_student1": auth_student1,
        "auth_staff": auth_staff,
        "auth_unauth": auth_unauth,
    }
    app.dependency_overrides.clear()


def test_unauthenticated_request_fails(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
    )
    assert resp.status_code == 401


def test_authorized_parent_creates_order_success(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["student_fee_assignment_id"] == str(fx["assign1"].id)
    assert data["school_id"] == str(fx["school"].id)
    assert data["provider"] == "RAZORPAY"
    assert data["status"] == "CREATED"
    assert Decimal(str(data["amount"])) == Decimal("10000.00")
    assert "gateway_order_id" in data
    assert data["gateway_order_id"].startswith("order_rzp_")


def test_authorized_student_creates_order_success(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_student1"],
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["student_fee_assignment_id"] == str(fx["assign1"].id)
    assert Decimal(str(data["amount"])) == Decimal("10000.00")


def test_unrelated_parent_denied(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    # Parent 2 trying to create payment order for Parent 1's child assignment
    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent2"],
    )

    assert resp.status_code == 403


def test_unrelated_student_denied(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    # Student 1 trying to pay Student 2's assignment
    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign2"].id)},
        headers=fx["auth_student1"],
    )

    assert resp.status_code == 403


def test_unauthorized_user_denied(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_unauth"],
    )

    assert resp.status_code == 403


def test_cross_tenant_assignment_denied(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    # User in School 1 attempting to pay assignment in School 2
    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign_t2"].id)},
        headers=fx["auth_parent1"],
    )

    # Must fail closed with 404 (does not leak cross-tenant existence)
    assert resp.status_code in (404, 403)


def test_server_side_amount_calculation_ignores_client_amount(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    # Request includes malicious/tampered client amount "1.00"
    payload = {
        "student_fee_assignment_id": str(fx["assign1"].id),
        "amount": 1.00,
    }

    resp = client.post(
        "/api/v1/payments/orders",
        json=payload,
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 201
    data = resp.json()
    # Server MUST override client amount with database outstanding balance (10000.00)
    assert Decimal(str(data["amount"])) == Decimal("10000.00")


def test_server_side_amount_calculation_with_discounts_and_payments(payment_orders_fixture, db_session):
    client = TestClient(app)
    fx = payment_orders_fixture
    db = db_session

    # Apply a discount of 2000 to assign2 (gross=8000)
    discount = FeeDiscount(
        id=uuid.uuid4(),
        student_fee_assignment_id=fx["assign2"].id,
        discount_type="SCHOLARSHIP",
        name="Merit Discount",
        amount=Decimal("2000.00"),
    )
    db.add(discount)
    db.commit()

    # Record a previous partial payment of 3000
    payment = FeePayment(
        id=uuid.uuid4(),
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assign2"].id,
        amount=Decimal("3000.00"),
        payment_date=date.today(),
        payment_mode=PaymentMode.CASH,
        reference_number="CASH123",
        receipt_number="REC123",
    )
    db.add(payment)
    db.commit()
    db.expire_all()

    # Gross: 8000, Discount: 2000, Net Payable: 6000, Paid: 3000 -> Outstanding Due: 3000.00
    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign2"].id)},
        headers=fx["auth_parent2"],
    )

    assert resp.status_code == 201
    data = resp.json()
    assert Decimal(str(data["amount"])) == Decimal("3000.00")


def test_already_paid_assignment_rejected(payment_orders_fixture, db_session):
    client = TestClient(app)
    fx = payment_orders_fixture
    db = db_session

    # Mark assign1 as PAID with full payment
    payment = FeePayment(
        id=uuid.uuid4(),
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assign1"].id,
        amount=Decimal("10000.00"),
        payment_date=date.today(),
        payment_mode=PaymentMode.CASH,
        receipt_number="REC_FULL",
    )
    fx["assign1"].status = StudentFeeAssignmentStatus.PAID
    db.add(payment)
    db.commit()
    db.expire_all()

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 422
    data = resp.json()
    err_msg = data.get("error", {}).get("message", data.get("message", ""))
    assert "already fully paid" in err_msg.lower() or "validation" in err_msg.lower()


def test_cancelled_assignment_rejected(payment_orders_fixture, db_session):
    client = TestClient(app)
    fx = payment_orders_fixture
    db = db_session

    fx["assign1"].status = StudentFeeAssignmentStatus.CANCELLED
    db.commit()
    db.expire_all()

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 422
    data = resp.json()
    err_msg = data.get("error", {}).get("message", data.get("message", ""))
    assert "cancelled" in err_msg.lower()


def test_stripe_order_creation(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={
            "student_fee_assignment_id": str(fx["assign1"].id),
            "provider": "STRIPE",
        },
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 201
    data = resp.json()
    assert data["provider"] == "STRIPE"
    assert data["gateway_order_id"].startswith("cs_test_")
    assert Decimal(str(data["amount"])) == Decimal("10000.00")


def test_unsupported_provider_rejected(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={
            "student_fee_assignment_id": str(fx["assign1"].id),
            "provider": "PAYPAL_INVALID",
        },
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 422


def test_unconfigured_provider_rejected(payment_orders_fixture, monkeypatch):
    client = TestClient(app)
    fx = payment_orders_fixture

    # Unset Razorpay keys to simulate missing configuration
    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "")

    resp = client.post(
        "/api/v1/payments/orders",
        json={
            "student_fee_assignment_id": str(fx["assign1"].id),
            "provider": "RAZORPAY",
        },
        headers=fx["auth_parent1"],
    )

    assert resp.status_code in (400, 422)
    data = resp.json()
    err_msg = data.get("error", {}).get("message", data.get("message", ""))
    assert "not configured" in err_msg.lower()


def test_idempotency_returns_existing_active_order(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    # First request creates order
    resp1 = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent1"],
    )
    assert resp1.status_code == 201
    data1 = resp1.json()

    # Second request for same assignment and same provider should return same active order ID
    resp2 = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent1"],
    )
    assert resp2.status_code == 201
    data2 = resp2.json()

    assert data1["id"] == data2["id"]
    assert data1["gateway_order_id"] == data2["gateway_order_id"]


def test_sanitized_response_contains_no_secrets(payment_orders_fixture):
    client = TestClient(app)
    fx = payment_orders_fixture

    resp = client.post(
        "/api/v1/payments/orders",
        json={"student_fee_assignment_id": str(fx["assign1"].id)},
        headers=fx["auth_parent1"],
    )

    assert resp.status_code == 201
    data = resp.json()

    # Verify no credentials leaked
    raw_str = str(data)
    assert "rzp_secret" not in raw_str
    assert "key_secret" not in raw_str
    assert "webhook_secret" not in raw_str
    assert "api_key" not in raw_str
