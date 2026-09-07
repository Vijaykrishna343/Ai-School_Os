import hashlib
import hmac
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.common.enums import Gender, StudentStatus
from app.common.enums.fees import FeeCategory, FeeStructureStatus, PaymentMode, StudentFeeAssignmentStatus
from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.common.exceptions import ForbiddenException, ValidationException
from app.core.config import settings
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.academic_year.academic_year import AcademicYear
from app.models.fees import (
    FeeItem,
    FeePayment,
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
from app.services.fee_service import fee_service
from app.services.payment_settlement_service import payment_settlement_service


@pytest.fixture(autouse=True)
def setup_settlement_db_tables(db_session, monkeypatch):
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
def settlement_fixture(db_session):
    school = School(
        id=uuid.uuid4(),
        name="Settlement Test School",
        code=f"STS-{uuid.uuid4().hex[:4]}",
        address_line1="100 Ledger St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    school_other = School(
        id=uuid.uuid4(),
        name="Other School",
        code=f"OTH-{uuid.uuid4().hex[:4]}",
        address_line1="200 Other St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school, school_other])
    db_session.commit()

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    ay_other = AcademicYear(
        school_id=school_other.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db_session.add_all([ay, ay_other])
    db_session.commit()

    sclass = SchoolClass(school_id=school.id, name="Grade 10", display_order=1)
    db_session.add(sclass)
    db_session.commit()

    section = Section(school_class_id=sclass.id, name="A")
    db_session.add(section)
    db_session.commit()

    parent = Parent(
        school_id=school.id,
        father_name="Parent Settlement",
        email="parent.settlement@school.com",
        primary_phone="9876543299",
        address_line1="Street 1",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent)
    db_session.commit()

    student = Student(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        section_id=section.id,
        parent_id=parent.id,
        admission_number="ADM-S001",
        roll_number="101",
        first_name="Sam",
        last_name="Settlement",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2024, 6, 1),
        email="sam.settlement@school.com",
        address_line1="Street 1",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add(student)
    db_session.commit()

    fee_struct = FeeStructure(
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sclass.id,
        name="Tuition Fee Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(fee_struct)
    db_session.commit()

    fee_item = FeeItem(
        fee_structure_id=fee_struct.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("10000.00"),
        is_optional=False,
    )
    db_session.add(fee_item)
    db_session.commit()

    assignment = StudentFeeAssignment(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=fee_struct.id,
        status=StudentFeeAssignmentStatus.PENDING,
    )
    db_session.add(assignment)
    db_session.commit()

    student_fee_item = StudentFeeItem(
        student_fee_assignment_id=assignment.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition Fee",
        amount=Decimal("10000.00"),
        is_optional=False,
        is_applicable=True,
    )
    db_session.add(student_fee_item)
    db_session.commit()

    parent_role = IdentityRole(name="Parent", description="Parent Role", is_system=True)
    user = IdentityUser(
        id=uuid.uuid4(),
        email="parent.settlement@school.com",
        first_name="Parent",
        last_name="Settlement",
        password_hash="hashed",
        school_id=school.id,
        is_active=True,
        roles=[parent_role],
    )
    db_session.add_all([parent_role, user])
    db_session.commit()

    return {
        "school": school,
        "school_other": school_other,
        "student": student,
        "assignment": assignment,
        "user": user,
    }


def test_basic_settlement_success(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    # 1. Create PaymentOrder for full amount 10,000
    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_settle_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    # 2. Create SUCCESS PaymentTransaction
    txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_settle_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("10000.00"),
        currency="INR",
        payment_method="card",
    )
    db_session.add(txn)
    db_session.commit()

    # 3. Perform automated fee settlement
    payment = payment_settlement_service.settle_payment_transaction(db_session, txn)

    assert payment is not None
    assert payment.amount == Decimal("10000.00")
    assert payment.reference_number == "pay_settle_001"
    assert payment.payment_mode == PaymentMode.CARD
    assert payment.receipt_number.startswith("REC-")

    # Verify assignment updated to PAID with 0 outstanding
    db_session.refresh(assignment)
    metrics = fee_service.calculate_metrics(assignment)
    assert metrics["total_paid"] == Decimal("10000.00")
    assert metrics["outstanding_due"] == Decimal("0.00")
    assert assignment.status == StudentFeeAssignmentStatus.PAID


def test_partial_settlement_flow(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    # Partial payment 1: 4,000
    order1 = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_partial_001",
        amount=Decimal("4000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order1)
    db_session.commit()

    txn1 = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order1.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_partial_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("4000.00"),
        currency="INR",
        payment_method="upi",
    )
    db_session.add(txn1)
    db_session.commit()

    payment1 = payment_settlement_service.settle_payment_transaction(db_session, txn1)
    assert payment1.amount == Decimal("4000.00")

    db_session.refresh(assignment)
    metrics1 = fee_service.calculate_metrics(assignment)
    assert metrics1["total_paid"] == Decimal("4000.00")
    assert metrics1["outstanding_due"] == Decimal("6000.00")
    assert assignment.status == StudentFeeAssignmentStatus.PARTIALLY_PAID

    # Partial payment 2: 6,000
    order2 = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_partial_002",
        amount=Decimal("6000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order2)
    db_session.commit()

    txn2 = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order2.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_partial_002",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("6000.00"),
        currency="INR",
        payment_method="card",
    )
    db_session.add(txn2)
    db_session.commit()

    payment2 = payment_settlement_service.settle_payment_transaction(db_session, txn2)
    assert payment2.amount == Decimal("6000.00")

    db_session.refresh(assignment)
    metrics2 = fee_service.calculate_metrics(assignment)
    assert metrics2["total_paid"] == Decimal("10000.00")
    assert metrics2["outstanding_due"] == Decimal("0.00")
    assert assignment.status == StudentFeeAssignmentStatus.PAID


def test_settlement_idempotency_same_transaction_twice(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_idempotent_001",
        amount=Decimal("5000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_idempotent_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("5000.00"),
        currency="INR",
    )
    db_session.add(txn)
    db_session.commit()

    # First settlement
    p1 = payment_settlement_service.settle_payment_transaction(db_session, txn)

    # Second settlement call with exact same transaction
    p2 = payment_settlement_service.settle_payment_transaction(db_session, txn)

    assert p1.id == p2.id
    assert p1.receipt_number == p2.receipt_number

    # Assert exactly 1 FeePayment exists in DB for this assignment
    payments = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments) == 1

    db_session.refresh(assignment)
    metrics = fee_service.calculate_metrics(assignment)
    assert metrics["total_paid"] == Decimal("5000.00")
    assert metrics["outstanding_due"] == Decimal("5000.00")


def test_verification_then_webhook_convergence(db_session, settlement_fixture):
    user = settlement_fixture["user"]
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_conv_rzp_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    client = TestClient(fastapi_app)

    # Step 1: Verification API call
    sig_payload = f"order_conv_rzp_001|pay_conv_rzp_001"
    signature = hmac.new("mock_rzp_secret".encode(), sig_payload.encode(), hashlib.sha256).hexdigest()

    verify_resp = client.post(
        "/api/v1/payments/verify",
        json={
            "payment_order_id": str(order.id),
            "provider": "RAZORPAY",
            "gateway_order_id": "order_conv_rzp_001",
            "gateway_payment_id": "pay_conv_rzp_001",
            "gateway_signature": signature,
        },
    )
    assert verify_resp.status_code == 200
    assert verify_resp.json()["success"] is True

    # Assert 1 FeePayment created
    payments1 = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments1) == 1

    # Step 2: Webhook arrives later for same payment
    webhook_payload = {
        "event_id": "evt_conv_001",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_conv_rzp_001",
                    "order_id": "order_conv_rzp_001",
                    "status": "captured",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    body_bytes = str(webhook_payload).replace("'", '"').encode("utf-8")
    webhook_sig = hmac.new("mock_rzp_webhook_secret".encode(), body_bytes, hashlib.sha256).hexdigest()

    webhook_resp = client.post(
        "/api/v1/payments/webhook/razorpay",
        content=body_bytes,
        headers={"x-razorpay-signature": webhook_sig, "content-type": "application/json"},
    )
    assert webhook_resp.status_code == 200

    # Assert STILL only 1 FeePayment exists in DB
    payments2 = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments2) == 1

    db_session.refresh(assignment)
    assert assignment.status == StudentFeeAssignmentStatus.PAID

    fastapi_app.dependency_overrides.pop(get_current_user, None)


def test_webhook_then_verification_convergence(db_session, settlement_fixture):
    user = settlement_fixture["user"]
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_conv_reverse_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    client = TestClient(fastapi_app)

    # Step 1: Webhook arrives first
    webhook_payload = {
        "event_id": "evt_conv_rev_001",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_conv_rev_001",
                    "order_id": "order_conv_reverse_001",
                    "status": "captured",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    body_bytes = str(webhook_payload).replace("'", '"').encode("utf-8")
    webhook_sig = hmac.new("mock_rzp_webhook_secret".encode(), body_bytes, hashlib.sha256).hexdigest()

    webhook_resp = client.post(
        "/api/v1/payments/webhook/razorpay",
        content=body_bytes,
        headers={"x-razorpay-signature": webhook_sig, "content-type": "application/json"},
    )
    assert webhook_resp.status_code == 200

    # Assert 1 FeePayment created
    payments1 = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments1) == 1

    # Step 2: Verification API arrives later
    sig_payload = f"order_conv_reverse_001|pay_conv_rev_001"
    signature = hmac.new("mock_rzp_secret".encode(), sig_payload.encode(), hashlib.sha256).hexdigest()

    verify_resp = client.post(
        "/api/v1/payments/verify",
        json={
            "payment_order_id": str(order.id),
            "provider": "RAZORPAY",
            "gateway_order_id": "order_conv_reverse_001",
            "gateway_payment_id": "pay_conv_rev_001",
            "gateway_signature": signature,
        },
    )
    assert verify_resp.status_code == 200

    # Assert STILL only 1 FeePayment exists in DB
    payments2 = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments2) == 1

    db_session.refresh(assignment)
    assert assignment.status == StudentFeeAssignmentStatus.PAID

    fastapi_app.dependency_overrides.pop(get_current_user, None)


def test_settlement_non_success_transaction_rejected(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_failed_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.FAILED,
    )
    db_session.add(order)
    db_session.commit()

    failed_txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_failed_001",
        status=PaymentTransactionStatus.FAILED,
        amount=Decimal("10000.00"),
        currency="INR",
    )
    db_session.add(failed_txn)
    db_session.commit()

    with pytest.raises(ValidationException) as exc_info:
        payment_settlement_service.settle_payment_transaction(db_session, failed_txn)
    assert "Only successful payment transactions can be settled" in str(exc_info.value)

    # Assert 0 FeePayment created
    payments = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments) == 0


def test_cross_tenant_settlement_rejected(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    school_other = settlement_fixture["school_other"]
    assignment = settlement_fixture["assignment"]

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_xtenant_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    # Mismatched transaction school_id
    xtenant_txn = PaymentTransaction(
        school_id=school_other.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_xtenant_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("10000.00"),
        currency="INR",
    )
    db_session.add(xtenant_txn)
    db_session.commit()

    with pytest.raises(ForbiddenException) as exc_info:
        payment_settlement_service.settle_payment_transaction(db_session, xtenant_txn)
    assert "Cross-tenant settlement attempt detected" in str(exc_info.value)


def test_mismatched_amount_settlement_rejected(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_amt_mismatch_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    mismatch_txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_amt_mismatch_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("5000.00"),  # Mismatched amount!
        currency="INR",
    )
    db_session.add(mismatch_txn)
    db_session.commit()

    with pytest.raises(ValidationException) as exc_info:
        payment_settlement_service.settle_payment_transaction(db_session, mismatch_txn)
    assert "does not match payment order amount" in str(exc_info.value)


def test_mismatched_currency_settlement_rejected(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_curr_mismatch_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    mismatch_txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_curr_mismatch_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("10000.00"),
        currency="USD",  # Mismatched currency!
    )
    db_session.add(mismatch_txn)
    db_session.commit()

    with pytest.raises(ValidationException) as exc_info:
        payment_settlement_service.settle_payment_transaction(db_session, mismatch_txn)
    assert "does not match payment order currency" in str(exc_info.value)


def test_overpayment_settlement_rejected(db_session, settlement_fixture):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    # Assignment total is 10,000.
    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_overpay_001",
        amount=Decimal("15000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    overpay_txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_overpay_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("15000.00"),  # Exceeds outstanding 10,000!
        currency="INR",
    )
    db_session.add(overpay_txn)
    db_session.commit()

    with pytest.raises(ValidationException) as exc_info:
        payment_settlement_service.settle_payment_transaction(db_session, overpay_txn)
    assert "exceeds outstanding due balance" in str(exc_info.value)

    # Assert 0 FeePayment created
    payments = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment.id, is_deleted=False).all()
    assert len(payments) == 0


def test_settlement_rollback_on_failure(db_session, settlement_fixture, monkeypatch):
    school = settlement_fixture["school"]
    assignment = settlement_fixture["assignment"]

    order = PaymentOrder(
        school_id=school.id,
        student_fee_assignment_id=assignment.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rollback_001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,
    )
    db_session.add(order)
    db_session.commit()

    txn = PaymentTransaction(
        school_id=school.id,
        payment_order_id=order.id,
        provider=PaymentProvider.RAZORPAY,
        gateway_transaction_id="pay_rollback_001",
        status=PaymentTransactionStatus.SUCCESS,
        amount=Decimal("10000.00"),
        currency="INR",
    )
    db_session.add(txn)
    db_session.commit()

    assignment_id = assignment.id

    # Monkeypatch fee_service.record_payment to raise an exception simulating failure during settlement
    def mock_record_payment_error(*args, **kwargs):
        raise RuntimeError("Simulated DB connection failure during payment record")

    monkeypatch.setattr(fee_service, "record_payment", mock_record_payment_error)

    with pytest.raises(RuntimeError):
        with db_session.begin_nested():
            payment_settlement_service.settle_payment_transaction(db_session, txn)

    payments = db_session.query(FeePayment).filter_by(student_fee_assignment_id=assignment_id, is_deleted=False).all()
    assert len(payments) == 0

    reloaded_assignment = db_session.get(StudentFeeAssignment, assignment_id)
    assert reloaded_assignment.status == StudentFeeAssignmentStatus.PENDING
