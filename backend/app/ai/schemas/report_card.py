"""
AI Report Card Remarks Pydantic Schemas for Phase 12.6.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GenerateReportCardRemarksRequest(BaseModel):
    report_card_id: uuid.UUID = Field(..., description="ID of target report card")
    tone: str = Field("BALANCED", description="BALANCED, ENCOURAGING, DIRECT, ACADEMIC_FOCUS")
    detail_level: str = Field("DETAILED", description="CONCISE, DETAILED")

    model_config = ConfigDict(from_attributes=True)


class ApplyReportCardRemarksRequest(BaseModel):
    report_card_id: uuid.UUID = Field(..., description="ID of target report card")
    teacher_remarks: Optional[str] = Field(None, description="Teacher remarks to apply")
    principal_remarks: Optional[str] = Field(None, description="Principal remarks to apply")

    model_config = ConfigDict(from_attributes=True)


class ReportCardRemarksResponse(BaseModel):
    id: uuid.UUID
    school_id: uuid.UUID
    report_card_id: uuid.UUID
    student_id: uuid.UUID
    created_by_user_id: Optional[uuid.UUID] = None
    tone: str
    detail_level: str
    teacher_remarks_draft: str
    principal_remarks_draft: str
    action_items: List[str] = Field(default_factory=list)
    strength_subjects: List[str] = Field(default_factory=list)
    focus_subjects: List[str] = Field(default_factory=list)
    token_count: int
    status: str
    assessed_at: datetime
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
