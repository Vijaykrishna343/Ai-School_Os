from uuid import UUID
from sqlalchemy.orm import Session

from app.repositories.dashboard_repository import (
    DashboardRepository,
    dashboard_repository,
)
from app.schemas.dashboard import (
    AdminDashboardSummaryResponse,
    CurrentAcademicTermSummary,
    CurrentAcademicYearSummary,
    TeacherDashboardSummaryResponse,
)
from app.identity.models.user import IdentityUser


class DashboardService:
    """
    Business logic layer for Admin Dashboard metrics.
    """

    def __init__(self, repository: DashboardRepository) -> None:
        self.repository = repository

    def get_admin_summary(
        self,
        db: Session,
        school_id: UUID,
    ) -> AdminDashboardSummaryResponse:
        """
        Aggregate and return all summary metrics for the given school ID.
        """
        students_count = self.repository.get_active_students_count(db, school_id)
        teachers_count = self.repository.get_active_teachers_count(db, school_id)
        parents_count = self.repository.get_active_parents_count(db, school_id)
        classes_count = self.repository.get_active_classes_count(db, school_id)
        sections_count = self.repository.get_active_sections_count(db, school_id)

        curr_year = self.repository.get_current_academic_year(db, school_id)
        curr_term = self.repository.get_current_academic_term(db, school_id)

        year_summary = None
        if curr_year:
            year_summary = CurrentAcademicYearSummary(
                id=curr_year.id,
                name=curr_year.name,
                status=str(curr_year.status.value) if hasattr(curr_year.status, "value") else str(curr_year.status),
                start_date=str(curr_year.start_date) if curr_year.start_date else None,
                end_date=str(curr_year.end_date) if curr_year.end_date else None,
            )

        term_summary = None
        if curr_term:
            term_summary = CurrentAcademicTermSummary(
                id=curr_term.id,
                name=curr_term.name,
                term_structure=getattr(curr_term, "code", None),
            )

        return AdminDashboardSummaryResponse(
            active_students=students_count,
            active_teachers=teachers_count,
            active_parents=parents_count,
            active_classes=classes_count,
            active_sections=sections_count,
            current_academic_year=year_summary,
            current_academic_term=term_summary,
        )

    def get_teacher_summary(
        self,
        db: Session,
        user: IdentityUser,
    ) -> TeacherDashboardSummaryResponse:
        """
        Aggregate and return summary metrics for a teacher context.
        Does NOT expose financial or administrative statistics.
        """
        school_id = user.school_id
        students_count = self.repository.get_active_students_count(db, school_id)
        classes_count = self.repository.get_active_classes_count(db, school_id)
        sections_count = self.repository.get_active_sections_count(db, school_id)

        curr_year = self.repository.get_current_academic_year(db, school_id)
        curr_term = self.repository.get_current_academic_term(db, school_id)

        year_summary = None
        if curr_year:
            year_summary = CurrentAcademicYearSummary(
                id=curr_year.id,
                name=curr_year.name,
                status=str(curr_year.status.value) if hasattr(curr_year.status, "value") else str(curr_year.status),
                start_date=str(curr_year.start_date) if curr_year.start_date else None,
                end_date=str(curr_year.end_date) if curr_year.end_date else None,
            )

        term_summary = None
        if curr_term:
            term_summary = CurrentAcademicTermSummary(
                id=curr_term.id,
                name=curr_term.name,
                term_structure=getattr(curr_term, "code", None),
            )

        user_full_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Teacher"

        return TeacherDashboardSummaryResponse(
            user_name=user_full_name,
            email=user.email,
            role="Teacher",
            assigned_students_count=students_count,
            active_classes_count=classes_count,
            active_sections_count=sections_count,
            current_academic_year=year_summary,
            current_academic_term=term_summary,
        )


dashboard_service = DashboardService(repository=dashboard_repository)
