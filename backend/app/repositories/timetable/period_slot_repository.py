from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.timetable.period_slot import PeriodSlot
from app.repositories.base import BaseRepository
from app.schemas.timetable.period_slot import PeriodSlotFilter


class PeriodSlotRepository(BaseRepository[PeriodSlot]):
    """
    Repository responsible for PeriodSlot database operations.
    """

    def __init__(self) -> None:
        super().__init__(PeriodSlot)

    def get_by_id_and_school(
        self,
        db: Session,
        slot_id: UUID,
        school_id: UUID,
    ) -> PeriodSlot | None:
        """
        Retrieve an active PeriodSlot by ID and school ID.
        """
        return db.scalar(
            select(PeriodSlot).where(
                PeriodSlot.id == slot_id,
                PeriodSlot.school_id == school_id,
                PeriodSlot.is_deleted.is_(False),
            )
        )

    def exists_by_display_order(
        self,
        db: Session,
        school_id: UUID,
        display_order: int,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active PeriodSlot with the same display_order exists for a school.
        """
        query = select(PeriodSlot).where(
            PeriodSlot.school_id == school_id,
            PeriodSlot.display_order == display_order,
            PeriodSlot.is_deleted.is_(False),
        )
        if exclude_id:
            query = query.where(PeriodSlot.id != exclude_id)

        result = db.scalar(query)
        return result is not None

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: PeriodSlotFilter,
    ) -> tuple[list[PeriodSlot], int]:
        """
        List active PeriodSlots matching filters for a tenant school.
        """
        query = select(PeriodSlot).where(
            PeriodSlot.school_id == school_id,
            PeriodSlot.is_deleted.is_(False),
        )

        if filters.period_type is not None:
            query = query.where(PeriodSlot.period_type == filters.period_type)

        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(PeriodSlot.name.ilike(search_pattern))

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(PeriodSlot.display_order.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


period_slot_repository = PeriodSlotRepository()
