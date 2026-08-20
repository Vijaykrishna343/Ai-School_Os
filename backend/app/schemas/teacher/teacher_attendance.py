from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field

from app.common.enums import AttendanceStatus


class TeacherAttendanceCreate(BaseModel):
    teacher_id: UUID
    attendance_date: date
    status: AttendanceStatus = AttendanceStatus.PRESENT
    check_in_time: str | None = None
    check_out_time: str | None = None
    remarks: str | None = None


class TeacherAttendanceUpdate(BaseModel):
    status: AttendanceStatus | None = None
    check_in_time: str | None = None
    check_out_time: str | None = None
    remarks: str | None = None


class TeacherAttendanceResponse(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    teacher_name: str | None = None
    employee_id: str | None = None
    department: str | None = None
    attendance_date: date
    status: AttendanceStatus
    check_in_time: str | None = None
    check_out_time: str | None = None
    remarks: str | None = None

    model_config = {"from_attributes": True}


class BulkTeacherAttendanceItem(BaseModel):
    teacher_id: UUID
    status: AttendanceStatus = AttendanceStatus.PRESENT
    check_in_time: str | None = None
    check_out_time: str | None = None
    remarks: str | None = None


class BulkTeacherAttendanceRequest(BaseModel):
    attendance_date: date
    items: list[BulkTeacherAttendanceItem]


class TeacherAttendanceSummaryResponse(BaseModel):
    attendance_date: date
    total_teachers: int
    present_count: int
    absent_count: int
    late_count: int
    leave_count: int
    half_day_count: int
