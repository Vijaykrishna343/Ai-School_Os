from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.student.student_enrollment_history import StudentEnrollmentHistory
from app.repositories.base import BaseRepository


class StudentEnrollmentHistoryRepository(BaseRepository[StudentEnrollmentHistory]):
    """
    Repository responsible for StudentEnrollmentHistory database operations.
    """

    def __init__(self) -> None:
        super().__init__(StudentEnrollmentHistory)

    def get_by_student_and_year(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
        academic_year_id: UUID,
    ) -> StudentEnrollmentHistory | None:
        """
        Get active enrollment history record for student in a specific academic year.
        """
        stmt = (
            select(StudentEnrollmentHistory)
            .where(
                StudentEnrollmentHistory.school_id == school_id,
                StudentEnrollmentHistory.student_id == student_id,
                StudentEnrollmentHistory.academic_year_id == academic_year_id,
                StudentEnrollmentHistory.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt)

    def get_by_student(
        self,
        db: Session,
        school_id: UUID,
        student_id: UUID,
    ) -> list[StudentEnrollmentHistory]:
        """
        Get all active enrollment history records for a student ordered by creation/academic year.
        """
        stmt = (
            select(StudentEnrollmentHistory)
            .where(
                StudentEnrollmentHistory.school_id == school_id,
                StudentEnrollmentHistory.student_id == student_id,
                StudentEnrollmentHistory.is_deleted.is_(False),
            )
            .order_by(StudentEnrollmentHistory.created_at.asc())
        )
        return list(db.scalars(stmt))


student_enrollment_history_repository = StudentEnrollmentHistoryRepository()
