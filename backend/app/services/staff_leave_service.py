from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, and_, or_, func

from app.common.enums import AttendanceStatus, TeacherStatus
from app.common.exceptions import (
    BadRequestException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.models.academic_year.academic_year import AcademicYear
from app.models.staff_leave import (
    StaffLeaveType,
    StaffLeaveBalance,
    StaffLeaveRequest,
    StaffLeaveApprovalHistory,
)
from app.schemas.staff_leave import (
    StaffLeaveTypeCreate,
    StaffLeaveTypeUpdate,
    StaffLeaveTypeResponse,
    StaffLeaveBalanceResponse,
    StaffLeaveBalanceAllocate,
    StaffLeaveRequestCreate,
    StaffLeaveRequestUpdate,
    StaffLeaveRequestResponse,
    StaffLeaveApprovalHistoryResponse,
    StaffLeaveSummaryReport,
)
from app.services.notification_service import notification_service
from app.models.notification import NotificationRecipientType, NotificationChannel
from app.api.v1.endpoints.audit_logs import write_audit_log

logger = get_logger(__name__)

DEFAULT_LEAVE_TYPES = [
    {"code": "CASUAL", "name": "Casual Leave", "max_days_per_year": Decimal("12.00"), "requires_attachment": False, "is_paid": True},
    {"code": "SICK", "name": "Sick Leave", "max_days_per_year": Decimal("10.00"), "requires_attachment": True, "is_paid": True},
    {"code": "EARNED", "name": "Earned / Privilege Leave", "max_days_per_year": Decimal("15.00"), "requires_attachment": False, "is_paid": True},
    {"code": "MATERNITY", "name": "Maternity Leave", "max_days_per_year": Decimal("180.00"), "requires_attachment": True, "is_paid": True},
    {"code": "PATERNITY", "name": "Paternity Leave", "max_days_per_year": Decimal("15.00"), "requires_attachment": False, "is_paid": True},
    {"code": "COMPENSATORY", "name": "Compensatory Off", "max_days_per_year": Decimal("5.00"), "requires_attachment": False, "is_paid": True},
    {"code": "UNPAID", "name": "Leave Without Pay (LWP)", "max_days_per_year": Decimal("90.00"), "requires_attachment": False, "is_paid": False},
    {"code": "OTHER", "name": "Special / Other Leave", "max_days_per_year": Decimal("5.00"), "requires_attachment": False, "is_paid": True},
]


class StaffLeaveService:
    """
    Core business logic for Staff Leave & Approval Management.
    Handles tenant isolation, balance tracking, approval workflows, attendance integration, and audit logging.
    """

    # ── LEAVE TYPES ─────────────────────────────────────────────────────────────

    def seed_default_leave_types(self, db: Session, school_id: uuid.UUID) -> list[StaffLeaveType]:
        """Idempotently seeds standard leave types for a school."""
        types = []
        for dt in DEFAULT_LEAVE_TYPES:
            existing = db.scalar(
                select(StaffLeaveType).where(
                    StaffLeaveType.school_id == school_id,
                    StaffLeaveType.code == dt["code"],
                    StaffLeaveType.is_deleted.is_(False),
                )
            )
            if not existing:
                lt = StaffLeaveType(
                    school_id=school_id,
                    code=dt["code"],
                    name=dt["name"],
                    max_days_per_year=dt["max_days_per_year"],
                    requires_attachment=dt["requires_attachment"],
                    is_paid=dt["is_paid"],
                    is_active=True,
                )
                db.add(lt)
                types.append(lt)
            else:
                types.append(existing)
        db.commit()
        return types

    def get_leave_types(self, db: Session, school_id: uuid.UUID) -> list[StaffLeaveType]:
        """Retrieves active leave types for school, seeding defaults if empty."""
        types = db.scalars(
            select(StaffLeaveType).where(
                StaffLeaveType.school_id == school_id,
                StaffLeaveType.is_deleted.is_(False),
            ).order_by(StaffLeaveType.code)
        ).all()
        if not types:
            return self.seed_default_leave_types(db, school_id)
        return list(types)

    def create_leave_type(self, db: Session, school_id: uuid.UUID, data: StaffLeaveTypeCreate) -> StaffLeaveType:
        """Creates a custom leave type for a school."""
        code_upper = data.code.strip().upper()
        existing = db.scalar(
            select(StaffLeaveType).where(
                StaffLeaveType.school_id == school_id,
                StaffLeaveType.code == code_upper,
                StaffLeaveType.is_deleted.is_(False),
            )
        )
        if existing:
            raise ValidationException(f"Leave type code '{code_upper}' already exists.")

        lt = StaffLeaveType(
            school_id=school_id,
            code=code_upper,
            name=data.name.strip(),
            description=data.description,
            max_days_per_year=data.max_days_per_year,
            requires_attachment=data.requires_attachment,
            is_paid=data.is_paid,
            is_active=data.is_active,
        )
        db.add(lt)
        db.commit()
        db.refresh(lt)
        return lt

    def update_leave_type(self, db: Session, school_id: uuid.UUID, type_id: uuid.UUID, data: StaffLeaveTypeUpdate) -> StaffLeaveType:
        """Updates a leave type configuration."""
        lt = db.scalar(
            select(StaffLeaveType).where(
                StaffLeaveType.id == type_id,
                StaffLeaveType.school_id == school_id,
                StaffLeaveType.is_deleted.is_(False),
            )
        )
        if not lt:
            raise NotFoundException("StaffLeaveType", str(type_id))

        if data.name is not None:
            lt.name = data.name.strip()
        if data.description is not None:
            lt.description = data.description
        if data.max_days_per_year is not None:
            lt.max_days_per_year = data.max_days_per_year
        if data.requires_attachment is not None:
            lt.requires_attachment = data.requires_attachment
        if data.is_paid is not None:
            lt.is_paid = data.is_paid
        if data.is_active is not None:
            lt.is_active = data.is_active

        db.commit()
        db.refresh(lt)
        return lt

    # ── LEAVE BALANCES ──────────────────────────────────────────────────────────

    def initialize_teacher_leave_balances(self, db: Session, school_id: uuid.UUID, teacher_id: uuid.UUID, academic_year_id: uuid.UUID) -> list[StaffLeaveBalance]:
        """Creates balance records for all active leave types for a teacher in an academic year."""
        leave_types = self.get_leave_types(db, school_id)
        balances = []

        for lt in leave_types:
            bal = db.scalar(
                select(StaffLeaveBalance).where(
                    StaffLeaveBalance.school_id == school_id,
                    StaffLeaveBalance.teacher_id == teacher_id,
                    StaffLeaveBalance.academic_year_id == academic_year_id,
                    StaffLeaveBalance.leave_type_id == lt.id,
                    StaffLeaveBalance.is_deleted.is_(False),
                )
            )
            if not bal:
                bal = StaffLeaveBalance(
                    school_id=school_id,
                    teacher_id=teacher_id,
                    academic_year_id=academic_year_id,
                    leave_type_id=lt.id,
                    allocated_days=lt.max_days_per_year,
                    used_days=Decimal("0.00"),
                    pending_days=Decimal("0.00"),
                )
                db.add(bal)
                balances.append(bal)
            else:
                balances.append(bal)
        db.commit()
        return balances

    def get_teacher_leave_balances(
        self, db: Session, school_id: uuid.UUID, teacher_id: uuid.UUID, academic_year_id: uuid.UUID
    ) -> list[StaffLeaveBalanceResponse]:
        """Returns balance details for a teacher."""
        self.initialize_teacher_leave_balances(db, school_id, teacher_id, academic_year_id)
        balances = db.scalars(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.school_id == school_id,
                StaffLeaveBalance.teacher_id == teacher_id,
                StaffLeaveBalance.academic_year_id == academic_year_id,
                StaffLeaveBalance.is_deleted.is_(False),
            )
        ).all()

        res = []
        for b in balances:
            lt = b.leave_type
            remaining = b.allocated_days - b.used_days - b.pending_days
            res.append(
                StaffLeaveBalanceResponse(
                    id=b.id,
                    school_id=b.school_id,
                    teacher_id=b.teacher_id,
                    academic_year_id=b.academic_year_id,
                    leave_type_id=b.leave_type_id,
                    leave_type_code=lt.code if lt else "",
                    leave_type_name=lt.name if lt else "",
                    allocated_days=b.allocated_days,
                    used_days=b.used_days,
                    pending_days=b.pending_days,
                    remaining_days=max(Decimal("0.00"), remaining),
                )
            )
        return res

    def allocate_leave_balance(self, db: Session, school_id: uuid.UUID, data: StaffLeaveBalanceAllocate) -> StaffLeaveBalanceResponse:
        """Manually sets/adjusts allocated leave quota for a teacher."""
        bal = db.scalar(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.school_id == school_id,
                StaffLeaveBalance.teacher_id == data.teacher_id,
                StaffLeaveBalance.academic_year_id == data.academic_year_id,
                StaffLeaveBalance.leave_type_id == data.leave_type_id,
                StaffLeaveBalance.is_deleted.is_(False),
            )
        )
        if not bal:
            bal = StaffLeaveBalance(
                school_id=school_id,
                teacher_id=data.teacher_id,
                academic_year_id=data.academic_year_id,
                leave_type_id=data.leave_type_id,
                allocated_days=data.allocated_days,
                used_days=Decimal("0.00"),
                pending_days=Decimal("0.00"),
            )
            db.add(bal)
        else:
            bal.allocated_days = data.allocated_days

        db.commit()
        db.refresh(bal)
        lt = bal.leave_type
        remaining = bal.allocated_days - bal.used_days - bal.pending_days
        return StaffLeaveBalanceResponse(
            id=bal.id,
            school_id=bal.school_id,
            teacher_id=bal.teacher_id,
            academic_year_id=bal.academic_year_id,
            leave_type_id=bal.leave_type_id,
            leave_type_code=lt.code if lt else "",
            leave_type_name=lt.name if lt else "",
            allocated_days=bal.allocated_days,
            used_days=bal.used_days,
            pending_days=bal.pending_days,
            remaining_days=max(Decimal("0.00"), remaining),
        )

    # ── LEAVE REQUEST WORKFLOW ──────────────────────────────────────────────────

    def _resolve_teacher_for_user(self, db: Session, school_id: uuid.UUID, user: IdentityUser) -> Teacher:
        """Finds active Teacher record linked to user account."""
        teacher = db.scalar(
            select(Teacher).where(
                Teacher.school_id == school_id,
                or_(Teacher.email == user.email, Teacher.id == user.id),
                Teacher.is_deleted.is_(False),
            )
        )
        if not teacher:
            # Fallback query by name if single match exists
            teachers = db.scalars(
                select(Teacher).where(
                    Teacher.school_id == school_id,
                    Teacher.first_name == user.first_name,
                    Teacher.last_name == user.last_name,
                    Teacher.is_deleted.is_(False),
                )
            ).all()
            if len(teachers) == 1:
                teacher = teachers[0]

        if not teacher:
            raise BadRequestException(f"Authenticated user '{user.email}' is not linked to a staff teacher profile.")
        return teacher

    def _calculate_requested_days(self, start_date: date, end_date: date, half_day_type: str) -> Decimal:
        """Calculates working days duration."""
        if end_date < start_date:
            raise ValidationException("End date cannot be earlier than start date.")

        if half_day_type in ("FIRST_HALF", "SECOND_HALF"):
            if start_date != end_date:
                raise ValidationException("Half-day leave requests must be for a single date.")
            return Decimal("0.50")

        total_days = (end_date - start_date).days + 1
        return Decimal(str(total_days))

    def create_leave_request(
        self, db: Session, school_id: uuid.UUID, current_user: IdentityUser, data: StaffLeaveRequestCreate
    ) -> StaffLeaveRequestResponse:
        """Submits a new staff leave request with balance verification and conflict checking."""
        teacher = self._resolve_teacher_for_user(db, school_id, current_user)

        # 1. Date Validation
        requested_days = self._calculate_requested_days(data.start_date, data.end_date, data.half_day_type)

        # 2. Leave Type Verification
        leave_type = db.scalar(
            select(StaffLeaveType).where(
                StaffLeaveType.id == data.leave_type_id,
                StaffLeaveType.school_id == school_id,
                StaffLeaveType.is_deleted.is_(False),
            )
        )
        if not leave_type:
            raise NotFoundException("StaffLeaveType", str(data.leave_type_id))

        if leave_type.requires_attachment and not data.attachment_url:
            raise ValidationException(f"Leave type '{leave_type.name}' requires a supporting attachment/document.")

        # 3. Prevent Overlapping Active Requests
        overlapping = db.scalar(
            select(StaffLeaveRequest).where(
                StaffLeaveRequest.school_id == school_id,
                StaffLeaveRequest.teacher_id == teacher.id,
                StaffLeaveRequest.status.in_(["PENDING", "APPROVED"]),
                StaffLeaveRequest.is_deleted.is_(False),
                or_(
                    and_(StaffLeaveRequest.start_date <= data.start_date, StaffLeaveRequest.end_date >= data.start_date),
                    and_(StaffLeaveRequest.start_date <= data.end_date, StaffLeaveRequest.end_date >= data.end_date),
                    and_(StaffLeaveRequest.start_date >= data.start_date, StaffLeaveRequest.end_date <= data.end_date),
                ),
            )
        )
        if overlapping:
            raise ValidationException(
                f"You already have an active leave request ({overlapping.status}) overlapping with {data.start_date} to {data.end_date}."
            )

        # 4. Balance Verification (unless UNPAID)
        self.initialize_teacher_leave_balances(db, school_id, teacher.id, data.academic_year_id)
        balance = db.scalar(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.school_id == school_id,
                StaffLeaveBalance.teacher_id == teacher.id,
                StaffLeaveBalance.academic_year_id == data.academic_year_id,
                StaffLeaveBalance.leave_type_id == data.leave_type_id,
                StaffLeaveBalance.is_deleted.is_(False),
            )
        )
        if balance and leave_type.is_paid:
            remaining = balance.allocated_days - balance.used_days - balance.pending_days
            if remaining < requested_days:
                raise ValidationException(
                    f"Insufficient leave balance for {leave_type.name}. Requested: {requested_days} day(s), Remaining: {remaining} day(s)."
                )

        # 5. Create Request
        req = StaffLeaveRequest(
            school_id=school_id,
            teacher_id=teacher.id,
            academic_year_id=data.academic_year_id,
            leave_type_id=data.leave_type_id,
            start_date=data.start_date,
            end_date=data.end_date,
            requested_days=requested_days,
            half_day_type=data.half_day_type,
            reason=data.reason.strip(),
            attachment_url=data.attachment_url,
            status="PENDING",
            requested_by_user_id=current_user.id,
        )
        db.add(req)
        db.flush()

        # Update pending balance
        if balance:
            balance.pending_days += requested_days

        # Add Workflow History
        history = StaffLeaveApprovalHistory(
            school_id=school_id,
            leave_request_id=req.id,
            action_by_user_id=current_user.id,
            action="SUBMITTED",
            from_status=None,
            to_status="PENDING",
            remarks=data.reason,
        )
        db.add(history)
        db.commit()

        # Audit & Notification
        write_audit_log(
            db=db,
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="CREATE",
            module="staff_leave",
            entity_type="StaffLeaveRequest",
            entity_id=str(req.id),
            details=f"Leave request created for teacher={teacher.first_name} {teacher.last_name} from {data.start_date} to {data.end_date}",
        )

        try:
            notification_service.create_and_send(
                db=db,
                school_id=school_id,
                recipient_type=NotificationRecipientType.STAFF,
                recipient_name=f"{teacher.first_name} {teacher.last_name}",
                recipient_contact=current_user.email,
                channel=NotificationChannel.EMAIL,
                template_key="general_announcement",
                template_variables={
                    "title": "Leave Request Submitted",
                    "message": f"Your leave request for {requested_days} day(s) from {data.start_date} to {data.end_date} has been submitted for approval.",
                },
                recipient_id=current_user.id,
            )
        except Exception as e:
            logger.warning("Notification error on leave request creation: %s", e)

        return self.get_leave_request_by_id(db, school_id, req.id, current_user)

    def approve_leave_request(
        self, db: Session, school_id: uuid.UUID, approver_user: IdentityUser, request_id: uuid.UUID, remarks: str | None = None
    ) -> StaffLeaveRequestResponse:
        """Approves a pending leave request, updates balances, and integrates with Teacher Attendance."""
        req = db.scalar(
            select(StaffLeaveRequest).where(
                StaffLeaveRequest.id == request_id,
                StaffLeaveRequest.school_id == school_id,
                StaffLeaveRequest.is_deleted.is_(False),
            )
        )
        if not req:
            raise NotFoundException("StaffLeaveRequest", str(request_id))

        if req.status != "PENDING":
            raise ValidationException(f"Cannot approve leave request in '{req.status}' status. Only PENDING requests can be approved.")

        # Prevent self-approval unless Super Admin
        if req.requested_by_user_id == approver_user.id and not getattr(approver_user, "is_super_admin", False):
            raise ForbiddenException("Self-approval of leave requests is prohibited.")

        # Update Request Status
        req.status = "APPROVED"
        req.approved_by_user_id = approver_user.id
        req.approved_at = datetime.now(timezone.utc)
        req.approval_remarks = remarks

        # Update Balance: move from pending -> used
        balance = db.scalar(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.school_id == school_id,
                StaffLeaveBalance.teacher_id == req.teacher_id,
                StaffLeaveBalance.academic_year_id == req.academic_year_id,
                StaffLeaveBalance.leave_type_id == req.leave_type_id,
                StaffLeaveBalance.is_deleted.is_(False),
            )
        )
        if balance:
            balance.pending_days = max(Decimal("0.00"), balance.pending_days - req.requested_days)
            balance.used_days += req.requested_days

        # Add Workflow History
        history = StaffLeaveApprovalHistory(
            school_id=school_id,
            leave_request_id=req.id,
            action_by_user_id=approver_user.id,
            action="APPROVED",
            from_status="PENDING",
            to_status="APPROVED",
            remarks=remarks,
        )
        db.add(history)

        # ── ATTENDANCE INTEGRATION ──────────────────────────────────────────────
        # Mark TeacherAttendance for each day as EXCUSED
        from datetime import timedelta
        curr_date = req.start_date
        lt_code = req.leave_type.code if req.leave_type else "LEAVE"
        att_status = AttendanceStatus.HALF_DAY if req.half_day_type in ("FIRST_HALF", "SECOND_HALF") else AttendanceStatus.EXCUSED

        while curr_date <= req.end_date:
            att = db.scalar(
                select(TeacherAttendance).where(
                    TeacherAttendance.school_id == school_id,
                    TeacherAttendance.teacher_id == req.teacher_id,
                    TeacherAttendance.attendance_date == curr_date,
                    TeacherAttendance.is_deleted.is_(False),
                )
            )
            if not att:
                att = TeacherAttendance(
                    school_id=school_id,
                    teacher_id=req.teacher_id,
                    attendance_date=curr_date,
                    status=att_status,
                    remarks=f"Approved Leave ({lt_code})",
                )
                db.add(att)
            else:
                att.status = att_status
                att.remarks = f"Approved Leave ({lt_code})"
            curr_date += timedelta(days=1)

        db.commit()

        # Audit & Notification
        write_audit_log(
            db=db,
            school_id=school_id,
            user_id=approver_user.id,
            user_email=approver_user.email,
            action="APPROVE",
            module="staff_leave",
            entity_type="StaffLeaveRequest",
            entity_id=str(req.id),
            details=f"Approved leave request {req.id} for teacher_id={req.teacher_id}",
        )

        try:
            teacher = req.teacher
            if teacher and teacher.email:
                notification_service.create_and_send(
                    db=db,
                    school_id=school_id,
                    recipient_type=NotificationRecipientType.STAFF,
                    recipient_name=f"{teacher.first_name} {teacher.last_name}",
                    recipient_contact=teacher.email,
                    channel=NotificationChannel.EMAIL,
                    template_key="general_announcement",
                    template_variables={
                        "title": "Leave Request Approved",
                        "message": f"Your leave request from {req.start_date} to {req.end_date} has been APPROVED by {approver_user.first_name} {approver_user.last_name}.",
                    },
                    recipient_id=req.requested_by_user_id,
                )
        except Exception as e:
            logger.warning("Notification error on leave approval: %s", e)

        return self.get_leave_request_by_id(db, school_id, req.id, approver_user)

    def reject_leave_request(
        self, db: Session, school_id: uuid.UUID, approver_user: IdentityUser, request_id: uuid.UUID, rejection_reason: str
    ) -> StaffLeaveRequestResponse:
        """Rejects a pending leave request and releases reserved pending balance."""
        req = db.scalar(
            select(StaffLeaveRequest).where(
                StaffLeaveRequest.id == request_id,
                StaffLeaveRequest.school_id == school_id,
                StaffLeaveRequest.is_deleted.is_(False),
            )
        )
        if not req:
            raise NotFoundException("StaffLeaveRequest", str(request_id))

        if req.status != "PENDING":
            raise ValidationException(f"Cannot reject leave request in '{req.status}' status. Only PENDING requests can be rejected.")

        req.status = "REJECTED"
        req.rejected_by_user_id = approver_user.id
        req.rejected_at = datetime.now(timezone.utc)
        req.rejection_reason = rejection_reason.strip()

        # Release pending balance
        balance = db.scalar(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.school_id == school_id,
                StaffLeaveBalance.teacher_id == req.teacher_id,
                StaffLeaveBalance.academic_year_id == req.academic_year_id,
                StaffLeaveBalance.leave_type_id == req.leave_type_id,
                StaffLeaveBalance.is_deleted.is_(False),
            )
        )
        if balance:
            balance.pending_days = max(Decimal("0.00"), balance.pending_days - req.requested_days)

        # Add Workflow History
        history = StaffLeaveApprovalHistory(
            school_id=school_id,
            leave_request_id=req.id,
            action_by_user_id=approver_user.id,
            action="REJECTED",
            from_status="PENDING",
            to_status="REJECTED",
            remarks=rejection_reason,
        )
        db.add(history)
        db.commit()

        # Audit & Notification
        write_audit_log(
            db=db,
            school_id=school_id,
            user_id=approver_user.id,
            user_email=approver_user.email,
            action="REJECT",
            module="staff_leave",
            entity_type="StaffLeaveRequest",
            entity_id=str(req.id),
            details=f"Rejected leave request {req.id}. Reason: {rejection_reason}",
        )

        try:
            teacher = req.teacher
            if teacher and teacher.email:
                notification_service.create_and_send(
                    db=db,
                    school_id=school_id,
                    recipient_type=NotificationRecipientType.STAFF,
                    recipient_name=f"{teacher.first_name} {teacher.last_name}",
                    recipient_contact=teacher.email,
                    channel=NotificationChannel.EMAIL,
                    template_key="general_announcement",
                    template_variables={
                        "title": "Leave Request Rejected",
                        "message": f"Your leave request from {req.start_date} to {req.end_date} was REJECTED. Reason: {rejection_reason}",
                    },
                    recipient_id=req.requested_by_user_id,
                )
        except Exception as e:
            logger.warning("Notification error on leave rejection: %s", e)

        return self.get_leave_request_by_id(db, school_id, req.id, approver_user)

    def cancel_leave_request(
        self, db: Session, school_id: uuid.UUID, current_user: IdentityUser, request_id: uuid.UUID, remarks: str | None = None
    ) -> StaffLeaveRequestResponse:
        """Cancels a leave request and updates balance/attendance accordingly."""
        req = db.scalar(
            select(StaffLeaveRequest).where(
                StaffLeaveRequest.id == request_id,
                StaffLeaveRequest.school_id == school_id,
                StaffLeaveRequest.is_deleted.is_(False),
            )
        )
        if not req:
            raise NotFoundException("StaffLeaveRequest", str(request_id))

        if req.status in ("CANCELLED", "REJECTED"):
            raise ValidationException(f"Leave request is already {req.status}.")

        old_status = req.status
        req.status = "CANCELLED"
        req.cancelled_by_user_id = current_user.id
        req.cancelled_at = datetime.now(timezone.utc)

        # Release balance
        balance = db.scalar(
            select(StaffLeaveBalance).where(
                StaffLeaveBalance.school_id == school_id,
                StaffLeaveBalance.teacher_id == req.teacher_id,
                StaffLeaveBalance.academic_year_id == req.academic_year_id,
                StaffLeaveBalance.leave_type_id == req.leave_type_id,
                StaffLeaveBalance.is_deleted.is_(False),
            )
        )
        if balance:
            if old_status == "PENDING":
                balance.pending_days = max(Decimal("0.00"), balance.pending_days - req.requested_days)
            elif old_status == "APPROVED":
                balance.used_days = max(Decimal("0.00"), balance.used_days - req.requested_days)

        # If it was APPROVED, clean up EXCUSED attendance records
        if old_status == "APPROVED":
            from datetime import timedelta
            curr_date = req.start_date
            while curr_date <= req.end_date:
                att = db.scalar(
                    select(TeacherAttendance).where(
                        TeacherAttendance.school_id == school_id,
                        TeacherAttendance.teacher_id == req.teacher_id,
                        TeacherAttendance.attendance_date == curr_date,
                        TeacherAttendance.is_deleted.is_(False),
                    )
                )
                if att and att.status in (AttendanceStatus.EXCUSED, AttendanceStatus.HALF_DAY):
                    db.delete(att)
                curr_date += timedelta(days=1)

        history = StaffLeaveApprovalHistory(
            school_id=school_id,
            leave_request_id=req.id,
            action_by_user_id=current_user.id,
            action="CANCELLED",
            from_status=old_status,
            to_status="CANCELLED",
            remarks=remarks or "Cancelled by user",
        )
        db.add(history)
        db.commit()

        write_audit_log(
            db=db,
            school_id=school_id,
            user_id=current_user.id,
            user_email=current_user.email,
            action="CANCEL",
            module="staff_leave",
            entity_type="StaffLeaveRequest",
            entity_id=str(req.id),
            details=f"Cancelled leave request {req.id}",
        )

        return self.get_leave_request_by_id(db, school_id, req.id, current_user)

    # ── QUERY / REPORTING METHODS ───────────────────────────────────────────────

    def get_leave_request_by_id(
        self, db: Session, school_id: uuid.UUID, request_id: uuid.UUID, current_user: IdentityUser
    ) -> StaffLeaveRequestResponse:
        """Fetches single leave request with full details."""
        req = db.scalar(
            select(StaffLeaveRequest).where(
                StaffLeaveRequest.id == request_id,
                StaffLeaveRequest.school_id == school_id,
                StaffLeaveRequest.is_deleted.is_(False),
            )
        )
        if not req:
            raise NotFoundException("StaffLeaveRequest", str(request_id))

        return self._to_request_response(req)

    def get_leave_requests(
        self,
        db: Session,
        school_id: uuid.UUID,
        current_user: IdentityUser,
        teacher_id: uuid.UUID | None = None,
        status: str | None = None,
        leave_type_id: uuid.UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        academic_year_id: uuid.UUID | None = None,
    ) -> list[StaffLeaveRequestResponse]:
        """Lists leave requests for school with scope-based authorization filtering."""
        query = select(StaffLeaveRequest).where(
            StaffLeaveRequest.school_id == school_id,
            StaffLeaveRequest.is_deleted.is_(False),
        )

        # Scoping: If user is a Teacher without management permissions, enforce self-only teacher_id
        is_approver_or_admin = any(
            r.name in ["Super Admin", "School Admin", "Principal", "Vice Principal"] for r in getattr(current_user, "roles", [])
        )
        if not is_approver_or_admin:
            try:
                self_teacher = self._resolve_teacher_for_user(db, school_id, current_user)
                query = query.where(StaffLeaveRequest.teacher_id == self_teacher.id)
            except BadRequestException:
                # User is not a teacher and not an approver -> empty result
                return []
        elif teacher_id:
            query = query.where(StaffLeaveRequest.teacher_id == teacher_id)

        if status:
            query = query.where(StaffLeaveRequest.status == status)
        if leave_type_id:
            query = query.where(StaffLeaveRequest.leave_type_id == leave_type_id)
        if academic_year_id:
            query = query.where(StaffLeaveRequest.academic_year_id == academic_year_id)
        if start_date:
            query = query.where(StaffLeaveRequest.start_date >= start_date)
        if end_date:
            query = query.where(StaffLeaveRequest.end_date <= end_date)

        requests = db.scalars(query.order_by(StaffLeaveRequest.created_at.desc())).all()
        return [self._to_request_response(r) for r in requests]

    def get_leave_summary_report(self, db: Session, school_id: uuid.UUID, academic_year_id: uuid.UUID) -> StaffLeaveSummaryReport:
        """Returns analytics summary for admin and approver dashboards."""
        all_reqs = db.scalars(
            select(StaffLeaveRequest).where(
                StaffLeaveRequest.school_id == school_id,
                StaffLeaveRequest.academic_year_id == academic_year_id,
                StaffLeaveRequest.is_deleted.is_(False),
            )
        ).all()

        total = len(all_reqs)
        pending = sum(1 for r in all_reqs if r.status == "PENDING")

        today = date.today()
        approved_today = sum(1 for r in all_reqs if r.status == "APPROVED" and r.approved_at and r.approved_at.date() == today)
        currently_on_leave = sum(1 for r in all_reqs if r.status == "APPROVED" and r.start_date <= today <= r.end_date)

        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}

        for r in all_reqs:
            code = r.leave_type.code if r.leave_type else "OTHER"
            by_type[code] = by_type.get(code, 0) + 1
            by_status[r.status] = by_status.get(r.status, 0) + 1

        return StaffLeaveSummaryReport(
            academic_year_id=academic_year_id,
            total_requests=total,
            pending_requests=pending,
            approved_today=approved_today,
            currently_on_leave=currently_on_leave,
            by_leave_type=by_type,
            by_status=by_status,
        )

    def _to_request_response(self, req: StaffLeaveRequest) -> StaffLeaveRequestResponse:
        """Maps ORM StaffLeaveRequest to StaffLeaveRequestResponse schema."""
        teacher = req.teacher
        t_name = f"{teacher.first_name} {teacher.last_name}" if teacher else None
        emp_id = teacher.employee_id if teacher else None

        ay = req.academic_year
        ay_name = ay.name if ay else None

        lt = req.leave_type
        lt_code = lt.code if lt else None
        lt_name = lt.name if lt else None

        history_res = [
            StaffLeaveApprovalHistoryResponse(
                id=h.id,
                action_by_user_id=h.action_by_user_id,
                action_by_name=f"{h.action_by.first_name} {h.action_by.last_name}" if h.action_by else None,
                action=h.action,
                from_status=h.from_status,
                to_status=h.to_status,
                remarks=h.remarks,
                created_at=h.created_at,
            )
            for h in (req.approval_history or [])
        ]

        return StaffLeaveRequestResponse(
            id=req.id,
            school_id=req.school_id,
            teacher_id=req.teacher_id,
            teacher_name=t_name,
            employee_id=emp_id,
            academic_year_id=req.academic_year_id,
            academic_year_name=ay_name,
            leave_type_id=req.leave_type_id,
            leave_type_code=lt_code,
            leave_type_name=lt_name,
            start_date=req.start_date,
            end_date=req.end_date,
            requested_days=req.requested_days,
            half_day_type=req.half_day_type,
            reason=req.reason,
            attachment_url=req.attachment_url,
            status=req.status,
            requested_by_user_id=req.requested_by_user_id,
            requested_by_name=f"{req.requested_by.first_name} {req.requested_by.last_name}" if req.requested_by else None,
            approved_by_user_id=req.approved_by_user_id,
            approved_by_name=f"{req.approved_by.first_name} {req.approved_by.last_name}" if req.approved_by else None,
            rejected_by_user_id=req.rejected_by_user_id,
            rejected_by_name=f"{req.rejected_by.first_name} {req.rejected_by.last_name}" if req.rejected_by else None,
            cancelled_by_user_id=req.cancelled_by_user_id,
            approval_remarks=req.approval_remarks,
            rejection_reason=req.rejection_reason,
            approved_at=req.approved_at,
            rejected_at=req.rejected_at,
            cancelled_at=req.cancelled_at,
            created_at=req.created_at,
            updated_at=req.updated_at,
            approval_history=history_res,
        )


staff_leave_service = StaffLeaveService()
