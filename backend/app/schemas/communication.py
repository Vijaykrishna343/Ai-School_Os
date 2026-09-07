from __future__ import annotations

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


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


# ── Notification Template Schemas ─────────────────────────────────────────────

class NotificationTemplateCreate(BaseModel):
    template_key: str = Field(..., max_length=100)
    name: str = Field(..., max_length=150)
    category: str = Field(default="ANNOUNCEMENT")
    title_template: str = Field(..., min_length=2)
    body_template: str = Field(..., min_length=2)


class NotificationTemplateResponse(BaseModel):
    id: str
    template_key: str
    name: str
    category: str
    title_template: str
    body_template: str
    is_active: bool
    is_custom: bool


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
