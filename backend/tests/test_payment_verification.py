import hashlib
import hmac
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.fees import FeeCategory, FeeStructureStatus, StudentFeeAssignmentStatus
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.core.config import settings
from app.database.common_model import CommonModel
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees import (
    FeeItem,
    FeeStructure,
    StudentFeeAssignment,
    StudentFeeItem,
)
from app.models.parent.parent import Parent
from app.models.payment.payment_order import PaymentOrder
from app.models.payment.payment_transaction import PaymentTransaction
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student


from app.dependencies.database import get_db


@pytest.fixture(autouse=True)
def setup_payment_db_tables(db_session, monkeypatch):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session

    monkeypatch.setattr(settings, "RAZORPAY_KEY_ID", "rzp_test_key")
    monkeypatch.setattr(settings, "RAZORPAY_KEY_SECRET", "mock_rzp_secret")
    monkeypatch.setattr(settings, "RAZORPAY_WEBHOOK_SECRET", "mock_rzp_webhook_secret")
    monkeypatch.setattr(settings, "STRIPE_PUBLISHABLE_KEY", "pk_test_key")
    monkeypatch.setattr(settings, "STRIPE_SECRET_KEY", "mock_stripe_secret")
    monkeypatch.setattr(settings, "STRIPE_WEBHOOK_SECRET", "mock_stripe_webhook_secret")

    yield
    fastapi_app.dependency_overrides.pop(get_db, None)




@pytest.fixture
def verification_fixture(db_session):
    school = School(
        id=uuid.uuid4(),
        name="Verification Test School",
        code=f"VTS-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)

    school_other = School(
        id=uuid.uuid4(),
        name="Other School",
        code=f"OTH-{uuid.uuid4().hex[:4]}",
        address_line1="456 Other St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school_other)
    db_session.commit()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db_session.add(ay)

    ay_other = AcademicYear(
        school_id=school_other.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db_session.add(ay_other)
    db_session.commit()

    sclass = SchoolClass(school_id=school.id, name="Grade 10", display_order=1)
    db_session.add(sclass)
    db_session.commit()

    section = Section(school_class_id=sclass.id, name="A")
    db_session.add(section)
    db_session.commit()

    parent_a = Parent(
        school_id=school.id,
        father_name="Parent Alpha",
        email="parent.alpha@school.com",
        primary_phone="9876543210",
        address_line1="Street 1",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    parent_b = Parent(
        school_id=school.id,
        father_name="Parent Beta",
        email="parent.beta@school.com",
        primary_phone="9876543211",
        address_line1="Street 2",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([parent_a, parent_b])
    db_session.commit()

    student_a = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent_a.id,
        admission_number="ADM-A001",
        roll_number="101",
        first_name="Alice",
        last_name="Alpha",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2024, 6, 1),
        email="alice.alpha@school.com",
        address_line1="Street 1",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    student_b = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent_b.id,
        admission_number="ADM-B002",
        roll_number="102",
        first_name="Bob",
        last_name="Beta",
        gender=Gender.MALE,
        date_of_birth=date(2010, 2, 2),
        admission_date=date(2024, 6, 1),
        email="bob.beta@school.com",
        address_line1="Street 2",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add_all([student_a, student_b])
    db_session.commit()

    fee_struct = FeeStructure(
        school_id=school.id,
        academic_year_id=ay.id,
        name="Tuition Fee Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(fee_struct)
    db_session.commit()

    fee_item = FeeItem(
        fee_structure_id=fee_struct.id,
        category=FeeCategory.TUITION,
        name="Tuition",
        amount=Decimal("5000.00"),
    )
    db_session.add(fee_item)
    db_session.commit()

    assignment_a = StudentFeeAssignment(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student_a.id,
        fee_structure_id=fee_struct.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 9, 30),
    )
    assignment_b = StudentFeeAssignment(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student_b.id,
        fee_structure_id=fee_struct.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 9, 30),
    )
    db_session.add_all([assignment_a, assignment_b])
    db_session.commit()

    sfi_a = StudentFeeItem(
        student_fee_assignment_id=assignment_a.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition",
        amount=Decimal("5000.00"),
    )
    sfi_b = StudentFeeItem(
        student_fee_assignment_id=assignment_b.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition",
        amount=Decimal("5000.00"),
    )
    db_session.add_all([sfi_a, sfi_b])
    db_session.commit()



    parent_role = IdentityRole(name="Parent", description="Parent Role", is_system=True)
    student_role = IdentityRole(name="Student", description="Student Role", is_system=True)
    db_session.add_all([parent_role, student_role])
    db_session.commit()

    user_parent_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email="parent.alpha@school.com",
        password_hash="hash",
        first_name="Parent",
        last_name="Alpha",
        is_active=True,
        status="ACTIVE",
    )
    user_parent_a.roles = [parent_role]

    user_parent_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email="parent.beta@school.com",
        password_hash="hash",
        first_name="Parent",
        last_name="Beta",
        is_active=True,
        status="ACTIVE",
    )
    user_parent_b.roles = [parent_role]

    user_student_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username="ADM-A001",
        email="alice.alpha@school.com",
        password_hash="hash",
        first_name="Alice",
        last_name="Alpha",
        is_active=True,
        status="ACTIVE",
    )
    user_student_a.roles = [student_role]

    db_session.add_all([user_parent_a, user_parent_b, user_student_a])
    db_session.commit()

    return {
        "school": school,
        "school_other": school_other,
        "student_a": student_a,
        "student_b": student_b,
        "parent_a": parent_a,
        "parent_b": parent_b,
        "user_parent_a": user_parent_a,
        "user_parent_b": user_parent_b,
        "user_student_a": user_student_a,
        "assignment_a": assignment_a,
        "assignment_b": assignment_b,
    }


