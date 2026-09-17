from __future__ import annotations

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.security.encryption import (
    encrypt_credential,
    decrypt_credential,
    mask_credential,
)
from app.models.communication import (
    SchoolCommunicationConfig,
    SmsProviderType,
    WhatsAppProviderType,
    NotificationTemplate,
)
from app.services.school_communication_config_service import SchoolCommunicationConfigService
from app.schemas.communication import SchoolCommunicationConfigUpdate


def test_encryption_utility_unit():
    """Test Fernet authenticated encryption, decryption, and masking."""
    secret = "my_secret_fast2sms_api_key_12345"
    encrypted = encrypt_credential(secret)
    assert encrypted is not None
    assert encrypted != secret
    assert "12345" not in encrypted

    decrypted = decrypt_credential(encrypted)
    assert decrypted == secret

    masked = mask_credential(decrypted)
    assert masked == "••••••••"
    assert "12345" not in masked

    assert mask_credential(None) is None


def test_service_get_or_create_and_update(db_session: Session, super_admin_user):
    """Test service layer get_or_create, credential encryption at rest, and secret rotation."""
    school_id = super_admin_user.school_id

    # 1. Get or create default config
    config = SchoolCommunicationConfigService.get_or_create_config(db_session, school_id)
    assert config.school_id == school_id
    assert config.sms_provider == SmsProviderType.MOCK
    assert config.sms_enabled is True

    # DTO should have unconfigured state and None masked secret for secrets
    dto = SchoolCommunicationConfigService.to_response_dto(config)
    assert dto.sms_configured is True
    assert dto.sms_api_key_masked is None

    # 2. Update config with credentials
    updates = SchoolCommunicationConfigUpdate(
        sms_provider=SmsProviderType.FAST2SMS,
        whatsapp_provider=WhatsAppProviderType.META_WHATSAPP_CLOUD,
        sms_enabled=True,
        whatsapp_enabled=True,
        sms_api_key="super_secret_sms_key_v1",
        sms_sender_id="SCHLOB",
        sms_entity_id="DLT_ENT_999",
        whatsapp_access_token="meta_token_abc_123",
        whatsapp_phone_number_id="WA_PHONE_111",
        whatsapp_business_account_id="WA_BIZ_222",
    )
    updated_config = SchoolCommunicationConfigService.update_config(db_session, school_id, updates)

    # Secrets must be stored encrypted in DB
    assert updated_config.sms_api_key_encrypted is not None
    assert "super_secret_sms_key_v1" not in updated_config.sms_api_key_encrypted
    assert decrypt_credential(updated_config.sms_api_key_encrypted) == "super_secret_sms_key_v1"

    assert updated_config.whatsapp_access_token_encrypted is not None
    assert "meta_token_abc_123" not in updated_config.whatsapp_access_token_encrypted
    assert decrypt_credential(updated_config.whatsapp_access_token_encrypted) == "meta_token_abc_123"

    # DTO must expose only masked indicator and metadata
    dto2 = SchoolCommunicationConfigService.to_response_dto(updated_config)
    assert dto2.sms_provider == SmsProviderType.FAST2SMS
    assert dto2.sms_configured is True
    assert dto2.sms_api_key_masked == "••••••••"
    assert dto2.whatsapp_configured is True
    assert dto2.whatsapp_access_token_masked == "••••••••"
    assert dto2.sms_sender_id == "SCHLOB"
    assert dto2.sms_entity_id == "DLT_ENT_999"

    # 3. Credential rotation test
    rotation_updates = SchoolCommunicationConfigUpdate(
        sms_api_key="super_secret_sms_key_v2_rotated",
    )
    rotated_config = SchoolCommunicationConfigService.update_config(db_session, school_id, rotation_updates)
    assert decrypt_credential(rotated_config.sms_api_key_encrypted) == "super_secret_sms_key_v2_rotated"
    dto_rotated = SchoolCommunicationConfigService.to_response_dto(rotated_config)
    assert dto_rotated.sms_api_key_masked == "••••••••"
    assert "v2_rotated" not in dto_rotated.model_dump_json()


