from datetime import datetime, timezone
from decimal import Decimal
import pytest

from app.common.enums.payment import PaymentOrderStatus, PaymentProvider, PaymentTransactionStatus
from app.common.exceptions.payment import (
    PaymentConfigurationError,
    PaymentInvalidRequestError,
    PaymentSignatureVerificationError,
    PaymentUnsupportedProviderError,
)
from app.schemas.payment import (
    GatewayOrderRequest,
    GatewayPaymentVerificationRequest,
)
from app.services.payment_gateway_service import PaymentGatewayFactory, payment_gateway_service
from app.services.payment_gateways.razorpay_adapter import RazorpayGatewayAdapter
from app.services.payment_gateways.stripe_adapter import StripeGatewayAdapter


def test_factory_resolution():
    razorpay_gw = PaymentGatewayFactory.get_gateway(
        PaymentProvider.RAZORPAY, key_id="rzp_test_123", key_secret="sec_123"
    )
    assert isinstance(razorpay_gw, RazorpayGatewayAdapter)
    assert razorpay_gw.provider == PaymentProvider.RAZORPAY

    stripe_gw = PaymentGatewayFactory.get_gateway(
        "stripe", key_id="pk_test_123", key_secret="sk_test_123"
    )
    assert isinstance(stripe_gw, StripeGatewayAdapter)
    assert stripe_gw.provider == PaymentProvider.STRIPE

    with pytest.raises(PaymentUnsupportedProviderError):
        PaymentGatewayFactory.get_gateway("OTHER")

    with pytest.raises(PaymentUnsupportedProviderError):
        PaymentGatewayFactory.get_gateway("INVALID_PROVIDER")


def test_order_creation_decimal_precision():
    gw = RazorpayGatewayAdapter(key_id="rzp_test", key_secret="rzp_secret")

    test_amounts = [
        (Decimal("100.00"), 10000),
        (Decimal("100.50"), 10050),
        (Decimal("999.99"), 99999),
        (Decimal("12345.67"), 1234567),
    ]

    for amount_dec, expected_paise in test_amounts:
        req = GatewayOrderRequest(
            amount=amount_dec,
            currency="INR",
            receipt="rcpt_1001",
            customer_name="Test Parent",
        )
        res = gw.create_order(req)
        assert res.provider == PaymentProvider.RAZORPAY
        assert res.amount == amount_dec
        assert res.status == PaymentOrderStatus.CREATED
        assert res.raw_response["amount"] == expected_paise
        assert res.raw_response["amount_due"] == expected_paise

    # Zero or negative amounts must fail
    with pytest.raises(Exception):
        GatewayOrderRequest(amount=Decimal("0.00"), receipt="rcpt_zero")

    with pytest.raises(PaymentInvalidRequestError):
        gw._get_amount_in_subunits(Decimal("-10.00"))


