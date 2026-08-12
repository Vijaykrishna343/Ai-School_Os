from datetime import date
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.models.timetable.teacher_substitution import TeacherSubstitution
from app.models.timetable.timetable_entry import TimetableEntry
from app.repositories.base import BaseRepository
from app.schemas.timetable.teacher_substitution import TeacherSubstitutionFilter


class TeacherSubstitutionRepository(BaseRepository[TeacherSubstitution]):
    """
    Repository responsible for TeacherSubstitution database operations and conflict queries.
    """

    def __init__(self) -> None:
        super().__init__(TeacherSubstitution)

    def get_by_id_and_school(
        self,
        db: Session,
        substitution_id: UUID,
        school_id: UUID,
    ) -> TeacherSubstitution | None:
        """
        Retrieve an active TeacherSubstitution by ID and school ID.
        """
        return db.scalar(
            select(TeacherSubstitution).where(
                TeacherSubstitution.id == substitution_id,
                TeacherSubstitution.school_id == school_id,
                TeacherSubstitution.is_deleted.is_(False),
            )
        )

    def get_with_details(
        self,
        db: Session,
        substitution_id: UUID,
        school_id: UUID,
    ) -> TeacherSubstitution | None:
        """
        Retrieve an active TeacherSubstitution by ID with all nested relations pre-fetched.
        """
        return db.scalar(
            select(TeacherSubstitution)
            .options(
                joinedload(TeacherSubstitution.original_teacher),
                joinedload(TeacherSubstitution.substitute_teacher),
                joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.period_slot),
                joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.subject),
                joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.classroom),
                joinedload(TeacherSubstitution.timetable_entry)
                .joinedload(TimetableEntry.timetable)
                .joinedload(TimetableEntry.timetable.property.mapper.class_.school_class),
                joinedload(TeacherSubstitution.timetable_entry)
                .joinedload(TimetableEntry.timetable)
                .joinedload(TimetableEntry.timetable.property.mapper.class_.section),
            )
            .where(
                TeacherSubstitution.id == substitution_id,
                TeacherSubstitution.school_id == school_id,
                TeacherSubstitution.is_deleted.is_(False),
            )
        )

    def get_active_by_slot_and_date(
        self,
        db: Session,
        timetable_entry_id: UUID,
        substitution_date: date,
        exclude_id: UUID | None = None,
    ) -> TeacherSubstitution | None:
        """
        Check if an active substitution already exists for a specific entry and date.
        """
        query = select(TeacherSubstitution).where(
            TeacherSubstitution.timetable_entry_id == timetable_entry_id,
            TeacherSubstitution.substitution_date == substitution_date,
            TeacherSubstitution.is_deleted.is_(False),
        )
        if exclude_id:
            query = query.where(TeacherSubstitution.id != exclude_id)

        return db.scalar(query)

    def find_substitute_conflict(
        self,
        db: Session,
        school_id: UUID,
        substitute_teacher_id: UUID,
        substitution_date: date,
        period_slot_id: UUID,
        exclude_id: UUID | None = None,
    ) -> TeacherSubstitution | None:
        """
        Find if the substitute teacher is already assigned to another active substitution
        on the same date and period slot.
        """
        query = (
            select(TeacherSubstitution)
            .join(TimetableEntry, TeacherSubstitution.timetable_entry_id == TimetableEntry.id)
            .where(
                TeacherSubstitution.school_id == school_id,
                TeacherSubstitution.substitute_teacher_id == substitute_teacher_id,
                TeacherSubstitution.substitution_date == substitution_date,
                TimetableEntry.period_slot_id == period_slot_id,
                TeacherSubstitution.is_deleted.is_(False),
                TimetableEntry.is_deleted.is_(False),
            )
        )
        if exclude_id:
            query = query.where(TeacherSubstitution.id != exclude_id)

        return db.scalar(query)

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: TeacherSubstitutionFilter,
    ) -> tuple[list[TeacherSubstitution], int]:
        """
        List active TeacherSubstitutions for a tenant school matching filters.
        """
        query = (
            select(TeacherSubstitution)
            .options(
                joinedload(TeacherSubstitution.original_teacher),
                joinedload(TeacherSubstitution.substitute_teacher),
                joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.period_slot),
                joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.subject),
                joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.classroom),
            )
            .where(
                TeacherSubstitution.school_id == school_id,
                TeacherSubstitution.is_deleted.is_(False),
            )
        )

        if filters.timetable_entry_id:
            query = query.where(TeacherSubstitution.timetable_entry_id == filters.timetable_entry_id)

        if filters.original_teacher_id:
            query = query.where(TeacherSubstitution.original_teacher_id == filters.original_teacher_id)

        if filters.substitute_teacher_id:
            query = query.where(TeacherSubstitution.substitute_teacher_id == filters.substitute_teacher_id)

        if filters.substitution_date:
            query = query.where(TeacherSubstitution.substitution_date == filters.substitution_date)

        if filters.start_date:
            query = query.where(TeacherSubstitution.substitution_date >= filters.start_date)

        if filters.end_date:
            query = query.where(TeacherSubstitution.substitution_date <= filters.end_date)

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(TeacherSubstitution.substitution_date.desc(), TeacherSubstitution.created_at.desc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total

    def list_active_substitutions_for_date_range(
        self,
        db: Session,
        school_id: UUID,
        start_date: date,
        end_date: date,
    ) -> list[TeacherSubstitution]:
        """
        List all active substitutions for a school within a date range with pre-fetched details.
        """
        return list(
            db.scalars(
                select(TeacherSubstitution)
                .options(
                    joinedload(TeacherSubstitution.substitute_teacher),
                    joinedload(TeacherSubstitution.original_teacher),
                    joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.period_slot),
                    joinedload(TeacherSubstitution.timetable_entry).joinedload(TimetableEntry.subject),
                )
                .where(
                    TeacherSubstitution.school_id == school_id,
                    TeacherSubstitution.substitution_date >= start_date,
                    TeacherSubstitution.substitution_date <= end_date,
                    TeacherSubstitution.is_deleted.is_(False),
                )
            )
        )


teacher_substitution_repository = TeacherSubstitutionRepository()
