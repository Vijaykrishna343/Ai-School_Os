import hashlib
import hmac
import json
import time
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
def setup_webhook_db_tables(db_session, monkeypatch):
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
def webhook_fixture(db_session):
    school = School(
        id=uuid.uuid4(),
        name="Webhook Test School",
        code=f"WTS-{uuid.uuid4().hex[:4]}",
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
        end_date=date(2027, 4, 30),
        status="ACTIVE",
    )
    db_session.add(ay)
    db_session.commit()

    sclass = SchoolClass(school_id=school.id, name="Grade 10", display_order=1)
    db_session.add(sclass)
    db_session.commit()

    section = Section(school_class_id=sclass.id, name="A")
    db_session.add(section)
    db_session.commit()

    parent = Parent(
        school_id=school.id,
        father_name="Parent Webhook",
        email="parent.wh@school.com",
        primary_phone="9876543210",
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
        admission_number="ADM-WH001",
        roll_number="101",
        first_name="Webhook",
        last_name="Child",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2024, 6, 1),
        email="webhook.child@school.com",
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
        name="Tuition Fee Structure",
        status=FeeStructureStatus.ACTIVE,
    )
    db_session.add(fee_struct)
    db_session.commit()

    fee_item = FeeItem(
        fee_structure_id=fee_struct.id,
        category=FeeCategory.TUITION,
        name="Tuition",
        amount=Decimal("10000.00"),
    )
    db_session.add(fee_item)
    db_session.commit()

    assignment = StudentFeeAssignment(
        school_id=school.id,
        academic_year_id=ay.id,
        student_id=student.id,
        fee_structure_id=fee_struct.id,
        status=StudentFeeAssignmentStatus.PENDING,
        due_date=date(2026, 9, 30),
    )
    db_session.add(assignment)
    db_session.commit()

    sfi = StudentFeeItem(
        student_fee_assignment_id=assignment.id,
        fee_item_id=fee_item.id,
        category=FeeCategory.TUITION,
        name="Tuition",
        amount=Decimal("10000.00"),
    )
    db_session.add(sfi)
    db_session.commit()



    return {
        "school": school,
        "student": student,
        "assignment": assignment,
    }


def compute_razorpay_webhook_sig(raw_bytes: bytes, secret: str = None) -> str:
    webhook_sec = secret or getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "") or "mock_rzp_webhook_secret"
    return hmac.new(webhook_sec.encode("utf-8"), raw_bytes, hashlib.sha256).hexdigest()


def compute_stripe_webhook_sig(raw_bytes: bytes, secret: str = None, timestamp: int = None) -> tuple[str, str]:
    webhook_sec = secret or getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or "mock_stripe_webhook_secret"
    ts = timestamp or int(time.time())
    signed_payload = f"{ts}.{raw_bytes.decode('utf-8')}".encode("utf-8")
    sig = hmac.new(webhook_sec.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    header_val = f"t={ts},v1={sig}"
    return header_val, sig



def test_razorpay_webhook_valid_signature(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_1001",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "entity": "event",
        "event_id": "event_rzp_1001",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_1001",
                    "order_id": "order_rzp_wh_1001",
                    "amount": 1000000,  # 10000.00 INR in paise
                    "currency": "INR",
                    "status": "captured",
                    "secret_key": "MOCK_SECRET_KEY_MUST_BE_REDACTED",
                    "card_number": "4111111111111111",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "x-razorpay-signature": sig,
            },
        )

    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True
    assert res_data["event_id"] == "event_rzp_1001"

    # Verify Order Status updated to PAID
    db_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert db_order.status == PaymentOrderStatus.PAID

    # Verify PaymentTransaction persisted with sanitized payload
    txn = db_session.query(PaymentTransaction).filter_by(gateway_event_id="event_rzp_1001").first()
    assert txn is not None
    assert txn.status == PaymentTransactionStatus.SUCCESS
    assert txn.amount == Decimal("10000.00")
    assert txn.raw_response["payload"]["payment"]["entity"]["secret_key"] == "[REDACTED]"


