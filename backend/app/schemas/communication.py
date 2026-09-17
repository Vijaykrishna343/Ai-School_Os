from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict
from app.models.communication import SmsProviderType, WhatsAppProviderType


# ── Preferences Schemas ────────────────────────────────────────────────────────

class UserCommunicationPreferenceResponse(BaseModel):
    id: UUID
    school_id: UUID
    user_id: UUID
    enable_in_app: bool
    enable_email: bool
    enable_sms: bool
    enable_whatsapp: bool
    enable_attendance: bool
    enable_fees: bool
    enable_exams: bool
    enable_events: bool
    enable_hostel: bool
    enable_leave: bool
    enable_emergency: bool
    enable_announcements: bool

    model_config = ConfigDict(from_attributes=True)


class UserCommunicationPreferenceUpdate(BaseModel):
    enable_in_app: bool | None = None
    enable_email: bool | None = None
    enable_sms: bool | None = None
    enable_whatsapp: bool | None = None
    enable_attendance: bool | None = None
    enable_fees: bool | None = None
    enable_exams: bool | None = None
    enable_events: bool | None = None
    enable_hostel: bool | None = None
    enable_leave: bool | None = None
    enable_announcements: bool | None = None


# ── School Communication Config Schemas ──────────────────────────────────────

class SchoolCommunicationConfigResponse(BaseModel):
    id: UUID
    school_id: UUID
    sms_provider: SmsProviderType
    whatsapp_provider: WhatsAppProviderType
    sms_enabled: bool
    whatsapp_enabled: bool
    sms_sender_id: str | None = None
    sms_entity_id: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    sms_configured: bool = False
    whatsapp_configured: bool = False
    sms_api_key_masked: str | None = None
    whatsapp_access_token_masked: str | None = None
    sms_monthly_quota: int = 10000
    sms_sent_this_month: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchoolCommunicationConfigUpdate(BaseModel):
    sms_provider: SmsProviderType | None = None
    whatsapp_provider: WhatsAppProviderType | None = None
    sms_enabled: bool | None = None
    whatsapp_enabled: bool | None = None
    sms_api_key: str | None = None
    sms_sender_id: str | None = None
    sms_entity_id: str | None = None
    whatsapp_access_token: str | None = None
    whatsapp_phone_number_id: str | None = None
    whatsapp_business_account_id: str | None = None
    sms_monthly_quota: int | None = None


# ── Notification Template Schemas ─────────────────────────────────────────────

class NotificationTemplateCreate(BaseModel):
    template_key: str = Field(..., max_length=100)
    name: str = Field(..., max_length=150)
    category: str = Field(default="ANNOUNCEMENT")
    title_template: str = Field(..., min_length=2)
    body_template: str = Field(..., min_length=2)
    dlt_entity_id: str | None = None
    dlt_template_id: str | None = None
    whatsapp_template_name: str | None = None
    whatsapp_language_code: str | None = None


class NotificationTemplateResponse(BaseModel):
    id: UUID | str
    template_key: str
    name: str
    category: str
    title_template: str
    body_template: str
    is_active: bool
    is_custom: bool = True
    dlt_entity_id: str | None = None
    dlt_template_id: str | None = None
    whatsapp_template_name: str | None = None
    whatsapp_language_code: str | None = None

    model_config = ConfigDict(from_attributes=True)



# ── Inbox & Provider Status Schemas ──────────────────────────────────────────

class InboxItemResponse(BaseModel):
    id: str
    title: str
    body: str
    template_key: str
    channel: str
    status: str
    is_read: bool
    created_at: str | None = None


class ProviderStatusResponse(BaseModel):
    channel: str
    provider_name: str
    is_configured: bool
    status: str


# ── Notification Detail & Analytics Schemas ──────────────────────────────────

class NotificationDetailResponse(BaseModel):
    id: UUID
    school_id: UUID
    recipient_type: str
    recipient_id: UUID | None = None
    recipient_name: str
    recipient_contact: str
    channel: str
    template_key: str
    title: str
    body: str
    status: str
    error_message: str | None = None
    sent_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    provider_name: str | None = None
    provider_message_id: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    idempotency_key: str | None = None

    model_config = ConfigDict(from_attributes=True)


class DailyVolumeItem(BaseModel):
    date: str
    count: int
    sent: int = 0
    failed: int = 0


class NotificationAnalyticsResponse(BaseModel):
    total_notifications: int
    sent_count: int
    delivered_count: int
    failed_count: int
    pending_count: int
    cancelled_count: int
    success_rate_percent: float
    failure_rate_percent: float
    pending_rate_percent: float
    by_channel: dict[str, int]
    by_event: dict[str, int]
    daily_volume: list[DailyVolumeItem]
    providers: list[ProviderStatusResponse]

    model_config = ConfigDict(from_attributes=True)

