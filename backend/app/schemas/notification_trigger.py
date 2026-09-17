"""
Notification Trigger Event Schema — Phase 27.4.1 Foundation
Defines provider-neutral notification trigger event contracts for ERP business events.
"""
from __future__ import annotations

from uuid import UUID
from typing import Any
from pydantic import BaseModel, Field

from app.models.notification import NotificationChannel, NotificationRecipientType


class NotificationTriggerEvent(BaseModel):
    """
    Provider-neutral notification event payload emitted by ERP business operations.
    Contains non-sensitive entity identifiers and template variables required for dispatch.
    """
    event_type: str = Field(..., description="Canonical event identifier (e.g. visitor_checkin, fee_receipt)")
    school_id: UUID = Field(..., description="Mandatory tenant school ID")
    recipient_type: NotificationRecipientType = Field(..., description="Recipient user classification")
    recipient_name: str = Field(..., description="Recipient display name")
    recipient_contact: str = Field(..., description="Recipient phone number or email address")
    channel: NotificationChannel = Field(default=NotificationChannel.IN_APP, description="Target notification channel")
    template_key: str = Field(..., description="Notification template key")
    template_variables: dict[str, str] = Field(default_factory=dict, description="Template variable substitutions")
    recipient_id: UUID | None = Field(default=None, description="Optional recipient user ID for inbox/preference lookup")
    idempotency_key: str | None = Field(default=None, description="Deterministic idempotency key")
    event_metadata: dict[str, Any] | None = Field(default_factory=dict, description="Safe, non-sensitive audit metadata")

    model_config = {"from_attributes": True}
