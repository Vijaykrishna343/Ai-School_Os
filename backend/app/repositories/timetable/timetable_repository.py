from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.repositories.base import BaseRepository
from app.schemas.timetable.timetable import TimetableFilter


class TimetableRepository(BaseRepository[Timetable]):
    """
    Repository responsible for Timetable database operations.
    """

    def __init__(self) -> None:
        super().__init__(Timetable)

    def get_by_id_and_school(
        self,
        db: Session,
        timetable_id: UUID,
        school_id: UUID,
    ) -> Timetable | None:
        """
        Retrieve an active Timetable by ID and school ID.
        """
        return db.scalar(
            select(Timetable).where(
                Timetable.id == timetable_id,
                Timetable.school_id == school_id,
                Timetable.is_deleted.is_(False),
            )
        )

    def get_with_entries(
        self,
        db: Session,
        timetable_id: UUID,
        school_id: UUID,
    ) -> Timetable | None:
        """
        Retrieve an active Timetable with all entries and nested relations pre-fetched.
        """
        return db.scalar(
            select(Timetable)
            .options(
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.period_slot),
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.subject),
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.teacher),
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.classroom),
                joinedload(Timetable.school_class),
                joinedload(Timetable.section),
                joinedload(Timetable.academic_year),
                joinedload(Timetable.academic_term),
            )
            .where(
                Timetable.id == timetable_id,
                Timetable.school_id == school_id,
                Timetable.is_deleted.is_(False),
            )
        )

    def get_active_by_section(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID,
        academic_year_id: UUID | None = None,
        academic_term_id: UUID | None = None,
    ) -> Timetable | None:
        """
        Retrieve active Timetable for a section with eager-loaded entries.
        """
        query = (
            select(Timetable)
            .options(
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.period_slot),
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.subject),
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.teacher),
                joinedload(Timetable.entries.and_(TimetableEntry.is_deleted.is_(False)))
                .joinedload(TimetableEntry.classroom),
                joinedload(Timetable.school_class),
                joinedload(Timetable.section),
                joinedload(Timetable.academic_year),
                joinedload(Timetable.academic_term),
            )
            .where(
                Timetable.school_id == school_id,
                Timetable.section_id == section_id,
                Timetable.is_active.is_(True),
                Timetable.is_deleted.is_(False),
            )
        )

        if academic_year_id:
            query = query.where(Timetable.academic_year_id == academic_year_id)
        if academic_term_id:
            query = query.where(Timetable.academic_term_id == academic_term_id)

        query = query.order_by(Timetable.created_at.desc())
        return db.scalar(query)

    def exists_by_section_and_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        section_id: UUID,
        academic_term_id: UUID | None = None,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active Timetable already exists for a section and year/term.
        """
        query = select(Timetable).where(
            Timetable.school_id == school_id,
            Timetable.academic_year_id == academic_year_id,
            Timetable.section_id == section_id,
            Timetable.is_deleted.is_(False),
        )
        if academic_term_id:
            query = query.where(Timetable.academic_term_id == academic_term_id)
        if exclude_id:
            query = query.where(Timetable.id != exclude_id)

        return db.scalar(query) is not None

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: TimetableFilter,
    ) -> tuple[list[Timetable], int]:
        """
        List active Timetables for a tenant school matching filters.
        """
        query = select(Timetable).where(
            Timetable.school_id == school_id,
            Timetable.is_deleted.is_(False),
        )

        if filters.academic_year_id:
            query = query.where(Timetable.academic_year_id == filters.academic_year_id)

        if filters.school_class_id:
            query = query.where(Timetable.school_class_id == filters.school_class_id)

        if filters.section_id:
            query = query.where(Timetable.section_id == filters.section_id)

        if filters.academic_term_id:
            query = query.where(Timetable.academic_term_id == filters.academic_term_id)

        if filters.status is not None:
            query = query.where(Timetable.status == filters.status)

        if filters.is_active is not None:
            query = query.where(Timetable.is_active == filters.is_active)

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(Timetable.created_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


timetable_repository = TimetableRepository()
