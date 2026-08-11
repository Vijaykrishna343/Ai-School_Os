from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus
from app.models.attendance import Attendance


class AttendanceAggregationService:
    """
    Reusable domain service for calculating attendance statistics across date ranges.
    """

    def calculate_attendance_summary(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID,
        student_id: UUID,
        start_date: date,
        end_date: date,
    ) -> dict[str, int | Decimal]:
        """
        Calculates working days, present days, and attendance percentage for a student.
        """
        # Working days = distinct attendance dates recorded for the section
        working_days_query = select(func.count(func.distinct(Attendance.attendance_date))).where(
            Attendance.school_id == school_id,
            Attendance.section_id == section_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
            Attendance.is_deleted.is_(False),
        )
        total_working_days = db.scalar(working_days_query) or 0

        if total_working_days == 0:
            return {
                "total_working_days": 0,
                "present_days": 0,
                "attendance_percentage": Decimal("0.00"),
            }

        # Present days = count of PRESENT and LATE status records for this student
        present_days_query = select(func.count()).where(
            Attendance.school_id == school_id,
            Attendance.student_id == student_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
            Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
            Attendance.is_deleted.is_(False),
        )
        present_days = db.scalar(present_days_query) or 0

        percentage = (Decimal(present_days) / Decimal(total_working_days) * Decimal("100.00")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        return {
            "total_working_days": total_working_days,
            "present_days": present_days,
            "attendance_percentage": percentage,
        }

    def calculate_bulk_attendance_summaries(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID,
        student_ids: list[UUID],
        start_date: date,
        end_date: date,
    ) -> dict[UUID, dict[str, int | Decimal]]:
        """
        Batch calculates working days, present days, and attendance percentage for a list of students.
        """
        if not student_ids:
            return {}

        working_days_query = select(func.count(func.distinct(Attendance.attendance_date))).where(
            Attendance.school_id == school_id,
            Attendance.section_id == section_id,
            Attendance.attendance_date >= start_date,
            Attendance.attendance_date <= end_date,
            Attendance.is_deleted.is_(False),
        )
        total_working_days = db.scalar(working_days_query) or 0

        if total_working_days == 0:
            return {
                sid: {
                    "total_working_days": 0,
                    "present_days": 0,
                    "attendance_percentage": Decimal("0.00"),
                }
                for sid in student_ids
            }

        present_days_query = (
            select(Attendance.student_id, func.count().label("present_count"))
            .where(
                Attendance.school_id == school_id,
                Attendance.student_id.in_(student_ids),
                Attendance.attendance_date >= start_date,
                Attendance.attendance_date <= end_date,
                Attendance.status.in_([AttendanceStatus.PRESENT, AttendanceStatus.LATE]),
                Attendance.is_deleted.is_(False),
            )
            .group_by(Attendance.student_id)
        )
        results = db.execute(present_days_query).all()
        present_map = {row.student_id: row.present_count for row in results}

        summaries = {}
        for sid in student_ids:
            present_days = present_map.get(sid, 0)
            pct = (Decimal(present_days) / Decimal(total_working_days) * Decimal("100.00")).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )
            summaries[sid] = {
                "total_working_days": total_working_days,
                "present_days": present_days,
                "attendance_percentage": pct,
            }

        return summaries


attendance_aggregation_service = AttendanceAggregationService()
