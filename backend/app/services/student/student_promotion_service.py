from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.enums import (
    EnrollmentStatus,
    PromotionDecision,
    StudentStatus,
    TransferCertificateStatus,
)
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.student.student_enrollment_history import StudentEnrollmentHistory
from app.models.student.transfer_certificate import TransferCertificate
from app.repositories.academic_year import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.section import (
    SectionRepository,
    section_repository,
)
from app.repositories.student import (
    StudentEnrollmentHistoryRepository,
    StudentRepository,
    TransferCertificateRepository,
    student_enrollment_history_repository,
    student_repository,
    transfer_certificate_repository,
)
from app.schemas.student.promotion_schema import (
    AcademicYearTransitionRequest,
    AcademicYearTransitionResponse,
    BulkPromotionResultResponse,
    BulkStudentPromotionRequest,
    BulkStudentRetentionRequest,
    StudentPromotionRequest,
    StudentRetentionRequest,
    TransferCertificateCreate,
)

from app.services.base_service import BaseService
from app.utils.roll_number import RollNumberGenerator

logger = get_logger(__name__)


class StudentPromotionService(BaseService[StudentEnrollmentHistoryRepository]):
    """
    Business logic for Student Promotion, Retention, Academic Year Transition,
    and Transfer Certificate (TC) operations.
    """

    def __init__(
        self,
        repository: StudentEnrollmentHistoryRepository = student_enrollment_history_repository,
        student_repo: StudentRepository = student_repository,
        tc_repo: TransferCertificateRepository = transfer_certificate_repository,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
        school_class_repo: SchoolClassRepository = school_class_repository,
        section_repo: SectionRepository = section_repository,
        school_repo: SchoolRepository = school_repository,
    ) -> None:
        super().__init__(repository)
        self.student_repository = student_repo
        self.tc_repository = tc_repo
        self.academic_year_repository = academic_year_repo
        self.school_class_repository = school_class_repo
        self.section_repository = section_repo
        self.school_repository = school_repo

    # ------------------------------------------------------------------
    # Validation Helpers
    # ------------------------------------------------------------------

    def _require_school_id(self, current_school_id: UUID | None) -> UUID:
        if current_school_id is None:
            raise ValidationException(
                "Authenticated user is not associated with a school."
            )
        return current_school_id

    def _get_valid_student(
        self,
        db: Session,
        student_id: UUID,
        school_id: UUID,
    ):
        student = self.student_repository.get(db, student_id)
        if student is None or student.is_deleted:
            raise NotFoundException("Student", str(student_id))
        if student.school_id != school_id:
            raise ValidationException("Student must belong to the user's school.")
        return student

    def _get_valid_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
        school_id: UUID,
    ):
        ay = self.academic_year_repository.get(db, academic_year_id)
        if ay is None or ay.is_deleted:
            raise NotFoundException("Academic Year", str(academic_year_id))
        if ay.school_id != school_id:
            raise ValidationException("Academic Year must belong to the user's school.")
        return ay

    def _get_valid_class(
        self,
        db: Session,
        class_id: UUID,
        school_id: UUID,
    ):
        sc = self.school_class_repository.get(db, class_id)
        if sc is None or sc.is_deleted:
            raise NotFoundException("School Class", str(class_id))
        if sc.school_id != school_id:
            raise ValidationException("School class must belong to the user's school.")
        return sc

    def _get_valid_section(
        self,
        db: Session,
        section_id: UUID,
        class_id: UUID,
        school_id: UUID,
    ):
        sec = self.section_repository.get(db, section_id)
        if sec is None or sec.is_deleted:
            raise NotFoundException("Section", str(section_id))
        if sec.school_class_id != class_id:
            raise ValidationException("Target section does not belong to target class.")
        return sec

    # ------------------------------------------------------------------
    # Query Methods
    # ------------------------------------------------------------------

    def get_student_enrollments(
        self,
        db: Session,
        student_id: UUID,
        current_school_id: UUID | None = None,
    ) -> list[StudentEnrollmentHistory]:
        """
        Retrieve complete historical enrollment records for a student.
        Enforces tenant isolation.
        """
        school_id = self._require_school_id(current_school_id)
        self._get_valid_student(db, student_id, school_id)

        return self.repository.get_by_student(db, school_id, student_id)

    # ------------------------------------------------------------------
    # Promotion & Retention Methods
    # ------------------------------------------------------------------

    def promote_student(
        self,
        db: Session,
        student_id: UUID,
        data: StudentPromotionRequest,
        current_school_id: UUID | None = None,
    ) -> StudentEnrollmentHistory:
        """
        Promote a single student to a new academic year, class, and section.
        Preserves previous year enrollment history and creates target enrollment.
        Includes retry logic for sequence roll number concurrency conflicts.
        """
        school_id = self._require_school_id(current_school_id)
        student = self._get_valid_student(db, student_id, school_id)

        if student.status != StudentStatus.ACTIVE:
            raise ValidationException(
                f"Cannot promote student '{student.full_name}' with status '{student.status.value}'."
            )

        if student.academic_year_id == data.target_academic_year_id:
            raise ValidationException(
                "Student is already enrolled in the target academic year."
            )

        # Validate entities
        self._get_valid_academic_year(db, data.target_academic_year_id, school_id)
        target_class = self._get_valid_class(db, data.target_class_id, school_id)
        self._get_valid_section(db, data.target_section_id, target_class.id, school_id)

        # Idempotency check: verify student isn't already enrolled in target year
        existing_target_history = self.repository.get_by_student_and_year(
            db, school_id, student_id, data.target_academic_year_id
        )
        if existing_target_history is not None:
            raise ValidationException(
                f"Student '{student.full_name}' is already finalized/enrolled for target academic year."
            )

        try:
            # 1. Preserve / update source academic year enrollment history
            source_history = self.repository.get_by_student_and_year(
                db, school_id, student_id, student.academic_year_id
            )
            if source_history is None:
                source_history = StudentEnrollmentHistory(
                    school_id=school_id,
                    student_id=student.id,
                    academic_year_id=student.academic_year_id,
                    school_class_id=student.school_class_id,
                    section_id=student.section_id,
                    roll_number=student.roll_number,
                    enrollment_status=EnrollmentStatus.PROMOTED,
                    promotion_decision=PromotionDecision.PROMOTED,
                    remarks=f"Promoted to {target_class.name}",
                )
                self.repository.create(db, source_history)
            else:
                source_history.promotion_decision = PromotionDecision.PROMOTED
                source_history.enrollment_status = EnrollmentStatus.PROMOTED
                self.repository.update(db, source_history)

            # 2. Determine roll number in target class/section with retries for concurrency
            max_retries = 5
            for attempt in range(max_retries):
                try:
                    if data.roll_number:
                        if self.student_repository.exists_by_roll_number(
                            db,
                            data.target_academic_year_id,
                            data.target_class_id,
                            data.target_section_id,
                            data.roll_number,
                        ):
                            raise AlreadyExistsException("Roll Number", data.roll_number)
                        new_roll_number = data.roll_number
                    else:
                        last_student = self.student_repository.get_last_roll_number(
                            db,
                            data.target_academic_year_id,
                            data.target_class_id,
                            data.target_section_id,
                        )
                        new_roll_number = RollNumberGenerator.generate(last_student)

                    # 3. Create target academic year enrollment history
                    target_history = StudentEnrollmentHistory(
                        school_id=school_id,
                        student_id=student.id,
                        academic_year_id=data.target_academic_year_id,
                        school_class_id=data.target_class_id,
                        section_id=data.target_section_id,
                        roll_number=new_roll_number,
                        enrollment_status=EnrollmentStatus.ENROLLED,
                        promotion_decision=PromotionDecision.PENDING,
                        remarks=data.remarks,
                    )
                    created_history = self.repository.create(db, target_history)

                    # 4. Update current placement on Student model
                    student.academic_year_id = data.target_academic_year_id
                    student.school_class_id = data.target_class_id
                    student.section_id = data.target_section_id
                    student.roll_number = new_roll_number
                    student.status = StudentStatus.ACTIVE
                    self.student_repository.update(db, student)

                    return created_history
                except (AlreadyExistsException, IntegrityError) as exc:
                    db.rollback()
                    if data.roll_number or attempt == max_retries - 1:
                        raise ValidationException(
                            f"Failed to assign unique roll number for student: {exc}"
                        ) from exc

            raise ValidationException("Failed to allocate roll number after max retries.")

        except Exception:
            db.rollback()
            raise

    def retain_student(
        self,
        db: Session,
        student_id: UUID,
        data: StudentRetentionRequest,
        current_school_id: UUID | None = None,
    ) -> StudentEnrollmentHistory:
        """
        Retain a student in the current class (or specified class) for a new academic year.
        """
        school_id = self._require_school_id(current_school_id)
        student = self._get_valid_student(db, student_id, school_id)

        if student.status != StudentStatus.ACTIVE:
            raise ValidationException(
                f"Cannot retain student '{student.full_name}' with status '{student.status.value}'."
            )

        if student.academic_year_id == data.target_academic_year_id:
            raise ValidationException(
                "Student is already enrolled in the target academic year."
            )

        self._get_valid_academic_year(db, data.target_academic_year_id, school_id)

        target_class_id = data.target_class_id or student.school_class_id
        target_section_id = data.target_section_id or student.section_id

        target_class = self._get_valid_class(db, target_class_id, school_id)
        self._get_valid_section(db, target_section_id, target_class.id, school_id)

        existing_target_history = self.repository.get_by_student_and_year(
            db, school_id, student_id, data.target_academic_year_id
        )
        if existing_target_history is not None:
            raise ValidationException(
                f"Student '{student.full_name}' is already finalized/enrolled for target academic year."
            )

        try:
            # Preserve source enrollment
            source_history = self.repository.get_by_student_and_year(
                db, school_id, student_id, student.academic_year_id
            )
            if source_history is None:
                source_history = StudentEnrollmentHistory(
                    school_id=school_id,
                    student_id=student.id,
                    academic_year_id=student.academic_year_id,
                    school_class_id=student.school_class_id,
                    section_id=student.section_id,
                    roll_number=student.roll_number,
                    enrollment_status=EnrollmentStatus.RETAINED,
                    promotion_decision=PromotionDecision.RETAINED,
                    remarks=f"Retained in {target_class.name}",
                )
                self.repository.create(db, source_history)
            else:
                source_history.promotion_decision = PromotionDecision.RETAINED
                source_history.enrollment_status = EnrollmentStatus.RETAINED
                self.repository.update(db, source_history)

            max_retries = 5
            for attempt in range(max_retries):
                try:
                    if data.roll_number:
                        if self.student_repository.exists_by_roll_number(
                            db,
                            data.target_academic_year_id,
                            target_class_id,
                            target_section_id,
                            data.roll_number,
                        ):
                            raise AlreadyExistsException("Roll Number", data.roll_number)
                        new_roll_number = data.roll_number
                    else:
                        last_student = self.student_repository.get_last_roll_number(
                            db,
                            data.target_academic_year_id,
                            target_class_id,
                            target_section_id,
                        )
                        new_roll_number = RollNumberGenerator.generate(last_student)

                    target_history = StudentEnrollmentHistory(
                        school_id=school_id,
                        student_id=student.id,
                        academic_year_id=data.target_academic_year_id,
                        school_class_id=target_class_id,
                        section_id=target_section_id,
                        roll_number=new_roll_number,
                        enrollment_status=EnrollmentStatus.RETAINED,
                        promotion_decision=PromotionDecision.PENDING,
                        remarks=data.remarks,
                    )
                    created_history = self.repository.create(db, target_history)

                    student.academic_year_id = data.target_academic_year_id
                    student.school_class_id = target_class_id
                    student.section_id = target_section_id
                    student.roll_number = new_roll_number
                    student.status = StudentStatus.ACTIVE
                    self.student_repository.update(db, student)

                    return created_history
                except (AlreadyExistsException, IntegrityError) as exc:
                    db.rollback()
                    if data.roll_number or attempt == max_retries - 1:
                        raise ValidationException(
                            f"Failed to assign unique roll number for student: {exc}"
                        ) from exc

            raise ValidationException("Failed to allocate roll number after max retries.")

        except Exception:
            db.rollback()
            raise

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    def bulk_promote_students(
        self,
        db: Session,
        data: BulkStudentPromotionRequest,
        current_school_id: UUID | None = None,
    ) -> BulkPromotionResultResponse:
        """
        Bulk promote multiple students in a transactional operation.
        Provides partial success (skips invalid students and records errors).
        """
        school_id = self._require_school_id(current_school_id)
        self._get_valid_academic_year(db, data.source_academic_year_id, school_id)
        self._get_valid_academic_year(db, data.target_academic_year_id, school_id)

        promoted_count = 0
        skipped_count = 0
        errors: list[dict[str, str]] = []

        for item in data.promotions:
            try:
                req = StudentPromotionRequest(
                    target_academic_year_id=data.target_academic_year_id,
                    target_class_id=item.target_class_id,
                    target_section_id=item.target_section_id,
                    roll_number=item.roll_number,
                    remarks=item.remarks,
                )
                self.promote_student(db, item.student_id, req, school_id)
                promoted_count += 1
            except (ValidationException, NotFoundException, AlreadyExistsException, IntegrityError) as exc:
                db.rollback()
                logger.warning(
                    "Bulk promotion skipped student %s: %s", item.student_id, str(exc)
                )
                skipped_count += 1
                errors.append({"student_id": str(item.student_id), "reason": str(exc)})
            except Exception as exc:
                db.rollback()
                logger.error(
                    "Unexpected error in bulk promotion for student %s: %s", item.student_id, str(exc)
                )
                skipped_count += 1
                errors.append({"student_id": str(item.student_id), "reason": "Unexpected server error."})

        return BulkPromotionResultResponse(
            total_processed=len(data.promotions),
            promoted_count=promoted_count,
            retained_count=0,
            skipped_count=skipped_count,
            errors=errors,
        )

    def bulk_retain_students(
        self,
        db: Session,
        data: BulkStudentRetentionRequest,
        current_school_id: UUID | None = None,
    ) -> BulkPromotionResultResponse:
        """
        Bulk retain multiple students in a transactional operation.
        Provides partial success (skips invalid students and records errors).
        """
        school_id = self._require_school_id(current_school_id)
        self._get_valid_academic_year(db, data.source_academic_year_id, school_id)
        self._get_valid_academic_year(db, data.target_academic_year_id, school_id)

        retained_count = 0
        skipped_count = 0
        errors: list[dict[str, str]] = []

        for item in data.retentions:
            try:
                req = StudentRetentionRequest(
                    target_academic_year_id=data.target_academic_year_id,
                    target_class_id=item.target_class_id,
                    target_section_id=item.target_section_id,
                    roll_number=item.roll_number,
                    remarks=item.remarks,
                )
                self.retain_student(db, item.student_id, req, school_id)
                retained_count += 1
            except (ValidationException, NotFoundException, AlreadyExistsException, IntegrityError) as exc:
                db.rollback()
                logger.warning(
                    "Bulk retention skipped student %s: %s", item.student_id, str(exc)
                )
                skipped_count += 1
                errors.append({"student_id": str(item.student_id), "reason": str(exc)})
            except Exception as exc:
                db.rollback()
                logger.error(
                    "Unexpected error in bulk retention for student %s: %s", item.student_id, str(exc)
                )
                skipped_count += 1
                errors.append({"student_id": str(item.student_id), "reason": "Unexpected server error."})

        return BulkPromotionResultResponse(
            total_processed=len(data.retentions),
            promoted_count=0,
            retained_count=retained_count,
            skipped_count=skipped_count,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Academic Year Transition
    # ------------------------------------------------------------------

    def transition_academic_year(
        self,
        db: Session,
        source_academic_year_id: UUID,
        data: AcademicYearTransitionRequest,
        current_school_id: UUID | None = None,
    ) -> AcademicYearTransitionResponse:
        """
        Execute controlled academic year transition.
        Ensures history for source year is preserved for ALL active students (unpaginated),
        and resets all current academic year flags for the school before activating target year.
        """
        school_id = self._require_school_id(current_school_id)
        source_ay = self._get_valid_academic_year(db, source_academic_year_id, school_id)
        target_ay = self._get_valid_academic_year(db, data.target_academic_year_id, school_id)

        if source_academic_year_id == data.target_academic_year_id:
            raise ValidationException(
                "Source and target academic years cannot be the same."
            )

        try:
            # 1. Fetch ALL active students in source academic year without pagination cap
            students = self.student_repository.get_all_active_by_school_and_year(
                db,
                school_id=school_id,
                academic_year_id=source_academic_year_id,
            )

            preserved_count = 0
            for student in students:
                existing_hist = self.repository.get_by_student_and_year(
                    db, school_id, student.id, source_academic_year_id
                )
                if existing_hist is None:
                    new_hist = StudentEnrollmentHistory(
                        school_id=school_id,
                        student_id=student.id,
                        academic_year_id=student.academic_year_id,
                        school_class_id=student.school_class_id,
                        section_id=student.section_id,
                        roll_number=student.roll_number,
                        enrollment_status=EnrollmentStatus.ENROLLED,
                        promotion_decision=PromotionDecision.PENDING,
                        remarks=f"Preserved during year transition to {target_ay.name}",
                    )
                    self.repository.create(db, new_hist)
                    preserved_count += 1

            # 2. Reset all active current flags for the school to preserve invariant: exactly one current year
            current_years = self.academic_year_repository.get_all_current_by_school(db, school_id)
            for curr_ay in current_years:
                curr_ay.is_current = False
                self.academic_year_repository.update(db, curr_ay)

            # 3. Activate target academic year
            target_ay.is_current = True
            self.academic_year_repository.update(db, target_ay)

            return AcademicYearTransitionResponse(
                source_academic_year_id=source_academic_year_id,
                target_academic_year_id=data.target_academic_year_id,
                total_students_preserved=preserved_count,
                message=f"Academic year successfully transitioned from '{source_ay.name}' to '{target_ay.name}'.",
            )
        except Exception:
            db.rollback()
            raise

    # ------------------------------------------------------------------
    # Transfer Certificate (TC) Methods
    # ------------------------------------------------------------------

    def issue_transfer_certificate(
        self,
        db: Session,
        student_id: UUID,
        data: TransferCertificateCreate,
        current_school_id: UUID | None = None,
    ) -> TransferCertificate:
        """
        Issue a Transfer Certificate (TC) for a student.
        Updates student status to TRANSFERRED and preserves enrollment history.
        Includes retries for auto-generated TC number sequence concurrency.
        """
        school_id = self._require_school_id(current_school_id)
        student = self._get_valid_student(db, student_id, school_id)
        self._get_valid_academic_year(db, data.academic_year_id, school_id)

        # Check for active issued TC
        active_tc = self.tc_repository.get_active_by_student(db, school_id, student_id)
        if active_tc is not None:
            raise ValidationException(
                f"Student '{student.full_name}' already has an active Transfer Certificate ({active_tc.tc_number})."
            )

        max_retries = 5
        for attempt in range(max_retries):
            try:
                if data.tc_number:
                    existing = self.tc_repository.get_by_tc_number(db, school_id, data.tc_number)
                    if existing is not None:
                        raise AlreadyExistsException("Transfer Certificate", data.tc_number)
                    tc_num = data.tc_number
                else:
                    last_tc = self.tc_repository.get_last_tc_number(db, school_id)
                    year_prefix = date.today().year
                    seq = 1
                    if last_tc and last_tc.tc_number.startswith(f"TC-{year_prefix}-"):
                        try:
                            seq = int(last_tc.tc_number.split("-")[-1]) + 1
                        except ValueError:
                            seq = 1
                    tc_num = f"TC-{year_prefix}-{(seq + attempt):04d}"

                tc = TransferCertificate(
                    school_id=school_id,
                    student_id=student_id,
                    academic_year_id=data.academic_year_id,
                    tc_number=tc_num,
                    issue_date=data.issue_date,
                    leaving_date=data.leaving_date,
                    reason=data.reason,
                    destination_school=data.destination_school,
                    remarks=data.remarks,
                    status=TransferCertificateStatus.ISSUED,
                )
                created_tc = self.tc_repository.create(db, tc)

                # Preserve history & update enrollment status
                history = self.repository.get_by_student_and_year(
                    db, school_id, student_id, student.academic_year_id
                )
                if history is None:
                    history = StudentEnrollmentHistory(
                        school_id=school_id,
                        student_id=student.id,
                        academic_year_id=student.academic_year_id,
                        school_class_id=student.school_class_id,
                        section_id=student.section_id,
                        roll_number=student.roll_number,
                        enrollment_status=EnrollmentStatus.TRANSFERRED,
                        promotion_decision=PromotionDecision.TRANSFERRED,
                        remarks=f"TC Issued: {tc_num}",
                    )
                    self.repository.create(db, history)
                else:
                    history.enrollment_status = EnrollmentStatus.TRANSFERRED
                    history.promotion_decision = PromotionDecision.TRANSFERRED
                    self.repository.update(db, history)

                # Update student status to TRANSFERRED
                student.status = StudentStatus.TRANSFERRED
                self.student_repository.update(db, student)

                return created_tc

            except (AlreadyExistsException, IntegrityError) as exc:
                db.rollback()
                if data.tc_number or attempt == max_retries - 1:
                    raise ValidationException(
                        f"Failed to generate unique Transfer Certificate number: {exc}"
                    ) from exc
            except Exception:
                db.rollback()
                raise

        raise ValidationException("Failed to issue Transfer Certificate after max retries.")

    def get_student_transfer_certificates(
        self,
        db: Session,
        student_id: UUID,
        current_school_id: UUID | None = None,
    ) -> list[TransferCertificate]:
        """
        Get all TCs issued for a student. Enforces tenant boundary.
        """
        school_id = self._require_school_id(current_school_id)
        self._get_valid_student(db, student_id, school_id)

        return self.tc_repository.get_by_student(db, school_id, student_id)


student_promotion_service = StudentPromotionService()
