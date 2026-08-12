from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.timetable.timetable_entry import (
    TeacherNested,
    TimetableEntryDetailResponse,
)


class TeacherSubstitutionBase(BaseModel):
    """
    Shared fields for TeacherSubstitution.
    """

    timetable_entry_id: UUID
    substitution_date: date
    substitute_teacher_id: UUID
    remarks: str | None = Field(default=None, max_length=255)


class TeacherSubstitutionCreate(TeacherSubstitutionBase):
    """
    Request payload for creating a TeacherSubstitution.
    """

    school_id: UUID


class TeacherSubstitutionUpdate(BaseModel):
    """
    Request payload for updating a TeacherSubstitution.
    """

    substitute_teacher_id: UUID | None = None
    remarks: str | None = Field(default=None, max_length=255)


class TeacherSubstitutionResponse(BaseModel):
    """
    API response representation for TeacherSubstitution.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    timetable_entry_id: UUID
    substitution_date: date
    original_teacher_id: UUID
    substitute_teacher_id: UUID
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime


class TeacherSubstitutionDetailResponse(TeacherSubstitutionResponse):
    """
    Detailed TeacherSubstitution response including nested teacher and entry objects.
    """

    original_teacher: TeacherNested
    substitute_teacher: TeacherNested
    timetable_entry: TimetableEntryDetailResponse


class TeacherSubstitutionListResponse(BaseModel):
    """
    Paginated API response representation for TeacherSubstitution lists.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[TeacherSubstitutionDetailResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TeacherSubstitutionFilter(BaseModel):
    """
    Filter parameters for listing TeacherSubstitutions.
    """

    school_id: UUID | None = None
    timetable_entry_id: UUID | None = None
    original_teacher_id: UUID | None = None
    substitute_teacher_id: UUID | None = None
    substitution_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
