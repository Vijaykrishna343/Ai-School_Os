from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session, selectinload

from app.models.grading.grade_scale import GradeScale
from app.models.grading.grade_scale_entry import GradeScaleEntry
from app.repositories.base import BaseRepository
from app.schemas.grading.grade_scale import GradeScaleFilter


class GradeScaleRepository(BaseRepository[GradeScale]):
    """
    Repository responsible for GradeScale and GradeScaleEntry database operations.
    """

    def __init__(self) -> None:
        super().__init__(GradeScale)

    def get_by_id_and_school(
        self,
        db: Session,
        scale_id: UUID,
        school_id: UUID,
    ) -> GradeScale | None:
        """
        Retrieve an active GradeScale by ID and school ID, eagerly loading active entries.
        """
        return db.scalar(
            select(GradeScale)
            .options(
                selectinload(
                    GradeScale.entries.and_(
                        GradeScaleEntry.is_deleted.is_(False)
                    )
                )
            )
            .where(
                GradeScale.id == scale_id,
                GradeScale.school_id == school_id,
                GradeScale.is_deleted.is_(False),
            )
        )

    def get_default_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> GradeScale | None:
        """
        Retrieve the active default GradeScale for a school.
        """
        return db.scalar(
            select(GradeScale)
            .options(
                selectinload(
                    GradeScale.entries.and_(
                        GradeScaleEntry.is_deleted.is_(False)
                    )
                )
            )
            .where(
                GradeScale.school_id == school_id,
                GradeScale.is_default.is_(True),
                GradeScale.is_deleted.is_(False),
            )
        )

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active GradeScale with the specified name exists for a school.
        """
        query = select(GradeScale).where(
            GradeScale.school_id == school_id,
            func.lower(GradeScale.name) == name.strip().lower(),
            GradeScale.is_deleted.is_(False),
        )
        if exclude_id is not None:
            query = query.where(GradeScale.id != exclude_id)

        return db.scalar(query) is not None

    def unset_default_for_school(
        self,
        db: Session,
        school_id: UUID,
        exclude_id: UUID | None = None,
    ) -> None:
        """
        Unset is_default=True for all active grade scales belonging to a school.
        """
        stmt = (
            update(GradeScale)
            .where(
                GradeScale.school_id == school_id,
                GradeScale.is_default.is_(True),
                GradeScale.is_deleted.is_(False),
            )
            .values(is_default=False)
        )
        if exclude_id is not None:
            stmt = stmt.where(GradeScale.id != exclude_id)

        db.execute(stmt)

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: GradeScaleFilter,
    ) -> tuple[list[GradeScale], int]:
        """
        List active GradeScales matching filters for a school.
        """
        query = (
            select(GradeScale)
            .options(
                selectinload(
                    GradeScale.entries.and_(
                        GradeScaleEntry.is_deleted.is_(False)
                    )
                )
            )
            .where(
                GradeScale.school_id == school_id,
                GradeScale.is_deleted.is_(False),
            )
        )

        if filters.is_default is not None:
            query = query.where(GradeScale.is_default == filters.is_default)

        if filters.search:
            query = query.where(
                GradeScale.name.ilike(f"%{filters.search}%")
            )

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(
                GradeScale.is_default.desc(),
                GradeScale.name,
            )
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


grade_scale_repository = GradeScaleRepository()
