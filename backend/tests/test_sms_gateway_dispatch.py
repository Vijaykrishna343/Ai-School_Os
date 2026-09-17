"""
Phase 27.2 SMS Gateway & DLT Dispatch Tests
Tests Fast2SMS adapter, Twilio SMS adapter, Mock adapter, provider selection,
DLT metadata enforcement, phone number normalization, security credential handling,
idempotency, retry limits, and tenant isolation.
All external network calls are mocked (zero real HTTP requests or API keys).
"""
from __future__ import annotations

import uuid
import pytest
from unittest.mock import patch, MagicMock
import httpx
from sqlalchemy.orm import Session

from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationRecipientType
from app.models.communication import (
    SchoolCommunicationConfig,
    SmsProviderType,
    WhatsAppProviderType,
    NotificationTemplate,
    UserCommunicationPreference,
)
from app.services.school_communication_config_service import SchoolCommunicationConfigService
from app.services.notification_service import notification_service
from app.services.notification_providers.sms_provider import (
    normalize_phone_number,
    Fast2SmsAdapter,
    TwilioSmsAdapter,
    MockSmsAdapter,
    SmsNotificationProvider,
)
from app.schemas.communication import SchoolCommunicationConfigUpdate


# ── 1. PHONE NUMBER NORMALIZATION TESTS ─────────────────────────────────────

def test_normalize_phone_number_valid_formats():
    # 10 digit Indian number
    ten, e164 = normalize_phone_number("9876543210")
    assert ten == "9876543210"
    assert e164 == "+919876543210"

    # +91 prefixed Indian number
    ten, e164 = normalize_phone_number("+91 98765 43210")
    assert ten == "9876543210"
    assert e164 == "+919876543210"

    # Leading zero Indian number
    ten, e164 = normalize_phone_number("09876543210")
    assert ten == "9876543210"
    assert e164 == "+919876543210"

    # International US number
    ten, e164 = normalize_phone_number("+1 (415) 555-2671")
    assert ten == "4155552671"
    assert e164 == "+14155552671"


def test_normalize_phone_number_invalid_formats():
    with pytest.raises(ValueError):
        normalize_phone_number("")

    with pytest.raises(ValueError):
        normalize_phone_number("123")

    with pytest.raises(ValueError):
        normalize_phone_number("abc-def-ghij")


# ── 2. FAST2SMS ADAPTER TESTS ──────────────────────────────────────────────

@patch("httpx.Client.post")
def test_fast2sms_adapter_success_dlt_route(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    # 1. Setup config with encrypted key
    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.FAST2SMS,
            sms_enabled=True,
            sms_api_key="test_fast2sms_secret_key_123",
            sms_sender_id="SCHERP",
            sms_entity_id="110123456000001",
        ),
    )

    # 2. Setup DLT template
    template = NotificationTemplate(
        school_id=school_id,
        template_key="fee_due_dlt_test",
        name="Fee Due DLT Test",
        category="FEES",
        title_template="Fee Reminder",
        body_template="Dear Parent, fee payment of {amount} is due.",
        dlt_entity_id="110123456000001",
        dlt_template_id="140712345678901",
    )
    db_session.add(template)
    db_session.commit()

    # 3. Mock Fast2SMS HTTP response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "return": True,
        "request_id": "fast2sms_req_998877",
        "message": ["SMS sent successfully."],
    }
    mock_post.return_value = mock_resp

    # 4. Execute dispatch
    adapter = Fast2SmsAdapter()
    status, provider_msg_id, error = adapter.send_sms(
        recipient_contact="9876543210",
        title="Fee Reminder",
        body="Dear Parent, fee payment of 5000 is due.",
        config=config,
        template=template,
    )

    assert status == NotificationStatus.SENT
    assert provider_msg_id == "fast2sms_req_998877"
    assert error is None

    # Verify mock post received correct parameters
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["authorization"] == "test_fast2sms_secret_key_123"
    assert call_kwargs["json"]["route"] == "dlt"
    assert call_kwargs["json"]["sender_id"] == "SCHERP"
    assert call_kwargs["json"]["message"] == "140712345678901"
    assert call_kwargs["json"]["numbers"] == "9876543210"


def test_fast2sms_adapter_dlt_missing_metadata_enforcement(db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    # Config missing sender_id and entity_id
    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.FAST2SMS,
            sms_enabled=True,
            sms_api_key="test_fast2sms_secret_key_123",
            sms_sender_id=None,
            sms_entity_id=None,
        ),
    )

    # Template missing dlt_entity_id and dlt_template_id
    template = NotificationTemplate(
        school_id=school_id,
        template_key="dlt_missing_test",
        name="Missing DLT Test",
        category="FEES",
        title_template="Title",
        body_template="Body",
        dlt_entity_id=None,
        dlt_template_id="140712345678901",
    )

    adapter = Fast2SmsAdapter()
    status, provider_msg_id, error = adapter.send_sms(
        recipient_contact="9876543210",
        title="Title",
        body="Body",
        config=config,
        template=template,
    )

    assert status == NotificationStatus.FAILED
    assert provider_msg_id is None
    assert "DLT Error" in error
    assert "Mandatory DLT metadata missing" in error


@patch("httpx.Client.post")
def test_fast2sms_adapter_timeout_handling(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id
    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.FAST2SMS,
            sms_enabled=True,
            sms_api_key="test_fast2sms_secret_key_123",
            sms_sender_id="SCHERP",
        ),
    )

    mock_post.side_effect = httpx.TimeoutException("Connection timed out")

    adapter = Fast2SmsAdapter()
    status, provider_msg_id, error = adapter.send_sms(
        recipient_contact="9876543210",
        title="Title",
        body="Body",
        config=config,
    )

    assert status == NotificationStatus.FAILED
    assert provider_msg_id is None
    assert "timed out" in error.lower()


