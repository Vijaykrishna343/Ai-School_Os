from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.timetable import TimetableStatus
from app.schemas.timetable.timetable_entry import TimetableEntryDetailResponse


class TimetableBase(BaseModel):
    """
    Shared fields for Timetable.
    """

    academic_year_id: UUID
    school_class_id: UUID
    section_id: UUID
    academic_term_id: UUID | None = None


class TimetableCreate(TimetableBase):
    """
    Request payload for creating a Timetable.
    """

    school_id: UUID


class TimetableUpdate(BaseModel):
    """
    Request payload for updating a Timetable.
    """

    academic_term_id: UUID | None = None
    is_active: bool | None = None


class TimetableResponse(TimetableBase):
    """
    API response representation for Timetable.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    status: TimetableStatus
    is_active: bool
    created_at: datetime
    updated_at: datetime


class TimetableDetailResponse(TimetableResponse):
    """
    Detailed Timetable response including full entry matrix for rendering.
    """

    entries: list[TimetableEntryDetailResponse] = Field(default_factory=list)


class TimetableListResponse(BaseModel):
    """
    Paginated API response representation for Timetable lists.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[TimetableResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class TimetableFilter(BaseModel):
    """
    Filter parameters for listing Timetables.
    """

    school_id: UUID | None = None
    academic_year_id: UUID | None = None
    school_class_id: UUID | None = None
    section_id: UUID | None = None
    academic_term_id: UUID | None = None
    status: TimetableStatus | None = None
    is_active: bool | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)


class TeacherScheduleEntryResponse(BaseModel):
    """
    Representation of a scheduled entry in a teacher's schedule view.
    """

    model_config = ConfigDict(from_attributes=True)

    entry_id: UUID
    timetable_id: UUID
    academic_year_id: UUID
    school_class_id: UUID
    section_id: UUID
    school_class_name: str
    section_name: str
    day_of_week: str
    period_slot: dict
    subject: dict
    classroom: dict | None = None
