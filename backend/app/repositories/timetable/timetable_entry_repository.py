from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums.timetable import DayOfWeek
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.repositories.base import BaseRepository


class TimetableEntryRepository(BaseRepository[TimetableEntry]):
    """
    Repository responsible for TimetableEntry database operations and conflict queries.
    """

    def __init__(self) -> None:
        super().__init__(TimetableEntry)

    def get_by_id_and_school(
        self,
        db: Session,
        entry_id: UUID,
        school_id: UUID,
    ) -> TimetableEntry | None:
        """
        Retrieve an active TimetableEntry by ID verifying tenant school ownership.
        """
        return db.scalar(
            select(TimetableEntry)
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                TimetableEntry.id == entry_id,
                Timetable.school_id == school_id,
                TimetableEntry.is_deleted.is_(False),
                Timetable.is_deleted.is_(False),
            )
        )

    def get_with_details(
        self,
        db: Session,
        entry_id: UUID,
        school_id: UUID,
    ) -> TimetableEntry | None:
        """
        Retrieve a TimetableEntry by ID with eager loaded relations.
        """
        return db.scalar(
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.period_slot),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.teacher),
                joinedload(TimetableEntry.classroom),
                joinedload(TimetableEntry.timetable).joinedload(Timetable.school_class),
                joinedload(TimetableEntry.timetable).joinedload(Timetable.section),
            )
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                TimetableEntry.id == entry_id,
                Timetable.school_id == school_id,
                TimetableEntry.is_deleted.is_(False),
                Timetable.is_deleted.is_(False),
            )
        )

    def list_by_timetable(
        self,
        db: Session,
        timetable_id: UUID,
    ) -> list[TimetableEntry]:
        """
        List all active entries for a timetable with eager loaded details.
        """
        return list(
            db.scalars(
                select(TimetableEntry)
                .options(
                    joinedload(TimetableEntry.period_slot),
                    joinedload(TimetableEntry.subject),
                    joinedload(TimetableEntry.teacher),
                    joinedload(TimetableEntry.classroom),
                )
                .where(
                    TimetableEntry.timetable_id == timetable_id,
                    TimetableEntry.is_deleted.is_(False),
                )
            )
        )

    def get_by_slot(
        self,
        db: Session,
        timetable_id: UUID,
        day_of_week: DayOfWeek,
        period_slot_id: UUID,
        exclude_entry_id: UUID | None = None,
    ) -> TimetableEntry | None:
        """
        Check if an active entry exists for a specific section timetable slot.
        """
        query = select(TimetableEntry).where(
            TimetableEntry.timetable_id == timetable_id,
            TimetableEntry.day_of_week == day_of_week,
            TimetableEntry.period_slot_id == period_slot_id,
            TimetableEntry.is_deleted.is_(False),
        )
        if exclude_entry_id:
            query = query.where(TimetableEntry.id != exclude_entry_id)

        return db.scalar(query)

    def find_teacher_conflict(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        teacher_id: UUID,
        day_of_week: DayOfWeek,
        period_slot_id: UUID,
        exclude_entry_id: UUID | None = None,
    ) -> TimetableEntry | None:
        """
        Find any conflicting active entry where the same teacher is scheduled
        at the same day and period slot within the same school and academic year.
        """
        query = (
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.timetable).joinedload(Timetable.school_class),
                joinedload(TimetableEntry.timetable).joinedload(Timetable.section),
                joinedload(TimetableEntry.period_slot),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.teacher),
            )
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                Timetable.school_id == school_id,
                Timetable.academic_year_id == academic_year_id,
                TimetableEntry.teacher_id == teacher_id,
                TimetableEntry.day_of_week == day_of_week,
                TimetableEntry.period_slot_id == period_slot_id,
                TimetableEntry.is_deleted.is_(False),
                Timetable.is_deleted.is_(False),
                Timetable.is_active.is_(True),
            )
        )
        if exclude_entry_id:
            query = query.where(TimetableEntry.id != exclude_entry_id)

        return db.scalar(query)

    def find_classroom_conflict(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        classroom_id: UUID,
        day_of_week: DayOfWeek,
        period_slot_id: UUID,
        exclude_entry_id: UUID | None = None,
    ) -> TimetableEntry | None:
        """
        Find any conflicting active entry where the same classroom is hosting another section
        at the same day and period slot within the same school and academic year.
        """
        query = (
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.timetable).joinedload(Timetable.school_class),
                joinedload(TimetableEntry.timetable).joinedload(Timetable.section),
                joinedload(TimetableEntry.period_slot),
                joinedload(TimetableEntry.classroom),
            )
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                Timetable.school_id == school_id,
                Timetable.academic_year_id == academic_year_id,
                TimetableEntry.classroom_id == classroom_id,
                TimetableEntry.day_of_week == day_of_week,
                TimetableEntry.period_slot_id == period_slot_id,
                TimetableEntry.is_deleted.is_(False),
                Timetable.is_deleted.is_(False),
                Timetable.is_active.is_(True),
            )
        )
        if exclude_entry_id:
            query = query.where(TimetableEntry.id != exclude_entry_id)

        return db.scalar(query)

    def list_by_teacher(
        self,
        db: Session,
        school_id: UUID,
        teacher_id: UUID,
        academic_year_id: UUID | None = None,
    ) -> list[TimetableEntry]:
        """
        List active scheduled entries for a teacher in a school across all timetables.
        """
        query = (
            select(TimetableEntry)
            .options(
                joinedload(TimetableEntry.period_slot),
                joinedload(TimetableEntry.subject),
                joinedload(TimetableEntry.teacher),
                joinedload(TimetableEntry.classroom),
                joinedload(TimetableEntry.timetable).joinedload(Timetable.school_class),
                joinedload(TimetableEntry.timetable).joinedload(Timetable.section),
            )
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                Timetable.school_id == school_id,
                TimetableEntry.teacher_id == teacher_id,
                TimetableEntry.is_deleted.is_(False),
                Timetable.is_deleted.is_(False),
            )
        )
        if academic_year_id:
            query = query.where(Timetable.academic_year_id == academic_year_id)

        return list(db.scalars(query))


timetable_entry_repository = TimetableEntryRepository()
