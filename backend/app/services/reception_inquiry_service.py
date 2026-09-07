from __future__ import annotations

from datetime import date, datetime
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.common.enums.visitor import HostType, ReceptionInquiryStatus
from app.common.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.identity.models.user import IdentityUser
from app.models.audit_log import AuditLog
from app.models.visitor.reception_inquiry import ReceptionInquiry
from app.models.visitor.visitor import Visitor
from app.schemas.visitor import (
    ReceptionInquiryCreate,
    ReceptionInquiryListResponse,
    ReceptionInquiryResponse,
    ReceptionInquiryUpdate,
)
from app.services.visitor_service import visitor_service


class ReceptionInquiryService:
    """
    Canonical service layer for reception inquiries and front-desk appointments.
    Enforces strict tenant isolation, state machine transitions, host & visitor linkage validation,
    and audit logging.
    """

    def validate_visitor(
        self,
        db: Session,
        current_school_id: UUID,
        visitor_id: UUID | None,
    ) -> Visitor | None:
        """
        Validates that the referenced visitor exists, is active (not deleted),
        and belongs to current_school_id.
        """
        if not visitor_id:
            return None

        visitor = db.scalar(
            select(Visitor).where(
                Visitor.id == visitor_id,
                Visitor.school_id == current_school_id,
                Visitor.is_deleted == False,
            )
        )
        if not visitor:
            raise ValidationException(
                "Referenced visitor not found or does not belong to your school."
            )
        return visitor

    def create_inquiry(
        self,
        db: Session,
        current_school_id: UUID,
        data: ReceptionInquiryCreate,
        current_user: IdentityUser | None = None,
        user_role: str | None = None,
    ) -> ReceptionInquiryResponse:
        """
        Logs a new front-desk reception inquiry or appointment.
        Enforces tenant isolation, visitor/host linkage validation, server-controlled initial status,
        and audit logging.
        """
        # 1. Visitor Linkage Validation
        if data.visitor_id:
            self.validate_visitor(db, current_school_id, data.visitor_id)

        # 2. Host Linkage Validation
        if data.host_type or data.host_id:
            visitor_service.validate_host(
                db=db,
                current_school_id=current_school_id,
                host_type=data.host_type,
                host_id=data.host_id,
            )

        # 3. Server-Controlled Initial Status
        # Newly created inquiries cannot start directly in RESOLVED or CANCELLED status.
        initial_status = data.status or ReceptionInquiryStatus.PENDING
        if initial_status in (
            ReceptionInquiryStatus.RESOLVED,
            ReceptionInquiryStatus.CANCELLED,
        ):
            raise ValidationException(
                f"Newly created inquiry cannot be assigned initial status '{initial_status.value}'."
            )

        inquiry = ReceptionInquiry(
            school_id=current_school_id,
            visitor_id=data.visitor_id,
            contact_name=data.contact_name.strip(),
            contact_phone=data.contact_phone.strip(),
            contact_email=data.contact_email.strip() if data.contact_email else None,
            subject=data.subject.strip(),
            details=data.details.strip() if data.details else None,
            host_type=data.host_type,
            host_id=data.host_id,
            appointment_time=data.appointment_time,
            status=initial_status,
            notes=data.notes.strip() if data.notes else None,
        )
        db.add(inquiry)
        db.flush()

        # 4. Audit Log
        if current_user:
            audit = AuditLog(
                school_id=current_school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role or "User",
                action="RECEPTION_INQUIRY_CREATED",
                module="RECEPTION",
                entity_type="ReceptionInquiry",
                entity_id=str(inquiry.id),
                status_code=201,
                details=f"Inquiry logged for '{inquiry.contact_name}' - Subject: '{inquiry.subject}'.",
            )
            db.add(audit)

        db.commit()
        db.refresh(inquiry)
        return ReceptionInquiryResponse.model_validate(inquiry)

    def list_inquiries(
        self,
        db: Session,
        current_school_id: UUID,
        status: ReceptionInquiryStatus | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        appointment_date: date | None = None,
        visitor_id: UUID | None = None,
        host_type: HostType | None = None,
        host_id: UUID | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> ReceptionInquiryListResponse:
        """
        Lists paginated reception inquiry records strictly scoped to current_school_id.
        Excludes soft-deleted records.
        """
        query = select(ReceptionInquiry).where(
            ReceptionInquiry.school_id == current_school_id,
            ReceptionInquiry.is_deleted == False,
        )

        if status:
            query = query.where(ReceptionInquiry.status == status)

        if start_date:
            query = query.where(func.date(ReceptionInquiry.created_at) >= start_date)

        if end_date:
            query = query.where(func.date(ReceptionInquiry.created_at) <= end_date)

        if appointment_date:
            query = query.where(
                func.date(ReceptionInquiry.appointment_time) == appointment_date
            )

        if visitor_id:
            query = query.where(ReceptionInquiry.visitor_id == visitor_id)

        if host_type:
            query = query.where(ReceptionInquiry.host_type == host_type)

        if host_id:
            query = query.where(ReceptionInquiry.host_id == host_id)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    ReceptionInquiry.contact_name.ilike(pattern),
                    ReceptionInquiry.contact_phone.ilike(pattern),
                    ReceptionInquiry.subject.ilike(pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        # Pagination & Ordering
        query = query.order_by(ReceptionInquiry.created_at.desc())
        offset = (page - 1) * page_size
        items = db.scalars(query.offset(offset).limit(page_size)).all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        responses = [ReceptionInquiryResponse.model_validate(item) for item in items]
        return ReceptionInquiryListResponse(
            items=responses,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_inquiry(
        self,
        db: Session,
        inquiry_id: UUID,
        current_school_id: UUID,
    ) -> ReceptionInquiryResponse:
        """
        Retrieves detailed reception inquiry record by ID within tenant isolation.
        """
        inquiry = db.scalar(
            select(ReceptionInquiry).where(
                ReceptionInquiry.id == inquiry_id,
                ReceptionInquiry.school_id == current_school_id,
                ReceptionInquiry.is_deleted == False,
            )
        )
        if not inquiry:
            raise NotFoundException("ReceptionInquiry", str(inquiry_id))

        return ReceptionInquiryResponse.model_validate(inquiry)

    def update_inquiry(
        self,
        db: Session,
        inquiry_id: UUID,
        current_school_id: UUID,
        data: ReceptionInquiryUpdate,
        current_user: IdentityUser | None = None,
        user_role: str | None = None,
    ) -> ReceptionInquiryResponse:
        """
        Updates an existing reception inquiry record.
        Enforces state machine transitions, host/visitor re-validation, immutable fields protection,
        and audit logging.
        """
        inquiry = db.scalar(
            select(ReceptionInquiry).where(
                ReceptionInquiry.id == inquiry_id,
                ReceptionInquiry.school_id == current_school_id,
                ReceptionInquiry.is_deleted == False,
            )
        )
        if not inquiry:
            raise NotFoundException("ReceptionInquiry", str(inquiry_id))

        # 1. State Machine Transitions
        if data.status is not None and data.status != inquiry.status:
            current_status = inquiry.status
            new_status = data.status

            # Rejections
            if current_status == ReceptionInquiryStatus.RESOLVED:
                raise ValidationException(
                    "Cannot modify status of an already RESOLVED inquiry."
                )

            if current_status == ReceptionInquiryStatus.CANCELLED:
                raise ValidationException(
                    "Cannot modify status of a CANCELLED inquiry."
                )

            # Valid transitions: PENDING -> IN_PROGRESS, RESOLVED, CANCELLED
            # IN_PROGRESS -> RESOLVED, CANCELLED
            if current_status == ReceptionInquiryStatus.PENDING:
                if new_status not in (
                    ReceptionInquiryStatus.IN_PROGRESS,
                    ReceptionInquiryStatus.RESOLVED,
                    ReceptionInquiryStatus.CANCELLED,
                ):
                    raise ValidationException(
                        f"Invalid status transition from {current_status.value} to {new_status.value}."
                    )
            elif current_status == ReceptionInquiryStatus.IN_PROGRESS:
                if new_status not in (
                    ReceptionInquiryStatus.RESOLVED,
                    ReceptionInquiryStatus.CANCELLED,
                ):
                    raise ValidationException(
                        f"Invalid status transition from {current_status.value} to {new_status.value}."
                    )

            inquiry.status = new_status

        # 2. Visitor Re-assignment Validation
        if data.visitor_id is not None:
            self.validate_visitor(db, current_school_id, data.visitor_id)
            inquiry.visitor_id = data.visitor_id

        # 3. Host Re-assignment Validation
        new_host_type = data.host_type if data.host_type is not None else inquiry.host_type
        new_host_id = data.host_id if data.host_id is not None else inquiry.host_id
        if (data.host_type is not None or data.host_id is not None) and (new_host_type or new_host_id):
            visitor_service.validate_host(
                db=db,
                current_school_id=current_school_id,
                host_type=new_host_type,
                host_id=new_host_id,
            )
            inquiry.host_type = new_host_type
            inquiry.host_id = new_host_id

        # 4. Partial Field Updates
        if data.contact_name is not None:
            inquiry.contact_name = data.contact_name.strip()
        if data.contact_phone is not None:
            inquiry.contact_phone = data.contact_phone.strip()
        if data.contact_email is not None:
            inquiry.contact_email = data.contact_email.strip() if data.contact_email else None
        if data.subject is not None:
            inquiry.subject = data.subject.strip()
        if data.details is not None:
            inquiry.details = data.details.strip() if data.details else None
        if data.appointment_time is not None:
            inquiry.appointment_time = data.appointment_time
        if data.notes is not None:
            inquiry.notes = data.notes.strip() if data.notes else None

        # 5. Audit Log
        if current_user:
            action = (
                "RECEPTION_INQUIRY_STATUS_CHANGED"
                if data.status is not None and data.status != inquiry.status
                else "RECEPTION_INQUIRY_UPDATED"
            )
            audit = AuditLog(
                school_id=current_school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role or "User",
                action=action,
                module="RECEPTION",
                entity_type="ReceptionInquiry",
                entity_id=str(inquiry.id),
                status_code=200,
                details=f"Inquiry ID {inquiry.id} updated (Status: {inquiry.status.value}).",
            )
            db.add(audit)

        db.commit()
        db.refresh(inquiry)
        return ReceptionInquiryResponse.model_validate(inquiry)


reception_inquiry_service = ReceptionInquiryService()