def test_stripe_webhook_valid_signature(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.STRIPE,
        gateway_order_id="cs_test_stripe_2002",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "id": "evt_stripe_2002",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_stripe_2002",
                "payment_intent": "pi_stripe_2002",
                "amount_total": 1000000,
                "currency": "inr",
                "payment_status": "paid",
                "api_key": "SECRET_STRIPE_API_KEY",
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig_header, _ = compute_stripe_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhook/stripe",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "stripe-signature": sig_header,
            },
        )

    assert resp.status_code == 200
    res_data = resp.json()
    assert res_data["success"] is True

    # Verify Order Status updated to PAID
    db_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert db_order.status == PaymentOrderStatus.PAID

    txn = db_session.query(PaymentTransaction).filter_by(gateway_event_id="evt_stripe_2002").first()
    assert txn is not None
    assert txn.raw_response["data"]["object"]["api_key"] == "[REDACTED]"


def test_webhook_missing_or_invalid_signature_rejection(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_1003",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "event_id": "event_rzp_1003",
        "event": "payment.captured",
        "payload": {"payment": {"entity": {"order_id": "order_rzp_wh_1003", "amount": 1000000}}},
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")

    with TestClient(fastapi_app) as client:
        # Missing signature
        resp1 = client.post("/api/v1/payments/webhook/razorpay", content=raw_body)
        assert resp1.status_code == 400

        # Invalid signature
        resp2 = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": "bogus_signature"},
        )
        assert resp2.status_code == 400


def test_webhook_replay_protection_exact_duplicate(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_1004",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "event_id": "event_rzp_1004",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_1004",
                    "order_id": "order_rzp_wh_1004",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        # First call: process normally
        resp1 = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
        assert resp1.status_code == 200
        assert resp1.json()["processed"] is True

        # Second call (exact replay): safe acknowledgement with processed=False
        resp2 = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
        assert resp2.status_code == 200
        assert resp2.json()["processed"] is False

    txns = db_session.query(PaymentTransaction).filter_by(gateway_event_id="event_rzp_1004").all()
    assert len(txns) == 1


def test_webhook_conflicting_replay_fails_closed(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_1005",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict1 = {
        "event_id": "event_rzp_1005",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_1005",
                    "order_id": "order_rzp_wh_1005",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    raw_body1 = json.dumps(payload_dict1).encode("utf-8")
    sig1 = compute_razorpay_webhook_sig(raw_body1)

    with TestClient(fastapi_app) as client:
        resp1 = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body1,
            headers={"x-razorpay-signature": sig1},
        )
        assert resp1.status_code == 200

        # Conflicting replay: same event_id but different amount!
        payload_dict2 = {
            "event_id": "event_rzp_1005",
            "event": "payment.captured",
            "payload": {
                "payment": {
                    "entity": {
                        "id": "pay_rzp_1005",
                        "order_id": "order_rzp_wh_1005",
                        "amount": 9999900,  # Conflicting amount
                        "currency": "INR",
                    }
                }
            },
        }
        raw_body2 = json.dumps(payload_dict2).encode("utf-8")
        sig2 = compute_razorpay_webhook_sig(raw_body2)

        resp2 = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body2,
            headers={"x-razorpay-signature": sig2},
        )
        assert resp2.status_code == 400


