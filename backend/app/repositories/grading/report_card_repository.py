from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.grading.report_card import ReportCard
from app.repositories.base import BaseRepository
from app.schemas.grading.report_card import ReportCardFilter


class ReportCardRepository(BaseRepository[ReportCard]):
    def __init__(self) -> None:
        super().__init__(ReportCard)

    def get_by_id_and_school(
        self,
        db: Session,
        report_card_id: UUID,
        school_id: UUID,
    ) -> ReportCard | None:
        return db.scalar(
            select(ReportCard).where(
                ReportCard.id == report_card_id,
                ReportCard.school_id == school_id,
                ReportCard.is_deleted.is_(False),
            )
        )

    def get_by_student_and_term(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        student_id: UUID,
        academic_term_id: UUID | None = None,
    ) -> ReportCard | None:
        query = select(ReportCard).where(
            ReportCard.school_id == school_id,
            ReportCard.academic_year_id == academic_year_id,
            ReportCard.student_id == student_id,
            ReportCard.is_deleted.is_(False),
        )
        if academic_term_id:
            query = query.where(ReportCard.academic_term_id == academic_term_id)
        else:
            query = query.where(ReportCard.academic_term_id.is_(None))

        return db.scalar(query)

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: ReportCardFilter,
    ) -> tuple[list[ReportCard], int]:
        query = select(ReportCard).where(
            ReportCard.school_id == school_id,
            ReportCard.is_deleted.is_(False),
        )

        if filters.academic_year_id:
            query = query.where(ReportCard.academic_year_id == filters.academic_year_id)
        if filters.academic_term_id:
            query = query.where(ReportCard.academic_term_id == filters.academic_term_id)
        if filters.school_class_id:
            query = query.where(ReportCard.school_class_id == filters.school_class_id)
        if filters.section_id:
            query = query.where(ReportCard.section_id == filters.section_id)
        if filters.student_id:
            query = query.where(ReportCard.student_id == filters.student_id)
        if filters.status:
            query = query.where(ReportCard.status == filters.status)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

        query = (
            query.order_by(ReportCard.created_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


report_card_repository = ReportCardRepository()
