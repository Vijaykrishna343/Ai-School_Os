"""
Academic Progression Execution Engine Service.

Executes atomic academic year rollover for students in a school based on
evaluated progression rules, section matching, class-level roll number allocation,
and stale-plan SHA-256 verification.

ATOMIC GUARANTEE:
The student rollover is executed in a single atomic transaction (T_main).
If any mutation fails, the entire transaction rolls back.
Failure recovery audits are persisted via an isolated database session (S_recovery).
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.orm import Session

from app.common.enums import AcademicYearStatus, EnrollmentStatus, PromotionDecision, StudentStatus
from app.common.exceptions import AlreadyExistsException, InternalServerException, NotFoundException, ValidationException
from app.common.logger.logger import get_logger
from app.database.session import SessionLocal
from app.identity.models.user import IdentityUser
from app.models.academic_year import AcademicYear, ClassProgressionRule
from app.models.academic_year.progression_execution import (
    ProgressionExecution,
    ProgressionExecutionItem,
    ProgressionExecutionStatus,
)
from app.models.student import Student, StudentEnrollmentHistory
from app.repositories.academic_year import (
    AcademicYearRepository,
    ClassProgressionRuleRepository,
    ProgressionExecutionRepository,
    academic_year_repository,
    class_progression_rule_repository,
    progression_execution_repository,
)
from app.repositories.school import SchoolRepository, school_repository
from app.repositories.student import (
    StudentEnrollmentHistoryRepository,
    StudentRepository,
    student_enrollment_history_repository,
    student_repository,
)
from app.schemas.student.progression_execution_schema import (
    ProgressionExecutionData,
    ProgressionExecutionRequest,
    ProgressionExecutionResponse,
    ProgressionExecutionSummaryResponse,
)
from app.services.student.progression_planner import ProgressionPlanner, progression_planner

logger = get_logger(__name__)


class ProgressionExecutionService:
    """
    Execution Engine Service for Academic Year Progression Rollover.
    """

    def __init__(
        self,
        planner: ProgressionPlanner = progression_planner,
        execution_repo: ProgressionExecutionRepository = progression_execution_repository,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
        student_repo: StudentRepository = student_repository,
        history_repo: StudentEnrollmentHistoryRepository = student_enrollment_history_repository,
        school_repo: SchoolRepository = school_repository,
    ) -> None:
        self.planner = planner
        self.execution_repository = execution_repo
        self.academic_year_repository = academic_year_repo
        self.student_repository = student_repo
        self.history_repository = history_repo
        self.school_repository = school_repo

    def execute_progression(
        self,
        db: Session,
        source_academic_year_id: UUID,
        request: ProgressionExecutionRequest,
        idempotency_key: str,
        current_user: IdentityUser,
    ) -> ProgressionExecutionResponse:
        """
        Execute academic progression rollover atomically.
        """
        # 1. Tenant Scoping
        school_id = current_user.school_id
        if school_id is None:
            raise ValidationException("Authenticated user is not associated with a school.")

        if not idempotency_key or not idempotency_key.strip():
            raise ValidationException("Idempotency-Key header is required for progression execution.")

        idempotency_key = idempotency_key.strip()

        # 2. Idempotency Check
        existing_execution = self.execution_repository.get_by_school_and_idempotency_key(db, school_id, idempotency_key)
        if existing_execution is not None:
            if existing_execution.status == ProgressionExecutionStatus.COMPLETED:
                logger.info("Returning cached completion response for idempotency key %s", idempotency_key)
                return self._build_execution_response(existing_execution, "Academic progression rollover already executed (cached).")
            elif existing_execution.status in (ProgressionExecutionStatus.PENDING, ProgressionExecutionStatus.RUNNING):
                raise ValidationException("Academic progression rollover is currently in progress for this idempotency key.")
            elif existing_execution.execution_plan_hash != request.execution_plan_hash:
                raise ValidationException("Idempotency key collision with a different execution plan payload.")

        # 3. Source and Target Academic Year Validation
        if source_academic_year_id == request.target_academic_year_id:
            raise ValidationException("Source and target academic years cannot be the same.")

        source_ay = self.academic_year_repository.get_by_id_and_school(db, source_academic_year_id, school_id)
        if source_ay is None or source_ay.is_deleted:
            raise NotFoundException("Source Academic Year", str(source_academic_year_id))

        target_ay = self.academic_year_repository.get_by_id_and_school(db, request.target_academic_year_id, school_id)
        if target_ay is None or target_ay.is_deleted:
            raise NotFoundException("Target Academic Year", str(request.target_academic_year_id))

        # Check if rollover already completed for target AY
        if target_ay.status == AcademicYearStatus.ACTIVE and target_ay.is_current:
            raise ValidationException("Academic year rollover has already been executed for the target academic year.")

        # 4. Check for active execution in progress for school
        active_execution = self.execution_repository.get_active_for_school(db, school_id)
        if active_execution is not None and active_execution.idempotency_key != idempotency_key:
            raise ValidationException("An academic progression rollover is currently in progress for this school.")

        # 5. Live Plan Calculation & SHA-256 Stale-Plan Verification
        live_plan = self.planner.calculate_plan(
            db=db,
            source_academic_year_id=source_academic_year_id,
            target_academic_year_id=request.target_academic_year_id,
            current_school_id=school_id,
        )

        if live_plan.execution_plan_hash != request.execution_plan_hash:
            logger.warning(
                "Stale plan hash mismatch for school %s. Expected %s, computed live %s",
                school_id,
                request.execution_plan_hash,
                live_plan.execution_plan_hash,
            )
            raise ValidationException(
                "Execution plan is stale. The underlying student, rule, or target occupancy state has changed post-preview. Please refresh preview and re-submit."
            )

        # 6. Begin Atomic Execution Run (T_main)
        now_utc = datetime.now(timezone.utc)
        execution_record = ProgressionExecution(
            school_id=school_id,
            source_academic_year_id=source_academic_year_id,
            target_academic_year_id=request.target_academic_year_id,
            execution_plan_hash=live_plan.execution_plan_hash,
            idempotency_key=idempotency_key,
            status=ProgressionExecutionStatus.RUNNING,
            total_students=live_plan.summary.total_students_evaluated,
            promoted_count=live_plan.summary.promoted_count,
            graduated_count=live_plan.summary.graduated_count,
            retained_count=live_plan.summary.retained_count,
            blocked_count=live_plan.summary.blocked_count,
            excluded_count=live_plan.summary.excluded_count,
            initiated_by_user_id=current_user.id if current_user else None,
            started_at=now_utc,
        )
        self.execution_repository.create(db, execution_record)

        try:
            # Lock active source student records deterministically by ID to prevent deadlocks
            lock_stmt = (
                select(Student)
                .where(
                    Student.school_id == school_id,
                    Student.academic_year_id == source_academic_year_id,
                    Student.is_deleted.is_(False),
                )
                .order_by(Student.id.asc())
                .with_for_update()
            )
            locked_students = list(db.scalars(lock_stmt))
            students_by_id = {s.id: s for s in locked_students}

            effective_date = target_ay.start_date if target_ay.start_date else date.today()

            # Process evaluated items
            for item in live_plan.evaluated_items:
                student = students_by_id.get(item.student_id)
                if student is None:
                    # Create skipped audit item if student disappeared
                    exec_item = ProgressionExecutionItem(
                        execution_id=execution_record.id,
                        student_id=item.student_id,
                        source_class_id=item.current_class_id,
                        source_section_id=item.current_section_id,
                        source_roll_number=item.current_roll_number,
                        target_class_id=item.target_class_id,
                        target_section_id=item.target_section_id,
                        allocated_roll_number=item.proposed_roll_number,
                        decision=item.decision.value if hasattr(item.decision, "value") else str(item.decision),
                        status="SKIPPED",
                        error_message="Student record no longer exists or was deleted",
                    )
                    db.add(exec_item)
                    continue

                if item.decision == PromotionDecision.PROMOTED:
                    # Update source history
                    source_history = self.history_repository.get_by_student_and_year(
                        db, school_id, student.id, source_academic_year_id
                    )
                    if source_history is not None:
                        source_history.promotion_decision = PromotionDecision.PROMOTED
                        source_history.enrollment_status = EnrollmentStatus.PROMOTED
                        source_history.end_date = effective_date
                        self.history_repository.update(db, source_history)
                    else:
                        source_history = StudentEnrollmentHistory(
                            school_id=school_id,
                            student_id=student.id,
                            academic_year_id=source_academic_year_id,
                            school_class_id=student.school_class_id,
                            section_id=student.section_id,
                            roll_number=student.roll_number,
                            enrollment_status=EnrollmentStatus.PROMOTED,
                            promotion_decision=PromotionDecision.PROMOTED,
                            start_date=student.admission_date,
                            end_date=effective_date,
                        )
                        self.history_repository.create(db, source_history)

                    # Create target history
                    target_history = StudentEnrollmentHistory(
                        school_id=school_id,
                        student_id=student.id,
                        academic_year_id=request.target_academic_year_id,
                        school_class_id=item.target_class_id,
                        section_id=item.target_section_id,
                        roll_number=item.proposed_roll_number,
                        enrollment_status=EnrollmentStatus.ENROLLED,
                        start_date=effective_date,
                    )
                    self.history_repository.create(db, target_history)

                    # Update student placement
                    student.academic_year_id = request.target_academic_year_id
                    student.school_class_id = item.target_class_id
                    student.section_id = item.target_section_id
                    student.roll_number = item.proposed_roll_number
                    student.status = StudentStatus.ACTIVE
                    self.student_repository.update(db, student)

                    exec_item = ProgressionExecutionItem(
                        execution_id=execution_record.id,
                        student_id=student.id,
                        source_class_id=item.current_class_id,
                        source_section_id=item.current_section_id,
                        source_roll_number=item.current_roll_number,
                        target_class_id=item.target_class_id,
                        target_section_id=item.target_section_id,
                        allocated_roll_number=item.proposed_roll_number,
                        decision=PromotionDecision.PROMOTED.value,
                        status="SUCCESS",
                        error_message=None,
                    )
                    db.add(exec_item)

                elif item.decision == PromotionDecision.GRADUATED:
                    source_history = self.history_repository.get_by_student_and_year(
                        db, school_id, student.id, source_academic_year_id
                    )
                    if source_history is not None:
                        source_history.promotion_decision = PromotionDecision.GRADUATED
                        source_history.enrollment_status = EnrollmentStatus.GRADUATED
                        source_history.end_date = effective_date
                        self.history_repository.update(db, source_history)
                    else:
                        source_history = StudentEnrollmentHistory(
                            school_id=school_id,
                            student_id=student.id,
                            academic_year_id=source_academic_year_id,
                            school_class_id=student.school_class_id,
                            section_id=student.section_id,
                            roll_number=student.roll_number,
                            enrollment_status=EnrollmentStatus.GRADUATED,
                            promotion_decision=PromotionDecision.GRADUATED,
                            start_date=student.admission_date,
                            end_date=effective_date,
                        )
                        self.history_repository.create(db, source_history)

                    student.status = StudentStatus.GRADUATED
                    self.student_repository.update(db, student)

                    exec_item = ProgressionExecutionItem(
                        execution_id=execution_record.id,
                        student_id=student.id,
                        source_class_id=item.current_class_id,
                        source_section_id=item.current_section_id,
                        source_roll_number=item.current_roll_number,
                        target_class_id=None,
                        target_section_id=None,
                        allocated_roll_number=None,
                        decision=PromotionDecision.GRADUATED.value,
                        status="SUCCESS",
                        error_message=None,
                    )
                    db.add(exec_item)

                else:
                    exec_item = ProgressionExecutionItem(
                        execution_id=execution_record.id,
                        student_id=student.id,
                        source_class_id=item.current_class_id,
                        source_section_id=item.current_section_id,
                        source_roll_number=item.current_roll_number,
                        target_class_id=item.target_class_id,
                        target_section_id=item.target_section_id,
                        allocated_roll_number=item.proposed_roll_number,
                        decision=item.decision.value if hasattr(item.decision, "value") else str(item.decision),
                        status="SKIPPED",
                        error_message=item.reason,
                    )
                    db.add(exec_item)

            # Atomic Academic Year Transition
            # Deactivate current flag on all academic years for this school
            db.execute(
                update(AcademicYear)
                .where(AcademicYear.school_id == school_id)
                .values(is_current=False)
            )

            source_ay.is_current = False
            source_ay.status = AcademicYearStatus.ARCHIVED
            self.academic_year_repository.update(db, source_ay)

            target_ay.is_current = True
            target_ay.status = AcademicYearStatus.ACTIVE
            self.academic_year_repository.update(db, target_ay)

            # Finalize Execution Record
            execution_record.status = ProgressionExecutionStatus.COMPLETED
            execution_record.completed_at = datetime.now(timezone.utc)
            self.execution_repository.update(db, execution_record)

            db.commit()
            logger.info("Academic progression rollover completed successfully for school %s", school_id)
            return self._build_execution_response(execution_record, "Academic progression rollover executed successfully.")

        except Exception as exc:
            db.rollback()
            logger.error("Rollover execution failed for school %s: %s", school_id, str(exc), exc_info=True)
            self._record_failed_execution(school_id, execution_record.id, str(exc))
            raise InternalServerException(f"Academic progression rollover failed: {str(exc)}") from exc

    def _record_failed_execution(
        self,
        school_id: UUID,
        execution_id: UUID,
        error_message: str,
    ) -> None:
        """
        Record FAILED status in an isolated recovery session (S_recovery).
        Ensures audit trail persists even when main transaction rolls back.
        """
        recovery_db = SessionLocal()
        try:
            record = recovery_db.scalar(
                select(ProgressionExecution).where(
                    ProgressionExecution.id == execution_id,
                    ProgressionExecution.school_id == school_id,
                )
            )
            if record is not None:
                record.status = ProgressionExecutionStatus.FAILED
                record.completed_at = datetime.now(timezone.utc)
                record.error_summary = error_message
                recovery_db.commit()
        except Exception as r_exc:
            recovery_db.rollback()
            logger.error("Failed to persist failure audit record in S_recovery: %s", str(r_exc), exc_info=True)
        finally:
            recovery_db.close()

    def _build_execution_response(
        self,
        execution: ProgressionExecution,
        message: str,
    ) -> ProgressionExecutionResponse:
        summary = ProgressionExecutionSummaryResponse(
            total_students_evaluated=execution.total_students,
            promoted_count=execution.promoted_count,
            graduated_count=execution.graduated_count,
            retained_count=execution.retained_count,
            blocked_count=execution.blocked_count,
            excluded_count=execution.excluded_count,
        )
        data = ProgressionExecutionData(
            execution_id=execution.id,
            status=execution.status.value if hasattr(execution.status, "value") else str(execution.status),
            source_academic_year_id=execution.source_academic_year_id,
            target_academic_year_id=execution.target_academic_year_id,
            summary=summary,
            started_at=execution.started_at,
            completed_at=execution.completed_at,
            error_summary=execution.error_summary,
        )
        return ProgressionExecutionResponse(
            success=True,
            message=message,
            data=data,
        )


progression_execution_service = ProgressionExecutionService()
