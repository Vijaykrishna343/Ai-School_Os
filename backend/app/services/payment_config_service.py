from __future__ import annotations

import os
from typing import Any
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.common.enums.payment import PaymentProvider
from app.common.logger.logger import get_logger
from app.common.security.encryption import (
    decrypt_credential,
    encrypt_credential,
    mask_credential,
)
from app.core.config import settings
from app.schemas.payment import PaymentConfigResponse, PaymentConfigUpdate

logger = get_logger(__name__)


class PaymentConfigService:
    """
    Manages payment provider configuration and encrypted credentials at rest.
    Enforces write-only secrets, masking in API responses, and multi-tenant isolation.
    """

    # In-memory tenant store fallback for encrypted credentials when DB table is not used
    _tenant_configs: dict[str, dict[str, Any]] = {}

    @classmethod
    def get_config(cls, school_id: UUID | str | None = None) -> PaymentConfigResponse:
        """
        Retrieves current payment provider configuration with secrets strictly masked.
        """
        key = str(school_id) if school_id else "global"
        stored = cls._tenant_configs.get(key, {})

        # Razorpay
        rzp_key_id = stored.get("razorpay_key_id") or getattr(settings, "RAZORPAY_KEY_ID", "") or ""
        rzp_key_secret_enc = stored.get("razorpay_key_secret_encrypted")
        rzp_secret_val = decrypt_credential(rzp_key_secret_enc) if rzp_key_secret_enc else getattr(settings, "RAZORPAY_KEY_SECRET", "")
        
        rzp_webhook_secret_enc = stored.get("razorpay_webhook_secret_encrypted")
        rzp_wh_val = decrypt_credential(rzp_webhook_secret_enc) if rzp_webhook_secret_enc else getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "")

        # Stripe
        stripe_pub_key = stored.get("stripe_publishable_key") or getattr(settings, "STRIPE_PUBLISHABLE_KEY", "") or ""
        stripe_secret_enc = stored.get("stripe_secret_key_encrypted")
        stripe_sec_val = decrypt_credential(stripe_secret_enc) if stripe_secret_enc else getattr(settings, "STRIPE_SECRET_KEY", "")
        
        stripe_wh_enc = stored.get("stripe_webhook_secret_encrypted")
        stripe_wh_val = decrypt_credential(stripe_wh_enc) if stripe_wh_enc else getattr(settings, "STRIPE_WEBHOOK_SECRET", "")

        return PaymentConfigResponse(
            school_id=school_id,
            razorpay_enabled=bool(rzp_key_id and rzp_secret_val),
            razorpay_key_id=rzp_key_id,
            razorpay_key_secret_masked=mask_credential(rzp_secret_val) if rzp_secret_val else None,
            razorpay_webhook_secret_masked=mask_credential(rzp_wh_val) if rzp_wh_val else None,
            razorpay_webhook_url="/api/v1/payments/webhooks/razorpay",
            stripe_enabled=bool(stripe_pub_key and stripe_sec_val),
            stripe_publishable_key=stripe_pub_key,
            stripe_secret_key_masked=mask_credential(stripe_sec_val) if stripe_sec_val else None,
            stripe_webhook_secret_masked=mask_credential(stripe_wh_val) if stripe_wh_val else None,
            stripe_webhook_url="/api/v1/payments/webhooks/stripe",
        )

    @classmethod
    def update_config(
        cls, updates: PaymentConfigUpdate, school_id: UUID | str | None = None
    ) -> PaymentConfigResponse:
        """
        Updates payment configuration and securely encrypts new credentials at rest.
        """
        key = str(school_id) if school_id else "global"
        if key not in cls._tenant_configs:
            cls._tenant_configs[key] = {}

        stored = cls._tenant_configs[key]

        # Update Razorpay Key ID
        if updates.razorpay_key_id is not None:
            stored["razorpay_key_id"] = updates.razorpay_key_id.strip()

        # Update Razorpay Key Secret (encrypted)
        if updates.razorpay_key_secret is not None:
            if updates.razorpay_key_secret.strip():
                stored["razorpay_key_secret_encrypted"] = encrypt_credential(updates.razorpay_key_secret.strip())
            else:
                stored["razorpay_key_secret_encrypted"] = None

        # Update Razorpay Webhook Secret (encrypted)
        if updates.razorpay_webhook_secret is not None:
            if updates.razorpay_webhook_secret.strip():
                stored["razorpay_webhook_secret_encrypted"] = encrypt_credential(updates.razorpay_webhook_secret.strip())
            else:
                stored["razorpay_webhook_secret_encrypted"] = None

        # Update Stripe Publishable Key
        if updates.stripe_publishable_key is not None:
            stored["stripe_publishable_key"] = updates.stripe_publishable_key.strip()

        # Update Stripe Secret Key (encrypted)
        if updates.stripe_secret_key is not None:
            if updates.stripe_secret_key.strip():
                stored["stripe_secret_key_encrypted"] = encrypt_credential(updates.stripe_secret_key.strip())
            else:
                stored["stripe_secret_key_encrypted"] = None

        # Update Stripe Webhook Secret (encrypted)
        if updates.stripe_webhook_secret is not None:
            if updates.stripe_webhook_secret.strip():
                stored["stripe_webhook_secret_encrypted"] = encrypt_credential(updates.stripe_webhook_secret.strip())
            else:
                stored["stripe_webhook_secret_encrypted"] = None

        logger.info("Payment provider configuration updated for school %s", key)
        return cls.get_config(school_id)

    @classmethod
    def resolve_credentials(
        cls, provider: PaymentProvider, school_id: UUID | str | None = None
    ) -> tuple[str, str, str]:
        """
        Resolves active plaintext credentials securely in-memory for gateway execution.
        Returns: (key_id, key_secret, webhook_secret)
        """
        key = str(school_id) if school_id else "global"
        stored = cls._tenant_configs.get(key, {})

        if provider == PaymentProvider.RAZORPAY:
            key_id = stored.get("razorpay_key_id") or getattr(settings, "RAZORPAY_KEY_ID", "") or ""
            key_sec_enc = stored.get("razorpay_key_secret_encrypted")
            key_sec = decrypt_credential(key_sec_enc) if key_sec_enc else (getattr(settings, "RAZORPAY_KEY_SECRET", "") or "")
            
            wh_sec_enc = stored.get("razorpay_webhook_secret_encrypted")
            wh_sec = decrypt_credential(wh_sec_enc) if wh_sec_enc else (getattr(settings, "RAZORPAY_WEBHOOK_SECRET", "") or "")
            return (key_id, key_sec, wh_sec)

        if provider == PaymentProvider.STRIPE:
            pub_key = stored.get("stripe_publishable_key") or getattr(settings, "STRIPE_PUBLISHABLE_KEY", "") or ""
            sec_enc = stored.get("stripe_secret_key_encrypted")
            sec = decrypt_credential(sec_enc) if sec_enc else (getattr(settings, "STRIPE_SECRET_KEY", "") or "")
            
            wh_enc = stored.get("stripe_webhook_secret_encrypted")
            wh_sec = decrypt_credential(wh_enc) if wh_enc else (getattr(settings, "STRIPE_WEBHOOK_SECRET", "") or "")
            return (pub_key, sec, wh_sec)

        return ("", "", "")


payment_config_service = PaymentConfigService()
