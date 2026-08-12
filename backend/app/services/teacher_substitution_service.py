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
from app.models.timetable.teacher_substitution import TeacherSubstitution
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.repositories.teacher.teacher_repository import (
    TeacherRepository,
    teacher_repository,
)
from app.repositories.timetable.teacher_substitution_repository import (
    TeacherSubstitutionRepository,
    teacher_substitution_repository,
)
from app.repositories.timetable.timetable_entry_repository import (
    TimetableEntryRepository,
    timetable_entry_repository,
)
from app.schemas.timetable.teacher_substitution import (
    TeacherSubstitutionCreate,
    TeacherSubstitutionDetailResponse,
    TeacherSubstitutionFilter,
    TeacherSubstitutionListResponse,
    TeacherSubstitutionResponse,
    TeacherSubstitutionUpdate,
)
from app.schemas.timetable.timetable_entry import (
    ClassroomNested,
    PeriodSlotNested,
    SubjectNested,
    TeacherNested,
    TimetableEntryDetailResponse,
)


class TeacherSubstitutionService:
    """
    Business logic service for managing daily TeacherSubstitutions.
    Maintains historical matrix integrity while ensuring substitute conflict freedom.
    """

    def __init__(
        self,
        repository: TeacherSubstitutionRepository = teacher_substitution_repository,
        entry_repository: TimetableEntryRepository = timetable_entry_repository,
        teacher_repository: TeacherRepository = teacher_repository,
        school_repository: SchoolRepository = school_repository,
    ) -> None:
        self.repository = repository
        self.entry_repository = entry_repository
        self.teacher_repository = teacher_repository
        self.school_repository = school_repository

    def create_substitution(
        self,
        db: Session,
        sub_data: TeacherSubstitutionCreate,
        current_school_id: UUID | None = None,
    ) -> TeacherSubstitutionDetailResponse:
        """
        Create a new TeacherSubstitution for a published timetable entry on a specific date.
        """
        if current_school_id is not None and sub_data.school_id != current_school_id:
            raise ForbiddenException("Cannot create teacher substitution for another school.")

        school_id = current_school_id or sub_data.school_id

        # 1. Retrieve entry with timetable and relations
        entry = self.entry_repository.get_with_details(db, sub_data.timetable_entry_id, school_id)
        if entry is None or entry.is_deleted:
            raise NotFoundException("TimetableEntry", str(sub_data.timetable_entry_id))

        timetable = entry.timetable
        if timetable is None or timetable.is_deleted or timetable.school_id != school_id:
            raise NotFoundException("Timetable", str(entry.timetable_id))

        # 2. Parent timetable must be PUBLISHED
        if timetable.status != TimetableStatus.PUBLISHED:
            raise ValidationException("Substitutions can only be assigned to PUBLISHED timetables.")

        # 3. Verify weekday match
        expected_day = sub_data.substitution_date.strftime("%A").upper()
        if expected_day != entry.day_of_week.value:
            raise ValidationException(
                f"substitution_date ({sub_data.substitution_date}) is a {expected_day}, "
                f"which does not match the timetable entry day ({entry.day_of_week.value})."
            )

        # 4. Set original_teacher_id snapshot
        original_teacher_id = entry.teacher_id
        if sub_data.substitute_teacher_id == original_teacher_id:
            raise ValidationException("Substitute teacher cannot be the same as the original teacher.")

        # 5. Verify substitute teacher exists and is active
        substitute = self.teacher_repository.get(db, sub_data.substitute_teacher_id)
        if substitute is None or substitute.is_deleted or substitute.school_id != school_id:
            raise NotFoundException("Substitute Teacher", str(sub_data.substitute_teacher_id))

        # 6. Check duplicate active substitution for entry + date
        existing_sub = self.repository.get_active_by_slot_and_date(
            db, sub_data.timetable_entry_id, sub_data.substitution_date
        )
        if existing_sub:
            raise AlreadyExistsException(
                "TeacherSubstitution for slot and date",
                f"{sub_data.substitution_date} {entry.period_slot.name}",
            )

        # 7. Check substitute regular schedule conflict
        teacher_reg_conflict = self.entry_repository.find_teacher_conflict(
            db,
            school_id=school_id,
            academic_year_id=timetable.academic_year_id,
            teacher_id=sub_data.substitute_teacher_id,
            day_of_week=entry.day_of_week,
            period_slot_id=entry.period_slot_id,
        )
        if teacher_reg_conflict:
            raise ValidationException(
                f"Substitute teacher '{substitute.first_name} {substitute.last_name}' is already scheduled "
                f"to teach another class during {entry.day_of_week.value} {entry.period_slot.name}."
            )

        # 8. Check substitute existing substitution schedule conflict
        sub_conflict = self.repository.find_substitute_conflict(
            db,
            school_id=school_id,
            substitute_teacher_id=sub_data.substitute_teacher_id,
            substitution_date=sub_data.substitution_date,
            period_slot_id=entry.period_slot_id,
        )
        if sub_conflict:
            raise ValidationException(
                f"Substitute teacher '{substitute.first_name} {substitute.last_name}' is already assigned "
                f"to another substitution during {sub_data.substitution_date} {entry.period_slot.name}."
            )

        substitution = TeacherSubstitution(
            school_id=school_id,
            timetable_entry_id=sub_data.timetable_entry_id,
            substitution_date=sub_data.substitution_date,
            original_teacher_id=original_teacher_id,
            substitute_teacher_id=sub_data.substitute_teacher_id,
            remarks=sub_data.remarks,
        )

        created = self.repository.create(db, substitution)
        return self.get_substitution(db, created.id, school_id)

    def get_substitution(
        self,
        db: Session,
        substitution_id: UUID,
        current_school_id: UUID | None = None,
    ) -> TeacherSubstitutionDetailResponse:
        """
        Retrieve a TeacherSubstitution by ID within tenant scope.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        sub = self.repository.get_with_details(db, substitution_id, current_school_id)
        if sub is None:
            raise NotFoundException("TeacherSubstitution", str(substitution_id))

        return self._build_substitution_detail_response(sub)

    def list_substitutions(
        self,
        db: Session,
        filters: TeacherSubstitutionFilter,
        current_school_id: UUID | None = None,
    ) -> TeacherSubstitutionListResponse:
        """
        List paginated TeacherSubstitutions for a tenant school.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        items, total = self.repository.list_by_school(db, current_school_id, filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        detail_items = [self._build_substitution_detail_response(item) for item in items]
        return TeacherSubstitutionListResponse(
            items=detail_items,
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_substitution(
        self,
        db: Session,
        substitution_id: UUID,
        sub_data: TeacherSubstitutionUpdate,
        current_school_id: UUID | None = None,
    ) -> TeacherSubstitutionDetailResponse:
        """
        Update an existing TeacherSubstitution.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        sub = self.repository.get_with_details(db, substitution_id, current_school_id)
        if sub is None:
            raise NotFoundException("TeacherSubstitution", str(substitution_id))

        entry = sub.timetable_entry
        timetable = entry.timetable

        if timetable.status != TimetableStatus.PUBLISHED:
            raise ValidationException("Substitutions cannot be modified for non-PUBLISHED timetables.")

        if sub_data.substitute_teacher_id is not None:
            if sub_data.substitute_teacher_id == sub.original_teacher_id:
                raise ValidationException("Substitute teacher cannot be the same as original teacher.")

            new_substitute = self.teacher_repository.get(db, sub_data.substitute_teacher_id)
            if new_substitute is None or new_substitute.is_deleted or new_substitute.school_id != current_school_id:
                raise NotFoundException("Substitute Teacher", str(sub_data.substitute_teacher_id))

            # Conflict checks excluding current substitution
            teacher_reg_conflict = self.entry_repository.find_teacher_conflict(
                db,
                school_id=current_school_id,
                academic_year_id=timetable.academic_year_id,
                teacher_id=sub_data.substitute_teacher_id,
                day_of_week=entry.day_of_week,
                period_slot_id=entry.period_slot_id,
            )
            if teacher_reg_conflict:
                raise ValidationException(
                    f"Substitute teacher '{new_substitute.first_name} {new_substitute.last_name}' is already "
                    f"scheduled to teach another class during {entry.day_of_week.value} {entry.period_slot.name}."
                )

            sub_conflict = self.repository.find_substitute_conflict(
                db,
                school_id=current_school_id,
                substitute_teacher_id=sub_data.substitute_teacher_id,
                substitution_date=sub.substitution_date,
                period_slot_id=entry.period_slot_id,
                exclude_id=substitution_id,
            )
            if sub_conflict:
                raise ValidationException(
                    f"Substitute teacher '{new_substitute.first_name} {new_substitute.last_name}' is already "
                    f"assigned to another substitution during {sub.substitution_date} {entry.period_slot.name}."
                )

            sub.substitute_teacher_id = sub_data.substitute_teacher_id

        if sub_data.remarks is not None:
            sub.remarks = sub_data.remarks

        self.repository.update(db, sub)
        return self.get_substitution(db, substitution_id, current_school_id)

    def delete_substitution(
        self,
        db: Session,
        substitution_id: UUID,
        current_school_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a TeacherSubstitution.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        sub = self.repository.get_by_id_and_school(db, substitution_id, current_school_id)
        if sub is None:
            raise NotFoundException("TeacherSubstitution", str(substitution_id))

        self.repository.delete(db, sub)

    def _build_substitution_detail_response(
        self, sub: TeacherSubstitution
    ) -> TeacherSubstitutionDetailResponse:
        entry = sub.timetable_entry
        return TeacherSubstitutionDetailResponse(
            id=sub.id,
            school_id=sub.school_id,
            timetable_entry_id=sub.timetable_entry_id,
            substitution_date=sub.substitution_date,
            original_teacher_id=sub.original_teacher_id,
            substitute_teacher_id=sub.substitute_teacher_id,
            remarks=sub.remarks,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            original_teacher=TeacherNested.model_validate(sub.original_teacher),
            substitute_teacher=TeacherNested.model_validate(sub.substitute_teacher),
            timetable_entry=TimetableEntryDetailResponse(
                id=entry.id,
                timetable_id=entry.timetable_id,
                day_of_week=entry.day_of_week,
                period_slot_id=entry.period_slot_id,
                subject_id=entry.subject_id,
                teacher_id=entry.teacher_id,
                classroom_id=entry.classroom_id,
                created_at=entry.created_at,
                updated_at=entry.updated_at,
                period_slot=PeriodSlotNested.model_validate(entry.period_slot),
                subject=SubjectNested.model_validate(entry.subject),
                teacher=TeacherNested.model_validate(entry.teacher),
                classroom=ClassroomNested.model_validate(entry.classroom) if entry.classroom else None,
            ),
        )


teacher_substitution_service = TeacherSubstitutionService()
