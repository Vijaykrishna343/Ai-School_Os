"""
Pydantic Schemas for Background Jobs — Phase 2 Workstream 3.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.models.background_job import JobStatus, JobType


class BackgroundJobCreate(BaseModel):
    job_type: JobType
    payload: dict[str, Any] = Field(default_factory=dict)
    idempotency_key: str | None = None
    max_retries: int = 3


class BackgroundJobResponse(BaseModel):
    id: UUID
    school_id: UUID
    created_by_user_id: UUID
    job_type: JobType
    status: JobStatus
    progress_percentage: int
    processed_items: int
    total_items: int
    payload: dict[str, Any]
    result: dict[str, Any] | None = None
    error_message: str | None = None
    idempotency_key: str | None = None
    retry_count: int
    max_retries: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BatchNotificationAsyncRequest(BaseModel):
    template_key: str
    template_variables: dict[str, str] = Field(default_factory=dict)
    recipients: list[dict[str, str]]
    channel: str = "IN_APP"
    idempotency_key: str | None = None
