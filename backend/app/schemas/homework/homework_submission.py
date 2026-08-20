"""
HomeworkSubmission Pydantic Schemas.
"""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.homework.homework_submission import SubmissionStatus


class HomeworkSubmissionCreate(BaseModel):
    content_text: str = Field(..., min_length=1)


class HomeworkSubmissionGrade(BaseModel):
    grade: str = Field(..., min_length=1, max_length=50)
    feedback: str | None = None


class HomeworkSubmissionResponse(BaseModel):
    id: UUID
    school_id: UUID
    homework_id: UUID
    student_id: UUID
    submitted_at: datetime
    status: SubmissionStatus
    content_text: str
    grade: str | None = None
    feedback: str | None = None
    reviewed_at: datetime | None = None
    reviewed_by_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    # Hydrated fields
    student_name: str | None = None
    admission_number: str | None = None
    homework_title: str | None = None
    subject_name: str | None = None

    model_config = {"from_attributes": True}


class HomeworkSubmissionListResponse(BaseModel):
    items: list[HomeworkSubmissionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
