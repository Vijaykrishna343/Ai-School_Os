from datetime import date
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.common.enums import AttendanceStatus
from app.common.exceptions import NotFoundException, BadRequestException
from app.common.logger.logger import get_logger
from app.identity.models.user import IdentityUser
from app.models.teacher.teacher import Teacher
from app.models.teacher.teacher_attendance import TeacherAttendance
from app.schemas.teacher.teacher_attendance import (
    TeacherAttendanceCreate,
    TeacherAttendanceUpdate,
    TeacherAttendanceResponse,
    BulkTeacherAttendanceRequest,
    TeacherAttendanceSummaryResponse,
)

logger = get_logger(__name__)


class TeacherAttendanceService:

    def list_attendance(
        self,
        db: Session,
        school_id: UUID,
        attendance_date: date,
        status: AttendanceStatus | None = None,
    ) -> list[TeacherAttendanceResponse]:
        """
        List teacher attendance for a specific date in a tenant school.
        Ensures all teachers have a record representation.
        """
        stmt = (
            select(TeacherAttendance)
            .where(
                TeacherAttendance.school_id == school_id,
                TeacherAttendance.attendance_date == attendance_date,
                TeacherAttendance.is_deleted.is_(False),
            )
        )
        existing_records = {att.teacher_id: att for att in db.scalars(stmt).all()}

        # Fetch all active teachers for the school
        teachers = db.scalars(
            select(Teacher).where(
                Teacher.school_id == school_id,
                Teacher.is_deleted.is_(False),
            )
        ).all()

        results = []
        for teacher in teachers:
            record = existing_records.get(teacher.id)
            if record:
                if status and record.status != status:
                    continue
                resp = TeacherAttendanceResponse(
                    id=record.id,
                    school_id=record.school_id,
                    teacher_id=record.teacher_id,
                    teacher_name=f"{teacher.first_name} {teacher.last_name}",
                    employee_id=teacher.employee_id,
                    department=getattr(teacher, "department", None) or getattr(teacher, "qualification", None),
                    attendance_date=record.attendance_date,
                    status=record.status,
                    check_in_time=record.check_in_time,
                    check_out_time=record.check_out_time,
                    remarks=record.remarks,
                )
            else:
                if status and status != AttendanceStatus.PRESENT:
                    # Unmarked defaults to PRESENT in summary view
                    continue
                resp = TeacherAttendanceResponse(
                    id=teacher.id,  # Fallback virtual ID
                    school_id=school_id,
                    teacher_id=teacher.id,
                    teacher_name=f"{teacher.first_name} {teacher.last_name}",
                    employee_id=teacher.employee_id,
                    department=getattr(teacher, "department", None) or getattr(teacher, "qualification", None),
                    attendance_date=attendance_date,
                    status=AttendanceStatus.PRESENT,
                    check_in_time=None,
                    check_out_time=None,
                    remarks=None,
                )
            results.append(resp)

        return results

    def bulk_mark_attendance(
        self,
        db: Session,
        school_id: UUID,
        data: BulkTeacherAttendanceRequest,
    ) -> list[TeacherAttendanceResponse]:
        """
        Bulk mark teacher attendance for a specific date.
        """
        responses = []
        for item in data.items:
            # Check existing record
            stmt = select(TeacherAttendance).where(
                TeacherAttendance.school_id == school_id,
                TeacherAttendance.teacher_id == item.teacher_id,
                TeacherAttendance.attendance_date == data.attendance_date,
                TeacherAttendance.is_deleted.is_(False),
            )
            record = db.scalar(stmt)

            if record:
                record.status = item.status
                if item.check_in_time is not None:
                    record.check_in_time = item.check_in_time
                if item.check_out_time is not None:
                    record.check_out_time = item.check_out_time
                if item.remarks is not None:
                    record.remarks = item.remarks
            else:
                record = TeacherAttendance(
                    school_id=school_id,
                    teacher_id=item.teacher_id,
                    attendance_date=data.attendance_date,
                    status=item.status,
                    check_in_time=item.check_in_time,
                    check_out_time=item.check_out_time,
                    remarks=item.remarks,
                )
                db.add(record)

            db.flush()
            teacher = db.get(Teacher, item.teacher_id)
            responses.append(
                TeacherAttendanceResponse(
                    id=record.id,
                    school_id=school_id,
                    teacher_id=item.teacher_id,
                    teacher_name=f"{teacher.first_name} {teacher.last_name}" if teacher else "Staff",
                    employee_id=teacher.employee_id if teacher else None,
                    department=(getattr(teacher, "department", None) or getattr(teacher, "qualification", None)) if teacher else None,
                    attendance_date=record.attendance_date,
                    status=record.status,
                    check_in_time=record.check_in_time,
                    check_out_time=record.check_out_time,
                    remarks=record.remarks,
                )
            )

        db.commit()
        return responses

    def update_attendance(
        self,
        db: Session,
        school_id: UUID,
        attendance_id: UUID,
        data: TeacherAttendanceUpdate,
    ) -> TeacherAttendanceResponse:
        """
        Update single teacher attendance record.
        """
        record = db.get(TeacherAttendance, attendance_id)
        if not record or record.school_id != school_id or record.is_deleted:
            # Check if attendance_id is actually a teacher_id for first-time creation
            teacher = db.get(Teacher, attendance_id)
            if teacher and teacher.school_id == school_id:
                record = TeacherAttendance(
                    school_id=school_id,
                    teacher_id=teacher.id,
                    attendance_date=date.today(),
                    status=data.status or AttendanceStatus.PRESENT,
                    check_in_time=data.check_in_time,
                    check_out_time=data.check_out_time,
                    remarks=data.remarks,
                )
                db.add(record)
                db.flush()
            else:
                raise NotFoundException("Teacher attendance record not found.")

        if data.status:
            record.status = data.status
        if data.check_in_time is not None:
            record.check_in_time = data.check_in_time
        if data.check_out_time is not None:
            record.check_out_time = data.check_out_time
        if data.remarks is not None:
            record.remarks = data.remarks

        db.commit()
        db.refresh(record)

        teacher = db.get(Teacher, record.teacher_id)
        return TeacherAttendanceResponse(
            id=record.id,
            school_id=record.school_id,
            teacher_id=record.teacher_id,
            teacher_name=f"{teacher.first_name} {teacher.last_name}" if teacher else "Staff",
            employee_id=teacher.employee_id if teacher else None,
            department=(getattr(teacher, "department", None) or getattr(teacher, "qualification", None)) if teacher else None,
            attendance_date=record.attendance_date,
            status=record.status,
            check_in_time=record.check_in_time,
            check_out_time=record.check_out_time,
            remarks=record.remarks,
        )

    def teacher_check_in(
        self,
        db: Session,
        user: IdentityUser,
    ) -> TeacherAttendanceResponse:
        """
        Teacher self check-in based on authenticated user link.
        """
        from datetime import datetime
        now_str = datetime.now().strftime("%I:%M %p")
        today = date.today()

        # Find linked teacher record for user
        teacher = db.scalar(
            select(Teacher).where(
                Teacher.school_id == user.school_id,
                Teacher.email == user.email,
                Teacher.is_deleted.is_(False),
            )
        )
        if not teacher:
            raise BadRequestException("Authenticated user is not linked to a staff teacher profile.")

        record = db.scalar(
            select(TeacherAttendance).where(
                TeacherAttendance.school_id == user.school_id,
                TeacherAttendance.teacher_id == teacher.id,
                TeacherAttendance.attendance_date == today,
                TeacherAttendance.is_deleted.is_(False),
            )
        )

        if not record:
            record = TeacherAttendance(
                school_id=user.school_id,
                teacher_id=teacher.id,
                attendance_date=today,
                status=AttendanceStatus.PRESENT,
                check_in_time=now_str,
            )
            db.add(record)
        else:
            record.check_in_time = now_str
            if record.status == AttendanceStatus.ABSENT:
                record.status = AttendanceStatus.PRESENT

        db.commit()
        db.refresh(record)

        return TeacherAttendanceResponse(
            id=record.id,
            school_id=record.school_id,
            teacher_id=record.teacher_id,
            teacher_name=f"{teacher.first_name} {teacher.last_name}",
            employee_id=teacher.employee_id,
            department=getattr(teacher, "department", None) or getattr(teacher, "qualification", None),
            attendance_date=record.attendance_date,
            status=record.status,
            check_in_time=record.check_in_time,
            check_out_time=record.check_out_time,
            remarks=record.remarks,
        )

    def teacher_check_out(
        self,
        db: Session,
        user: IdentityUser,
    ) -> TeacherAttendanceResponse:
        """
        Teacher self check-out based on authenticated user link.
        """
        from datetime import datetime
        now_str = datetime.now().strftime("%I:%M %p")
        today = date.today()

        teacher = db.scalar(
            select(Teacher).where(
                Teacher.school_id == user.school_id,
                Teacher.email == user.email,
                Teacher.is_deleted.is_(False),
            )
        )
        if not teacher:
            raise BadRequestException("Authenticated user is not linked to a staff teacher profile.")

        record = db.scalar(
            select(TeacherAttendance).where(
                TeacherAttendance.school_id == user.school_id,
                TeacherAttendance.teacher_id == teacher.id,
                TeacherAttendance.attendance_date == today,
                TeacherAttendance.is_deleted.is_(False),
            )
        )

        if not record:
            record = TeacherAttendance(
                school_id=user.school_id,
                teacher_id=teacher.id,
                attendance_date=today,
                status=AttendanceStatus.PRESENT,
                check_in_time=now_str,
                check_out_time=now_str,
            )
            db.add(record)
        else:
            record.check_out_time = now_str

        db.commit()
        db.refresh(record)

        return TeacherAttendanceResponse(
            id=record.id,
            school_id=record.school_id,
            teacher_id=record.teacher_id,
            teacher_name=f"{teacher.first_name} {teacher.last_name}",
            employee_id=teacher.employee_id,
            department=getattr(teacher, "department", None) or getattr(teacher, "qualification", None),
            attendance_date=record.attendance_date,
            status=record.status,
            check_in_time=record.check_in_time,
            check_out_time=record.check_out_time,
            remarks=record.remarks,
        )

    def get_summary(
        self,
        db: Session,
        school_id: UUID,
        attendance_date: date,
    ) -> TeacherAttendanceSummaryResponse:
        """
        Get staff attendance metrics summary for a specific date.
        """
        total_teachers = db.scalar(
            select(func.count(Teacher.id)).where(
                Teacher.school_id == school_id,
                Teacher.is_deleted.is_(False),
            )
        ) or 0

        records = db.scalars(
            select(TeacherAttendance).where(
                TeacherAttendance.school_id == school_id,
                TeacherAttendance.attendance_date == attendance_date,
                TeacherAttendance.is_deleted.is_(False),
            )
        ).all()

        counts = {
            AttendanceStatus.PRESENT: 0,
            AttendanceStatus.ABSENT: 0,
            AttendanceStatus.LATE: 0,
            AttendanceStatus.EXCUSED: 0,
            AttendanceStatus.HALF_DAY: 0,
        }
        marked_ids = set()
        for r in records:
            marked_ids.add(r.teacher_id)
            if r.status in counts:
                counts[r.status] += 1

        # Unmarked default to present
        unmarked_count = max(0, total_teachers - len(marked_ids))
        counts[AttendanceStatus.PRESENT] += unmarked_count

        return TeacherAttendanceSummaryResponse(
            attendance_date=attendance_date,
            total_teachers=total_teachers,
            present_count=counts[AttendanceStatus.PRESENT],
            absent_count=counts[AttendanceStatus.ABSENT],
            late_count=counts[AttendanceStatus.LATE],
            leave_count=counts[AttendanceStatus.EXCUSED],
            half_day_count=counts[AttendanceStatus.HALF_DAY],
        )


teacher_attendance_service = TeacherAttendanceService()
