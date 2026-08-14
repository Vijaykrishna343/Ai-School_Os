from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year import AcademicYear
from app.models.parent import Parent
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.models.teacher import Teacher


from app.common.enums import AcademicYearStatus


class DashboardRepository:
    """
    Data access layer for Admin Dashboard metrics and summary queries.
    All operations enforce strict tenant isolation using school_id and respect soft deletion.
    """

    def get_active_students_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Student.id))
            .filter(
                Student.school_id == school_id,
                Student.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_teachers_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Teacher.id))
            .filter(
                Teacher.school_id == school_id,
                Teacher.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_parents_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Parent.id))
            .filter(
                Parent.school_id == school_id,
                Parent.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_classes_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(SchoolClass.id))
            .filter(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_sections_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Section.id))
            .join(SchoolClass, Section.school_class_id == SchoolClass.id)
            .filter(
                SchoolClass.school_id == school_id,
                Section.is_deleted == False,  # noqa: E712
                SchoolClass.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )


    def get_current_academic_year(self, db: Session, school_id: UUID) -> AcademicYear | None:
        return (
            db.query(AcademicYear)
            .filter(
                AcademicYear.school_id == school_id,
                AcademicYear.status == AcademicYearStatus.ACTIVE,
                AcademicYear.is_deleted == False,  # noqa: E712
            )
            .first()
        )


    def get_current_academic_term(self, db: Session, school_id: UUID) -> AcademicTerm | None:
        return (
            db.query(AcademicTerm)
            .filter(
                AcademicTerm.school_id == school_id,
                AcademicTerm.is_active == True,  # noqa: E712
                AcademicTerm.is_deleted == False,  # noqa: E712
            )
            .first()
        )


dashboard_repository = DashboardRepository()
