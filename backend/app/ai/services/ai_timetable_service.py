from __future__ import annotations

import uuid
from typing import Any
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.enums.timetable import DayOfWeek, TimetableStatus
from app.common.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
)
from app.identity.models.user import IdentityUser
from app.models.ai.ai_timetable_draft import AITimetableDraft, AITimetableDraftEntry
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.models.academic_year.academic_year import AcademicYear

from app.ai.security.tenant_boundary import AITenantBoundaryService
from app.ai.timetable.solver import (
    TimetableCPSATSolver,
    TimetableSolverInput,
    PeriodSlotInput,
    ClassroomInput,
    CurriculumRequirementInput,
    TeacherUnavailabilityInput,
    SectionUnavailabilityInput,
)
from app.ai.timetable.validator import timetable_validator
from app.ai.services.ai_audit_service import ai_audit_service


class AITimetableService:
    """
    Service orchestrating AI Timetable Generation, Solvers, Validation, Approval, and Publishing.
    Enforces strict zero-trust tenant boundaries and explicit multi-stage human approval.
    """

    def generate_draft(
        self,
        db: Session,
        current_user: IdentityUser,
        academic_year_id: uuid.UUID,
        name: str = "AI Timetable Draft",
        timeout_seconds: float = 30.0,
        class_section_ids: list[uuid.UUID] | None = None,
    ) -> AITimetableDraft:
        # 1. Validate tenant boundary
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)

        # 2. Verify Academic Year
        ay = db.scalar(
            select(AcademicYear).where(
                AcademicYear.id == academic_year_id,
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
        )
        if not ay:
            raise NotFoundException("AcademicYear", str(academic_year_id))

        # 3. Create Draft in SOLVING state
        draft = AITimetableDraft(
            id=uuid.uuid4(),
            school_id=school_id,
            academic_year_id=academic_year_id,
            name=name,
            status="SOLVING",
            solver_status="UNKNOWN",
            created_by_id=current_user.id,
        )
        db.add(draft)
        db.commit()
        db.refresh(draft)

        try:
            # 4. Fetch School Resources
            period_slots_orm = db.scalars(
                select(PeriodSlot)
                .where(PeriodSlot.school_id == school_id, PeriodSlot.is_deleted.is_(False))
                .order_by(PeriodSlot.display_order)
            ).all()

            classrooms_orm = db.scalars(
                select(Classroom).where(Classroom.school_id == school_id, Classroom.is_deleted.is_(False))
            ).all()

            sections_stmt = select(Section).join(SchoolClass).where(
                SchoolClass.school_id == school_id,
                Section.is_deleted.is_(False),
                SchoolClass.is_deleted.is_(False),
            )
            if class_section_ids:
                sections_stmt = sections_stmt.where(Section.id.in_(class_section_ids))
            sections_orm = db.scalars(sections_stmt).all()

            subjects_orm = db.scalars(
                select(Subject).where(Subject.school_id == school_id, Subject.is_deleted.is_(False))
            ).all()

            teachers_orm = db.scalars(
                select(Teacher).where(Teacher.school_id == school_id, Teacher.is_deleted.is_(False))
            ).all()

            days = ["MONDAY", "TUESDAY", "WEDNESDAY", "THURSDAY", "FRIDAY"]

            # Build solver inputs
            slots_input = [PeriodSlotInput(id=str(s.id), name=s.name, display_order=s.display_order) for s in period_slots_orm]
            rooms_input = [ClassroomInput(id=str(r.id), name=r.room_number, is_lab=(getattr(r, "room_type", "") == "LAB")) for r in classrooms_orm]

            # Construct curriculum requirements (e.g. distribute subjects & teachers among sections)
            curriculum_reqs: list[CurriculumRequirementInput] = []
            if sections_orm and subjects_orm and teachers_orm:
                for sec in sections_orm:
                    # Allocate 4 weekly periods per available subject
                    for subj_idx, subj in enumerate(subjects_orm[:min(len(subjects_orm), len(slots_input))]):
                        assigned_teacher = teachers_orm[subj_idx % len(teachers_orm)]
                        curriculum_reqs.append(
                            CurriculumRequirementInput(
                                section_id=str(sec.id),
                                school_class_id=str(sec.school_class_id),
                                subject_id=str(subj.id),
                                teacher_id=str(assigned_teacher.id),
                                required_weekly_periods=4,
                            )
                        )

            solver_input = TimetableSolverInput(
                school_id=str(school_id),
                academic_year_id=str(academic_year_id),
                days=days,
                period_slots=slots_input,
                classrooms=rooms_input,
                curriculum_requirements=curriculum_reqs,
                timeout_seconds=timeout_seconds,
            )

            # 5. Run CP-SAT Solver
            solver = TimetableCPSATSolver()
            solver_result = solver.solve(solver_input)

            # 6. Run Deterministic Validator
            val_report = timetable_validator.validate(solver_input, solver_result.assignments)

            # 7. Persist Results
            draft.solver_status = solver_result.status
            draft.solver_duration_ms = solver_result.solver_duration_ms
            draft.objective_score = solver_result.objective_score
            draft.constraint_summary = solver_result.constraint_stats
            draft.validation_report = {
                "is_valid": val_report.is_valid,
                "hard_violations": val_report.hard_violations,
                "soft_penalties": val_report.soft_penalties,
                "summary_stats": val_report.summary_stats,
            }
            draft.error_message = solver_result.error_message

            if solver_result.status in ("OPTIMAL", "FEASIBLE") and val_report.is_valid:
                draft.status = "SOLVED"
                # Store entries
                for a in solver_result.assignments:
                    entry = AITimetableDraftEntry(
                        id=uuid.uuid4(),
                        draft_id=draft.id,
                        school_class_id=uuid.UUID(a.school_class_id),
                        section_id=uuid.UUID(a.section_id),
                        subject_id=uuid.UUID(a.subject_id),
                        teacher_id=uuid.UUID(a.teacher_id),
                        classroom_id=uuid.UUID(a.classroom_id) if a.classroom_id else None,
                        period_slot_id=uuid.UUID(a.period_slot_id),
                        day_of_week=a.day_of_week,
                    )
                    db.add(entry)
            else:
                draft.status = "FAILED"

            db.commit()
            db.refresh(draft)

            # 8. Log Audit Event
            ai_audit_service.log_ai_event(
                db=db,
                school_id=school_id,
                user_id=current_user.id,
                capability="TIMETABLE_SOLVER",
                provider_type="OR_TOOLS_CP_SAT",
                model_name="cp-sat-v9",
                prompt_tokens=len(curriculum_reqs),
                completion_tokens=len(solver_result.assignments),
                estimated_cost_usd=0.0,  # Local solver computation
                latency_ms=solver_result.solver_duration_ms,
                status="SUCCESS" if draft.status == "SOLVED" else "FAILED",
                error_message=solver_result.error_message,
            )

            return draft

        except Exception as exc:
            db.rollback()
            draft_failed = db.scalar(select(AITimetableDraft).where(AITimetableDraft.id == draft.id))
            if draft_failed:
                draft_failed.status = "FAILED"
                draft_failed.error_message = str(exc)
                db.commit()
            raise BadRequestException(f"Timetable solver execution failed: {str(exc)}")

    def get_draft(self, db: Session, current_user: IdentityUser, draft_id: uuid.UUID) -> AITimetableDraft:
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        draft = db.scalar(
            select(AITimetableDraft).where(
                AITimetableDraft.id == draft_id,
                AITimetableDraft.school_id == school_id,
                AITimetableDraft.is_deleted.is_(False),
            )
        )
        if not draft:
            raise NotFoundException("AITimetableDraft", str(draft_id))
        return draft

    def list_drafts(
        self,
        db: Session,
        current_user: IdentityUser,
        academic_year_id: uuid.UUID | None = None,
    ) -> list[AITimetableDraft]:
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        stmt = select(AITimetableDraft).where(
            AITimetableDraft.school_id == school_id,
            AITimetableDraft.is_deleted.is_(False),
        )
        if academic_year_id:
            stmt = stmt.where(AITimetableDraft.academic_year_id == academic_year_id)
        stmt = stmt.order_by(AITimetableDraft.created_at.desc())
        return list(db.scalars(stmt).all())

    def approve_draft(self, db: Session, current_user: IdentityUser, draft_id: uuid.UUID) -> AITimetableDraft:
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        draft = self.get_draft(db, current_user, draft_id)

        if draft.status != "SOLVED":
            raise BadRequestException(f"Only drafts in 'SOLVED' status can be approved. Current status: '{draft.status}'.")

        val_report = draft.validation_report or {}
        if not val_report.get("is_valid", False):
            raise BadRequestException("Cannot approve a timetable draft with unresolved hard constraint violations.")

        draft.status = "APPROVED"
        draft.approved_by_id = current_user.id
        draft.approved_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(draft)
        return draft

    def publish_draft(self, db: Session, current_user: IdentityUser, draft_id: uuid.UUID) -> AITimetableDraft:
        school_id = AITenantBoundaryService.validate_and_get_school_id(current_user)
        draft = self.get_draft(db, current_user, draft_id)

        if draft.status != "APPROVED":
            raise BadRequestException(f"Only drafts in 'APPROVED' status can be published. Current status: '{draft.status}'.")

        # Convert draft entries to primary Timetable and TimetableEntry records
        draft_entries = db.scalars(
            select(AITimetableDraftEntry).where(
                AITimetableDraftEntry.draft_id == draft.id,
                AITimetableDraftEntry.is_deleted.is_(False),
            )
        ).all()

        # Group entries by section
        entries_by_section: dict[tuple[uuid.UUID, uuid.UUID], list[AITimetableDraftEntry]] = {}
        for entry in draft_entries:
            key = (entry.school_class_id, entry.section_id)
            entries_by_section.setdefault(key, []).append(entry)

        for (class_id, sec_id), entries in entries_by_section.items():
            # Get or create primary Timetable record
            primary_tt = db.scalar(
                select(Timetable).where(
                    Timetable.school_id == school_id,
                    Timetable.academic_year_id == draft.academic_year_id,
                    Timetable.school_class_id == class_id,
                    Timetable.section_id == sec_id,
                    Timetable.is_deleted.is_(False),
                )
            )
            if not primary_tt:
                primary_tt = Timetable(
                    id=uuid.uuid4(),
                    school_id=school_id,
                    academic_year_id=draft.academic_year_id,
                    school_class_id=class_id,
                    section_id=sec_id,
                    status=TimetableStatus.PUBLISHED,
                )
                db.add(primary_tt)
                db.flush()
            else:
                primary_tt.status = TimetableStatus.PUBLISHED
                # Remove existing entries if replacing
                existing_entries = db.scalars(
                    select(TimetableEntry).where(
                        TimetableEntry.timetable_id == primary_tt.id,
                        TimetableEntry.is_deleted.is_(False),
                    )
                ).all()
                for old in existing_entries:
                    db.delete(old)
                db.flush()

            # Insert new primary entries
            for e in entries:
                day_enum = DayOfWeek(e.day_of_week) if hasattr(DayOfWeek, e.day_of_week) else DayOfWeek.MONDAY
                primary_entry = TimetableEntry(
                    id=uuid.uuid4(),
                    timetable_id=primary_tt.id,
                    period_slot_id=e.period_slot_id,
                    subject_id=e.subject_id,
                    teacher_id=e.teacher_id,
                    classroom_id=e.classroom_id,
                    day_of_week=day_enum,
                )
                db.add(primary_entry)

        draft.status = "PUBLISHED"
        draft.published_by_id = current_user.id
        draft.published_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(draft)
        return draft


ai_timetable_service = AITimetableService()
