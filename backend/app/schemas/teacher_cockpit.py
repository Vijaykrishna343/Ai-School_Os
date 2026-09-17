"""
Teacher Classroom Command Cockpit Schemas — Phase 30.3
Strongly-typed contracts for teacher daily operational workspace.
"""
from __future__ import annotations

from datetime import date, time
from typing import Any, Dict, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TeacherProfileHeader(BaseModel):
    """Basic teacher identity and school context for the cockpit header."""
    model_config = ConfigDict(from_attributes=True)

    teacher_id: Optional[UUID] = None
    first_name: str
    last_name: str
    full_name: str
    employee_id: Optional[str] = None
    email: str
    phone: Optional[str] = None
    qualification: Optional[str] = None
    specialization: Optional[str] = None
    school_id: UUID
    school_name: str


class CockpitMetricsSummary(BaseModel):
    """High-level metrics summary for today's operational load."""
    model_config = ConfigDict(from_attributes=True)

    total_classes_today: int = 0
    completed_classes_today: int = 0
    pending_attendance_count: int = 0
    active_homework_count: int = 0
    pending_homework_reviews_count: int = 0
    upcoming_exams_count: int = 0
    active_alerts_count: int = 0


class CockpitScheduleEntry(BaseModel):
    """Single period timetable entry for today with status and attendance metadata."""
    model_config = ConfigDict(from_attributes=True)

    timetable_entry_id: UUID
    timetable_id: UUID
    period_slot_id: UUID
    slot_number: int
    slot_name: str
    start_time: str
    end_time: str
    period_type: str
    subject_id: UUID
    subject_name: str
    subject_code: str
    school_class_id: UUID
    class_name: str
    section_id: Optional[UUID] = None
    section_name: Optional[str] = None
    classroom_id: Optional[UUID] = None
    room_number: Optional[str] = None
    building: Optional[str] = None
    is_substitution: bool = False
    original_teacher_id: Optional[UUID] = None
    original_teacher_name: Optional[str] = None
    status: str = "UPCOMING"  # COMPLETED, IN_PROGRESS, UPCOMING
    attendance_marked: bool = False
    attendance_stats: Optional[Dict[str, int]] = None


class CurrentAndNextClass(BaseModel):
    """Active class in session and the immediate next upcoming class."""
    model_config = ConfigDict(from_attributes=True)

    current_class: Optional[CockpitScheduleEntry] = None
    next_class: Optional[CockpitScheduleEntry] = None


class CockpitAttendanceSection(BaseModel):
    """Class/section attendance roster status for today."""
    model_config = ConfigDict(from_attributes=True)

    school_class_id: UUID
    class_name: str
    section_id: UUID
    section_name: str
    is_marked: bool = False
    total_students: int = 0
    present_count: int = 0
    absent_count: int = 0
    late_count: int = 0
    half_day_count: int = 0
    attendance_pct: float = 0.0


class CockpitHomeworkItem(BaseModel):
    """Active or recent homework assignment created by the teacher."""
    model_config = ConfigDict(from_attributes=True)

    homework_id: UUID
    title: str
    description: Optional[str] = None
    subject_name: str
    class_name: str
    section_name: Optional[str] = None
    assigned_date: str
    due_date: str
    status: str
    total_submissions: int = 0
    graded_submissions: int = 0
    pending_review_count: int = 0


class CockpitExamItem(BaseModel):
    """Upcoming examination schedule relevant to teacher's subjects/classes."""
    model_config = ConfigDict(from_attributes=True)

    exam_id: UUID
    exam_name: str
    exam_schedule_id: UUID
    subject_name: str
    class_name: str
    section_name: Optional[str] = None
    exam_date: str
    start_time: str
    end_time: str
    max_marks: float
    passing_marks: float
    results_entered_count: int = 0
    total_students_count: int = 0
    grading_status: str = "NOT_STARTED"  # NOT_STARTED, IN_PROGRESS, COMPLETED


class CockpitAlertItem(BaseModel):
    """Operational notification/reminder for the teacher."""
    model_config = ConfigDict(from_attributes=True)

    id: str
    severity: str = "INFO"  # INFO, WARNING, URGENT, SUCCESS
    title: str
    message: str
    category: str  # ATTENDANCE, HOMEWORK, EXAM, TIMETABLE, GENERAL
    action_route: Optional[str] = None


class CockpitQuickActions(BaseModel):
    """Authorized action permissions and target frontend routes."""
    model_config = ConfigDict(from_attributes=True)

    can_mark_attendance: bool = False
    can_manage_homework: bool = False
    can_enter_marks: bool = False
    can_view_timetable: bool = False
    can_apply_leave: bool = False


class TeacherCockpitResponse(BaseModel):
    """Consolidated root response for the Teacher Classroom Command Cockpit."""
    model_config = ConfigDict(from_attributes=True)

    today_date: str
    day_of_week: str
    teacher: TeacherProfileHeader
    summary: CockpitMetricsSummary
    current_and_next: CurrentAndNextClass
    today_schedule: List[CockpitScheduleEntry] = Field(default_factory=list)
    attendance_roster: List[CockpitAttendanceSection] = Field(default_factory=list)
    homework_overview: List[CockpitHomeworkItem] = Field(default_factory=list)
    upcoming_exams: List[CockpitExamItem] = Field(default_factory=list)
    alerts: List[CockpitAlertItem] = Field(default_factory=list)
    quick_actions: CockpitQuickActions
