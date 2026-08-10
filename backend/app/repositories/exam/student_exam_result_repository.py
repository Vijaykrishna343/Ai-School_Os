from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.repositories.base import BaseRepository
from app.schemas.exam.student_exam_result import StudentExamResultFilter


class StudentExamResultRepository(BaseRepository[StudentExamResult]):
    """
    Repository responsible for StudentExamResult database operations.
    """

    def __init__(self) -> None:
        """
        Initialize StudentExamResultRepository with StudentExamResult model.
        """
        super().__init__(StudentExamResult)

    def get_by_id_and_school(
        self,
        db: Session,
        result_id: UUID,
        school_id: UUID,
    ) -> StudentExamResult | None:
        """
        Retrieve an active student exam result by ID and school ID (via ExamSchedule).
        """
        return db.scalar(
            select(StudentExamResult)
            .join(ExamSchedule, StudentExamResult.exam_schedule_id == ExamSchedule.id)
            .where(
                StudentExamResult.id == result_id,
                ExamSchedule.school_id == school_id,
                StudentExamResult.is_deleted.is_(False),
                ExamSchedule.is_deleted.is_(False),
            )
        )

    def exists_active_result(
        self,
        db: Session,
        exam_schedule_id: UUID,
        student_id: UUID,
        exclude_result_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active student exam result exists for the specified exam schedule and student.
        """
        query = select(StudentExamResult).where(
            StudentExamResult.exam_schedule_id == exam_schedule_id,
            StudentExamResult.student_id == student_id,
            StudentExamResult.is_deleted.is_(False),
        )

        if exclude_result_id is not None:
            query = query.where(StudentExamResult.id != exclude_result_id)

        result = db.scalar(query)
        return result is not None

    def list(
        self,
        db: Session,
        filters: StudentExamResultFilter,
    ) -> tuple[list[StudentExamResult], int]:
        """
        List active student exam results matching filters.
        """
        query = select(StudentExamResult).where(
            StudentExamResult.is_deleted.is_(False)
        )

        if filters.school_id:
            query = query.join(
                ExamSchedule,
                StudentExamResult.exam_schedule_id == ExamSchedule.id,
            ).where(
                ExamSchedule.school_id == filters.school_id,
                ExamSchedule.is_deleted.is_(False),
            )


        if filters.exam_schedule_id:
            query = query.where(
                StudentExamResult.exam_schedule_id == filters.exam_schedule_id
            )

        if filters.student_id:
            query = query.where(
                StudentExamResult.student_id == filters.student_id
            )

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(StudentExamResult.created_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


student_exam_result_repository = StudentExamResultRepository()