def test_webhook_amount_mismatch_rejection(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_1006",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "event_id": "event_rzp_1006",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_1006",
                    "order_id": "order_rzp_wh_1006",
                    "amount": 500000,  # 5000.00 INR vs order amount 10000.00
                    "currency": "INR",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
    assert resp.status_code == 400


def test_webhook_prevent_paid_order_state_regression(db_session, webhook_fixture):
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_1007",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.PAID,  # Order is already PAID
    )
    db_session.add(order)
    db_session.commit()

    # Webhook receives payment.failed event
    payload_dict = {
        "event_id": "event_rzp_1007",
        "event": "payment.failed",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_1007",
                    "order_id": "order_rzp_wh_1007",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhook/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
    assert resp.status_code == 200

    # Order status MUST REMAIN PAID (no state regression)
    db_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert db_order.status == PaymentOrderStatus.PAID


def test_dedicated_razorpay_webhook_endpoint(db_session, webhook_fixture):
    """Verifies the dedicated POST /api/v1/payments/webhooks/razorpay endpoint."""
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_dedicated_1",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "event_id": "evt_rzp_dedicated_1",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_ded_1",
                    "order_id": "order_rzp_wh_dedicated_1",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhooks/razorpay",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "x-razorpay-signature": sig,
            },
        )
    assert resp.status_code == 200
    assert resp.json()["success"] is True
    assert resp.json()["event_id"] == "evt_rzp_dedicated_1"

    db_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert db_order.status == PaymentOrderStatus.PAID


def test_dedicated_stripe_webhook_endpoint(db_session, webhook_fixture):
    """Verifies the dedicated POST /api/v1/payments/webhooks/stripe endpoint."""
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.STRIPE,
        gateway_order_id="cs_test_stripe_dedicated_1",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "id": "evt_stripe_dedicated_1",
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "id": "cs_test_stripe_dedicated_1",
                "payment_intent": "pi_stripe_ded_1",
                "amount_total": 1000000,
                "currency": "inr",
                "payment_status": "paid",
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig_header, _ = compute_stripe_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhooks/stripe",
            content=raw_body,
            headers={
                "Content-Type": "application/json",
                "stripe-signature": sig_header,
            },
        )
    assert resp.status_code == 200
    assert resp.json()["success"] is True

    db_order = db_session.query(PaymentOrder).filter_by(id=order.id).first()
    assert db_order.status == PaymentOrderStatus.PAID