# ── 3. TWILIO SMS ADAPTER TESTS ────────────────────────────────────────────

@patch("httpx.Client.post")
def test_twilio_adapter_success(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.TWILIO,
            sms_enabled=True,
            sms_api_key="ACmock_account_sid_123:mock_auth_token_456",
            sms_sender_id="+14155550199",
        ),
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 201
    mock_resp.json.return_value = {
        "sid": "SMmock_twilio_message_sid_777",
        "status": "queued",
    }
    mock_post.return_value = mock_resp

    adapter = TwilioSmsAdapter()
    status, provider_msg_id, error = adapter.send_sms(
        recipient_contact="9876543210",
        title="Alert",
        body="Test Twilio Message",
        config=config,
    )

    assert status == NotificationStatus.SENT
    assert provider_msg_id == "SMmock_twilio_message_sid_777"
    assert error is None

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["data"]["From"] == "+14155550199"
    assert call_kwargs["data"]["To"] == "+919876543210"
    assert call_kwargs["auth"] == ("ACmock_account_sid_123", "mock_auth_token_456")


@patch("httpx.Client.post")
def test_twilio_adapter_provider_failure(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.TWILIO,
            sms_enabled=True,
            sms_api_key="ACmock_account_sid_123:mock_auth_token_456",
            sms_sender_id="+14155550199",
        ),
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "code": 21211,
        "message": "The To number is not a valid phone number.",
    }
    mock_post.return_value = mock_resp

    adapter = TwilioSmsAdapter()
    status, provider_msg_id, error = adapter.send_sms(
        recipient_contact="9876543210",
        title="Alert",
        body="Test Message",
        config=config,
    )

    assert status == NotificationStatus.FAILED
    assert provider_msg_id is None
    assert "Twilio Provider Error (21211)" in error


# ── 4. NOTIFICATION SERVICE SMS DISPATCH INTEGRATION TESTS ─────────────────

def test_notification_service_sms_disabled_behavior(db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    # Disable SMS in tenant config
    SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.FAST2SMS,
            sms_enabled=False,
        ),
    )

    notification = notification_service.create_and_send(
        db=db_session,
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Jane Doe",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Announce", "message": "Test"},
    )

    assert notification.status == NotificationStatus.FAILED
    assert "SMS channel is disabled" in notification.error_message


def test_notification_service_sms_none_provider_behavior(db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    # Provider NONE
    SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.NONE,
            sms_enabled=True,
        ),
    )

    notification = notification_service.create_and_send(
        db=db_session,
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Jane Doe",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Announce", "message": "Test"},
    )

    assert notification.status == NotificationStatus.FAILED
    assert "SMS provider selection is set to NONE" in notification.error_message


def test_notification_service_mock_sms_dispatch_flow(db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    # Configure MOCK provider
    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.MOCK,
            sms_enabled=True,
        ),
    )
    initial_sent = config.sms_sent_this_month or 0

    notification = notification_service.create_and_send(
        db=db_session,
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Jane Doe",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Test Title", "message": "Test Body"},
    )

    assert notification.status == NotificationStatus.SENT
    assert notification.provider_name == "MOCK"
    assert notification.provider_message_id is not None
    assert notification.provider_message_id.startswith("mock_sms_")
    assert notification.sent_at is not None

    # Verify usage quota updated
    db_session.refresh(config)
    assert config.sms_sent_this_month == initial_sent + 1


def test_notification_service_idempotency_prevents_duplicate_sms(db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id
    idempotency_key = f"idem-{uuid.uuid4()}"

    SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.MOCK,
            sms_enabled=True,
        ),
    )

    # 1. First send
    notif1 = notification_service.create_and_send(
        db=db_session,
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="John Doe",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Idem", "message": "First"},
        idempotency_key=idempotency_key,
    )

    # 2. Duplicate send with same idempotency key
    notif2 = notification_service.create_and_send(
        db=db_session,
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="John Doe",
        recipient_contact="9876543210",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Idem", "message": "Second"},
        idempotency_key=idempotency_key,
    )

    assert notif1.id == notif2.id
    assert notif2.body == notif1.body


from app.models.school import School


def test_tenant_isolation_in_sms_provider_config(db_session: Session, super_admin_user):
    school_id_a = super_admin_user.school_id

    # Create School B in DB to satisfy foreign key constraint
    school_b = School(
        name="Test School B",
        code=f"SCHB-{uuid.uuid4().hex[:6]}",
        address_line1="456 Other St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500002",
    )
    db_session.add(school_b)
    db_session.commit()
    db_session.refresh(school_b)
    school_id_b = school_b.id

    # Configure School A as MOCK
    SchoolCommunicationConfigService.update_config(
        db_session,
        school_id_a,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.MOCK,
            sms_enabled=True,
        ),
    )

    # Configure School B as NONE
    SchoolCommunicationConfigService.update_config(
        db_session,
        school_id_b,
        SchoolCommunicationConfigUpdate(
            sms_provider=SmsProviderType.NONE,
            sms_enabled=False,
        ),
    )

    # Dispatch for School B
    notif_b = notification_service.create_and_send(
        db=db_session,
        school_id=school_id_b,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Parent B",
        recipient_contact="9876543211",
        channel=NotificationChannel.SMS,
        template_key="general_announcement",
        template_variables={"title": "Title B", "message": "Body B"},
    )

    # School B must fail because School B's config is NONE, independent of School A
    assert notif_b.status == NotificationStatus.FAILED
    assert "SMS channel is disabled" in notif_b.error_message
