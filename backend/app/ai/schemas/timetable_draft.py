from __future__ import annotations

import uuid
from typing import Any
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class TimetableGenerateRequest(BaseModel):
    academic_year_id: uuid.UUID
    name: str = "AI Timetable Draft"
    timeout_seconds: float = 30.0
    class_section_ids: list[uuid.UUID] | None = None


class DraftEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_class_id: uuid.UUID
    section_id: uuid.UUID
    subject_id: uuid.UUID
    teacher_id: uuid.UUID
    classroom_id: uuid.UUID | None = None
    period_slot_id: uuid.UUID
    day_of_week: str


class AITimetableDraftResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID
    academic_year_id: uuid.UUID
    name: str
    status: str
    solver_status: str
    objective_score: int
    solver_duration_ms: int
    constraint_summary: dict[str, Any] | None = None
    validation_report: dict[str, Any] | None = None
    error_message: str | None = None
    created_by_id: uuid.UUID
    approved_by_id: uuid.UUID | None = None
    published_by_id: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
    approved_at: datetime | None = None
    published_at: datetime | None = None
    entries: list[DraftEntryResponse] = []
