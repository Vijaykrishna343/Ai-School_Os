"""
AI Communication Draft Pydantic Schemas for Phase 12.5.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ChannelVariantSchema(BaseModel):
    title: str = Field(..., description="Channel specific title or subject line")
    body: str = Field(..., description="Channel specific message content")

    model_config = ConfigDict(from_attributes=True)


class GenerateCommunicationDraftRequest(BaseModel):
    category: str = Field("ANNOUNCEMENT", description="ANNOUNCEMENT, ACADEMIC_NOTICE, EMERGENCY_ALERT, EVENT_INVITATION, PARENT_UPDATE")
    target_audience: str = Field("PARENTS", description="PARENTS, STUDENTS, TEACHERS, ALL_STAFF")
    tone: str = Field("FORMAL", description="FORMAL, URGENT, FRIENDLY, ENCOURAGING")
    key_details: str = Field(..., min_length=5, description="Event summary, notice details, or announcement prompt")
    requested_channels: List[str] = Field(default_factory=lambda: ["SMS", "EMAIL", "WHATSAPP", "IN_APP"], description="List of channels to generate")

    model_config = ConfigDict(from_attributes=True)


class CommunicationDraftResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    created_by_user_id: Optional[uuid.UUID] = None
    category: str
    target_audience: str
    tone: str
    prompt_summary: str
    channel_variants: Dict[str, ChannelVariantSchema]
    pii_redact_log: List[str] = Field(default_factory=list)
    token_count: int
    status: str
    assessed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CommunicationDraftListResponse(BaseModel):
    total: int
    drafts: List[CommunicationDraftResponse]

    model_config = ConfigDict(from_attributes=True)
