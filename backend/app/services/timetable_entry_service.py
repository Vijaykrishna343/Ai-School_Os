from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums.timetable import TimetableStatus
from app.common.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.models.timetable.timetable_entry import TimetableEntry
from app.repositories.timetable.timetable_entry_repository import (
    TimetableEntryRepository,
    timetable_entry_repository,
)
from app.repositories.timetable.timetable_repository import (
    TimetableRepository,
    timetable_repository,
)
from app.schemas.timetable.timetable_entry import (
    TimetableEntryCreate,
    TimetableEntryUpdate,
)
from app.services.timetable_conflict_service import (
    TimetableConflictService,
    timetable_conflict_service,
)


class TimetableEntryService:
    """
    Business logic service for managing individual TimetableEntry records.
    """

    def __init__(
        self,
        repository: TimetableEntryRepository = timetable_entry_repository,
        timetable_repo: TimetableRepository = timetable_repository,
        conflict_service: TimetableConflictService = timetable_conflict_service,
    ) -> None:
        self.repository = repository
        self.timetable_repository = timetable_repo
        self.conflict_service = conflict_service

    def create_entry(
        self,
        db: Session,
        timetable_id: UUID,
        entry_data: TimetableEntryCreate,
        current_school_id: UUID | None = None,
    ) -> TimetableEntry:
        """
        Create a new TimetableEntry under a timetable after validating conflicts and tenant ownership.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        timetable = self.timetable_repository.get_by_id_and_school(
            db, timetable_id, current_school_id
        )
        if timetable is None:
            raise NotFoundException("Timetable", str(timetable_id))

        if timetable.status != TimetableStatus.DRAFT:
            raise ValidationException(f"Cannot modify entries of a {timetable.status.value} timetable. Structure is immutable.")

        self.conflict_service.validate_entry(
            db,
            school_id=current_school_id,
            timetable=timetable,
            day_of_week=entry_data.day_of_week,
            period_slot_id=entry_data.period_slot_id,
            subject_id=entry_data.subject_id,
            teacher_id=entry_data.teacher_id,
            classroom_id=entry_data.classroom_id,
        )

        entry = TimetableEntry(
            timetable_id=timetable.id,
            day_of_week=entry_data.day_of_week,
            period_slot_id=entry_data.period_slot_id,
            subject_id=entry_data.subject_id,
            teacher_id=entry_data.teacher_id,
            classroom_id=entry_data.classroom_id,
        )

        created = self.repository.create(db, entry)
        return self.repository.get_with_details(db, created.id, current_school_id)

    def get_entry(
        self,
        db: Session,
        entry_id: UUID,
        current_school_id: UUID | None = None,
    ) -> TimetableEntry:
        """
        Retrieve a TimetableEntry by ID within tenant scope.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        entry = self.repository.get_with_details(db, entry_id, current_school_id)
        if entry is None:
            raise NotFoundException("TimetableEntry", str(entry_id))

        return entry

    def list_entries_by_timetable(
        self,
        db: Session,
        timetable_id: UUID,
        current_school_id: UUID | None = None,
    ) -> list[TimetableEntry]:
        """
        List all active entries for a timetable with eager loaded details.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        timetable = self.timetable_repository.get_by_id_and_school(
            db, timetable_id, current_school_id
        )
        if timetable is None:
            raise NotFoundException("Timetable", str(timetable_id))

        return self.repository.list_by_timetable(db, timetable_id)

    def update_entry(
        self,
        db: Session,
        entry_id: UUID,
        entry_data: TimetableEntryUpdate,
        current_school_id: UUID | None = None,
    ) -> TimetableEntry:
        """
        Update an existing TimetableEntry after validating conflicts.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        entry = self.repository.get_with_details(db, entry_id, current_school_id)
        if entry is None:
            raise NotFoundException("TimetableEntry", str(entry_id))

        if entry.timetable.status != TimetableStatus.DRAFT:
            raise ValidationException(f"Cannot modify entries of a {entry.timetable.status.value} timetable. Structure is immutable.")

        new_day = entry_data.day_of_week if entry_data.day_of_week is not None else entry.day_of_week
        new_slot_id = entry_data.period_slot_id if entry_data.period_slot_id is not None else entry.period_slot_id
        new_subject_id = entry_data.subject_id if entry_data.subject_id is not None else entry.subject_id
        new_teacher_id = entry_data.teacher_id if entry_data.teacher_id is not None else entry.teacher_id
        new_classroom_id = entry_data.classroom_id if entry_data.classroom_id is not None else entry.classroom_id

        self.conflict_service.validate_entry(
            db,
            school_id=current_school_id,
            timetable=entry.timetable,
            day_of_week=new_day,
            period_slot_id=new_slot_id,
            subject_id=new_subject_id,
            teacher_id=new_teacher_id,
            classroom_id=new_classroom_id,
            exclude_entry_id=entry_id,
        )

        entry.day_of_week = new_day
        entry.period_slot_id = new_slot_id
        entry.subject_id = new_subject_id
        entry.teacher_id = new_teacher_id
        entry.classroom_id = new_classroom_id

        self.repository.update(db, entry)
        return self.repository.get_with_details(db, entry_id, current_school_id)

    def delete_entry(
        self,
        db: Session,
        entry_id: UUID,
        current_school_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a TimetableEntry.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        entry = self.repository.get_by_id_and_school(db, entry_id, current_school_id)
        if entry is None:
            raise NotFoundException("TimetableEntry", str(entry_id))

        if entry.timetable.status != TimetableStatus.DRAFT:
            raise ValidationException(f"Cannot modify entries of a {entry.timetable.status.value} timetable. Structure is immutable.")

        self.repository.delete(db, entry)


timetable_entry_service = TimetableEntryService()
