from uuid import UUID
from pydantic import BaseModel, ConfigDict


class CurrentAcademicYearSummary(BaseModel):
    id: UUID
    name: str
    status: str
    start_date: str | None = None
    end_date: str | None = None

    model_config = ConfigDict(from_attributes=True)


class CurrentAcademicTermSummary(BaseModel):
    id: UUID
    name: str
    term_structure: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminDashboardSummaryResponse(BaseModel):
    active_students: int
    active_teachers: int
    active_parents: int
    active_classes: int
    active_sections: int
    current_academic_year: CurrentAcademicYearSummary | None = None
    current_academic_term: CurrentAcademicTermSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class TeacherDashboardSummaryResponse(BaseModel):
    user_name: str
    email: str
    role: str
    assigned_students_count: int
    active_classes_count: int
    active_sections_count: int
    current_academic_year: CurrentAcademicYearSummary | None = None
    current_academic_term: CurrentAcademicTermSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class ChildSummaryItem(BaseModel):
    id: UUID
    first_name: str
    last_name: str
    admission_number: str
    roll_number: str | None = None
    school_class_name: str | None = None
    section_name: str | None = None


class AttendanceDashboardSummary(BaseModel):
    total_days: int = 0
    present_days: int = 0
    absent_days: int = 0
    late_days: int = 0
    attendance_percentage: float = 0.0


class FeeDashboardSummary(BaseModel):
    total_assigned: str = "0.00"
    total_paid: str = "0.00"
    total_due: str = "0.00"
    pending_assignments_count: int = 0
    next_due_date: str | None = None
    status: str = "NO_FEES"


class RecentExamResultItem(BaseModel):
    id: UUID
    exam_name: str
    subject_name: str
    marks_obtained: str
    maximum_marks: str
    passing_marks: str
    grade: str | None = None


class AcademicDashboardSummary(BaseModel):
    latest_term_gpa: str | None = None
    published_report_cards_count: int = 0
    recent_results: list[RecentExamResultItem] = []


class HomeworkDashboardItem(BaseModel):
    id: UUID
    title: str
    subject_name: str
    due_date: str
    is_submitted: bool = False


class ExamDashboardItem(BaseModel):
    id: UUID
    exam_name: str
    subject_name: str
    exam_date: str
    start_time: str
    end_time: str


class ParentDashboardSummaryResponse(BaseModel):
    parent_name: str
    email: str | None = None
    children: list[ChildSummaryItem] = []
    selected_child_id: UUID | None = None
    zero_child_state: bool = False
    attendance_summary: AttendanceDashboardSummary | None = None
    fees_summary: FeeDashboardSummary | None = None
    academics_summary: AcademicDashboardSummary | None = None
    recent_homework: list[HomeworkDashboardItem] = []
    upcoming_exams: list[ExamDashboardItem] = []
    unread_notifications_count: int = 0
    current_academic_year: CurrentAcademicYearSummary | None = None
    current_academic_term: CurrentAcademicTermSummary | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentDashboardSummaryResponse(BaseModel):
    student_info: ChildSummaryItem
    attendance_summary: AttendanceDashboardSummary
    fees_summary: FeeDashboardSummary
    academics_summary: AcademicDashboardSummary
    recent_homework: list[HomeworkDashboardItem] = []
    upcoming_exams: list[ExamDashboardItem] = []
    unread_notifications_count: int = 0
    current_academic_year: CurrentAcademicYearSummary | None = None
    current_academic_term: CurrentAcademicTermSummary | None = None

    model_config = ConfigDict(from_attributes=True)

