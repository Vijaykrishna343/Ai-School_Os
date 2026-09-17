from __future__ import annotations

from datetime import date, datetime, timezone
import uuid
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.common.enums.admissions import (
    AdmissionApplicationStatus,
    AdmissionCycleStatus,
    AdmissionDecisionType,
    ApplicantStatus,
)
from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
    ValidationException,
)
from app.identity.models.user import IdentityUser
from app.models.academic_year.academic_year import AcademicYear
from app.models.admissions import (
    AdmissionApplication,
    AdmissionCycle,
    AdmissionDecision,
    Applicant,
    ApplicationStatusHistory,
)
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.schemas.admissions import (
    AdmissionApplicationCreate,
    AdmissionApplicationUpdate,
    AdmissionCycleCreate,
    AdmissionCycleUpdate,
    AdmissionDecisionCreate,
    ApplicantCreate,
    ApplicantUpdate,
    ApplicationReviewRequest,
    ApplicationSubmitRequest,
    ApplicationWithdrawRequest,
)


class AdmissionsService:
    """
    Comprehensive service handling business logic, validation, lifecycle state transitions,
    and multi-tenant data management for the School ERP Admissions Pipeline.
    """

    # =========================================================================
    # 1. ADMISSION CYCLES
    # =========================================================================

    def create_cycle(
        self,
        db: Session,
        school_id: UUID,
        payload: AdmissionCycleCreate,
    ) -> AdmissionCycle:
        if payload.end_date < payload.start_date:
            raise BadRequestException("Cycle end_date must be on or after start_date")

        # Verify academic year belongs to this school
        ay = db.scalars(
            select(AcademicYear).where(
                AcademicYear.id == payload.academic_year_id,
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
        ).first()
        if not ay:
            raise NotFoundException("Academic Year", str(payload.academic_year_id))

        # Check unique code per school
        existing = db.scalars(
            select(AdmissionCycle).where(
                AdmissionCycle.school_id == school_id,
                AdmissionCycle.code == payload.code,
                AdmissionCycle.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Admission Cycle with code", payload.code)

        cycle = AdmissionCycle(
            school_id=school_id,
            academic_year_id=payload.academic_year_id,
            name=payload.name,
            code=payload.code,
            start_date=payload.start_date,
            end_date=payload.end_date,
            status=payload.status,
            description=payload.description,
            is_active=payload.is_active,
        )
        db.add(cycle)
        db.commit()
        db.refresh(cycle)
        return cycle

    def get_cycle(
        self,
        db: Session,
        school_id: UUID,
        cycle_id: UUID,
    ) -> AdmissionCycle:
        cycle = db.scalars(
            select(AdmissionCycle).where(
                AdmissionCycle.id == cycle_id,
                AdmissionCycle.school_id == school_id,
                AdmissionCycle.is_deleted.is_(False),
            )
        ).first()
        if not cycle:
            raise NotFoundException("Admission Cycle", str(cycle_id))
        return cycle

    def list_cycles(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID | None = None,
        status: AdmissionCycleStatus | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AdmissionCycle], int, int]:
        query = select(AdmissionCycle).where(
            AdmissionCycle.school_id == school_id,
            AdmissionCycle.is_deleted.is_(False),
        )

        if academic_year_id:
            query = query.where(AdmissionCycle.academic_year_id == academic_year_id)
        if status:
            query = query.where(AdmissionCycle.status == status)
        if is_active is not None:
            query = query.where(AdmissionCycle.is_active.is_(is_active))
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    AdmissionCycle.name.ilike(term),
                    AdmissionCycle.code.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(AdmissionCycle.start_date.desc(), AdmissionCycle.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_cycle(
        self,
        db: Session,
        school_id: UUID,
        cycle_id: UUID,
        payload: AdmissionCycleUpdate,
    ) -> AdmissionCycle:
        cycle = self.get_cycle(db, school_id, cycle_id)

        start_date = payload.start_date if payload.start_date is not None else cycle.start_date
        end_date = payload.end_date if payload.end_date is not None else cycle.end_date
        if end_date < start_date:
            raise BadRequestException("Cycle end_date must be on or after start_date")

        if payload.code and payload.code != cycle.code:
            existing = db.scalars(
                select(AdmissionCycle).where(
                    AdmissionCycle.school_id == school_id,
                    AdmissionCycle.code == payload.code,
                    AdmissionCycle.id != cycle_id,
                    AdmissionCycle.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Admission Cycle with code", payload.code)
            cycle.code = payload.code

        if payload.name is not None:
            cycle.name = payload.name
        if payload.start_date is not None:
            cycle.start_date = payload.start_date
        if payload.end_date is not None:
            cycle.end_date = payload.end_date
        if payload.description is not None:
            cycle.description = payload.description
        if payload.status is not None:
            cycle.status = payload.status
        if payload.is_active is not None:
            cycle.is_active = payload.is_active

        db.commit()
        db.refresh(cycle)
        return cycle

    def delete_cycle(
        self,
        db: Session,
        school_id: UUID,
        cycle_id: UUID,
    ) -> None:
        cycle = self.get_cycle(db, school_id, cycle_id)
        cycle.is_deleted = True
        cycle.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 2. APPLICANTS / PROSPECTS
    # =========================================================================

    def create_applicant(
        self,
        db: Session,
        school_id: UUID,
        payload: ApplicantCreate,
    ) -> Applicant:
        if payload.admission_cycle_id:
            cycle = db.scalars(
                select(AdmissionCycle).where(
                    AdmissionCycle.id == payload.admission_cycle_id,
                    AdmissionCycle.school_id == school_id,
                    AdmissionCycle.is_deleted.is_(False),
                )
            ).first()
            if not cycle:
                raise NotFoundException("Admission Cycle", str(payload.admission_cycle_id))

        # Handle applicant number
        applicant_number = payload.applicant_number
        if not applicant_number:
            applicant_number = f"APP-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"
        else:
            existing = db.scalars(
                select(Applicant).where(
                    Applicant.school_id == school_id,
                    Applicant.applicant_number == applicant_number,
                    Applicant.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Applicant with number", applicant_number)

        applicant = Applicant(
            school_id=school_id,
            admission_cycle_id=payload.admission_cycle_id,
            applicant_number=applicant_number,
            first_name=payload.first_name,
            middle_name=payload.middle_name,
            last_name=payload.last_name,
            date_of_birth=payload.date_of_birth,
            gender=payload.gender,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            parent_name=payload.parent_name,
            parent_phone=payload.parent_phone,
            parent_email=payload.parent_email,
            source=payload.source,
            status=payload.status,
            notes=payload.notes,
        )
        db.add(applicant)
        db.commit()
        db.refresh(applicant)
        return applicant

    def get_applicant(
        self,
        db: Session,
        school_id: UUID,
        applicant_id: UUID,
    ) -> Applicant:
        applicant = db.scalars(
            select(Applicant).where(
                Applicant.id == applicant_id,
                Applicant.school_id == school_id,
                Applicant.is_deleted.is_(False),
            )
        ).first()
        if not applicant:
            raise NotFoundException("Applicant", str(applicant_id))
        return applicant

    def list_applicants(
        self,
        db: Session,
        school_id: UUID,
        admission_cycle_id: UUID | None = None,
        status: ApplicantStatus | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Applicant], int, int]:
        query = select(Applicant).where(
            Applicant.school_id == school_id,
            Applicant.is_deleted.is_(False),
        )

        if admission_cycle_id:
            query = query.where(Applicant.admission_cycle_id == admission_cycle_id)
        if status:
            query = query.where(Applicant.status == status)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Applicant.first_name.ilike(term),
                    Applicant.last_name.ilike(term),
                    Applicant.applicant_number.ilike(term),
                    Applicant.email.ilike(term),
                    Applicant.phone.ilike(term),
                    Applicant.parent_name.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(Applicant.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_applicant(
        self,
        db: Session,
        school_id: UUID,
        applicant_id: UUID,
        payload: ApplicantUpdate,
    ) -> Applicant:
        applicant = self.get_applicant(db, school_id, applicant_id)

        if payload.admission_cycle_id is not None:
            cycle = db.scalars(
                select(AdmissionCycle).where(
                    AdmissionCycle.id == payload.admission_cycle_id,
                    AdmissionCycle.school_id == school_id,
                    AdmissionCycle.is_deleted.is_(False),
                )
            ).first()
            if not cycle:
                raise NotFoundException("Admission Cycle", str(payload.admission_cycle_id))
            applicant.admission_cycle_id = payload.admission_cycle_id

        if payload.applicant_number and payload.applicant_number != applicant.applicant_number:
            existing = db.scalars(
                select(Applicant).where(
                    Applicant.school_id == school_id,
                    Applicant.applicant_number == payload.applicant_number,
                    Applicant.id != applicant_id,
                    Applicant.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Applicant with number", payload.applicant_number)
            applicant.applicant_number = payload.applicant_number

        if payload.first_name is not None:
            applicant.first_name = payload.first_name
        if payload.middle_name is not None:
            applicant.middle_name = payload.middle_name
        if payload.last_name is not None:
            applicant.last_name = payload.last_name
        if payload.date_of_birth is not None:
            applicant.date_of_birth = payload.date_of_birth
        if payload.gender is not None:
            applicant.gender = payload.gender
        if payload.email is not None:
            applicant.email = payload.email
        if payload.phone is not None:
            applicant.phone = payload.phone
        if payload.address is not None:
            applicant.address = payload.address
        if payload.parent_name is not None:
            applicant.parent_name = payload.parent_name
        if payload.parent_phone is not None:
            applicant.parent_phone = payload.parent_phone
        if payload.parent_email is not None:
            applicant.parent_email = payload.parent_email
        if payload.source is not None:
            applicant.source = payload.source
        if payload.status is not None:
            applicant.status = payload.status
        if payload.notes is not None:
            applicant.notes = payload.notes

        db.commit()
        db.refresh(applicant)
        return applicant

    def delete_applicant(
        self,
        db: Session,
        school_id: UUID,
        applicant_id: UUID,
    ) -> None:
        applicant = self.get_applicant(db, school_id, applicant_id)
        applicant.is_deleted = True
        applicant.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 3. ADMISSION APPLICATIONS
    # =========================================================================

    def create_application(
        self,
        db: Session,
        school_id: UUID,
        payload: AdmissionApplicationCreate,
    ) -> AdmissionApplication:
        # Validate applicant belongs to school
        applicant = db.scalars(
            select(Applicant).where(
                Applicant.id == payload.applicant_id,
                Applicant.school_id == school_id,
                Applicant.is_deleted.is_(False),
            )
        ).first()
        if not applicant:
            raise NotFoundException("Applicant", str(payload.applicant_id))

        # Validate cycle belongs to school
        cycle = db.scalars(
            select(AdmissionCycle).where(
                AdmissionCycle.id == payload.admission_cycle_id,
                AdmissionCycle.school_id == school_id,
                AdmissionCycle.is_deleted.is_(False),
            )
        ).first()
        if not cycle:
            raise NotFoundException("Admission Cycle", str(payload.admission_cycle_id))

        # Validate academic year belongs to school
        ay = db.scalars(
            select(AcademicYear).where(
                AcademicYear.id == payload.academic_year_id,
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
        ).first()
        if not ay:
            raise NotFoundException("Academic Year", str(payload.academic_year_id))

        # Validate class belongs to school
        cls = db.scalars(
            select(SchoolClass).where(
                SchoolClass.id == payload.target_class_id,
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted.is_(False),
            )
        ).first()
        if not cls:
            raise NotFoundException("School Class", str(payload.target_class_id))

        # Validate section if provided
        if payload.target_section_id:
            sec = db.scalars(
                select(Section).where(
                    Section.id == payload.target_section_id,
                    Section.school_class_id == cls.id,
                    Section.is_deleted.is_(False),
                )
            ).first()
            if not sec:
                raise NotFoundException("Section", str(payload.target_section_id))

        # Check duplicate active application in same cycle
        active_app = db.scalars(
            select(AdmissionApplication).where(
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.applicant_id == payload.applicant_id,
                AdmissionApplication.admission_cycle_id == payload.admission_cycle_id,
                AdmissionApplication.is_deleted.is_(False),
                AdmissionApplication.status.not_in(
                    [AdmissionApplicationStatus.REJECTED, AdmissionApplicationStatus.WITHDRAWN]
                ),
            )
        ).first()
        if active_app:
            raise AlreadyExistsException(
                "Active Admission Application for this applicant in cycle",
                str(payload.admission_cycle_id),
            )

        app_number = payload.application_number
        if not app_number:
            app_number = f"ADM-{date.today().year}-{uuid.uuid4().hex[:6].upper()}"
        else:
            existing_num = db.scalars(
                select(AdmissionApplication).where(
                    AdmissionApplication.school_id == school_id,
                    AdmissionApplication.application_number == app_number,
                    AdmissionApplication.is_deleted.is_(False),
                )
            ).first()
            if existing_num:
                raise AlreadyExistsException("Application with number", app_number)

        app_date = payload.application_date or date.today()

        application = AdmissionApplication(
            school_id=school_id,
            applicant_id=payload.applicant_id,
            admission_cycle_id=payload.admission_cycle_id,
            academic_year_id=payload.academic_year_id,
            target_class_id=payload.target_class_id,
            target_section_id=payload.target_section_id,
            application_number=app_number,
            application_date=app_date,
            status=payload.status,
            remarks=payload.remarks,
        )
        db.add(application)
        db.flush()

        # Record initial status history
        history = ApplicationStatusHistory(
            school_id=school_id,
            application_id=application.id,
            old_status=None,
            new_status=payload.status.value,
            changed_at=datetime.now(timezone.utc),
            reason="Application created",
            remarks=payload.remarks,
        )
        db.add(history)

        db.commit()
        db.refresh(application)
        return application

    def get_application(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
    ) -> AdmissionApplication:
        application = db.scalars(
            select(AdmissionApplication).where(
                AdmissionApplication.id == application_id,
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.is_deleted.is_(False),
            )
        ).first()
        if not application:
            raise NotFoundException("Admission Application", str(application_id))
        return application

    def list_applications(
        self,
        db: Session,
        school_id: UUID,
        admission_cycle_id: UUID | None = None,
        applicant_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        target_class_id: UUID | None = None,
        status: AdmissionApplicationStatus | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AdmissionApplication], int, int]:
        query = select(AdmissionApplication).where(
            AdmissionApplication.school_id == school_id,
            AdmissionApplication.is_deleted.is_(False),
        )

        if admission_cycle_id:
            query = query.where(AdmissionApplication.admission_cycle_id == admission_cycle_id)
        if applicant_id:
            query = query.where(AdmissionApplication.applicant_id == applicant_id)
        if academic_year_id:
            query = query.where(AdmissionApplication.academic_year_id == academic_year_id)
        if target_class_id:
            query = query.where(AdmissionApplication.target_class_id == target_class_id)
        if status:
            query = query.where(AdmissionApplication.status == status)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    AdmissionApplication.application_number.ilike(term),
                    AdmissionApplication.remarks.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(AdmissionApplication.application_date.desc(), AdmissionApplication.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_application(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
        payload: AdmissionApplicationUpdate,
    ) -> AdmissionApplication:
        application = self.get_application(db, school_id, application_id)

        if application.status not in [AdmissionApplicationStatus.DRAFT, AdmissionApplicationStatus.SUBMITTED]:
            raise BadRequestException("Cannot edit application details once under review or decided")

        if payload.target_class_id is not None:
            cls = db.scalars(
                select(SchoolClass).where(
                    SchoolClass.id == payload.target_class_id,
                    SchoolClass.school_id == school_id,
                    SchoolClass.is_deleted.is_(False),
                )
            ).first()
            if not cls:
                raise NotFoundException("School Class", str(payload.target_class_id))
            application.target_class_id = payload.target_class_id

        if payload.target_section_id is not None:
            sec = db.scalars(
                select(Section).where(
                    Section.id == payload.target_section_id,
                    Section.school_class_id == application.target_class_id,
                    Section.is_deleted.is_(False),
                )
            ).first()
            if not sec:
                raise NotFoundException("Section", str(payload.target_section_id))
            application.target_section_id = payload.target_section_id

        if payload.application_date is not None:
            application.application_date = payload.application_date
        if payload.remarks is not None:
            application.remarks = payload.remarks

        db.commit()
        db.refresh(application)
        return application

    # =========================================================================
    # 4. LIFECYCLE WORKFLOW & STATUS TRANSITIONS
    # =========================================================================

    def submit_application(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
        user_id: UUID | None,
        payload: ApplicationSubmitRequest | None = None,
    ) -> AdmissionApplication:
        # Row-level locking to ensure concurrency safety
        application = db.scalars(
            select(AdmissionApplication)
            .where(
                AdmissionApplication.id == application_id,
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()
        if not application:
            raise NotFoundException("Admission Application", str(application_id))

        # Idempotency check: if already SUBMITTED, return cleanly
        if application.status == AdmissionApplicationStatus.SUBMITTED:
            return application

        if application.status != AdmissionApplicationStatus.DRAFT:
            raise BadRequestException(f"Application cannot be submitted from status '{application.status.value}'. Must be DRAFT.")

        old_status = application.status.value
        application.status = AdmissionApplicationStatus.SUBMITTED
        application.submitted_at = datetime.now(timezone.utc)
        if payload and payload.remarks:
            application.remarks = payload.remarks

        history = ApplicationStatusHistory(
            school_id=school_id,
            application_id=application.id,
            old_status=old_status,
            new_status=AdmissionApplicationStatus.SUBMITTED.value,
            changed_by_user_id=user_id,
            changed_at=datetime.now(timezone.utc),
            reason="Application submitted by user",
            remarks=payload.remarks if payload else None,
        )
        db.add(history)
        db.commit()
        db.refresh(application)
        return application

    def start_review_application(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
        user_id: UUID | None,
        payload: ApplicationReviewRequest | None = None,
    ) -> AdmissionApplication:
        # Row-level locking for concurrency protection
        application = db.scalars(
            select(AdmissionApplication)
            .where(
                AdmissionApplication.id == application_id,
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()
        if not application:
            raise NotFoundException("Admission Application", str(application_id))

        # Idempotency check: if already UNDER_REVIEW, return cleanly
        if application.status == AdmissionApplicationStatus.UNDER_REVIEW:
            return application

        if application.status not in [AdmissionApplicationStatus.SUBMITTED, AdmissionApplicationStatus.WAITLISTED]:
            raise BadRequestException(
                f"Application cannot be moved to UNDER_REVIEW from status '{application.status.value}'. Must be SUBMITTED or WAITLISTED."
            )

        old_status = application.status.value
        application.status = AdmissionApplicationStatus.UNDER_REVIEW
        application.reviewed_at = datetime.now(timezone.utc)

        history = ApplicationStatusHistory(
            school_id=school_id,
            application_id=application.id,
            old_status=old_status,
            new_status=AdmissionApplicationStatus.UNDER_REVIEW.value,
            changed_by_user_id=user_id,
            changed_at=datetime.now(timezone.utc),
            reason="Application moved to review",
            remarks=payload.remarks if payload else None,
        )
        db.add(history)
        db.commit()
        db.refresh(application)
        return application

    def record_decision(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
        user_id: UUID | None,
        payload: AdmissionDecisionCreate,
    ) -> tuple[AdmissionApplication, AdmissionDecision]:
        # Row-level locking for atomic decision recording
        application = db.scalars(
            select(AdmissionApplication)
            .where(
                AdmissionApplication.id == application_id,
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()
        if not application:
            raise NotFoundException("Admission Application", str(application_id))

        if application.status not in [AdmissionApplicationStatus.UNDER_REVIEW, AdmissionApplicationStatus.WAITLISTED]:
            raise BadRequestException(
                f"Cannot record decision for application with status '{application.status.value}'. Must be UNDER_REVIEW or WAITLISTED."
            )

        # Map decision_type to application status
        if payload.decision_type in (AdmissionDecisionType.ACCEPTED, AdmissionDecisionType.CONDITIONAL_ACCEPT):
            target_status = AdmissionApplicationStatus.ACCEPTED
        elif payload.decision_type == AdmissionDecisionType.REJECTED:
            target_status = AdmissionApplicationStatus.REJECTED
        elif payload.decision_type == AdmissionDecisionType.WAITLISTED:
            target_status = AdmissionApplicationStatus.WAITLISTED
        elif payload.decision_type == AdmissionDecisionType.WITHDRAWN:
            target_status = AdmissionApplicationStatus.WITHDRAWN
        else:
            raise BadRequestException(f"Unsupported decision type '{payload.decision_type}'")

        old_status = application.status.value
        now_ts = datetime.now(timezone.utc)

        decision = AdmissionDecision(
            school_id=school_id,
            application_id=application.id,
            decision_type=payload.decision_type,
            decided_by_user_id=user_id,
            decided_at=now_ts,
            comments=payload.comments,
            conditions=payload.conditions,
        )
        db.add(decision)

        application.status = target_status
        application.decision_at = now_ts

        history = ApplicationStatusHistory(
            school_id=school_id,
            application_id=application.id,
            old_status=old_status,
            new_status=target_status.value,
            changed_by_user_id=user_id,
            changed_at=now_ts,
            reason=f"Admission Decision: {payload.decision_type.value}",
            remarks=payload.comments,
        )
        db.add(history)

        db.commit()
        db.refresh(application)
        db.refresh(decision)
        return application, decision

    def withdraw_application(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
        user_id: UUID | None,
        payload: ApplicationWithdrawRequest,
    ) -> AdmissionApplication:
        # Row-level locking for atomic withdrawal
        application = db.scalars(
            select(AdmissionApplication)
            .where(
                AdmissionApplication.id == application_id,
                AdmissionApplication.school_id == school_id,
                AdmissionApplication.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()
        if not application:
            raise NotFoundException("Admission Application", str(application_id))

        # Idempotency check: if already WITHDRAWN, return cleanly
        if application.status == AdmissionApplicationStatus.WITHDRAWN:
            return application

        if application.status == AdmissionApplicationStatus.REJECTED:
            raise BadRequestException("Cannot withdraw an application that has already been rejected")

        if application.status == AdmissionApplicationStatus.ENROLLED:
            raise BadRequestException("Cannot withdraw an application that has already been enrolled in SIS")

        old_status = application.status.value
        now_ts = datetime.now(timezone.utc)

        application.status = AdmissionApplicationStatus.WITHDRAWN
        history = ApplicationStatusHistory(
            school_id=school_id,
            application_id=application.id,
            old_status=old_status,
            new_status=AdmissionApplicationStatus.WITHDRAWN.value,
            changed_by_user_id=user_id,
            changed_at=now_ts,
            reason=f"Application Withdrawn: {payload.reason}",
            remarks=payload.remarks,
        )
        db.add(history)
        db.commit()
        db.refresh(application)
        return application

    # =========================================================================
    # 5. STATUS HISTORY & DECISIONS (READ-ONLY AUDIT)
    # =========================================================================

    def get_application_history(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
    ) -> list[ApplicationStatusHistory]:
        # Validate application exists and belongs to school
        self.get_application(db, school_id, application_id)

        items = db.scalars(
            select(ApplicationStatusHistory)
            .where(
                ApplicationStatusHistory.application_id == application_id,
                ApplicationStatusHistory.school_id == school_id,
                ApplicationStatusHistory.is_deleted.is_(False),
            )
            .order_by(ApplicationStatusHistory.changed_at.asc())
        ).all()
        return list(items)

    def get_application_decisions(
        self,
        db: Session,
        school_id: UUID,
        application_id: UUID,
    ) -> list[AdmissionDecision]:
        # Validate application exists and belongs to school
        self.get_application(db, school_id, application_id)

        items = db.scalars(
            select(AdmissionDecision)
            .where(
                AdmissionDecision.application_id == application_id,
                AdmissionDecision.school_id == school_id,
                AdmissionDecision.is_deleted.is_(False),
            )
            .order_by(AdmissionDecision.decided_at.desc())
        ).all()
        return list(items)


admissions_service = AdmissionsService()
