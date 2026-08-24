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
    ParentDashboardSummaryResponse,
    StudentDashboardSummaryResponse,
    ChildSummaryItem,
)
from app.common.authorization import (
    enforce_relationship_access,
    resolve_parent_linked_student_ids,
    resolve_student_id_for_user,
)
from app.common.exceptions import ForbiddenException, NotFoundException
from app.models.student import Student


class DashboardService:
    """
    Business logic layer for Dashboard metrics across Admin, Teacher, Parent, and Student personas.
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

    def get_parent_summary(
        self,
        db: Session,
        user: IdentityUser,
        requested_student_id: UUID | None = None,
    ) -> ParentDashboardSummaryResponse:
        """
        Aggregate and return summary metrics for a Parent context.
        Strictly enforces Parent -> Linked Child relationship authorization.
        Handles multi-child switching and zero-child fail-closed state.
        """
        school_id = user.school_id
        linked_student_ids = resolve_parent_linked_student_ids(db, school_id, user)

        curr_year = self.repository.get_current_academic_year(db, school_id)
        curr_term = self.repository.get_current_academic_term(db, school_id)

        year_summary = CurrentAcademicYearSummary(
            id=curr_year.id,
            name=curr_year.name,
            status=str(curr_year.status.value) if hasattr(curr_year.status, "value") else str(curr_year.status),
            start_date=str(curr_year.start_date) if curr_year.start_date else None,
            end_date=str(curr_year.end_date) if curr_year.end_date else None,
        ) if curr_year else None

        term_summary = CurrentAcademicTermSummary(
            id=curr_term.id,
            name=curr_term.name,
            term_structure=getattr(curr_term, "code", None),
        ) if curr_term else None

        parent_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or "Guardian"

        # If a specific student_id is requested, enforce relationship authorization first!
        if requested_student_id:
            target_student_id = enforce_relationship_access(db, school_id, user, requested_student_id)
            if isinstance(target_student_id, list):
                target_student_id = target_student_id[0]
        else:
            target_student_id = linked_student_ids[0] if linked_student_ids else None

        # Zero-child state (only if no specific child requested or after validation)
        if not linked_student_ids or not target_student_id:
            return ParentDashboardSummaryResponse(
                parent_name=parent_name,
                email=user.email,
                children=[],
                selected_child_id=None,
                zero_child_state=True,
                attendance_summary=None,
                fees_summary=None,
                academics_summary=None,
                recent_homework=[],
                upcoming_exams=[],
                unread_notifications_count=self.repository.get_unread_notifications_count(db, school_id, user.id),
                current_academic_year=year_summary,
                current_academic_term=term_summary,
            )

        # Build list of linked children
        students = (
            db.query(Student)
            .filter(
                Student.id.in_(linked_student_ids),
                Student.school_id == school_id,
                Student.is_deleted == False,  # noqa: E712
            )
            .all()
        )

        children_items = []
        for st in students:
            c_name = st.school_class.name if st.school_class else None
            s_name = st.section.name if st.section else None
            children_items.append(
                ChildSummaryItem(
                    id=st.id,
                    first_name=st.first_name,
                    last_name=st.last_name,
                    admission_number=st.admission_number,
                    roll_number=st.roll_number,
                    school_class_name=c_name,
                    section_name=s_name,
                )
            )

        allowed_id = target_student_id

        target_student = db.query(Student).filter(Student.id == allowed_id, Student.school_id == school_id).first()

        section_id = target_student.section_id if target_student else None

        att_summary = self.repository.get_student_attendance_summary(db, school_id, allowed_id)
        fees_summary = self.repository.get_student_fees_summary(db, school_id, allowed_id)
        academics_summary = self.repository.get_student_academics_summary(db, school_id, allowed_id)
        homework_items = self.repository.get_student_recent_homework(db, school_id, section_id, allowed_id)
        exam_items = self.repository.get_student_upcoming_exams(db, school_id, section_id)
        unread_count = self.repository.get_unread_notifications_count(db, school_id, user.id)

        return ParentDashboardSummaryResponse(
            parent_name=parent_name,
            email=user.email,
            children=children_items,
            selected_child_id=allowed_id,
            zero_child_state=False,
            attendance_summary=att_summary,
            fees_summary=fees_summary,
            academics_summary=academics_summary,
            recent_homework=homework_items,
            upcoming_exams=exam_items,
            unread_notifications_count=unread_count,
            current_academic_year=year_summary,
            current_academic_term=term_summary,
        )

    def get_student_summary(
        self,
        db: Session,
        user: IdentityUser,
    ) -> StudentDashboardSummaryResponse:
        """
        Aggregate and return summary metrics for a Student context.
        Strictly enforces Student -> Self relationship authorization.
        """
        school_id = user.school_id
        student_id = resolve_student_id_for_user(db, school_id, user)
        if not student_id:
            raise ForbiddenException("Student profile not found for authenticated user.")

        allowed_id = enforce_relationship_access(db, school_id, user, student_id)
        if isinstance(allowed_id, list):
            allowed_id = allowed_id[0]

        student = db.query(Student).filter(Student.id == allowed_id, Student.school_id == school_id).first()
        if not student:
            raise NotFoundException("Student record not found.")

        c_name = student.school_class.name if student.school_class else None
        s_name = student.section.name if student.section else None
        student_info = ChildSummaryItem(
            id=student.id,
            first_name=student.first_name,
            last_name=student.last_name,
            admission_number=student.admission_number,
            roll_number=student.roll_number,
            school_class_name=c_name,
            section_name=s_name,
        )

        curr_year = self.repository.get_current_academic_year(db, school_id)
        curr_term = self.repository.get_current_academic_term(db, school_id)

        year_summary = CurrentAcademicYearSummary(
            id=curr_year.id,
            name=curr_year.name,
            status=str(curr_year.status.value) if hasattr(curr_year.status, "value") else str(curr_year.status),
            start_date=str(curr_year.start_date) if curr_year.start_date else None,
            end_date=str(curr_year.end_date) if curr_year.end_date else None,
        ) if curr_year else None

        term_summary = CurrentAcademicTermSummary(
            id=curr_term.id,
            name=curr_term.name,
            term_structure=getattr(curr_term, "code", None),
        ) if curr_term else None

        section_id = student.section_id
        att_summary = self.repository.get_student_attendance_summary(db, school_id, allowed_id)
        fees_summary = self.repository.get_student_fees_summary(db, school_id, allowed_id)
        academics_summary = self.repository.get_student_academics_summary(db, school_id, allowed_id)
        homework_items = self.repository.get_student_recent_homework(db, school_id, section_id, allowed_id)
        exam_items = self.repository.get_student_upcoming_exams(db, school_id, section_id)
        unread_count = self.repository.get_unread_notifications_count(db, school_id, user.id)

        return StudentDashboardSummaryResponse(
            student_info=student_info,
            attendance_summary=att_summary,
            fees_summary=fees_summary,
            academics_summary=academics_summary,
            recent_homework=homework_items,
            upcoming_exams=exam_items,
            unread_notifications_count=unread_count,
            current_academic_year=year_summary,
            current_academic_term=term_summary,
        )


dashboard_service = DashboardService(repository=dashboard_repository)

