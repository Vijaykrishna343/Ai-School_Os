from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import AttendanceStatus


class AttendanceCreate(BaseModel):
    """
    Request body for creating an individual Attendance record.
    """

    student_id: UUID
    attendance_date: date
    status: AttendanceStatus
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceBulkItem(BaseModel):
    """
    Individual student record inside a bulk attendance payload.
    """

    student_id: UUID
    status: AttendanceStatus
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceBulkCreate(BaseModel):
    """
    Request body for marking bulk attendance for an entire class/section.
    """

    section_id: UUID
    attendance_date: date
    records: list[AttendanceBulkItem] = Field(..., min_length=1)


class AttendanceUpdate(BaseModel):
    """
    Request body for updating an existing Attendance record.
    """

    status: AttendanceStatus | None = None
    remarks: str | None = Field(default=None, max_length=255)


class AttendanceResponse(BaseModel):
    """
    API response representation for Attendance.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    school_class_id: UUID
    section_id: UUID
    student_id: UUID
    attendance_date: date
    status: AttendanceStatus
    remarks: str | None = None
    recorded_by_user_id: UUID | None = None
    created_at: datetime
    updated_at: datetime


class AttendanceListResponse(BaseModel):
    """
    Paginated API response representation for Attendance lists.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[AttendanceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
