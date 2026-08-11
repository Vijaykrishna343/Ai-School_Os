from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GradeScaleEntryBase(BaseModel):
    grade_code: str = Field(
        ...,
        max_length=10,
        description="Grade symbol, e.g., A+, A, B",
    )
    min_percentage: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="Minimum percentage boundary",
    )
    max_percentage: Decimal = Field(
        ...,
        ge=0,
        le=100,
        description="Maximum percentage boundary",
    )
    grade_point: Decimal = Field(
        Decimal("0.00"),
        ge=0,
        description="GPA / Grade point value",
    )
    description: str | None = Field(None, max_length=100)
    is_pass: bool = Field(
        True,
        description="Whether this grade is considered a passing grade",
    )


class GradeScaleEntryCreate(GradeScaleEntryBase):
    pass


class GradeScaleEntryResponse(GradeScaleEntryBase):
    id: UUID
    grade_scale_id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GradeScaleBase(BaseModel):
    name: str = Field(
        ...,
        max_length=100,
        description="Name of grading scale, e.g. CBSE 10-Point Scale",
    )
    description: str | None = Field(None, description="Optional description")
    is_default: bool = Field(
        False,
        description="Set as default grading scale for the school",
    )


class GradeScaleCreate(GradeScaleBase):
    entries: list[GradeScaleEntryCreate] = Field(default_factory=list)


class GradeScaleUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    is_default: bool | None = None
    entries: list[GradeScaleEntryCreate] | None = None


class GradeScaleResponse(GradeScaleBase):
    id: UUID
    school_id: UUID
    entries: list[GradeScaleEntryResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class GradeScaleFilter(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
    search: str | None = None
    is_default: bool | None = None


class GradeScaleListResponse(BaseModel):
    items: list[GradeScaleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class GradeMatchRequest(BaseModel):
    percentage: Decimal = Field(..., ge=0, le=100)
    grade_scale_id: UUID | None = None


class GradeMatchResponse(BaseModel):
    percentage: Decimal
    matched_entry: GradeScaleEntryResponse | None = None