def test_razorpay_payment_verification_signature():
    secret = "sample_razorpay_secret_key_123"
    gw = RazorpayGatewayAdapter(key_id="rzp_key", key_secret=secret)

    order_id = "order_N6x8Y9zA"
    payment_id = "pay_P1q2R3s4"

    # Compute valid signature
    import hashlib, hmac
    valid_sig = hmac.new(
        secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    req_valid = GatewayPaymentVerificationRequest(
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=order_id,
        gateway_payment_id=payment_id,
        gateway_signature=valid_sig,
    )
    result_valid = gw.verify_payment_signature(req_valid)
    assert result_valid.is_valid is True
    assert result_valid.provider == PaymentProvider.RAZORPAY

    req_invalid = GatewayPaymentVerificationRequest(
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id=order_id,
        gateway_payment_id=payment_id,
        gateway_signature="forged_invalid_signature_hex",
    )
    result_invalid = gw.verify_payment_signature(req_invalid)
    assert result_invalid.is_valid is False


def test_razorpay_webhook_signature_and_event_normalization():
    webhook_secret = "razorpay_wh_secret_999"
    gw = RazorpayGatewayAdapter(key_id="key", key_secret="sec", webhook_secret=webhook_secret)

    raw_payload = '{"event":"order.paid","payload":{"order":{"entity":{"id":"order_1001","amount":50000,"currency":"INR"}},"payment":{"entity":{"id":"pay_2002","order_id":"order_1001","amount":50000,"currency":"INR"}}}}'

    import hashlib, hmac
    valid_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        raw_payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    assert gw.verify_webhook_signature(raw_payload, valid_sig) is True
    assert gw.verify_webhook_signature(raw_payload, "invalid_sig") is False

    # Normalization
    event = gw.parse_webhook_event(raw_payload, signature=valid_sig)
    assert event.provider == PaymentProvider.RAZORPAY
    assert event.event_type == "order.paid"
    assert event.gateway_order_id == "order_1001"
    assert event.gateway_transaction_id == "pay_2002"
    assert event.amount == Decimal("500.00")
    assert event.currency == "INR"
    assert event.status == PaymentTransactionStatus.SUCCESS

    # Tampered signature should raise error
    with pytest.raises(PaymentSignatureVerificationError):
        gw.parse_webhook_event(raw_payload, signature="tampered_sig")


def test_stripe_webhook_signature_and_event_normalization():
    webhook_secret = "whsec_stripe_test_secret_777"
    gw = StripeGatewayAdapter(publishable_key="pk", secret_key="sk", webhook_secret=webhook_secret)

    timestamp = str(int(datetime.now(timezone.utc).timestamp()))
    raw_payload = '{"id":"evt_stripe_123","type":"checkout.session.completed","data":{"object":{"id":"cs_test_999","payment_intent":"pi_888","amount_total":75000,"currency":"inr"}}}'

    signed_payload = f"{timestamp}.{raw_payload}".encode("utf-8")
    import hashlib, hmac
    v1_sig = hmac.new(
        webhook_secret.encode("utf-8"),
        signed_payload,
        hashlib.sha256,
    ).hexdigest()

    sig_header = f"t={timestamp},v1={v1_sig}"

    assert gw.verify_webhook_signature(raw_payload, sig_header) is True
    assert gw.verify_webhook_signature(raw_payload, f"t={timestamp},v1=invalid") is False

    # Event normalization
    event = gw.parse_webhook_event(raw_payload, signature=sig_header)
    assert event.provider == PaymentProvider.STRIPE
    assert event.event_id == "evt_stripe_123"
    assert event.event_type == "checkout.session.completed"
    assert event.gateway_order_id == "cs_test_999"
    assert event.gateway_transaction_id == "pi_888"
    assert event.amount == Decimal("750.00")
    assert event.currency == "INR"
    assert event.status == PaymentTransactionStatus.SUCCESS


def test_missing_credentials_configuration_error():
    gw_unconfigured = RazorpayGatewayAdapter(key_id="", key_secret="", webhook_secret="")

    req = GatewayOrderRequest(amount=Decimal("100.00"), receipt="rcpt_1")
    with pytest.raises(PaymentConfigurationError):
        gw_unconfigured.create_order(req)

    ver_req = GatewayPaymentVerificationRequest(
        provider=PaymentProvider.RAZORPAY,
        gateway_order_id="ord_1",
        gateway_payment_id="pay_1",
        gateway_signature="sig",
    )
    with pytest.raises(PaymentConfigurationError):
        gw_unconfigured.verify_payment_signature(ver_req)


def test_tenant_credentials_isolation():
    # Tenant A and Tenant B gateways must not leak secrets or share state
    gw_tenant_a = PaymentGatewayFactory.get_gateway(
        PaymentProvider.RAZORPAY, key_id="key_tenant_a", key_secret="secret_a", webhook_secret="wh_a"
    )
    gw_tenant_b = PaymentGatewayFactory.get_gateway(
        PaymentProvider.RAZORPAY, key_id="key_tenant_b", key_secret="secret_b", webhook_secret="wh_b"
    )

    assert gw_tenant_a.key_id == "key_tenant_a"
    assert gw_tenant_b.key_id == "key_tenant_b"
    assert gw_tenant_a.key_secret != gw_tenant_b.key_secret

    # Verify secret credentials do not appear in string representation or DTOs
    order_req = GatewayOrderRequest(amount=Decimal("250.00"), receipt="rcpt_a")
    order_res = gw_tenant_a.create_order(order_req)

    res_dict_str = str(order_res.model_dump())
    assert "secret_a" not in res_dict_str
    assert "wh_a" not in res_dict_str
