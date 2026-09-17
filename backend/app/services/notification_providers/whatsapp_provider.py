"""
WhatsApp Notification Provider Adapters — Phase 27.3
Implements Meta WhatsApp Cloud API v21.0 adapter, Twilio WhatsApp adapter, and Mock adapter.
Enforces multi-tenant isolated configuration, Fernet token decryption at execution time,
template/HSM messaging, recipient phone normalization, HTTPS security, and timeouts.
"""
from __future__ import annotations

import abc
import os
import re
import uuid
from typing import Optional
import httpx
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.common.logger.logger import get_logger
from app.common.security.encryption import decrypt_credential
from app.models.notification import Notification, NotificationChannel, NotificationStatus
from app.models.communication import (
    SchoolCommunicationConfig,
    WhatsAppProviderType,
    NotificationTemplate,
)
from app.services.notification_providers.base_provider import BaseNotificationProvider

logger = get_logger(__name__)


def normalize_whatsapp_number(raw_contact: str) -> str:
    """
    Normalizes a WhatsApp recipient phone number into clean digits (e.g. '919876543210').
    Strips 'whatsapp:', leading '+', spaces, and dashes.
    Raises ValueError if invalid.
    """
    if not raw_contact or not str(raw_contact).strip():
        raise ValueError("Recipient WhatsApp number is empty.")

    contact_str = str(raw_contact).strip()
    if contact_str.lower().startswith("whatsapp:"):
        contact_str = contact_str[9:]

    digits = re.sub(r"\D", "", contact_str)

    if len(digits) == 10:
        digits = f"91{digits}"
    elif digits.startswith("0") and len(digits) == 11:
        digits = f"91{digits[1:]}"

    if len(digits) < 10 or len(digits) > 15:
        raise ValueError(f"Invalid WhatsApp recipient number format: '{raw_contact}'")

    return digits


class BaseWhatsAppAdapter(abc.ABC):
    """
    Abstract Base Class for WhatsApp Gateway Adapters.
    """

    @abc.abstractmethod
    def send_whatsapp(
        self,
        recipient_contact: str,
        title: str,
        body: str,
        config: SchoolCommunicationConfig,
        template: Optional[NotificationTemplate] = None,
    ) -> tuple[NotificationStatus, Optional[str], Optional[str]]:
        """
        Dispatches WhatsApp message.
        Returns tuple of (NotificationStatus, provider_message_id, error_message).
        """
        ...


