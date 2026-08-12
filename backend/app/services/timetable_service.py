from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums.timetable import TimetableStatus
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.timetable.timetable import Timetable
from app.repositories.academic_term.academic_term_repository import (
    AcademicTermRepository,
    academic_term_repository,
)
from app.repositories.academic_year.academic_year_repository import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.repositories.school_class.school_class_repository import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.section.section_repository import (
    SectionRepository,
    section_repository,
)
from app.repositories.teacher.teacher_repository import (
    TeacherRepository,
    teacher_repository,
)
from app.repositories.timetable.timetable_entry_repository import (
    TimetableEntryRepository,
    timetable_entry_repository,
)
from app.repositories.timetable.timetable_repository import (
    TimetableRepository,
    timetable_repository,
)
from app.schemas.timetable.timetable import (
    TeacherScheduleEntryResponse,
    TimetableCreate,
    TimetableDetailResponse,
    TimetableFilter,
    TimetableListResponse,
    TimetableResponse,
    TimetableUpdate,
)
from app.schemas.timetable.timetable_entry import (
    ClassroomNested,
    PeriodSlotNested,
    SubjectNested,
    TeacherNested,
    TimetableEntryDetailResponse,
)


class TimetableService:
    """
    Business logic service for managing Timetable containers, section schedules, and teacher views.
    """

    def __init__(
        self,
        repository: TimetableRepository = timetable_repository,
        entry_repository: TimetableEntryRepository = timetable_entry_repository,
        school_repo: SchoolRepository = school_repository,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
        academic_term_repo: AcademicTermRepository = academic_term_repository,
        school_class_repo: SchoolClassRepository = school_class_repository,
        section_repo: SectionRepository = section_repository,
        teacher_repo: TeacherRepository = teacher_repository,
    ) -> None:
        self.repository = repository
        self.entry_repository = entry_repository
        self.school_repository = school_repo
        self.academic_year_repository = academic_year_repo
        self.academic_term_repository = academic_term_repo
        self.school_class_repository = school_class_repo
        self.section_repository = section_repo
        self.teacher_repository = teacher_repo

    def create_timetable(
        self,
        db: Session,
        timetable_data: TimetableCreate,
        current_school_id: UUID | None = None,
    ) -> Timetable:
        """
        Create a new Timetable container for a class section.
        """
        if current_school_id is not None and timetable_data.school_id != current_school_id:
            raise ForbiddenException("Cannot create timetable for another school.")

        school = self.school_repository.get(db, timetable_data.school_id)
        if school is None or school.is_deleted:
            raise NotFoundException("School", str(timetable_data.school_id))

        ay = self.academic_year_repository.get(db, timetable_data.academic_year_id)
        if ay is None or ay.is_deleted:
            raise NotFoundException("AcademicYear", str(timetable_data.academic_year_id))
        if ay.school_id != timetable_data.school_id:
            raise ValidationException("Academic year must belong to the same school.")

        sc = self.school_class_repository.get(db, timetable_data.school_class_id)
        if sc is None or sc.is_deleted:
            raise NotFoundException("SchoolClass", str(timetable_data.school_class_id))
        if sc.school_id != timetable_data.school_id:
            raise ValidationException("School class must belong to the same school.")

        sec = self.section_repository.get(db, timetable_data.section_id)
        if sec is None or sec.is_deleted:
            raise NotFoundException("Section", str(timetable_data.section_id))
        if sec.school_class_id != timetable_data.school_class_id:
            raise ValidationException("Section must belong to the specified school class.")

        if timetable_data.academic_term_id:
            term = self.academic_term_repository.get_by_id_and_school(
                db, timetable_data.academic_term_id, timetable_data.school_id
            )
            if term is None or term.is_deleted:
                raise NotFoundException("AcademicTerm", str(timetable_data.academic_term_id))
            if term.academic_year_id != timetable_data.academic_year_id:
                raise ValidationException("Academic term must belong to the specified academic year.")

        if self.repository.exists_by_section_and_year(
            db,
            school_id=timetable_data.school_id,
            academic_year_id=timetable_data.academic_year_id,
            section_id=timetable_data.section_id,
            academic_term_id=timetable_data.academic_term_id,
        ):
            raise AlreadyExistsException(
                "Timetable for section in academic year/term", str(timetable_data.section_id)
            )

        timetable = Timetable(
            school_id=timetable_data.school_id,
            academic_year_id=timetable_data.academic_year_id,
            school_class_id=timetable_data.school_class_id,
            section_id=timetable_data.section_id,
            academic_term_id=timetable_data.academic_term_id,
            status=TimetableStatus.DRAFT,
            is_active=True,
        )

        created = self.repository.create(db, timetable)
        return self.repository.get_with_entries(db, created.id, timetable_data.school_id)

    def get_timetable(
        self,
        db: Session,
        timetable_id: UUID,
        current_school_id: UUID | None = None,
    ) -> TimetableDetailResponse:
        """
        Get a specific Timetable with full entry matrix for frontend rendering.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        timetable = self.repository.get_with_entries(db, timetable_id, current_school_id)
        if timetable is None:
            raise NotFoundException("Timetable", str(timetable_id))

        return self._build_timetable_detail_response(timetable)

    def list_timetables(
        self,
        db: Session,
        filters: TimetableFilter,
        current_school_id: UUID | None = None,
    ) -> TimetableListResponse:
        """
        List paginated Timetables for a tenant school.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        items, total = self.repository.list_by_school(db, current_school_id, filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return TimetableListResponse(
            items=[TimetableResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_timetable(
        self,
        db: Session,
        timetable_id: UUID,
        timetable_data: TimetableUpdate,
        current_school_id: UUID | None = None,
    ) -> TimetableDetailResponse:
        """
        Update an existing Timetable.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        timetable = self.repository.get_by_id_and_school(db, timetable_id, current_school_id)
        if timetable is None:
            raise NotFoundException("Timetable", str(timetable_id))

        if timetable_data.academic_term_id is not None:
            term = self.academic_term_repository.get_by_id_and_school(
                db, timetable_data.academic_term_id, current_school_id
            )
            if term is None or term.is_deleted:
                raise NotFoundException("AcademicTerm", str(timetable_data.academic_term_id))
            if term.academic_year_id != timetable.academic_year_id:
                raise ValidationException("Academic term must belong to the specified academic year.")
            timetable.academic_term_id = timetable_data.academic_term_id

        if timetable_data.is_active is not None:
            timetable.is_active = timetable_data.is_active

        self.repository.update(db, timetable)
        return self.get_timetable(db, timetable_id, current_school_id)

    def get_section_timetable(
        self,
        db: Session,
        section_id: UUID,
        current_school_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        academic_term_id: UUID | None = None,
    ) -> TimetableDetailResponse:
        """
        Retrieve active timetable matrix for a section.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        sec = self.section_repository.get(db, section_id)
        if sec is None or sec.is_deleted:
            raise NotFoundException("Section", str(section_id))

        timetable = self.repository.get_active_by_section(
            db,
            school_id=current_school_id,
            section_id=section_id,
            academic_year_id=academic_year_id,
            academic_term_id=academic_term_id,
        )
        if timetable is None:
            raise NotFoundException("Active Timetable for section", str(section_id))

        return self._build_timetable_detail_response(timetable)

    def get_teacher_schedule(
        self,
        db: Session,
        teacher_id: UUID,
        current_school_id: UUID | None = None,
        academic_year_id: UUID | None = None,
    ) -> list[TeacherScheduleEntryResponse]:
        """
        Retrieve scheduled entries for a teacher in a school across all active timetables.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        teacher = self.teacher_repository.get(db, teacher_id)
        if teacher is None or teacher.is_deleted or teacher.school_id != current_school_id:
            raise NotFoundException("Teacher", str(teacher_id))

        entries = self.entry_repository.list_by_teacher(
            db,
            school_id=current_school_id,
            teacher_id=teacher_id,
            academic_year_id=academic_year_id,
        )

        schedule: list[TeacherScheduleEntryResponse] = []
        for entry in entries:
            schedule.append(
                TeacherScheduleEntryResponse(
                    entry_id=entry.id,
                    timetable_id=entry.timetable_id,
                    academic_year_id=entry.timetable.academic_year_id,
                    school_class_id=entry.timetable.school_class_id,
                    section_id=entry.timetable.section_id,
                    school_class_name=entry.timetable.school_class.name,
                    section_name=entry.timetable.section.name,
                    day_of_week=entry.day_of_week.value,
                    period_slot={
                        "id": str(entry.period_slot.id),
                        "name": entry.period_slot.name,
                        "period_type": entry.period_slot.period_type.value,
                        "start_time": entry.period_slot.start_time.isoformat(),
                        "end_time": entry.period_slot.end_time.isoformat(),
                        "display_order": entry.period_slot.display_order,
                    },
                    subject={
                        "id": str(entry.subject.id),
                        "subject_name": entry.subject.subject_name,
                        "subject_code": entry.subject.subject_code,
                    },
                    classroom=(
                        {
                            "id": str(entry.classroom.id),
                            "room_number": entry.classroom.room_number,
                            "building_name": entry.classroom.building_name,
                            "capacity": entry.classroom.capacity,
                            "room_type": entry.classroom.room_type.value,
                        }
                        if entry.classroom
                        else None
                    ),
                )
            )

        return schedule

    def _build_timetable_detail_response(self, timetable: Timetable) -> TimetableDetailResponse:
        entry_responses: list[TimetableEntryDetailResponse] = []
        for e in timetable.entries:
            if e.is_deleted:
                continue
            entry_responses.append(
                TimetableEntryDetailResponse(
                    id=e.id,
                    timetable_id=e.timetable_id,
                    day_of_week=e.day_of_week,
                    period_slot_id=e.period_slot_id,
                    subject_id=e.subject_id,
                    teacher_id=e.teacher_id,
                    classroom_id=e.classroom_id,
                    created_at=e.created_at,
                    updated_at=e.updated_at,
                    period_slot=PeriodSlotNested.model_validate(e.period_slot),
                    subject=SubjectNested.model_validate(e.subject),
                    teacher=TeacherNested.model_validate(e.teacher),
                    classroom=ClassroomNested.model_validate(e.classroom) if e.classroom else None,
                )
            )

        return TimetableDetailResponse(
            id=timetable.id,
            school_id=timetable.school_id,
            academic_year_id=timetable.academic_year_id,
            school_class_id=timetable.school_class_id,
            section_id=timetable.section_id,
            academic_term_id=timetable.academic_term_id,
            status=timetable.status,
            is_active=timetable.is_active,
            created_at=timetable.created_at,
            updated_at=timetable.updated_at,
            entries=entry_responses,
        )


timetable_service = TimetableService()
