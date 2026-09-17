from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus, StudentStatus
from app.common.exceptions.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.identity.models.user import IdentityUser
from app.models.attendance import Attendance
from app.repositories.attendance.attendance_repository import (
    AttendanceRepository,
    attendance_repository,
)
from app.repositories.section.section_repository import (
    SectionRepository,
    section_repository,
)
from app.repositories.student.student_repository import (
    StudentRepository,
    student_repository,
)
from typing import Any
from sqlalchemy import select
from app.common.logger.logger import get_logger
from app.models.notification import NotificationChannel, NotificationRecipientType
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.schemas.notification_trigger import NotificationTriggerEvent
from app.services.notification_trigger_service import notification_trigger_service

logger = get_logger(__name__)


def _resolve_absence_recipient(
    db: Session,
    school_id: UUID,
    student: Student,
) -> dict[str, Any] | None:
    """
    Resolves recipient for student absence notification strictly within school_id.
    Prefers primary parent/guardian; falls back to Student if parent is missing,
    soft-deleted, or has no contact.
    Guarantees tenant isolation by failing closed if student does not belong to school_id.
    """
    if student.school_id != school_id:
        return None

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
            if contact:
                return {
                    "recipient_type": NotificationRecipientType.PARENT,
                    "recipient_id": parent.id,
                    "recipient_name": p_name,
                    "recipient_contact": contact,
                    "phone": parent.primary_phone,
                    "email": parent.email,
                    "student_name": f"{student.first_name} {student.last_name or ''}".strip(),
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
            "student_name": s_name,
        }

    return None