class MetaWhatsAppAdapter(BaseWhatsAppAdapter):
    """
    Meta WhatsApp Cloud API Gateway Adapter (Graph API v21.0).
    Endpoint: https://graph.facebook.com/v21.0/{phone_number_id}/messages
    """
    META_GRAPH_VERSION = "v21.0"

    def send_whatsapp(
        self,
        recipient_contact: str,
        title: str,
        body: str,
        config: SchoolCommunicationConfig,
        template: Optional[NotificationTemplate] = None,
    ) -> tuple[NotificationStatus, Optional[str], Optional[str]]:
        # 1. Decrypt Access Token
        access_token = decrypt_credential(config.whatsapp_access_token_encrypted)
        if not access_token:
            return NotificationStatus.FAILED, None, "Meta WhatsApp Error: Access token is missing or failed to decrypt."

        phone_number_id = config.whatsapp_phone_number_id
        if not phone_number_id:
            return NotificationStatus.FAILED, None, "Meta WhatsApp Error: WhatsApp Phone Number ID is not configured."

        # 2. Normalize Phone Number
        try:
            clean_digits = normalize_whatsapp_number(recipient_contact)
        except ValueError as err:
            return NotificationStatus.FAILED, None, f"Meta WhatsApp Error: {err}"

        # 3. Construct Graph API Request Payload
        graph_url = f"https://graph.facebook.com/{self.META_GRAPH_VERSION}/{phone_number_id}/messages"

        if template and template.whatsapp_template_name:
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_digits,
                "type": "template",
                "template": {
                    "name": template.whatsapp_template_name,
                    "language": {"code": template.whatsapp_language_code or "en"},
                    "components": [
                        {
                            "type": "body",
                            "parameters": [{"type": "text", "text": body}],
                        }
                    ],
                },
            }
        else:
            message_text = f"*{title}*\n\n{body}" if title else body
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": clean_digits,
                "type": "text",
                "text": {"body": message_text},
            }

        headers = {
            "Authorization": f"Bearer {access_token.strip()}",
            "Content-Type": "application/json",
        }

        # 4. Execute HTTPS Outbound Request (10.0s Timeout)
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(graph_url, json=payload, headers=headers)

            if resp.status_code in (200, 201):
                data = resp.json()
                messages = data.get("messages", [])
                wamid = messages[0].get("id") if messages and isinstance(messages, list) else None
                return NotificationStatus.SENT, str(wamid or f"meta_wamid_{clean_digits}"), None
            else:
                data = resp.json()
                err = data.get("error", {})
                code = err.get("code")
                msg = err.get("message", "Meta Graph API request rejected.")
                return NotificationStatus.FAILED, None, f"Meta WhatsApp Error ({code}): {msg}"

        except httpx.TimeoutException:
            logger.error("Meta WhatsApp request timed out for school %s", config.school_id)
            return NotificationStatus.FAILED, None, "Meta WhatsApp Error: Outbound HTTP request timed out."
        except httpx.RequestError as exc:
            logger.error("Meta WhatsApp network error for school %s: %s", config.school_id, type(exc).__name__)
            return NotificationStatus.FAILED, None, f"Meta WhatsApp Error: Network failure ({type(exc).__name__})."
        except Exception as exc:
            logger.error("Meta WhatsApp dispatch error for school %s: %s", config.school_id, type(exc).__name__)
            return NotificationStatus.FAILED, None, f"Meta WhatsApp Error: Unexpected failure ({type(exc).__name__})."


