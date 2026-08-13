from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProgressionExecutionRequest(BaseModel):
    """
    Request schema for executing academic progression rollover.
    """

    target_academic_year_id: UUID = Field(
        ...,
        description="ID of target academic year to promote students into.",
    )
    execution_plan_hash: str = Field(
        ...,
        min_length=64,
        max_length=64,
        description="SHA-256 plan hash returned by progression preview endpoint.",
    )
    confirm_warnings: bool = Field(
        default=False,
        description="Acknowledgement flag confirming execution despite preview warnings.",
    )


class ProgressionExecutionSummaryResponse(BaseModel):
    total_students_evaluated: int
    promoted_count: int
    graduated_count: int
    retained_count: int
    blocked_count: int
    excluded_count: int


class ProgressionExecutionData(BaseModel):
    execution_id: UUID
    status: str
    source_academic_year_id: UUID
    target_academic_year_id: UUID
    summary: ProgressionExecutionSummaryResponse
    started_at: datetime
    completed_at: datetime | None = None
    error_summary: str | None = None


class ProgressionExecutionResponse(BaseModel):
    success: bool = True
    message: str = "Academic progression rollover executed successfully."
    data: ProgressionExecutionData
