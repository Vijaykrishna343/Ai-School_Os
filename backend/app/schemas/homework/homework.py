"""
Homework Pydantic Schemas.
"""
from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.homework.homework import HomeworkStatus


class HomeworkCreate(BaseModel):
    teacher_id: UUID | None = None
    school_class_id: UUID
    section_id: UUID | None = None
    subject_id: UUID
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    assigned_date: date | None = None
    due_date: date


class HomeworkUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    due_date: date | None = None
    status: HomeworkStatus | None = None


class HomeworkResponse(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    school_class_id: UUID
    section_id: UUID | None = None
    subject_id: UUID
    title: str
    description: str
    assigned_date: date
    due_date: date
    status: HomeworkStatus
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    # Hydrated fields
    teacher_name: str | None = None
    school_class_name: str | None = None
    section_name: str | None = None
    subject_name: str | None = None
    submission_count: int = 0

    model_config = {"from_attributes": True}


class HomeworkListResponse(BaseModel):
    items: list[HomeworkResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class HomeworkSummaryResponse(BaseModel):
    total_homework: int
    draft_count: int
    published_count: int
    due_soon_count: int
    closed_count: int