class TwilioWhatsAppAdapter(BaseWhatsAppAdapter):
    """
    Twilio WhatsApp Gateway Adapter.
    """

    def send_whatsapp(
        self,
        recipient_contact: str,
        title: str,
        body: str,
        config: SchoolCommunicationConfig,
        template: Optional[NotificationTemplate] = None,
    ) -> tuple[NotificationStatus, Optional[str], Optional[str]]:
        decrypted_key = decrypt_credential(config.whatsapp_access_token_encrypted)
        account_sid: Optional[str] = None
        auth_token: Optional[str] = None

        if decrypted_key and ":" in decrypted_key:
            parts = decrypted_key.split(":", 1)
            account_sid = parts[0].strip()
            auth_token = parts[1].strip()

        if not account_sid:
            account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        if not auth_token:
            auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        whatsapp_number = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

        if not account_sid or not auth_token:
            return (
                NotificationStatus.FAILED,
                None,
                "Twilio WhatsApp Error: Account SID or Auth Token missing.",
            )

        try:
            clean_digits = normalize_whatsapp_number(recipient_contact)
            target = f"whatsapp:+{clean_digits}"
        except ValueError as err:
            return NotificationStatus.FAILED, None, f"Twilio WhatsApp Error: {err}"

        twilio_url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Messages.json"
        data = {
            "From": whatsapp_number,
            "To": target,
            "Body": f"*{title}*\n\n{body}" if title else body,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(twilio_url, data=data, auth=(account_sid, auth_token))

            if resp.status_code in (200, 201):
                sid = resp.json().get("sid")
                return NotificationStatus.SENT, str(sid), None
            else:
                resp_json = resp.json()
                code = resp_json.get("code")
                msg = resp_json.get("message", "Twilio WhatsApp dispatch failed.")
                return NotificationStatus.FAILED, None, f"Twilio WhatsApp Error ({code}): {msg}"

        except httpx.TimeoutException:
            logger.error("Twilio WhatsApp request timed out for school %s", config.school_id)
            return NotificationStatus.FAILED, None, "Twilio WhatsApp Error: Outbound HTTP request timed out."
        except httpx.RequestError as exc:
            logger.error("Twilio WhatsApp network error for school %s: %s", config.school_id, type(exc).__name__)
            return NotificationStatus.FAILED, None, f"Twilio WhatsApp Error: Network failure ({type(exc).__name__})."
        except Exception as exc:
            logger.error("Twilio WhatsApp dispatch error for school %s: %s", config.school_id, type(exc).__name__)
            return NotificationStatus.FAILED, None, f"Twilio WhatsApp Error: Unexpected failure ({type(exc).__name__})."


class MockWhatsAppAdapter(BaseWhatsAppAdapter):
    """
    Mock WhatsApp Adapter for local development & testing.
    """

    def send_whatsapp(
        self,
        recipient_contact: str,
        title: str,
        body: str,
        config: SchoolCommunicationConfig,
        template: Optional[NotificationTemplate] = None,
    ) -> tuple[NotificationStatus, Optional[str], Optional[str]]:
        mock_wamid = f"mock_wamid_{uuid.uuid4().hex[:10]}"
        logger.info(
            "[MOCK WHATSAPP ADAPTER] Dispatched contact=%s | title='%s' | body='%s' | mock_wamid=%s",
            recipient_contact,
            title,
            body,
            mock_wamid,
        )
        return NotificationStatus.SENT, mock_wamid, None


class WhatsAppNotificationProvider(BaseNotificationProvider):
    """
    Production WhatsApp Channel Dispatcher.
    Loads tenant communication config, resolves Meta WhatsApp Cloud API / Twilio / Mock adapter,
    and records provider dispatch metadata.
    """

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.WHATSAPP

    @property
    def provider_name(self) -> str:
        return "tenant_whatsapp_provider"

    def send(
        self, notification: Notification, db: Optional[Session] = None
    ) -> tuple[NotificationStatus, Optional[str]]:
        if not db:
            return NotificationStatus.SENT, None

        # 1. Fetch Tenant Configuration
        from app.services.school_communication_config_service import SchoolCommunicationConfigService
        config = SchoolCommunicationConfigService.get_or_create_config(db, notification.school_id)

        # 2. Check explicitly disabled channel for configured providers
        if not config.whatsapp_enabled and config.whatsapp_provider in (
            WhatsAppProviderType.META_WHATSAPP_CLOUD,
            WhatsAppProviderType.TWILIO_WHATSAPP,
        ):
            return NotificationStatus.FAILED, "WhatsApp channel is disabled for this school."

        if config.whatsapp_provider == WhatsAppProviderType.NONE and not config.whatsapp_enabled:
            return NotificationStatus.FAILED, "WhatsApp provider selection is set to NONE for this school."

        # 3. Fetch Notification Template for HSM Metadata
        template: Optional[NotificationTemplate] = None
        if notification.template_key:
            template = db.scalar(
                select(NotificationTemplate).where(
                    NotificationTemplate.school_id == notification.school_id,
                    NotificationTemplate.template_key == notification.template_key,
                    NotificationTemplate.is_deleted.is_(False),
                )
            )

        # 4. Select Gateway Adapter
        adapter: BaseWhatsAppAdapter
        if config.whatsapp_provider == WhatsAppProviderType.META_WHATSAPP_CLOUD:
            adapter = MetaWhatsAppAdapter()
        elif config.whatsapp_provider == WhatsAppProviderType.TWILIO_WHATSAPP:
            adapter = TwilioWhatsAppAdapter()
        else:
            # Fallback for MOCK or unconfigured default in dev/test
            adapter = MockWhatsAppAdapter()

        # 5. Execute Adapter Dispatch
        status, provider_msg_id, error = adapter.send_whatsapp(
            recipient_contact=notification.recipient_contact,
            title=notification.title,
            body=notification.body,
            config=config,
            template=template,
        )

        # 6. Populate Notification Record Metadata
        notification.provider_name = config.whatsapp_provider.value
        notification.provider_message_id = provider_msg_id

        return status, error