def test_api_get_and_put_config(authenticated_client: TestClient, db_session: Session, super_admin_user):
    """Test GET and PUT /api/v1/notifications/config API endpoints with authentication, RBAC, and masking."""

    # GET config
    response = authenticated_client.get("/api/v1/notifications/config")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "sms_provider" in data["data"]
    assert "sms_api_key_encrypted" not in data["data"]

    # PUT config update
    payload = {
        "sms_provider": "FAST2SMS",
        "whatsapp_provider": "META_WHATSAPP_CLOUD",
        "sms_enabled": True,
        "whatsapp_enabled": True,
        "sms_api_key": "fast2sms_secret_key_777",
        "sms_sender_id": "MYSCHL",
        "sms_entity_id": "170115998877",
        "whatsapp_access_token": "wa_token_secret_888",
        "whatsapp_phone_number_id": "1002345",
        "whatsapp_business_account_id": "2003456",
    }
    update_res = authenticated_client.put("/api/v1/notifications/config", json=payload)
    assert update_res.status_code == 200
    res_data = update_res.json()["data"]

    assert res_data["sms_provider"] == "FAST2SMS"
    assert res_data["whatsapp_provider"] == "META_WHATSAPP_CLOUD"
    assert res_data["sms_enabled"] is True
    assert res_data["whatsapp_enabled"] is True
    assert res_data["sms_configured"] is True
    assert res_data["whatsapp_configured"] is True
    assert res_data["sms_api_key_masked"] == "••••••••"
    assert res_data["whatsapp_access_token_masked"] == "••••••••"
    assert res_data["sms_sender_id"] == "MYSCHL"
    assert res_data["sms_entity_id"] == "170115998877"

    # CRITICAL SECURITY CHECK: Ensure raw secret string NEVER appears anywhere in raw response JSON
    raw_response_text = update_res.text
    assert "fast2sms_secret_key_777" not in raw_response_text
    assert "wa_token_secret_888" not in raw_response_text


def test_dlt_template_metadata_persistence(authenticated_client: TestClient, db_session: Session, super_admin_user):
    """Test creating custom notification template with Indian SMS DLT and WhatsApp metadata."""
    payload = {
        "template_key": "dlt_fee_reminder_alert",
        "name": "DLT Fee Reminder Template",
        "category": "FEES",
        "title_template": "Fee Due: {student_name}",
        "body_template": "Dear parent, fee of Rs.{amount} is due by {due_date}.",
        "dlt_entity_id": "DLT_ENT_123456",
        "dlt_template_id": "DLT_TPL_654321",
        "whatsapp_template_name": "fee_due_template_v1",
        "whatsapp_language_code": "en_US",
    }

    res = authenticated_client.post("/api/v1/notifications/templates", json=payload)
    assert res.status_code == 201
    tpl_data = res.json()["data"]

    assert tpl_data["template_key"] == "dlt_fee_reminder_alert"
    assert tpl_data["dlt_entity_id"] == "DLT_ENT_123456"
    assert tpl_data["dlt_template_id"] == "DLT_TPL_654321"
    assert tpl_data["whatsapp_template_name"] == "fee_due_template_v1"
    assert tpl_data["whatsapp_language_code"] == "en_US"

    # Verify template resolution via list endpoint
    list_res = authenticated_client.get("/api/v1/notifications/templates")
    assert list_res.status_code == 200
    all_tpls = list_res.json()["data"]
    target = next((t for t in all_tpls if t["template_key"] == "dlt_fee_reminder_alert"), None)
    assert target is not None
    assert target["dlt_entity_id"] == "DLT_ENT_123456"
    assert target["dlt_template_id"] == "DLT_TPL_654321"

