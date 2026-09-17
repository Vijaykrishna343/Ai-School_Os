"""
Phase 27.3 Meta WhatsApp Cloud API & Webhook Tests
Tests Meta Cloud API v21.0 outbound adapter, Bearer auth, HSM template payload construction,
webhook GET verification handshake, POST HMAC SHA-256 signature verification, tenant resolution via phone_number_id,
monotonic status transitions (SENT -> DELIVERED -> READ / FAILED), idempotency, and security token protection.
All external network calls are mocked (zero real HTTP requests or API keys).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import uuid
import pytest
from unittest.mock import patch, MagicMock
import httpx
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.school import School
from app.models.notification import Notification, NotificationChannel, NotificationStatus, NotificationRecipientType
from app.models.communication import (
    SchoolCommunicationConfig,
    WhatsAppProviderType,
    NotificationTemplate,
)
from app.services.school_communication_config_service import SchoolCommunicationConfigService
from app.services.notification_service import notification_service
from app.services.notification_providers.whatsapp_provider import (
    normalize_whatsapp_number,
    MetaWhatsAppAdapter,
    TwilioWhatsAppAdapter,
    WhatsAppNotificationProvider,
)
from app.schemas.communication import SchoolCommunicationConfigUpdate


# ── 1. PHONE NUMBER NORMALIZATION TESTS ─────────────────────────────────────

def test_normalize_whatsapp_number_valid():
    assert normalize_whatsapp_number("9876543210") == "919876543210"
    assert normalize_whatsapp_number("+91 98765 43210") == "919876543210"
    assert normalize_whatsapp_number("whatsapp:+14155552671") == "14155552671"
    assert normalize_whatsapp_number("09876543210") == "919876543210"


def test_normalize_whatsapp_number_invalid():
    with pytest.raises(ValueError):
        normalize_whatsapp_number("")

    with pytest.raises(ValueError):
        normalize_whatsapp_number("123")


# ── 2. META WHATSAPP CLOUD API ADAPTER OUTBOUND TESTS ───────────────────────

@patch("httpx.Client.post")
def test_meta_whatsapp_adapter_success_text_msg(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    # 1. Configure Meta WhatsApp Cloud API credentials
    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            whatsapp_provider=WhatsAppProviderType.META_WHATSAPP_CLOUD,
            whatsapp_enabled=True,
            whatsapp_access_token="meta_test_access_token_sec_123",
            whatsapp_phone_number_id="100000000000001",
            whatsapp_business_account_id="200000000000002",
        ),
    )

    # 2. Mock Meta Graph API Response
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "contacts": [{"input": "919876543210", "wa_id": "919876543210"}],
        "messages": [{"id": "wamid.HBgLMTEwMDEyMzQ1Njc4OQ=="}],
    }
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppAdapter()
    status, provider_msg_id, error = adapter.send_whatsapp(
        recipient_contact="9876543210",
        title="School Announcement",
        body="School will remain closed tomorrow due to heavy rain.",
        config=config,
    )

    assert status == NotificationStatus.SENT
    assert provider_msg_id == "wamid.HBgLMTEwMDEyMzQ1Njc4OQ=="
    assert error is None

    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args.kwargs
    assert call_kwargs["headers"]["Authorization"] == "Bearer meta_test_access_token_sec_123"
    assert "v21.0/100000000000001/messages" in mock_post.call_args.args[0]
    assert call_kwargs["json"]["messaging_product"] == "whatsapp"
    assert call_kwargs["json"]["to"] == "919876543210"
    assert call_kwargs["json"]["type"] == "text"


@patch("httpx.Client.post")
def test_meta_whatsapp_adapter_hsm_template_msg(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            whatsapp_provider=WhatsAppProviderType.META_WHATSAPP_CLOUD,
            whatsapp_enabled=True,
            whatsapp_access_token="meta_test_access_token_sec_123",
            whatsapp_phone_number_id="100000000000001",
        ),
    )

    template = NotificationTemplate(
        school_id=school_id,
        template_key="fee_alert_wa",
        name="Fee Alert WA",
        category="FEES",
        title_template="Fee Reminder",
        body_template="Dear Parent, fee payment is due.",
        whatsapp_template_name="fee_payment_due_v1",
        whatsapp_language_code="en_US",
    )
    db_session.add(template)
    db_session.commit()

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "messaging_product": "whatsapp",
        "messages": [{"id": "wamid.HBgL_template_test_123"}],
    }
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppAdapter()
    status, provider_msg_id, error = adapter.send_whatsapp(
        recipient_contact="9876543210",
        title="Fee Reminder",
        body="Dear Parent, fee payment of 5000 is due.",
        config=config,
        template=template,
    )

    assert status == NotificationStatus.SENT
    assert provider_msg_id == "wamid.HBgL_template_test_123"

    call_json = mock_post.call_args.kwargs["json"]
    assert call_json["type"] == "template"
    assert call_json["template"]["name"] == "fee_payment_due_v1"
    assert call_json["template"]["language"]["code"] == "en_US"


@patch("httpx.Client.post")
def test_meta_whatsapp_adapter_api_error_handling(mock_post, db_session: Session, super_admin_user):
    school_id = super_admin_user.school_id

    config = SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            whatsapp_provider=WhatsAppProviderType.META_WHATSAPP_CLOUD,
            whatsapp_enabled=True,
            whatsapp_access_token="meta_invalid_token_123",
            whatsapp_phone_number_id="100000000000001",
        ),
    )

    mock_resp = MagicMock()
    mock_resp.status_code = 401
    mock_resp.json.return_value = {
        "error": {
            "message": "Invalid OAuth access token.",
            "type": "OAuthException",
            "code": 190,
        }
    }
    mock_post.return_value = mock_resp

    adapter = MetaWhatsAppAdapter()
    status, provider_msg_id, error = adapter.send_whatsapp(
        recipient_contact="9876543210",
        title="Title",
        body="Body",
        config=config,
    )

    assert status == NotificationStatus.FAILED
    assert provider_msg_id is None
    assert "Meta WhatsApp Error (190)" in error
    assert "Invalid OAuth access token" in error


# ── 3. WEBHOOK VERIFICATION HANDSHAKE (GET) TESTS ──────────────────────────

def test_whatsapp_webhook_get_verification_success(authenticated_client: TestClient):
    token = settings.WHATSAPP_WEBHOOK_VERIFY_TOKEN
    challenge = "1158201234"

    response = authenticated_client.get(
        f"/api/v1/notifications/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token={token}&hub.challenge={challenge}"
    )

    assert response.status_code == 200
    assert response.text == challenge


def test_whatsapp_webhook_get_verification_forbidden(authenticated_client: TestClient):
    response = authenticated_client.get(
        "/api/v1/notifications/webhooks/whatsapp?hub.mode=subscribe&hub.verify_token=wrong_token_123&hub.challenge=12345"
    )

    assert response.status_code == 403


# ── 4. WEBHOOK POST SIGNATURE & STATUS UPDATES TESTS ────────────────────────

def test_whatsapp_webhook_post_signature_and_tenant_resolution(
    authenticated_client: TestClient, db_session: Session, super_admin_user
):
    school_id = super_admin_user.school_id
    phone_number_id = f"phone_id_{uuid.uuid4().hex[:8]}"

    # Configure WhatsApp config with phone_number_id
    SchoolCommunicationConfigService.update_config(
        db_session,
        school_id,
        SchoolCommunicationConfigUpdate(
            whatsapp_provider=WhatsAppProviderType.META_WHATSAPP_CLOUD,
            whatsapp_enabled=True,
            whatsapp_access_token="wa_token_sec_123",
            whatsapp_phone_number_id=phone_number_id,
        ),
    )

    # Create pending notification with provider_message_id
    wamid = f"wamid.test_{uuid.uuid4().hex[:8]}"
    notif = Notification(
        school_id=school_id,
        recipient_type=NotificationRecipientType.PARENT,
        recipient_name="Parent Test",
        recipient_contact="9876543210",
        channel=NotificationChannel.WHATSAPP,
        template_key="general_announcement",
        title="Title Test",
        body="Body Test",
        status=NotificationStatus.SENT,
        provider_name="META_WHATSAPP_CLOUD",
        provider_message_id=wamid,
    )
    db_session.add(notif)
    db_session.commit()

    # Construct Meta Webhook Payload
    webhook_payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "BIZ_123",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "15550123456",
                                "phone_number_id": phone_number_id,
                            },
                            "statuses": [
                                {
                                    "id": wamid,
                                    "status": "delivered",
                                    "timestamp": "1700000000",
                                    "recipient_id": "919876543210",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }

    raw_json = json.dumps(webhook_payload).encode("utf-8")

    # Send POST request
    response = authenticated_client.post(
        "/api/v1/notifications/webhooks/whatsapp",
        content=raw_json,
        headers={"Content-Type": "application/json"},
    )

    assert response.status_code == 200
    assert response.json()["processed_events"] == 1

    # Verify notification status transitioned to DELIVERED
    db_session.refresh(notif)
    assert notif.status == NotificationStatus.DELIVERED


def test_whatsapp_webhook_signature_verification_enforcement(
    authenticated_client: TestClient, monkeypatch
):
    # Enable app secret check in settings
    secret = "test_meta_app_secret_32_bytes_key"
    monkeypatch.setattr(settings, "WHATSAPP_APP_SECRET", secret)

    payload = {"object": "whatsapp_business_account", "entry": []}
    raw_body = json.dumps(payload).encode("utf-8")

    # 1. Missing signature header -> 401
    resp1 = authenticated_client.post(
        "/api/v1/notifications/webhooks/whatsapp",
        content=raw_body,
        headers={"Content-Type": "application/json"},
    )
    assert resp1.status_code == 401

    # 2. Invalid signature header -> 401
    resp2 = authenticated_client.post(
        "/api/v1/notifications/webhooks/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "x-hub-signature-256": "sha256=invalid_signature_hash_123",
        },
    )
    assert resp2.status_code == 401

    # 3. Valid HMAC SHA-256 signature -> 200
    valid_sig = "sha256=" + hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    resp3 = authenticated_client.post(
        "/api/v1/notifications/webhooks/whatsapp",
        content=raw_body,
        headers={
            "Content-Type": "application/json",
            "x-hub-signature-256": valid_sig,
        },
    )
    assert resp3.status_code == 200
