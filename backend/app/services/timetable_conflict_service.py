from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums.timetable import DayOfWeek
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.timetable.timetable import Timetable
from app.repositories.timetable.classroom_repository import ClassroomRepository, classroom_repository
from app.repositories.timetable.period_slot_repository import PeriodSlotRepository, period_slot_repository
from app.repositories.subject.subject_repository import SubjectRepository, subject_repository
from app.repositories.teacher.teacher_repository import TeacherRepository, teacher_repository
from app.repositories.timetable.timetable_entry_repository import (
    TimetableEntryRepository,
    timetable_entry_repository,
)


class TimetableConflictService:
    """
    Business logic service for validating timetable entry conflicts
    (Section conflict, Teacher double-booking, Classroom double-booking, and Tenant scoping).
    """

    def __init__(
        self,
        entry_repo: TimetableEntryRepository = timetable_entry_repository,
        period_slot_repo: PeriodSlotRepository = period_slot_repository,
        subject_repo: SubjectRepository = subject_repository,
        teacher_repo: TeacherRepository = teacher_repository,
        classroom_repo: ClassroomRepository = classroom_repository,
    ) -> None:
        self.entry_repository = entry_repo
        self.period_slot_repository = period_slot_repo
        self.subject_repository = subject_repo
        self.teacher_repository = teacher_repo
        self.classroom_repository = classroom_repo

    def validate_entry(
        self,
        db: Session,
        school_id: UUID,
        timetable: Timetable,
        day_of_week: DayOfWeek,
        period_slot_id: UUID,
        subject_id: UUID,
        teacher_id: UUID,
        classroom_id: UUID | None = None,
        exclude_entry_id: UUID | None = None,
    ) -> None:
        """
        Validate all conflict rules for a timetable entry before creation or update.
        """
        # 1. Verify PeriodSlot exists and belongs to school
        slot = self.period_slot_repository.get_by_id_and_school(db, period_slot_id, school_id)
        if slot is None or slot.is_deleted:
            raise NotFoundException("PeriodSlot", str(period_slot_id))

        # 2. Verify Subject exists and belongs to school
        subject = self.subject_repository.get(db, subject_id)
        if subject is None or subject.is_deleted or subject.school_id != school_id:
            raise NotFoundException("Subject", str(subject_id))

        # 3. Verify Teacher exists and belongs to school
        teacher = self.teacher_repository.get(db, teacher_id)
        if teacher is None or teacher.is_deleted or teacher.school_id != school_id:
            raise NotFoundException("Teacher", str(teacher_id))

        # 4. Verify Classroom exists and belongs to school if provided
        classroom = None
        if classroom_id:
            classroom = self.classroom_repository.get_by_id_and_school(db, classroom_id, school_id)
            if classroom is None or classroom.is_deleted:
                raise NotFoundException("Classroom", str(classroom_id))

        # 5. Check Section Slot Conflict (same timetable, day, period_slot)
        existing_slot_entry = self.entry_repository.get_by_slot(
            db, timetable.id, day_of_week, period_slot_id, exclude_entry_id=exclude_entry_id
        )
        if existing_slot_entry:
            raise AlreadyExistsException(
                "TimetableEntry for period slot",
                f"{day_of_week.value} {slot.name}",
            )

        # 6. Check Teacher Double-Booking Conflict
        teacher_conflict = self.entry_repository.find_teacher_conflict(
            db,
            school_id=school_id,
            academic_year_id=timetable.academic_year_id,
            teacher_id=teacher_id,
            day_of_week=day_of_week,
            period_slot_id=period_slot_id,
            exclude_entry_id=exclude_entry_id,
        )
        if teacher_conflict:
            t_class = (
                teacher_conflict.timetable.school_class.name
                if teacher_conflict.timetable and teacher_conflict.timetable.school_class
                else "another class"
            )
            t_sec = (
                teacher_conflict.timetable.section.name
                if teacher_conflict.timetable and teacher_conflict.timetable.section
                else ""
            )
            raise ValidationException(
                f"Teacher '{teacher.first_name} {teacher.last_name}' is already scheduled to teach "
                f"{t_class} {t_sec} during {day_of_week.value} {slot.name}."
            )

        # 7. Check Classroom Double-Booking Conflict (if classroom_id provided)
        if classroom_id and classroom:
            room_conflict = self.entry_repository.find_classroom_conflict(
                db,
                school_id=school_id,
                academic_year_id=timetable.academic_year_id,
                classroom_id=classroom_id,
                day_of_week=day_of_week,
                period_slot_id=period_slot_id,
                exclude_entry_id=exclude_entry_id,
            )
            if room_conflict:
                r_class = (
                    room_conflict.timetable.school_class.name
                    if room_conflict.timetable and room_conflict.timetable.school_class
                    else "another class"
                )
                r_sec = (
                    room_conflict.timetable.section.name
                    if room_conflict.timetable and room_conflict.timetable.section
                    else ""
                )
                raise ValidationException(
                    f"Classroom '{classroom.room_number}' is already occupied by "
                    f"{r_class} {r_sec} during {day_of_week.value} {slot.name}."
                )


timetable_conflict_service = TimetableConflictService()