def _trigger_student_absence_notification(
    db: Session,
    school_id: UUID,
    student: Student,
    attendance_date: date,
) -> None:
    """
    Stages student absence notification prior to DB commit.
    Wrapped in isolated try-except so notification errors never roll back attendance.
    """
    try:
        recipient = _resolve_absence_recipient(db=db, school_id=school_id, student=student)
        if not recipient:
            return

        date_str = attendance_date.strftime("%Y-%m-%d")
        template_variables = {
            "student_name": recipient["student_name"],
            "date": date_str,
        }

        metadata = {
            "student_id": str(student.id),
            "attendance_date": date_str,
            "school_id": str(school_id),
            "event_type": "student_absence",
        }

        channels = [NotificationChannel.IN_APP]
        if recipient.get("phone"):
            channels.append(NotificationChannel.SMS)
            channels.append(NotificationChannel.WHATSAPP)
        if recipient.get("email"):
            channels.append(NotificationChannel.EMAIL)

        for ch in channels:
            idempotency_key = f"student_absence:{student.id}:{date_str}:{ch.value.lower()}"
            event = NotificationTriggerEvent(
                event_type="student_absence",
                school_id=school_id,
                recipient_type=recipient["recipient_type"],
                recipient_name=recipient["recipient_name"],
                recipient_contact=recipient["recipient_contact"],
                channel=ch,
                template_key="student_absent_alert",
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
        logger.warning(
            "Failed to stage student absence notification for student %s on %s: %s",
            student.id,
            attendance_date,
            exc,
        )


class AttendanceService:
    """
    Service layer for managing Attendance business logic and validations.
    """

    def __init__(
        self,
        att_repo: AttendanceRepository = attendance_repository,
        stud_repo: StudentRepository = student_repository,
        sec_repo: SectionRepository = section_repository,
    ) -> None:
        self.attendance_repository = att_repo
        self.student_repository = stud_repo
        self.section_repository = sec_repo

    def create_attendance(
        self,
        db: Session,
        current_user: IdentityUser,
        attendance_in: AttendanceCreate,
    ) -> Attendance:
        """
        Create a single student daily attendance record.
        """
        school_id = current_user.school_id
        if not school_id:
            raise ValidationException("Authenticated user is not associated with a school.")

        student = self.student_repository.get_by_id(db, attendance_in.student_id)
        if not student or student.school_id != school_id or student.is_deleted:
            raise NotFoundException("Student not found.")

        if student.status != StudentStatus.ACTIVE:
            raise ValidationException(f"Cannot mark attendance for inactive student '{student.full_name}'.")

        existing = self.attendance_repository.get_existing_record(
            db,
            school_id=school_id,
            academic_year_id=student.academic_year_id,
            section_id=student.section_id,
            student_id=student.id,
            attendance_date=attendance_in.attendance_date,
        )
        if existing:
            raise AlreadyExistsException(
                f"Attendance for student '{student.full_name}' on {attendance_in.attendance_date} already exists."
            )

        attendance = Attendance(
            school_id=school_id,
            academic_year_id=student.academic_year_id,
            school_class_id=student.school_class_id,
            section_id=student.section_id,
            student_id=student.id,
            attendance_date=attendance_in.attendance_date,
            status=attendance_in.status,
            remarks=attendance_in.remarks,
            recorded_by_user_id=current_user.id,
        )
        saved = self.attendance_repository.create(db, attendance)
        if attendance_in.status == AttendanceStatus.ABSENT:
            _trigger_student_absence_notification(db, school_id, student, attendance_in.attendance_date)
        return saved

    def create_bulk_attendance(
        self,
        db: Session,
        current_user: IdentityUser,
        bulk_in: AttendanceBulkCreate,
    ) -> list[Attendance]:
        """
        Mark attendance for an entire class/section in a single atomic transaction.

        Validates all student records BEFORE performing any database insertions.
        Fails safely without creating partial records if any student is invalid or duplicate.
        """
        school_id = current_user.school_id
        if not school_id:
            raise ValidationException("Authenticated user is not associated with a school.")

        section = self.section_repository.get_by_id(db, bulk_in.section_id)
        if not section or section.is_deleted or section.school_class.school_id != school_id:
            raise NotFoundException("Section not found.")

        # Extract student IDs from request payload
        payload_student_ids = [rec.student_id for rec in bulk_in.records]
        if len(payload_student_ids) != len(set(payload_student_ids)):
            raise ValidationException("Duplicate student IDs found in bulk attendance payload.")

        # Check existing attendance records for these students on this date
        existing_records = self.attendance_repository.get_existing_for_students_and_date(
            db,
            school_id=school_id,
            section_id=bulk_in.section_id,
            student_ids=payload_student_ids,
            attendance_date=bulk_in.attendance_date,
        )
        if existing_records:
            existing_student_ids = {r.student_id for r in existing_records}
            raise AlreadyExistsException(
                f"Attendance records already exist for {len(existing_student_ids)} student(s) in this section on {bulk_in.attendance_date}."
            )

        new_attendance_records: list[Attendance] = []
        student_map: dict[UUID, Student] = {}

        # Validate all records before saving
        for item in bulk_in.records:
            student = self.student_repository.get_by_id(db, item.student_id)
            if not student or student.school_id != school_id or student.is_deleted:
                raise NotFoundException(f"Student ID {item.student_id} not found.")

            if student.section_id != bulk_in.section_id:
                raise ValidationException(
                    f"Student '{student.full_name}' does not belong to section ID {bulk_in.section_id}."
                )

            if student.status != StudentStatus.ACTIVE:
                raise ValidationException(
                    f"Cannot mark attendance for inactive student '{student.full_name}'."
                )

            student_map[student.id] = student
            att_record = Attendance(
                school_id=school_id,
                academic_year_id=student.academic_year_id,
                school_class_id=student.school_class_id,
                section_id=student.section_id,
                student_id=student.id,
                attendance_date=bulk_in.attendance_date,
                status=item.status,
                remarks=item.remarks,
                recorded_by_user_id=current_user.id,
            )
            new_attendance_records.append(att_record)

        # Atomically save all valid records
        saved_records = self.attendance_repository.create_bulk(db, new_attendance_records)

        # Stage absence notifications for absent students
        for att_rec in saved_records:
            if att_rec.status == AttendanceStatus.ABSENT:
                st = student_map.get(att_rec.student_id)
                if st:
                    _trigger_student_absence_notification(db, school_id, st, bulk_in.attendance_date)

        return saved_records

    def get_attendance(
        self,
        db: Session,
        current_user: IdentityUser,
        attendance_id: UUID,
    ) -> Attendance:
        """
        Retrieve an attendance record by ID with school tenant isolation.
        """
        school_id = current_user.school_id
        if not school_id:
            raise ValidationException("Authenticated user is not associated with a school.")

        attendance = self.attendance_repository.get_by_id_and_school(
            db, attendance_id, school_id
        )
        if not attendance:
            raise NotFoundException("Attendance record not found.")

        return attendance

    def list_attendance(
        self,
        db: Session,
        current_user: IdentityUser,
        section_id: UUID | None = None,
        school_class_id: UUID | None = None,
        student_id: UUID | None = None,
        student_ids: list[UUID] | None = None,
        attendance_date: date | None = None,
        status: AttendanceStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Attendance], int, int]:
        """
        Retrieve paginated attendance records filtered by tenant school ID and query filters.
        """
        school_id = current_user.school_id
        if not school_id:
            raise ValidationException("Authenticated user is not associated with a school.")

        return self.attendance_repository.get_paginated_by_school(
            db,
            school_id=school_id,
            section_id=section_id,
            school_class_id=school_class_id,
            student_id=student_id,
            student_ids=student_ids,
            attendance_date=attendance_date,
            status=status,
            page=page,
            page_size=page_size,
        )

    def update_attendance(
        self,
        db: Session,
        current_user: IdentityUser,
        attendance_id: UUID,
        update_in: AttendanceUpdate,
    ) -> Attendance:
        """
        Update an existing attendance record.
        """
        attendance = self.get_attendance(db, current_user, attendance_id)
        old_status = attendance.status

        if update_in.status is not None:
            attendance.status = update_in.status
        if update_in.remarks is not None:
            attendance.remarks = update_in.remarks

        attendance.recorded_by_user_id = current_user.id
        updated = self.attendance_repository.update(db, attendance)

        if update_in.status == AttendanceStatus.ABSENT and old_status != AttendanceStatus.ABSENT:
            st = self.student_repository.get_by_id(db, updated.student_id)
            if st:
                _trigger_student_absence_notification(db, attendance.school_id, st, updated.attendance_date)

        return updated

    def delete_attendance(
        self,
        db: Session,
        current_user: IdentityUser,
        attendance_id: UUID,
    ) -> None:
        """
        Soft-delete an attendance record.
        """
        attendance = self.get_attendance(db, current_user, attendance_id)
        if current_user and current_user.id:
            attendance.deleted_by_user_id = current_user.id
        self.attendance_repository.delete(db, attendance)


attendance_service = AttendanceService()
