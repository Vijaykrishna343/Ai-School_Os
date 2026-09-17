from __future__ import annotations

import random
import string
from datetime import date, datetime, timezone
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.enums.visitor import HostType, VisitorStatus
from app.common.exceptions import (
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.models.audit_log import AuditLog
from app.models.notification import NotificationChannel, NotificationRecipientType
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.visitor.visitor import Visitor
from app.schemas.notification_trigger import NotificationTriggerEvent
from app.schemas.visitor import (
    ReceptionInquiryResponse,
    VisitorBadgeResponse,
    VisitorCreate,
    VisitorListResponse,
    VisitorPreRegister,
    VisitorResponse,
    VisitorSummaryResponse,
)
from app.services.notification_trigger_service import notification_trigger_service

logger = get_logger(__name__)


def _resolve_host_recipient(
    db: Session,
    school_id: UUID,
    host_type: HostType | None,
    host_id: UUID | None,
) -> dict[str, Any] | None:
    """
    Resolves host recipient details strictly scoped to school_id.
    Guarantees tenant isolation by querying host entities within school_id only.
    Returns recipient info dict or None if no valid host recipient is found.
    """
    if not host_type or not host_id:
        return None

    if host_type == HostType.TEACHER:
        teacher = db.scalar(
            select(Teacher).where(
                Teacher.id == host_id,
                Teacher.school_id == school_id,
                Teacher.is_deleted == False,
            )
        )
        if teacher:
            contact = teacher.phone or teacher.email
            return {
                "recipient_type": NotificationRecipientType.TEACHER,
                "recipient_id": teacher.id,
                "recipient_name": teacher.full_name,
                "recipient_contact": contact,
                "phone": teacher.phone,
                "email": teacher.email,
            }

    elif host_type == HostType.STAFF:
        teacher = db.scalar(
            select(Teacher).where(
                Teacher.id == host_id,
                Teacher.school_id == school_id,
                Teacher.is_deleted == False,
            )
        )
        if teacher:
            contact = teacher.phone or teacher.email
            return {
                "recipient_type": NotificationRecipientType.STAFF,
                "recipient_id": teacher.id,
                "recipient_name": teacher.full_name,
                "recipient_contact": contact,
                "phone": teacher.phone,
                "email": teacher.email,
            }
        user = db.scalar(
            select(IdentityUser).where(
                IdentityUser.id == host_id,
                IdentityUser.school_id == school_id,
                IdentityUser.is_deleted == False,
            )
        )
        if user:
            name = f"{user.first_name} {user.last_name or ''}".strip()
            contact = user.phone or user.email
            return {
                "recipient_type": NotificationRecipientType.STAFF,
                "recipient_id": user.id,
                "recipient_name": name,
                "recipient_contact": contact,
                "phone": user.phone,
                "email": user.email,
            }

    elif host_type == HostType.STUDENT:
        student = db.scalar(
            select(Student).where(
                Student.id == host_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        )
        if student:
            if student.parent_id:
                parent = db.scalar(
                    select(Parent).where(
                        Parent.id == student.parent_id,
                        Parent.school_id == school_id,
                        Parent.is_deleted == False,
                    )
                )
                if parent:
                    p_name = (
                        parent.father_name
                        or parent.guardian_name
                        or parent.mother_name
                        or f"Parent of {student.first_name}"
                    )
                    contact = parent.primary_phone or parent.email
                    return {
                        "recipient_type": NotificationRecipientType.PARENT,
                        "recipient_id": parent.id,
                        "recipient_name": p_name,
                        "recipient_contact": contact,
                        "phone": parent.primary_phone,
                        "email": parent.email,
                    }
            s_name = f"{student.first_name} {student.last_name or ''}".strip()
            contact = student.phone or student.email
            if contact:
                return {
                    "recipient_type": NotificationRecipientType.STUDENT,
                    "recipient_id": student.id,
                    "recipient_name": s_name,
                    "recipient_contact": contact,
                    "phone": student.phone,
                    "email": student.email,
                }

    return None


def _trigger_visitor_checkin_notification(
    db: Session,
    visitor: Visitor,
) -> None:
    """
    Stages visitor arrival notification event(s) prior to DB commit.
    Wrapped in isolated try-except so notification errors never roll back visitor operation.
    """
    try:
        recipient = _resolve_host_recipient(
            db=db,
            school_id=visitor.school_id,
            host_type=visitor.host_type,
            host_id=visitor.host_id,
        )
        if not recipient:
            return

        template_variables = {
            "visitor_name": visitor.visitor_name,
            "purpose": visitor.purpose or "N/A",
            "pass_number": visitor.pass_number or "N/A",
            "host_name": recipient["recipient_name"],
            "check_in_time": visitor.check_in_time.strftime("%Y-%m-%d %H:%M") if visitor.check_in_time else "",
        }

        # Safe audit metadata - strictly omitting PII/ID proof details
        metadata = {
            "visitor_id": str(visitor.id),
            "school_id": str(visitor.school_id),
            "host_type": visitor.host_type.value if visitor.host_type else None,
            "host_id": str(visitor.host_id) if visitor.host_id else None,
            "event_type": "visitor_checkin",
        }

        channels = [NotificationChannel.IN_APP]
        if recipient.get("phone"):
            channels.append(NotificationChannel.SMS)

        for ch in channels:
            idempotency_key = f"visitor_checkin:{visitor.id}:{ch.value.lower()}"
            event = NotificationTriggerEvent(
                event_type="visitor_checkin",
                school_id=visitor.school_id,
                recipient_type=recipient["recipient_type"],
                recipient_name=recipient["recipient_name"],
                recipient_contact=recipient["recipient_contact"],
                channel=ch,
                template_key="visitor_checkin",
                template_variables=template_variables,
                recipient_id=recipient["recipient_id"],
                idempotency_key=idempotency_key,
                event_metadata=metadata,
            )
            notification_trigger_service.stage_notification_event(
                db=db,
                event=event,
                auto_dispatch_on_commit=True,
            )
    except Exception as exc:
        logger.warning("Failed to stage visitor check-in notification for visitor %s: %s", visitor.id, exc)


def _trigger_visitor_checkout_notification(
    db: Session,
    visitor: Visitor,
) -> None:
    """
    Stages visitor departure notification event prior to DB commit.
    Wrapped in isolated try-except so notification errors never roll back visitor checkout.
    Target channel: IN_APP.
    """
    try:
        recipient = _resolve_host_recipient(
            db=db,
            school_id=visitor.school_id,
            host_type=visitor.host_type,
            host_id=visitor.host_id,
        )
        if not recipient:
            return

        template_variables = {
            "visitor_name": visitor.visitor_name,
            "purpose": visitor.purpose or "N/A",
            "pass_number": visitor.pass_number or "N/A",
            "host_name": recipient["recipient_name"],
            "check_out_time": visitor.check_out_time.strftime("%Y-%m-%d %H:%M") if visitor.check_out_time else "",
        }

        # Safe audit metadata - strictly omitting PII/ID proof details
        metadata = {
            "visitor_id": str(visitor.id),
            "school_id": str(visitor.school_id),
            "host_type": visitor.host_type.value if visitor.host_type else None,
            "host_id": str(visitor.host_id) if visitor.host_id else None,
            "event_type": "visitor_checkout",
        }

        idempotency_key = f"visitor_checkout:{visitor.id}:in_app"
        event = NotificationTriggerEvent(
            event_type="visitor_checkout",
            school_id=visitor.school_id,
            recipient_type=recipient["recipient_type"],
            recipient_name=recipient["recipient_name"],
            recipient_contact=recipient["recipient_contact"],
            channel=NotificationChannel.IN_APP,
            template_key="visitor_checkout",
            template_variables=template_variables,
            recipient_id=recipient["recipient_id"],
            idempotency_key=idempotency_key,
            event_metadata=metadata,
        )
        notification_trigger_service.stage_notification_event(
            db=db,
            event=event,
            auto_dispatch_on_commit=True,
        )
    except Exception as exc:
        logger.warning("Failed to stage visitor check-out notification for visitor %s: %s", visitor.id, exc)



class VisitorService:
    """
    Canonical service layer for visitor management operations.
    Enforces strict tenant isolation, state machine transitions, host linkage validation,
    pass number generation, and audit logging.
    """

    def validate_host(
        self,
        db: Session,
        current_school_id: UUID,
        host_type: HostType | None,
        host_id: UUID | None,
    ) -> None:
        """
        Validates that the referenced host exists and belongs to current_school_id.
        """
        if not host_type or not host_id:
            return

        if host_type == HostType.TEACHER:
            teacher = db.scalar(
                select(Teacher).where(
                    Teacher.id == host_id,
                    Teacher.school_id == current_school_id,
                    Teacher.is_deleted == False,
                )
            )
            if not teacher:
                raise ValidationException(
                    "Referenced teacher host not found or does not belong to your school."
                )

        elif host_type == HostType.STUDENT:
            student = db.scalar(
                select(Student).where(
                    Student.id == host_id,
                    Student.school_id == current_school_id,
                    Student.is_deleted == False,
                )
            )
            if not student:
                raise ValidationException(
                    "Referenced student host not found or does not belong to your school."
                )

        elif host_type == HostType.STAFF:
            # Check Teacher or IdentityUser
            teacher = db.scalar(
                select(Teacher).where(
                    Teacher.id == host_id,
                    Teacher.school_id == current_school_id,
                    Teacher.is_deleted == False,
                )
            )
            user = db.scalar(
                select(IdentityUser).where(
                    IdentityUser.id == host_id,
                    IdentityUser.school_id == current_school_id,
                    IdentityUser.is_deleted == False,
                )
            )
            if not teacher and not user:
                raise ValidationException(
                    "Referenced staff host not found or does not belong to your school."
                )

    def _generate_pass_number(
        self,
        db: Session,
        current_school_id: UUID,
        today_date: date,
    ) -> str:
        """
        Generates a tenant-unique pass number (e.g. GP-YYYYMMDD-XXXX).
        """
        date_str = today_date.strftime("%Y%m%d")
        
        # Count visitors created today for this school
        today_count = db.scalar(
            select(func.count(Visitor.id)).where(
                Visitor.school_id == current_school_id,
                func.date(Visitor.created_at) == today_date,
            )
        ) or 0

        seq = today_count + 1
        suffix = f"{seq:04d}"
        pass_number = f"GP-{date_str}-{suffix}"

        # Collision check
        exists = db.scalar(
            select(Visitor).where(
                Visitor.school_id == current_school_id,
                Visitor.pass_number == pass_number,
                Visitor.is_deleted == False,
            )
        )
        if exists:
            rand_suffix = "".join(random.choices(string.digits, k=4))
            pass_number = f"GP-{date_str}-{rand_suffix}"

        return pass_number

    def check_in_visitor(
        self,
        db: Session,
        current_school_id: UUID,
        data: VisitorCreate,
        current_user: IdentityUser | None = None,
        user_role: str | None = None,
    ) -> VisitorResponse:
        """
        Registers and checks in a new visitor.
        Server-generates check-in timestamp and tenant-unique pass number.
        """
        # 1. Host Linkage Validation
        self.validate_host(
            db=db,
            current_school_id=current_school_id,
            host_type=data.host_type,
            host_id=data.host_id,
        )

        # 2. Duplicate Active Visitor Check
        existing_active = db.scalar(
            select(Visitor).where(
                Visitor.school_id == current_school_id,
                Visitor.visitor_name == data.visitor_name,
                Visitor.phone == data.phone,
                Visitor.status == VisitorStatus.CHECKED_IN,
                Visitor.is_deleted == False,
            )
        )
        if existing_active:
            raise ValidationException(
                f"Visitor '{data.visitor_name}' with phone '{data.phone}' is already actively checked in."
            )

        # 3. Timestamps & Pass Number
        now = datetime.now(timezone.utc)
        pass_number = data.pass_number or self._generate_pass_number(
            db, current_school_id, now.date()
        )

        status = VisitorStatus.CHECKED_IN

        visitor = Visitor(
            id=uuid4(),
            school_id=current_school_id,
            visitor_name=data.visitor_name.strip(),
            phone=data.phone.strip(),
            email=data.email.strip() if data.email else None,
            id_proof_type=data.id_proof_type,
            id_proof_number=data.id_proof_number.strip() if data.id_proof_number else None,
            purpose=data.purpose.strip(),
            host_type=data.host_type,
            host_id=data.host_id,
            check_in_time=now,
            status=status,
            pass_number=pass_number,
            remarks=data.remarks.strip() if data.remarks else None,
        )
        db.add(visitor)

        # 4. Audit Log
        if current_user:
            audit = AuditLog(
                school_id=current_school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role or "User",
                action="VISITOR_CHECK_IN",
                module="VISITORS",
                entity_type="Visitor",
                entity_id=str(visitor.id),
                status_code=201,
                details=f"Visitor {visitor.visitor_name} checked in with pass {visitor.pass_number}.",
            )
            db.add(audit)

        _trigger_visitor_checkin_notification(db, visitor)
        try:
            db.commit()
            db.refresh(visitor)
        except IntegrityError:
            db.rollback()
            # Retry with randomized suffix if pass_number collision occurred under race condition
            visitor.pass_number = f"GP-{now.strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=4))}"
            db.add(visitor)
            _trigger_visitor_checkin_notification(db, visitor)
            db.commit()
            db.refresh(visitor)

        return VisitorResponse.model_validate(visitor)

    def pre_register_visitor(
        self,
        db: Session,
        current_school_id: UUID,
        data: VisitorPreRegister,
        current_user: IdentityUser | None = None,
        user_role: str | None = None,
    ) -> VisitorResponse:
        """
        Pre-registers an expected visitor for the authenticated school.
        Status is strictly enforced as EXPECTED by the server.
        Generates a tenant-unique gate pass number for pre-registration reference.
        """
        # 1. Host Linkage Validation
        self.validate_host(
            db=db,
            current_school_id=current_school_id,
            host_type=data.host_type,
            host_id=data.host_id,
        )

        # 2. Check for duplicate expected visitor
        existing_expected = db.scalar(
            select(Visitor).where(
                Visitor.school_id == current_school_id,
                Visitor.visitor_name == data.visitor_name.strip(),
                Visitor.phone == data.phone.strip(),
                Visitor.status == VisitorStatus.EXPECTED,
                Visitor.is_deleted == False,
            )
        )
        if existing_expected:
            raise ValidationException(
                f"Visitor '{data.visitor_name}' with phone '{data.phone}' is already pre-registered as EXPECTED."
            )

        now = datetime.now(timezone.utc)
        pass_number = self._generate_pass_number(db, current_school_id, now.date())

        visitor = Visitor(
            id=uuid4(),
            school_id=current_school_id,
            visitor_name=data.visitor_name.strip(),
            phone=data.phone.strip(),
            email=data.email.strip() if data.email else None,
            id_proof_type=data.id_proof_type,
            id_proof_number=data.id_proof_number.strip() if data.id_proof_number else None,
            purpose=data.purpose.strip(),
            host_type=data.host_type,
            host_id=data.host_id,
            check_in_time=None,
            check_out_time=None,
            status=VisitorStatus.EXPECTED,
            pass_number=pass_number,
            remarks=data.remarks.strip() if data.remarks else None,
        )
        db.add(visitor)

        if current_user:
            audit = AuditLog(
                school_id=current_school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role or "User",
                action="VISITOR_PRE_REGISTERED",
                module="VISITORS",
                entity_type="Visitor",
                entity_id=str(visitor.id),
                status_code=201,
                details=f"Visitor {visitor.visitor_name} pre-registered with pass {visitor.pass_number}.",
            )
            db.add(audit)

        try:
            db.commit()
            db.refresh(visitor)
        except IntegrityError:
            db.rollback()
            visitor.pass_number = f"GP-{now.strftime('%Y%m%d')}-{''.join(random.choices(string.digits, k=4))}"
            db.add(visitor)
            db.commit()
            db.refresh(visitor)

        return VisitorResponse.model_validate(visitor)

    def quick_check_in_visitor(
        self,
        db: Session,
        visitor_id: UUID,
        current_school_id: UUID,
        remarks: str | None = None,
        current_user: IdentityUser | None = None,
        user_role: str | None = None,
    ) -> VisitorResponse:
        """
        Transitions an EXPECTED visitor to CHECKED_IN.
        Enforces state machine transitions, check-in timestamp generation, and audit logging.
        """
        visitor = db.scalar(
            select(Visitor).where(
                Visitor.id == visitor_id,
                Visitor.school_id == current_school_id,
                Visitor.is_deleted == False,
            )
        )
        if not visitor:
            raise NotFoundException("Visitor", str(visitor_id))

        if visitor.status == VisitorStatus.CHECKED_IN:
            raise ValidationException("Visitor is already checked in.")

        if visitor.status != VisitorStatus.EXPECTED:
            raise ValidationException(
                f"Cannot perform quick check-in for visitor with status '{visitor.status.value}'. Status must be EXPECTED."
            )

        now = datetime.now(timezone.utc)
        visitor.status = VisitorStatus.CHECKED_IN
        visitor.check_in_time = now
        if not visitor.pass_number:
            visitor.pass_number = self._generate_pass_number(db, current_school_id, now.date())
        if remarks:
            visitor.remarks = remarks.strip()

        if current_user:
            audit = AuditLog(
                school_id=current_school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role or "User",
                action="VISITOR_QUICK_CHECK_IN",
                module="VISITORS",
                entity_type="Visitor",
                entity_id=str(visitor.id),
                status_code=200,
                details=f"Expected visitor {visitor.visitor_name} quick checked in with pass {visitor.pass_number}.",
            )
            db.add(audit)

        _trigger_visitor_checkin_notification(db, visitor)
        db.commit()
        db.refresh(visitor)
        return VisitorResponse.model_validate(visitor)

    def get_visitor_badge(
        self,
        db: Session,
        visitor_id: UUID,
        current_school_id: UUID,
    ) -> VisitorBadgeResponse:
        """
        Retrieves privacy-preserving visitor badge data for printing and pass rendering.
        Omits sensitive ID proof numbers.
        """
        visitor = db.scalar(
            select(Visitor).where(
                Visitor.id == visitor_id,
                Visitor.school_id == current_school_id,
                Visitor.is_deleted == False,
            )
        )
        if not visitor:
            raise NotFoundException("Visitor", str(visitor_id))

        return VisitorBadgeResponse.model_validate(visitor)

    def check_out_visitor(
        self,
        db: Session,
        visitor_id: UUID,
        current_school_id: UUID,
        remarks: str | None = None,
        current_user: IdentityUser | None = None,
        user_role: str | None = None,
    ) -> VisitorResponse:
        """
        Checks out an active visitor.
        Server-generates checkout timestamp and enforces state machine transitions.
        """
        visitor = db.scalar(
            select(Visitor).where(
                Visitor.id == visitor_id,
                Visitor.school_id == current_school_id,
                Visitor.is_deleted == False,
            )
        )
        if not visitor:
            raise NotFoundException("Visitor", str(visitor_id))

        # State Machine Validation
        if visitor.status == VisitorStatus.CHECKED_OUT:
            raise ValidationException("Visitor is already checked out.")

        if visitor.status in (VisitorStatus.CANCELLED, VisitorStatus.EXPIRED):
            raise ValidationException(
                f"Cannot check out a visitor with status '{visitor.status.value}'."
            )

        now = datetime.now(timezone.utc)
        visitor.status = VisitorStatus.CHECKED_OUT
        visitor.check_out_time = now
        if remarks:
            visitor.remarks = remarks.strip()

        if current_user:
            audit = AuditLog(
                school_id=current_school_id,
                user_id=current_user.id,
                user_email=current_user.email,
                role_name=user_role or "User",
                action="VISITOR_CHECK_OUT",
                module="VISITORS",
                entity_type="Visitor",
                entity_id=str(visitor.id),
                status_code=200,
                details=f"Visitor {visitor.visitor_name} checked out.",
            )
            db.add(audit)

        _trigger_visitor_checkout_notification(db, visitor)
        db.commit()
        db.refresh(visitor)
        return VisitorResponse.model_validate(visitor)

    def list_visitors(
        self,
        db: Session,
        current_school_id: UUID,
        status: VisitorStatus | None = None,
        search: str | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> VisitorListResponse:
        """
        Lists paginated visitor records for current_school_id.
        Applies privacy-preserving summary schema (omitting sensitive ID proof numbers).
        """
        query = select(Visitor).where(
            Visitor.school_id == current_school_id,
            Visitor.is_deleted == False,
        )

        if status:
            query = query.where(Visitor.status == status)

        if start_date:
            query = query.where(func.date(Visitor.check_in_time) >= start_date)

        if end_date:
            query = query.where(func.date(Visitor.check_in_time) <= end_date)

        if search:
            pattern = f"%{search.strip()}%"
            query = query.where(
                or_(
                    Visitor.visitor_name.ilike(pattern),
                    Visitor.phone.ilike(pattern),
                    Visitor.pass_number.ilike(pattern),
                    Visitor.purpose.ilike(pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = db.scalar(count_query) or 0

        # Pagination & Ordering
        query = query.order_by(Visitor.check_in_time.desc(), Visitor.created_at.desc())
        offset = (page - 1) * page_size
        items = db.scalars(query.offset(offset).limit(page_size)).all()

        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        summary_items = [VisitorSummaryResponse.model_validate(v) for v in items]
        return VisitorListResponse(
            items=summary_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    def get_visitor(
        self,
        db: Session,
        visitor_id: UUID,
        current_school_id: UUID,
    ) -> VisitorResponse:
        """
        Retrieves detailed visitor record for authorized single-item view.
        """
        visitor = db.scalar(
            select(Visitor).where(
                Visitor.id == visitor_id,
                Visitor.school_id == current_school_id,
                Visitor.is_deleted == False,
            )
        )
        if not visitor:
            raise NotFoundException("Visitor", str(visitor_id))

        return VisitorResponse.model_validate(visitor)


visitor_service = VisitorService()