def test_unknown_order_webhook_rejection(db_session, webhook_fixture):
    """Verifies that unmapped provider order returns 404 without guessing tenant."""
    payload_dict = {
        "event_id": "evt_rzp_unknown_999",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_unk_999",
                    "order_id": "order_rzp_nonexistent_999",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhooks/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
    assert resp.status_code == 404


def test_currency_mismatch_webhook_rejection(db_session, webhook_fixture):
    """Verifies that currency mismatch is strictly rejected."""
    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_curr_1",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "event_id": "evt_rzp_curr_1",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_curr_1",
                    "order_id": "order_rzp_wh_curr_1",
                    "amount": 1000000,
                    "currency": "USD",  # Mismatch!
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        resp = client.post(
            "/api/v1/payments/webhooks/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
    assert resp.status_code == 400
    res_json = resp.json()
    msg = res_json.get("error", {}).get("message") or res_json.get("message") or res_json.get("detail", "")
    assert "Currency mismatch" in msg


def test_payment_settlement_receipt_and_idempotency(db_session, webhook_fixture):
    """Verifies that repeated webhook deliveries produce exactly one FeePayment and Receipt."""
    from app.models.fees.fee_payment import FeePayment

    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_wh_settle_1",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    payload_dict = {
        "event_id": "evt_rzp_settle_1",
        "event": "payment.captured",
        "payload": {
            "payment": {
                "entity": {
                    "id": "pay_rzp_settle_1",
                    "order_id": "order_rzp_wh_settle_1",
                    "amount": 1000000,
                    "currency": "INR",
                }
            }
        },
    }
    raw_body = json.dumps(payload_dict).encode("utf-8")
    sig = compute_razorpay_webhook_sig(raw_body)

    with TestClient(fastapi_app) as client:
        # First Delivery
        resp1 = client.post(
            "/api/v1/payments/webhooks/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
        assert resp1.status_code == 200
        assert resp1.json()["processed"] is True

        # Second Delivery (Replay)
        resp2 = client.post(
            "/api/v1/payments/webhooks/razorpay",
            content=raw_body,
            headers={"x-razorpay-signature": sig},
        )
        assert resp2.status_code == 200
        assert resp2.json()["processed"] is False

    # Verify exactly one FeePayment exists
    payments = db_session.query(FeePayment).filter_by(
        student_fee_assignment_id=fx["assignment"].id
    ).all()
    assert len(payments) == 1
    assert payments[0].amount == Decimal("10000.00")
    assert payments[0].receipt_number is not None


def test_payment_config_get_and_update(db_session, webhook_fixture):
    """Verifies GET/PUT /api/v1/payments/config masks secrets and stores encrypted."""
    from app.identity.models.role import IdentityRole
    from app.identity.models.user import IdentityUser
    from app.identity.security.current_user import get_current_user

    fx = webhook_fixture
    super_admin_role = IdentityRole(
        id=uuid.uuid4(),
        school_id=fx["school"].id,
        name="Super Admin",
        description="Super Administrator",
    )
    db_session.add(super_admin_role)
    db_session.commit()

    admin_user = IdentityUser(
        id=uuid.uuid4(),
        email="admin.fin@school.com",
        username="admin_fin",
        password_hash="mock",
        first_name="Admin",
        last_name="Finance",
        school_id=fx["school"].id,
        is_active=True,
    )
    admin_user.roles = [super_admin_role]
    db_session.add(admin_user)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: admin_user

    with TestClient(fastapi_app) as client:
        # 1. Update config with test credentials
        put_resp = client.put(
            "/api/v1/payments/config",
            json={
                "razorpay_key_id": "rzp_live_key_999",
                "razorpay_key_secret": "rzp_secret_super_secret_val",
                "razorpay_webhook_secret": "rzp_wh_secret_super_val",
                "stripe_publishable_key": "pk_live_stripe_999",
                "stripe_secret_key": "sk_live_stripe_super_secret_val",
                "stripe_webhook_secret": "whsec_stripe_super_secret_val",
            },
        )
        assert put_resp.status_code == 200
        data = put_resp.json()
        assert data["razorpay_key_id"] == "rzp_live_key_999"
        assert "super_secret_val" not in (data.get("razorpay_key_secret_masked") or "")
        assert (data.get("razorpay_key_secret_masked") or "").startswith("••••")
        assert (data.get("stripe_secret_key_masked") or "").startswith("••••")

        # 2. GET config and verify secrets are strictly masked
        get_resp = client.get("/api/v1/payments/config")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["razorpay_key_id"] == "rzp_live_key_999"
        assert "super_secret" not in json.dumps(get_data)

    fastapi_app.dependency_overrides.pop(get_current_user, None)


def test_authoritative_order_status_polling(db_session, webhook_fixture):
    """Verifies GET /api/v1/payments/orders/{order_id} returns authoritative state."""
    from app.identity.models.role import IdentityRole
    from app.identity.models.user import IdentityUser
    from app.identity.security.current_user import get_current_user

    fx = webhook_fixture
    order = PaymentOrder(
        school_id=fx["school"].id,
        student_fee_assignment_id=fx["assignment"].id,
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="order_rzp_status_poll_1",
        amount=Decimal("10000.00"),
        currency="INR",
        status=PaymentOrderStatus.CREATED,
    )
    db_session.add(order)
    db_session.commit()

    admin_role = IdentityRole(
        id=uuid.uuid4(),
        school_id=fx["school"].id,
        name="Super Admin",
        description="Super Administrator",
    )
    db_session.add(admin_role)
    db_session.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        email="parent.wh@school.com",
        username="parent_wh",
        password_hash="mock",
        first_name="Parent",
        last_name="User",
        school_id=fx["school"].id,
        is_active=True,
    )
    user.roles = [admin_role]
    db_session.add(user)
    db_session.commit()

    fastapi_app.dependency_overrides[get_current_user] = lambda: user

    with TestClient(fastapi_app) as client:
        resp = client.get(f"/api/v1/payments/orders/{order.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["order_id"] == str(order.id)
        assert data["status"] == "CREATED"
        assert Decimal(str(data["amount"])) == Decimal("10000.00")
        assert data["is_settled"] is False

    fastapi_app.dependency_overrides.pop(get_current_user, None)

