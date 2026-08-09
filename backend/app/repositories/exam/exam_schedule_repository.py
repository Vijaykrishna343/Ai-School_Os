from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.exam.exam_schedule import ExamSchedule
from app.repositories.base import BaseRepository
from app.schemas.exam.exam_schedule import ExamScheduleFilter


class ExamScheduleRepository(BaseRepository[ExamSchedule]):
    """
    Repository responsible for ExamSchedule database operations.
    """

    def __init__(self) -> None:
        super().__init__(ExamSchedule)

    def exists_active_schedule(
        self,
        db: Session,
        exam_id: UUID,
        section_id: UUID,
        subject_id: UUID,
        exam_date: date,
        exclude_schedule_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active exam schedule exists for the specified exam, section, subject, and date.
        """
        query = select(ExamSchedule).where(
            ExamSchedule.exam_id == exam_id,
            ExamSchedule.section_id == section_id,
            ExamSchedule.subject_id == subject_id,
            ExamSchedule.exam_date == exam_date,
            ExamSchedule.is_deleted.is_(False),
        )

        if exclude_schedule_id is not None:
            query = query.where(ExamSchedule.id != exclude_schedule_id)

        result = db.scalar(query)
        return result is not None

    def get_by_id_and_school(
        self,
        db: Session,
        schedule_id: UUID,
        school_id: UUID,
    ) -> ExamSchedule | None:
        """
        Retrieve an active exam schedule by ID and school ID.
        """
        return db.scalar(
            select(ExamSchedule).where(
                ExamSchedule.id == schedule_id,
                ExamSchedule.school_id == school_id,
                ExamSchedule.is_deleted.is_(False),
            )
        )

    def list(
        self,
        db: Session,
        filters: ExamScheduleFilter,
    ) -> tuple[list[ExamSchedule], int]:
        """
        List active exam schedules matching filters.
        """
        query = select(ExamSchedule).where(ExamSchedule.is_deleted.is_(False))

        if filters.exam_id:
            query = query.where(ExamSchedule.exam_id == filters.exam_id)

        if filters.school_id:
            query = query.where(ExamSchedule.school_id == filters.school_id)

        if filters.academic_year_id:
            query = query.where(ExamSchedule.academic_year_id == filters.academic_year_id)

        if filters.school_class_id:
            query = query.where(ExamSchedule.school_class_id == filters.school_class_id)

        if filters.section_id:
            query = query.where(ExamSchedule.section_id == filters.section_id)

        if filters.subject_id:
            query = query.where(ExamSchedule.subject_id == filters.subject_id)

        if filters.exam_date:
            query = query.where(ExamSchedule.exam_date == filters.exam_date)

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(ExamSchedule.exam_date, ExamSchedule.start_time)
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


exam_schedule_repository = ExamScheduleRepository()
