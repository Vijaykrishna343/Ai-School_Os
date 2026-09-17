from __future__ import annotations

from uuid import UUID
from sqlalchemy.orm import Session
from app.models.communication import (
    SchoolCommunicationConfig,
    SmsProviderType,
    WhatsAppProviderType,
)
from app.schemas.communication import (
    SchoolCommunicationConfigUpdate,
    SchoolCommunicationConfigResponse,
)
from app.common.security.encryption import (
    encrypt_credential,
    decrypt_credential,
    mask_credential,
)


class SchoolCommunicationConfigService:

    @staticmethod
    def get_or_create_config(db: Session, school_id: UUID) -> SchoolCommunicationConfig:
        """Fetch the school's communication config, creating a default entry if one does not exist."""
        config = (
            db.query(SchoolCommunicationConfig)
            .filter(
                SchoolCommunicationConfig.school_id == school_id,
                SchoolCommunicationConfig.is_deleted.is_(False),
            )
            .first()
        )
        if not config:
            config = SchoolCommunicationConfig(
                school_id=school_id,
                sms_provider=SmsProviderType.MOCK,
                whatsapp_provider=WhatsAppProviderType.MOCK,
                sms_enabled=True,
                whatsapp_enabled=True,
                sms_monthly_quota=10000,
                sms_sent_this_month=0,
            )
            db.add(config)
            db.commit()
            db.refresh(config)
        return config

    @staticmethod
    def update_config(
        db: Session, school_id: UUID, updates: SchoolCommunicationConfigUpdate
    ) -> SchoolCommunicationConfig:
        """Update provider configuration and securely encrypt any new credentials provided."""
        config = SchoolCommunicationConfigService.get_or_create_config(db, school_id)

        if updates.sms_provider is not None:
            config.sms_provider = updates.sms_provider
        if updates.whatsapp_provider is not None:
            config.whatsapp_provider = updates.whatsapp_provider
        if updates.sms_enabled is not None:
            config.sms_enabled = updates.sms_enabled
        if updates.whatsapp_enabled is not None:
            config.whatsapp_enabled = updates.whatsapp_enabled
        if updates.sms_sender_id is not None:
            config.sms_sender_id = updates.sms_sender_id
        if updates.sms_entity_id is not None:
            config.sms_entity_id = updates.sms_entity_id
        if updates.whatsapp_phone_number_id is not None:
            config.whatsapp_phone_number_id = updates.whatsapp_phone_number_id
        if updates.whatsapp_business_account_id is not None:
            config.whatsapp_business_account_id = updates.whatsapp_business_account_id
        if updates.sms_monthly_quota is not None:
            config.sms_monthly_quota = updates.sms_monthly_quota

        # Handle secret updates cleanly (encrypted at rest)
        if updates.sms_api_key is not None:
            if updates.sms_api_key.strip():
                config.sms_api_key_encrypted = encrypt_credential(updates.sms_api_key.strip())
            else:
                config.sms_api_key_encrypted = None

        if updates.whatsapp_access_token is not None:
            if updates.whatsapp_access_token.strip():
                config.whatsapp_access_token_encrypted = encrypt_credential(
                    updates.whatsapp_access_token.strip()
                )
            else:
                config.whatsapp_access_token_encrypted = None

        db.add(config)
        db.commit()
        db.refresh(config)
        return config

    @staticmethod
    def to_response_dto(config: SchoolCommunicationConfig) -> SchoolCommunicationConfigResponse:
        """Convert ORM model to response DTO ensuring plaintext secrets are NEVER returned."""
        sms_decrypted = decrypt_credential(config.sms_api_key_encrypted)
        wa_decrypted = decrypt_credential(config.whatsapp_access_token_encrypted)

        sms_configured = (
            config.sms_provider == SmsProviderType.MOCK
            or bool(config.sms_api_key_encrypted)
        )
        whatsapp_configured = (
            config.whatsapp_provider == WhatsAppProviderType.MOCK
            or bool(config.whatsapp_access_token_encrypted)
        )

        return SchoolCommunicationConfigResponse(
            id=config.id,
            school_id=config.school_id,
            sms_provider=config.sms_provider,
            whatsapp_provider=config.whatsapp_provider,
            sms_enabled=config.sms_enabled,
            whatsapp_enabled=config.whatsapp_enabled,
            sms_sender_id=config.sms_sender_id,
            sms_entity_id=config.sms_entity_id,
            whatsapp_phone_number_id=config.whatsapp_phone_number_id,
            whatsapp_business_account_id=config.whatsapp_business_account_id,
            sms_configured=sms_configured,
            whatsapp_configured=whatsapp_configured,
            sms_api_key_masked=mask_credential(sms_decrypted),
            whatsapp_access_token_masked=mask_credential(wa_decrypted),
            sms_monthly_quota=config.sms_monthly_quota,
            sms_sent_this_month=config.sms_sent_this_month,
            created_at=config.created_at,
            updated_at=config.updated_at,
        )
