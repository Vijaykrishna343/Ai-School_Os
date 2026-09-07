"""
Phase 12.7 Typed Domain Tool Handlers for AI School OS.
Provides safe, read-only analytics handlers for:
1. Academic Risk Summary (get_academic_risk_summary)
2. Attendance Analytics (get_attendance_analytics)
3. Fee Delinquency Summary (get_fee_delinquency_summary)
4. Exam Performance Summary (get_exam_performance_summary)
5. Homework Completion Summary (get_homework_completion_summary)
6. Timetable Schedule Summary (get_timetable_schedule_summary)
7. Staff Leave Summary (get_staff_leave_summary)

All handlers strictly enforce tenant boundary scoping (school_id == current_user_school_id),
use typed SQLAlchemy queries, scrub sensitive PII, and return JSON-serializable structured dicts.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.exceptions import BadRequestException, ForbiddenException
from app.common.enums import AttendanceStatus
from app.common.enums.fees import StudentFeeAssignmentStatus
from app.common.enums.timetable import DayOfWeek
from app.models.academic_year.academic_year import AcademicYear
from app.models.ai.ai_student_risk_assessment import AIStudentRiskAssessment
from app.models.attendance.attendance import Attendance
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.models.grading.report_card import ReportCard
from app.models.grading.report_card_item_snapshot import ReportCardItemSnapshot
from app.models.homework.homework import Homework
from app.models.homework.homework_submission import HomeworkSubmission, SubmissionStatus
from app.models.school_class.school_class import SchoolClass
from app.models.staff_leave import StaffLeaveRequest
from app.models.student.student import Student
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry


def _enforce_tenant_scope(school_id: uuid.UUID, current_user_school_id: uuid.UUID) -> uuid.UUID:
    """
    Enforces that caller cannot override or query outside their authenticated tenant scope.
    """
    if not current_user_school_id:
        raise ForbiddenException("Tenant context required for domain tool execution.")
    return current_user_school_id


def _parse_uuid(val: Any, param_name: str) -> uuid.UUID | None:
    if val is None:
        return None
    if isinstance(val, uuid.UUID):
        return val
    try:
        return uuid.UUID(str(val))
    except (ValueError, TypeError):
        raise BadRequestException(f"Invalid UUID format for parameter '{param_name}'.")


def get_academic_risk_summary(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    class_id: str | uuid.UUID | None = None,
    risk_level: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns aggregated academic risk evaluation summary.
    Enforces school_id tenant scoping and PII safety.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)
    parsed_class_id = _parse_uuid(class_id, "class_id")

    query = select(AIStudentRiskAssessment).where(
        AIStudentRiskAssessment.school_id == effective_school_id,
        AIStudentRiskAssessment.is_deleted == False,
    )

    if parsed_class_id:
        query = query.join(Student, AIStudentRiskAssessment.student_id == Student.id).where(
            Student.school_class_id == parsed_class_id,
            Student.is_deleted == False,
        )

    if risk_level:
        valid_levels = {"LOW", "MEDIUM", "MODERATE", "HIGH", "CRITICAL", "INSUFFICIENT_DATA"}
        normalized_level = risk_level.strip().upper()
        if normalized_level not in valid_levels:
            raise BadRequestException(f"Invalid risk_level parameter '{risk_level}'.")
        query = query.where(AIStudentRiskAssessment.risk_level == normalized_level)

    assessments = db.scalars(query).all()

    total_assessed = len(assessments)
    if total_assessed == 0:
        return {
            "total_assessed": 0,
            "high_risk_count": 0,
            "moderate_risk_count": 0,
            "low_risk_count": 0,
            "insufficient_data_count": 0,
            "average_risk_score": 0.0,
            "flagged_students_summary": [],
        }

    high_count = sum(1 for a in assessments if a.risk_level in ("HIGH", "CRITICAL"))
    moderate_count = sum(1 for a in assessments if a.risk_level in ("MODERATE", "MEDIUM"))
    low_count = sum(1 for a in assessments if a.risk_level == "LOW")
    insufficient_count = sum(1 for a in assessments if a.risk_level == "INSUFFICIENT_DATA")

    valid_scores = [float(a.risk_score) for a in assessments if a.risk_score is not None]
    avg_score = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0.0

    # Top flagged students (high/critical/moderate), max 5, PII minimized
    flagged = [a for a in assessments if a.risk_level in ("HIGH", "CRITICAL", "MODERATE", "MEDIUM")]
    flagged.sort(key=lambda x: float(x.risk_score or 0.0), reverse=True)

    flagged_summary = []
    for a in flagged[:5]:
        flagged_summary.append(
            {
                "assessment_id": str(a.id),
                "student_id": str(a.student_id),
                "risk_level": a.risk_level,
                "risk_score": float(a.risk_score) if a.risk_score is not None else None,
                "failed_subjects_count": a.failed_subjects_count,
            }
        )

    return {
        "total_assessed": total_assessed,
        "high_risk_count": high_count,
        "moderate_risk_count": moderate_count,
        "low_risk_count": low_count,
        "insufficient_data_count": insufficient_count,
        "average_risk_score": avg_score,
        "flagged_students_summary": flagged_summary,
    }


def get_attendance_analytics(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    days: int = 30,
    class_id: str | uuid.UUID | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns attendance metrics over lookback days.
    Enforces safe days bounds (1 to 90) and school_id tenant scoping.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)
    parsed_class_id = _parse_uuid(class_id, "class_id")

    try:
        days_val = int(days)
    except (ValueError, TypeError):
        raise BadRequestException("Parameter 'days' must be an integer.")

    if days_val < 1 or days_val > 90:
        raise BadRequestException("Parameter 'days' must be between 1 and 90.")

    start_date = date.today() - timedelta(days=days_val)

    query = select(Attendance).where(
        Attendance.school_id == effective_school_id,
        Attendance.is_deleted == False,
        Attendance.attendance_date >= start_date,
    )

    if parsed_class_id:
        query = query.where(Attendance.school_class_id == parsed_class_id)

    records = db.scalars(query).all()
    total_records = len(records)

    if total_records == 0:
        return {
            "days_analyzed": days_val,
            "total_records": 0,
            "present_count": 0,
            "absent_count": 0,
            "late_count": 0,
            "overall_attendance_pct": 0.0,
        }

    present_count = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent_count = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    late_count = sum(1 for r in records if r.status in (AttendanceStatus.LATE, AttendanceStatus.HALF_DAY))

    effective_present = present_count + late_count
    overall_pct = round((effective_present / total_records) * 100.0, 1)

    return {
        "days_analyzed": days_val,
        "total_records": total_records,
        "present_count": present_count,
        "absent_count": absent_count,
        "late_count": late_count,
        "overall_attendance_pct": overall_pct,
    }


def get_fee_delinquency_summary(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    status: str | None = None,
    days_overdue: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns student fee assignment delinquency metrics.
    Enforces school_id tenant scoping.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)

    query = select(StudentFeeAssignment).where(
        StudentFeeAssignment.school_id == effective_school_id,
        StudentFeeAssignment.is_deleted == False,
    )

    if status:
        valid_statuses = {s.value for s in StudentFeeAssignmentStatus}
        norm_status = status.strip().upper()
        if norm_status not in valid_statuses:
            raise BadRequestException(f"Invalid fee status parameter '{status}'.")
        query = query.where(StudentFeeAssignment.status == StudentFeeAssignmentStatus(norm_status))

    if days_overdue is not None:
        try:
            overdue_val = int(days_overdue)
        except (ValueError, TypeError):
            raise BadRequestException("Parameter 'days_overdue' must be an integer.")
        if overdue_val < 0:
            raise BadRequestException("Parameter 'days_overdue' must be non-negative.")
        cutoff_date = date.today() - timedelta(days=overdue_val)
        query = query.where(
            StudentFeeAssignment.due_date.isnot(None),
            StudentFeeAssignment.due_date <= cutoff_date,
        )

    assignments = db.scalars(query).all()
    total_count = len(assignments)

    if total_count == 0:
        return {
            "total_assignments": 0,
            "paid_count": 0,
            "pending_count": 0,
            "partial_count": 0,
            "overdue_count": 0,
        }

    paid_cnt = sum(1 for a in assignments if a.status == StudentFeeAssignmentStatus.PAID)
    pending_cnt = sum(1 for a in assignments if a.status == StudentFeeAssignmentStatus.PENDING)
    partial_cnt = sum(1 for a in assignments if a.status == StudentFeeAssignmentStatus.PARTIALLY_PAID)
    
    today_dt = date.today()
    overdue_cnt = sum(
        1 for a in assignments
        if a.due_date and a.due_date < today_dt and a.status not in (StudentFeeAssignmentStatus.PAID, StudentFeeAssignmentStatus.CANCELLED)
    )

    return {
        "total_assignments": total_count,
        "paid_count": paid_cnt,
        "pending_count": pending_cnt,
        "partial_count": partial_cnt,
        "overdue_count": overdue_cnt,
    }


def get_exam_performance_summary(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    academic_term_id: str | uuid.UUID | None = None,
    class_id: str | uuid.UUID | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns exam performance metrics from finalized report cards.
    Enforces school_id tenant scoping.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)
    parsed_term_id = _parse_uuid(academic_term_id, "academic_term_id")
    parsed_class_id = _parse_uuid(class_id, "class_id")

    query = select(ReportCard).where(
        ReportCard.school_id == effective_school_id,
        ReportCard.is_deleted == False,
        ReportCard.status.in_(["FINALIZED", "PUBLISHED"]),
    )

    if parsed_term_id:
        query = query.where(ReportCard.academic_term_id == parsed_term_id)
    if parsed_class_id:
        query = query.where(ReportCard.school_class_id == parsed_class_id)

    cards = db.scalars(query).all()
    total_cards = len(cards)

    if total_cards == 0:
        return {
            "total_report_cards": 0,
            "average_percentage": 0.0,
            "passed_count": 0,
            "failed_count": 0,
            "pass_rate_pct": 0.0,
        }

    percentages = [float(c.percentage) for c in cards if c.percentage is not None]
    avg_pct = round(sum(percentages) / len(percentages), 1) if percentages else 0.0

    passed_cnt = sum(1 for c in cards if c.is_passed is True)
    failed_cnt = sum(1 for c in cards if c.is_passed is False)
    pass_rate = round((passed_cnt / total_cards) * 100.0, 1)

    return {
        "total_report_cards": total_cards,
        "average_percentage": avg_pct,
        "passed_count": passed_cnt,
        "failed_count": failed_cnt,
        "pass_rate_pct": pass_rate,
    }


def get_homework_completion_summary(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    days: int = 30,
    class_id: str | uuid.UUID | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns homework completion metrics.
    Enforces safe days bound (1 to 90) and school_id tenant scoping.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)
    parsed_class_id = _parse_uuid(class_id, "class_id")

    try:
        days_val = int(days)
    except (ValueError, TypeError):
        raise BadRequestException("Parameter 'days' must be an integer.")

    if days_val < 1 or days_val > 90:
        raise BadRequestException("Parameter 'days' must be between 1 and 90.")

    start_date = datetime.now(timezone.utc) - timedelta(days=days_val)

    hw_query = select(Homework).where(
        Homework.school_id == effective_school_id,
        Homework.is_deleted == False,
        Homework.created_at >= start_date,
    )
    if parsed_class_id:
        hw_query = hw_query.where(Homework.school_class_id == parsed_class_id)

    homeworks = db.scalars(hw_query).all()
    total_assigned = len(homeworks)

    if total_assigned == 0:
        return {
            "days_analyzed": days_val,
            "total_homeworks_assigned": 0,
            "total_submissions": 0,
            "late_submissions_count": 0,
            "completion_rate_pct": 0.0,
        }

    hw_ids = [h.id for h in homeworks]
    sub_query = select(HomeworkSubmission).where(
        HomeworkSubmission.school_id == effective_school_id,
        HomeworkSubmission.is_deleted == False,
        HomeworkSubmission.homework_id.in_(hw_ids),
    )
    submissions = db.scalars(sub_query).all()

    total_submissions = len(submissions)
    late_count = sum(1 for s in submissions if s.status == SubmissionStatus.LATE)

    return {
        "days_analyzed": days_val,
        "total_homeworks_assigned": total_assigned,
        "total_submissions": total_submissions,
        "late_submissions_count": late_count,
        "completion_rate_pct": round((total_submissions / (total_assigned * 20)) * 100.0, 1) if total_assigned else 0.0,
    }


def get_timetable_schedule_summary(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    day_of_week: str | None = None,
    teacher_id: str | uuid.UUID | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns timetable schedule entry summary metrics.
    Enforces school_id tenant scoping.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)
    parsed_teacher_id = _parse_uuid(teacher_id, "teacher_id")

    query = select(TimetableEntry).join(Timetable, TimetableEntry.timetable_id == Timetable.id).where(
        Timetable.school_id == effective_school_id,
        Timetable.is_deleted == False,
        TimetableEntry.is_deleted == False,
    )

    if day_of_week:
        valid_days = {d.value for d in DayOfWeek}
        norm_day = day_of_week.strip().upper()
        if norm_day not in valid_days:
            raise BadRequestException(f"Invalid day_of_week parameter '{day_of_week}'.")
        query = query.where(TimetableEntry.day_of_week == DayOfWeek(norm_day))

    if parsed_teacher_id:
        query = query.where(TimetableEntry.teacher_id == parsed_teacher_id)

    entries = db.scalars(query).all()
    total_entries = len(entries)

    unique_teachers = len({e.teacher_id for e in entries if e.teacher_id})
    unique_timetables = len({e.timetable_id for e in entries if e.timetable_id})

    return {
        "total_scheduled_entries": total_entries,
        "unique_teachers_scheduled": unique_teachers,
        "unique_timetables_active": unique_timetables,
        "day_filter": day_of_week.strip().upper() if day_of_week else "ALL",
    }


def get_staff_leave_summary(
    db: Session,
    school_id: uuid.UUID,
    current_user_school_id: uuid.UUID,
    status: str | None = None,
    days: int = 30,
    **kwargs: Any,
) -> dict[str, Any]:
    """
    Returns staff leave request summary metrics.
    Enforces safe days bound (1 to 90) and school_id tenant scoping.
    """
    effective_school_id = _enforce_tenant_scope(school_id, current_user_school_id)

    try:
        days_val = int(days)
    except (ValueError, TypeError):
        raise BadRequestException("Parameter 'days' must be an integer.")

    if days_val < 1 or days_val > 90:
        raise BadRequestException("Parameter 'days' must be between 1 and 90.")

    start_cutoff = date.today() - timedelta(days=days_val)

    query = select(StaffLeaveRequest).where(
        StaffLeaveRequest.school_id == effective_school_id,
        StaffLeaveRequest.is_deleted == False,
        StaffLeaveRequest.start_date >= start_cutoff,
    )

    if status:
        valid_statuses = {"PENDING", "APPROVED", "REJECTED", "CANCELLED"}
        norm_status = status.strip().upper()
        if norm_status not in valid_statuses:
            raise BadRequestException(f"Invalid staff leave status parameter '{status}'.")
        query = query.where(StaffLeaveRequest.status == norm_status)

    requests = db.scalars(query).all()
    total_requests = len(requests)

    if total_requests == 0:
        return {
            "days_analyzed": days_val,
            "total_requests": 0,
            "approved_count": 0,
            "pending_count": 0,
            "rejected_count": 0,
            "total_approved_leave_days": 0.0,
            "currently_on_leave_staff_count": 0,
        }

    approved_cnt = sum(1 for r in requests if r.status == "APPROVED")
    pending_cnt = sum(1 for r in requests if r.status == "PENDING")
    rejected_cnt = sum(1 for r in requests if r.status == "REJECTED")

    approved_days_sum = float(sum(r.requested_days for r in requests if r.status == "APPROVED"))

    today_curr = date.today()
    currently_on_leave = sum(
        1 for r in requests
        if r.status == "APPROVED" and r.start_date <= today_curr <= r.end_date
    )

    return {
        "days_analyzed": days_val,
        "total_requests": total_requests,
        "approved_count": approved_cnt,
        "pending_count": pending_cnt,
        "rejected_count": rejected_cnt,
        "total_approved_leave_days": approved_days_sum,
        "currently_on_leave_staff_count": currently_on_leave,
    }
