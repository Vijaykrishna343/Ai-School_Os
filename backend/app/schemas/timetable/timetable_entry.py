from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.timetable import DayOfWeek, PeriodType, RoomType


class TimetableEntryBase(BaseModel):
    """
    Shared fields for TimetableEntry.
    """

    day_of_week: DayOfWeek
    period_slot_id: UUID
    subject_id: UUID
    teacher_id: UUID
    classroom_id: UUID | None = None


class TimetableEntryCreate(TimetableEntryBase):
    """
    Request payload for creating a TimetableEntry.
    """

    pass


class TimetableEntryUpdate(BaseModel):
    """
    Request payload for updating a TimetableEntry.
    """

    day_of_week: DayOfWeek | None = None
    period_slot_id: UUID | None = None
    subject_id: UUID | None = None
    teacher_id: UUID | None = None
    classroom_id: UUID | None = None


class TimetableEntryResponse(TimetableEntryBase):
    """
    API response representation for TimetableEntry.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timetable_id: UUID
    created_at: datetime
    updated_at: datetime


class PeriodSlotNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    period_type: PeriodType
    start_time: time
    end_time: time
    display_order: int


class SubjectNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subject_name: str
    subject_code: str


class TeacherNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    first_name: str
    last_name: str
    employee_id: str


class ClassroomNested(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    room_number: str
    building_name: str | None = None
    capacity: int
    room_type: RoomType


class TimetableEntryDetailResponse(BaseModel):
    """
    Detailed response for TimetableEntry with nested entity details for frontend rendering.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    timetable_id: UUID
    day_of_week: DayOfWeek
    period_slot_id: UUID
    subject_id: UUID
    teacher_id: UUID
    classroom_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    period_slot: PeriodSlotNested
    subject: SubjectNested
    teacher: TeacherNested
    classroom: ClassroomNested | None = None
