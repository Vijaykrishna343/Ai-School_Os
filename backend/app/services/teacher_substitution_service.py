from math import ceil
from uuid import UUID
from datetime import date

from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.common.enums import AttendanceStatus, TeacherStatus
from app.common.enums.timetable import TimetableStatus
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.models.timetable.teacher_substitution import TeacherSubstitution
from app.models.timetable.timetable_entry import TimetableEntry
from app.models.timetable.timetable import Timetable
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
    AffectedSlotsResponse,
    AffectedTimetableSlotItem,
    AutoAssignSubstitutionsRequest,
    AutoAssignSubstitutionsResponse,
    SubstituteCandidateRecommendation,
    SubstituteRecommendationsResponse,
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

    def get_affected_slots(
        self,
        db: Session,
        current_school_id: UUID,
        substitution_date: date,
        school_class_id: UUID | None = None,
    ) -> AffectedSlotsResponse:
        """
        Get all timetable slots affected by absent or on-leave teachers for a specific date.
        """
        # 1. Query attendance records for absent/excused teachers
        absent_attendances = db.scalars(
            select(TeacherAttendance).where(
                TeacherAttendance.school_id == current_school_id,
                TeacherAttendance.attendance_date == substitution_date,
                TeacherAttendance.status.in_([
                    AttendanceStatus.ABSENT,
                    AttendanceStatus.EXCUSED,
                    AttendanceStatus.HALF_DAY,
                ]),
                TeacherAttendance.is_deleted.is_(False),
            )
        ).all()
        absent_teacher_ids = {att.teacher_id for att in absent_attendances}

        if not absent_teacher_ids:
            return AffectedSlotsResponse(
                substitution_date=substitution_date,
                total_affected_slots=0,
                unassigned_count=0,
                assigned_count=0,
                items=[],
            )

        # 2. Match day of week
        target_day_str = substitution_date.strftime("%A").upper()

        # 3. Query timetable entries for absent teachers in published timetables
        stmt = (
            select(TimetableEntry)
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                Timetable.school_id == current_school_id,
                Timetable.status == TimetableStatus.PUBLISHED,
                Timetable.is_deleted.is_(False),
                TimetableEntry.teacher_id.in_(absent_teacher_ids),
                TimetableEntry.day_of_week == target_day_str,
                TimetableEntry.is_deleted.is_(False),
            )
        )
        if school_class_id:
            stmt = stmt.where(Timetable.school_class_id == school_class_id)

        entries = db.scalars(stmt).all()

        # 4. Fetch existing substitutions on that date
        existing_subs = db.scalars(
            select(TeacherSubstitution).where(
                TeacherSubstitution.school_id == current_school_id,
                TeacherSubstitution.substitution_date == substitution_date,
                TeacherSubstitution.is_deleted.is_(False),
            )
        ).all()
        sub_by_entry_id = {sub.timetable_entry_id: sub for sub in existing_subs}

        # 5. Build items
        items: list[AffectedTimetableSlotItem] = []
        assigned_count = 0
        unassigned_count = 0

        for entry in entries:
            sub = sub_by_entry_id.get(entry.id)
            orig_t = entry.teacher
            sub_t = sub.substitute_teacher if sub else None
            tt = entry.timetable

            status_str = "ASSIGNED" if sub else "UNASSIGNED"
            if sub:
                assigned_count += 1
            else:
                unassigned_count += 1

            items.append(
                AffectedTimetableSlotItem(
                    timetable_entry_id=entry.id,
                    timetable_id=entry.timetable_id,
                    class_name=tt.school_class.name if tt and tt.school_class else "",
                    section_name=tt.section.name if tt and tt.section else "",
                    period_slot_name=entry.period_slot.name if entry.period_slot else "",
                    start_time=entry.period_slot.start_time.strftime("%H:%M") if entry.period_slot and entry.period_slot.start_time else "",
                    end_time=entry.period_slot.end_time.strftime("%H:%M") if entry.period_slot and entry.period_slot.end_time else "",
                    day_of_week=entry.day_of_week.value if hasattr(entry.day_of_week, "value") else str(entry.day_of_week),
                    subject_name=entry.subject.subject_name if entry.subject else "",
                    subject_code=entry.subject.subject_code if entry.subject else "",
                    original_teacher_id=entry.teacher_id,
                    original_teacher_name=f"{orig_t.first_name} {orig_t.last_name}" if orig_t else "Teacher",
                    substitution_id=sub.id if sub else None,
                    substitute_teacher_id=sub.substitute_teacher_id if sub else None,
                    substitute_teacher_name=f"{sub_t.first_name} {sub_t.last_name}" if sub_t else None,
                    status=status_str,
                )
            )

        return AffectedSlotsResponse(
            substitution_date=substitution_date,
            total_affected_slots=len(items),
            unassigned_count=unassigned_count,
            assigned_count=assigned_count,
            items=items,
        )

    def get_recommendations(
        self,
        db: Session,
        current_school_id: UUID,
        timetable_entry_id: UUID,
        substitution_date: date,
    ) -> SubstituteRecommendationsResponse:
        """
        Evaluate, score, and rank candidate substitute teachers for a specific timetable entry and date.
        """
        entry = self.entry_repository.get_with_details(db, timetable_entry_id, current_school_id)
        if entry is None or entry.is_deleted:
            raise NotFoundException("TimetableEntry", str(timetable_entry_id))

        tt = entry.timetable
        if tt is None or tt.is_deleted or tt.school_id != current_school_id:
            raise NotFoundException("Timetable", str(entry.timetable_id))

        if tt.status != TimetableStatus.PUBLISHED:
            raise ValidationException("Substitutions can only be recommended for PUBLISHED timetables.")

        expected_day = substitution_date.strftime("%A").upper()
        if expected_day != entry.day_of_week.value:
            raise ValidationException(
                f"substitution_date ({substitution_date}) day {expected_day} does not match entry day {entry.day_of_week.value}."
            )

        # Fetch all active teachers in school
        active_teachers = db.scalars(
            select(Teacher).where(
                Teacher.school_id == current_school_id,
                Teacher.status == TeacherStatus.ACTIVE,
                Teacher.is_deleted.is_(False),
            )
        ).all()

        # Attendance exclusions
        absent_records = db.scalars(
            select(TeacherAttendance).where(
                TeacherAttendance.school_id == current_school_id,
                TeacherAttendance.attendance_date == substitution_date,
                TeacherAttendance.status.in_([
                    AttendanceStatus.ABSENT,
                    AttendanceStatus.EXCUSED,
                    AttendanceStatus.HALF_DAY,
                ]),
                TeacherAttendance.is_deleted.is_(False),
            )
        ).all()
        absent_teacher_ids = {r.teacher_id for r in absent_records}

        # Regular schedule conflicts for period slot
        regular_conflicts = db.scalars(
            select(TimetableEntry.teacher_id)
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                Timetable.school_id == current_school_id,
                Timetable.academic_year_id == tt.academic_year_id,
                Timetable.is_deleted.is_(False),
                TimetableEntry.day_of_week == entry.day_of_week,
                TimetableEntry.period_slot_id == entry.period_slot_id,
                TimetableEntry.is_deleted.is_(False),
            )
        ).all()
        regular_busy_ids = set(regular_conflicts)

        # Existing substitution conflicts for period slot on date
        sub_conflicts = db.scalars(
            select(TeacherSubstitution.substitute_teacher_id)
            .join(TimetableEntry, TeacherSubstitution.timetable_entry_id == TimetableEntry.id)
            .where(
                TeacherSubstitution.school_id == current_school_id,
                TeacherSubstitution.substitution_date == substitution_date,
                TimetableEntry.period_slot_id == entry.period_slot_id,
                TeacherSubstitution.is_deleted.is_(False),
            )
        ).all()
        sub_busy_ids = set(sub_conflicts)

        # Count total substitutions today per teacher for workload score
        daily_subs = db.scalars(
            select(TeacherSubstitution)
            .where(
                TeacherSubstitution.school_id == current_school_id,
                TeacherSubstitution.substitution_date == substitution_date,
                TeacherSubstitution.is_deleted.is_(False),
            )
        ).all()
        subs_today_map: dict[UUID, int] = {}
        for s in daily_subs:
            subs_today_map[s.substitute_teacher_id] = subs_today_map.get(s.substitute_teacher_id, 0) + 1

        # Teachers subject familiarity: query all entries taught by teacher
        teacher_entries = db.scalars(
            select(TimetableEntry)
            .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
            .where(
                Timetable.school_id == current_school_id,
                Timetable.is_deleted.is_(False),
                TimetableEntry.is_deleted.is_(False),
            )
        ).all()

        teacher_subjects_map: dict[UUID, set[UUID]] = {}
        teacher_sections_map: dict[UUID, set[UUID]] = {}
        teacher_classes_map: dict[UUID, set[UUID]] = {}

        for te in teacher_entries:
            teacher_subjects_map.setdefault(te.teacher_id, set()).add(te.subject_id)
            if te.timetable:
                teacher_sections_map.setdefault(te.teacher_id, set()).add(te.timetable.section_id)
                teacher_classes_map.setdefault(te.teacher_id, set()).add(te.timetable.school_class_id)

        candidates: list[SubstituteCandidateRecommendation] = []
        target_subject_name = entry.subject.subject_name.lower() if entry.subject else ""

        for teacher in active_teachers:
            t_id = teacher.id
            reasons = []

            # 1. Hard Filter Checks
            if t_id == entry.teacher_id:
                continue
            if t_id in absent_teacher_ids:
                continue
            if t_id in regular_busy_ids:
                continue
            if t_id in sub_busy_ids:
                continue

            score = 0

            # 2. Soft Scoring
            # Subject Qualification (Max 40 pts)
            t_subjects = teacher_subjects_map.get(t_id, set())
            if entry.subject_id in t_subjects:
                score += 40
                reasons.append(f"Teaches {entry.subject.subject_name}")
            else:
                qual_str = f"{teacher.qualification or ''} {teacher.specialization or ''}".lower()
                if target_subject_name and target_subject_name in qual_str:
                    score += 25
                    reasons.append(f"Qualified in {entry.subject.subject_name}")
                else:
                    score += 5

            # Class / Section Familiarity (Max 25 pts)
            t_sections = teacher_sections_map.get(t_id, set())
            t_classes = teacher_classes_map.get(t_id, set())

            if tt.section_id in t_sections:
                score += 25
                reasons.append(f"Teaches in Grade {tt.school_class.name}-{tt.section.name}")
            elif tt.school_class_id in t_classes:
                score += 15
                reasons.append(f"Teaches in Grade {tt.school_class.name}")

            # Workload Burden (Max 25 pts)
            subs_count = subs_today_map.get(t_id, 0)
            if subs_count == 0:
                score += 25
                reasons.append("0 Substitutions today")
            elif subs_count == 1:
                score += 15
                reasons.append("1 Substitution today")
            else:
                score += 5

            # Schedule Buffer (Max 10 pts)
            score += 10
            reasons.append("Available & Conflict-Free")

            candidates.append(
                SubstituteCandidateRecommendation(
                    teacher_id=t_id,
                    teacher_name=f"{teacher.first_name} {teacher.last_name}",
                    employee_id=teacher.employee_id,
                    qualification=teacher.qualification,
                    specialization=teacher.specialization,
                    score=min(score, 100),
                    match_reasons=reasons,
                    is_available=True,
                )
            )

        candidates.sort(key=lambda c: (c.score, c.teacher_name), reverse=True)

        return SubstituteRecommendationsResponse(
            timetable_entry_id=timetable_entry_id,
            substitution_date=substitution_date,
            candidates=candidates,
        )

    def auto_assign_substitutions(
        self,
        db: Session,
        current_school_id: UUID,
        req: AutoAssignSubstitutionsRequest,
    ) -> AutoAssignSubstitutionsResponse:
        """
        Perform bulk automatic substitution assignment for affected timetable slots on a date.
        """
        affected = self.get_affected_slots(db, current_school_id, req.substitution_date, req.school_class_id)
        
        target_items = [
            item for item in affected.items
            if req.override_existing or item.status == "UNASSIGNED"
        ]

        if not target_items:
            return AutoAssignSubstitutionsResponse(
                substitution_date=req.substitution_date,
                total_unassigned_processed=0,
                assigned_count=0,
                skipped_count=0,
                created_substitutions=[],
            )

        created_subs: list[TeacherSubstitutionDetailResponse] = []
        skipped_count = 0

        # Track teachers assigned during this batch run to avoid period double-booking in loop
        assigned_in_batch: dict[tuple[date, UUID], set[UUID]] = {}

        for item in target_items:
            recs = self.get_recommendations(
                db, current_school_id, item.timetable_entry_id, req.substitution_date
            )

            # Filter out candidates already assigned in this batch run for entry period_slot
            entry = self.entry_repository.get(db, item.timetable_entry_id)
            slot_id = entry.period_slot_id if entry else None

            available_candidates = [
                c for c in recs.candidates
                if c.is_available and c.score > 0 and (
                    slot_id is None or c.teacher_id not in assigned_in_batch.get((req.substitution_date, slot_id), set())
                )
            ]

            if not available_candidates:
                skipped_count += 1
                continue

            top_candidate = available_candidates[0]

            # If item was already assigned and override_existing is True, delete existing sub first
            if item.substitution_id and req.override_existing:
                try:
                    self.delete_substitution(db, item.substitution_id, current_school_id)
                except Exception:
                    pass

            sub_create = TeacherSubstitutionCreate(
                school_id=current_school_id,
                timetable_entry_id=item.timetable_entry_id,
                substitution_date=req.substitution_date,
                substitute_teacher_id=top_candidate.teacher_id,
                remarks=f"Auto-assigned by Intelligent Substitution Engine (Score: {top_candidate.score}/100)",
            )

            sub_detail = self.create_substitution(db, sub_create, current_school_id)
            created_subs.append(sub_detail)

            if slot_id:
                assigned_in_batch.setdefault((req.substitution_date, slot_id), set()).add(top_candidate.teacher_id)

        return AutoAssignSubstitutionsResponse(
            substitution_date=req.substitution_date,
            total_unassigned_processed=len(target_items),
            assigned_count=len(created_subs),
            skipped_count=skipped_count,
            created_substitutions=created_subs,
        )


teacher_substitution_service = TeacherSubstitutionService()