def generate_razorpay_signature(order_id: str, payment_id: str, secret: str = None) -> str:
    secret_key = secret or getattr(settings, "RAZORPAY_KEY_SECRET", "") or "mock_rzp_secret"
    msg = f"{order_id}|{payment_id}"
    return hmac.new(secret_key.encode(), msg.encode(), hashlib.sha256).hexdigest()



def test_verification_authenticated_success_razorpay(db_session, verification_fixture):
    fx = verification_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment_a"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_12345",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payment_id = "pay_rzp_99999"
    sig = generate_razorpay_signature("order_rzp_12345", payment_id)

    fastapi_app.dependency_overrides[get_current_user] = lambda: fx["user_parent_a"]
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(order.id),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": payment_id,
                "gateway_signature": sig,
            },
        )
    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["status"] == "PAID"
    assert data["gateway_transaction_id"] == payment_id

    # Verify database update
    db_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert db_order.status == PaymentOrderStatus.PAID

    txn = db_session.query(PaymentTransaction).filter_by(payment_order_id=order.id).first()
    assert txn is not None
    assert txn.status == PaymentTransactionStatus.SUCCESS
    assert txn.amount == Decimal("5000.00")


def test_verification_unauthenticated_rejection(verification_fixture):
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(uuid.uuid4()),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": "pay_123",
                "gateway_signature": "sig",
            },
        )
    assert resp.status_code == 401


def test_verification_unauthorized_parent_rejection(db_session, verification_fixture):
    fx = verification_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment_a"].id,  # Student A belongs to Parent A
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_12345",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payment_id = "pay_rzp_99999"
    sig = generate_razorpay_signature("order_rzp_12345", payment_id)

    # Parent B tries to verify payment for Student A
    fastapi_app.dependency_overrides[get_current_user] = lambda: fx["user_parent_b"]
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(order.id),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": payment_id,
                "gateway_signature": sig,
            },
        )
    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 403


def test_verification_invalid_signature_rejection(db_session, verification_fixture):
    fx = verification_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment_a"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_12345",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: fx["user_parent_a"]
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(order.id),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": "pay_rzp_99999",
                "gateway_signature": "invalid_forged_signature",
            },
        )
    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 400
    err_msg = resp.json().get("error", {}).get("message", resp.json().get("message", ""))
    assert "signature" in err_msg.lower()


def test_verification_amount_mismatch_rejection(db_session, verification_fixture):
    fx = verification_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment_a"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_12345",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payment_id = "pay_rzp_99999"
    sig = generate_razorpay_signature("order_rzp_12345", payment_id)

    fastapi_app.dependency_overrides[get_current_user] = lambda: fx["user_parent_a"]
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(order.id),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": payment_id,
                "gateway_signature": sig,
                "amount": 1000.00,  # Mismatched amount
            },
        )
    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 400


def test_verification_currency_mismatch_rejection(db_session, verification_fixture):
    fx = verification_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment_a"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_12345",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payment_id = "pay_rzp_99999"
    sig = generate_razorpay_signature("order_rzp_12345", payment_id)

    fastapi_app.dependency_overrides[get_current_user] = lambda: fx["user_parent_a"]
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(order.id),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": payment_id,
                "gateway_signature": sig,
                "currency": "USD",  # Mismatched currency
            },
        )
    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 400


def test_verification_already_paid_order_idempotency(db_session, verification_fixture):
    fx = verification_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment_a"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_12345",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,  # Already PAID
    )
    db_session.add(order)
    db_session.commit()

    payment_id = "pay_rzp_99999"
    sig = generate_razorpay_signature("order_rzp_12345", payment_id)

    fastapi_app.dependency_overrides[get_current_user] = lambda: fx["user_parent_a"]
    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/verify",
            json={
                "provider": "RAZORPAY",
                "payment_order_id": str(order.id),
                "gateway_order_id": "order_rzp_12345",
                "gateway_payment_id": payment_id,
                "gateway_signature": sig,
            },
        )
    fastapi_app.dependency_overrides.clear()

    assert resp.status_code == 200
    assert resp.json()["status"] == "PAID"
    assert resp.json()["success"] is True
