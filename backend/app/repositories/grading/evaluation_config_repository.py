from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.grading.evaluation_config import EvaluationConfig
from app.repositories.base import BaseRepository


class EvaluationConfigRepository(BaseRepository[EvaluationConfig]):
    def __init__(self) -> None:
        super().__init__(EvaluationConfig)

    def get_by_id_and_school(
        self,
        db: Session,
        config_id: UUID,
        school_id: UUID,
    ) -> EvaluationConfig | None:
        return db.scalar(
            select(EvaluationConfig).where(
                EvaluationConfig.id == config_id,
                EvaluationConfig.school_id == school_id,
                EvaluationConfig.is_deleted.is_(False),
            )
        )

    def get_default_for_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
    ) -> EvaluationConfig | None:
        return db.scalar(
            select(EvaluationConfig).where(
                EvaluationConfig.school_id == school_id,
                EvaluationConfig.academic_year_id == academic_year_id,
                EvaluationConfig.is_default.is_(True),
                EvaluationConfig.is_deleted.is_(False),
            )
        )

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[EvaluationConfig], int]:
        query = select(EvaluationConfig).where(
            EvaluationConfig.school_id == school_id,
            EvaluationConfig.is_deleted.is_(False),
        )

        if academic_year_id:
            query = query.where(EvaluationConfig.academic_year_id == academic_year_id)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0

        query = (
            query.order_by(EvaluationConfig.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(db.scalars(query)), total


evaluation_config_repository = EvaluationConfigRepository()
