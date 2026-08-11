from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.exam import parse_legacy_exam_type
from app.models.exam.exam import Exam
from app.repositories.base import BaseRepository
from app.schemas.exam.exam import ExamFilter


class ExamRepository(BaseRepository[Exam]):
    """
    Repository responsible for Exam database operations.
    """

    def __init__(self) -> None:
        super().__init__(Exam)

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        name: str,
    ) -> bool:
        """
        Check if an active exam with the specified name exists for school and academic year.
        """
        result = db.scalar(
            select(Exam).where(
                Exam.school_id == school_id,
                Exam.academic_year_id == academic_year_id,
                Exam.name == name,
                Exam.is_deleted.is_(False),
            )
        )
        return result is not None

    def get_by_id_and_school(
        self,
        db: Session,
        exam_id: UUID,
        school_id: UUID,
    ) -> Exam | None:
        """
        Retrieve an active exam by ID and school ID.
        """
        return db.scalar(
            select(Exam).where(
                Exam.id == exam_id,
                Exam.school_id == school_id,
                Exam.is_deleted.is_(False),
            )
        )

    def list(
        self,
        db: Session,
        filters: ExamFilter,
    ) -> tuple[list[Exam], int]:
        """
        List active exams matching filters.
        """
        query = select(Exam).where(Exam.is_deleted.is_(False))

        if filters.school_id:
            query = query.where(Exam.school_id == filters.school_id)

        if filters.academic_year_id:
            query = query.where(Exam.academic_year_id == filters.academic_year_id)

        if filters.academic_term_id:
            query = query.where(Exam.academic_term_id == filters.academic_term_id)

        if filters.assessment_type:
            query = query.where(Exam.assessment_type == filters.assessment_type)

        if filters.attempt_type:
            query = query.where(Exam.attempt_type == filters.attempt_type)

        if filters.exam_type and not filters.attempt_type:
            try:
                _, legacy_attempt = parse_legacy_exam_type(filters.exam_type)
                query = query.where(Exam.attempt_type == legacy_attempt)
            except ValueError:
                # If invalid legacy exam_type filter provided, return empty
                query = query.where(False)

        if filters.status:
            query = query.where(Exam.status == filters.status)

        if filters.search:
            query = query.where(Exam.name.ilike(f"%{filters.search}%"))

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(Exam.start_date.desc(), Exam.name)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


exam_repository = ExamRepository()
