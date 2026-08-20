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
