from uuid import UUID
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year import AcademicYear
from app.models.parent import Parent
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.models.teacher import Teacher


from app.common.enums import AcademicYearStatus
from app.schemas.dashboard import (
    AttendanceDashboardSummary,
    FeeDashboardSummary,
    AcademicDashboardSummary,
    RecentExamResultItem,
    HomeworkDashboardItem,
    ExamDashboardItem,
)


class DashboardRepository:
    """
    Data access layer for Admin Dashboard metrics and summary queries.
    All operations enforce strict tenant isolation using school_id and respect soft deletion.
    """

    def get_active_students_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Student.id))
            .filter(
                Student.school_id == school_id,
                Student.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_teachers_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Teacher.id))
            .filter(
                Teacher.school_id == school_id,
                Teacher.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_parents_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Parent.id))
            .filter(
                Parent.school_id == school_id,
                Parent.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_classes_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(SchoolClass.id))
            .filter(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

    def get_active_sections_count(self, db: Session, school_id: UUID) -> int:
        return (
            db.query(func.count(Section.id))
            .join(SchoolClass, Section.school_class_id == SchoolClass.id)
            .filter(
                SchoolClass.school_id == school_id,
                Section.is_deleted == False,  # noqa: E712
                SchoolClass.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )


    def get_current_academic_year(self, db: Session, school_id: UUID) -> AcademicYear | None:
        return (
            db.query(AcademicYear)
            .filter(
                AcademicYear.school_id == school_id,
                AcademicYear.status == AcademicYearStatus.ACTIVE,
                AcademicYear.is_deleted == False,  # noqa: E712
            )
            .first()
        )


    def get_current_academic_term(self, db: Session, school_id: UUID) -> AcademicTerm | None:
        return (
            db.query(AcademicTerm)
            .filter(
                AcademicTerm.school_id == school_id,
                AcademicTerm.is_active == True,  # noqa: E712
                AcademicTerm.is_deleted == False,  # noqa: E712
            )
            .first()
        )

    def get_student_attendance_summary(self, db: Session, school_id: UUID, student_id: UUID) -> AttendanceDashboardSummary:
        from app.models.attendance.attendance import Attendance
        from app.common.enums.attendance import AttendanceStatus

        records = (
            db.query(Attendance.status, func.count(Attendance.id))
            .filter(
                Attendance.school_id == school_id,
                Attendance.student_id == student_id,
                Attendance.is_deleted == False,  # noqa: E712
            )
            .group_by(Attendance.status)
            .all()
        )
        counts = {str(r[0].value) if hasattr(r[0], "value") else str(r[0]): r[1] for r in records}
        present = counts.get("PRESENT", 0)
        absent = counts.get("ABSENT", 0)
        late = counts.get("LATE", 0)
        half_day = counts.get("HALF_DAY", 0)
        total = present + absent + late + half_day

        pct = round(((present + (half_day * 0.5)) / total * 100), 1) if total > 0 else 0.0

        return AttendanceDashboardSummary(
            total_days=total,
            present_days=present,
            absent_days=absent,
            late_days=late,
            attendance_percentage=pct,
        )

    def get_student_fees_summary(self, db: Session, school_id: UUID, student_id: UUID) -> FeeDashboardSummary:
        from app.models.fees.student_fee_assignment import StudentFeeAssignment
        from decimal import Decimal

        assignments = (
            db.query(StudentFeeAssignment)
            .filter(
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.student_id == student_id,
                StudentFeeAssignment.is_deleted == False,  # noqa: E712
            )
            .all()
        )

        if not assignments:
            return FeeDashboardSummary(
                total_assigned="0.00",
                total_paid="0.00",
                total_due="0.00",
                pending_assignments_count=0,
                next_due_date=None,
                status="NO_FEES",
            )

        total_assigned = Decimal("0.00")
        total_paid = Decimal("0.00")
        total_due = Decimal("0.00")
        pending_count = 0
        due_dates = []

        for a in assignments:
            t_amt = getattr(a, "total_amount", None) or getattr(a, "net_amount", Decimal("0.00"))
            p_amt = getattr(a, "paid_amount", Decimal("0.00"))
            d_amt = getattr(a, "due_amount", None)
            if d_amt is None:
                d_amt = max(Decimal("0.00"), t_amt - p_amt)

            total_assigned += t_amt
            total_paid += p_amt
            total_due += d_amt

            if d_amt > Decimal("0.00"):
                pending_count += 1
                if getattr(a, "due_date", None):
                    due_dates.append(a.due_date)

        next_due = str(min(due_dates)) if due_dates else None
        fee_status = "PAID" if total_due == Decimal("0.00") else ("PARTIALLY_PAID" if total_paid > Decimal("0.00") else "PENDING")

        return FeeDashboardSummary(
            total_assigned=f"{total_assigned:.2f}",
            total_paid=f"{total_paid:.2f}",
            total_due=f"{total_due:.2f}",
            pending_assignments_count=pending_count,
            next_due_date=next_due,
            status=fee_status,
        )

    def get_student_academics_summary(self, db: Session, school_id: UUID, student_id: UUID) -> AcademicDashboardSummary:
        from app.models.exam.student_exam_result import StudentExamResult
        from app.models.grading.report_card import ReportCard
        from app.common.enums.report_card import ReportCardStatus

        results = (
            db.query(StudentExamResult)
            .join(StudentExamResult.exam_schedule)
            .filter(
                StudentExamResult.student_id == student_id,
                StudentExamResult.is_deleted == False,  # noqa: E712
            )
            .order_by(StudentExamResult.created_at.desc())
            .limit(5)
            .all()
        )

        recent_items = []
        for r in results:
            sch = r.exam_schedule
            exam_name = sch.exam.name if sch and sch.exam else "Exam"
            subj_name = getattr(sch.subject, "subject_name", getattr(sch.subject, "name", "Subject")) if sch and sch.subject else "Subject"
            max_m = str(getattr(sch, "maximum_marks", getattr(sch, "max_marks", "100.00")))
            pass_m = str(getattr(sch, "passing_marks", getattr(sch, "pass_marks", "35.00")))
            obtained_m = str(getattr(r, "marks_obtained", getattr(r, "obtained_marks", "0.00")))

            recent_items.append(
                RecentExamResultItem(
                    id=r.id,
                    exam_name=exam_name,
                    subject_name=subj_name,
                    marks_obtained=obtained_m,
                    maximum_marks=max_m,
                    passing_marks=pass_m,
                    grade=getattr(r, "grade", None),
                )
            )

        report_cards_count = (
            db.query(func.count(ReportCard.id))
            .filter(
                ReportCard.school_id == school_id,
                ReportCard.student_id == student_id,
                ReportCard.status == ReportCardStatus.FINALIZED,
                ReportCard.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )

        latest_card = (
            db.query(ReportCard)
            .filter(
                ReportCard.school_id == school_id,
                ReportCard.student_id == student_id,
                ReportCard.status == ReportCardStatus.FINALIZED,
                ReportCard.is_deleted == False,  # noqa: E712
            )
            .order_by(ReportCard.created_at.desc())
            .first()
        )
        gpa = str(latest_card.gpa) if latest_card and getattr(latest_card, "gpa", None) else None

        return AcademicDashboardSummary(
            latest_term_gpa=gpa,
            published_report_cards_count=report_cards_count,
            recent_results=recent_items,
        )

    def get_student_recent_homework(self, db: Session, school_id: UUID, section_id: UUID | None, student_id: UUID) -> list[HomeworkDashboardItem]:
        if not section_id:
            return []

        from app.models.homework.homework import Homework
        from app.models.homework.homework_submission import HomeworkSubmission

        homeworks = (
            db.query(Homework)
            .filter(
                Homework.school_id == school_id,
                Homework.section_id == section_id,
                Homework.is_deleted == False,  # noqa: E712
            )
            .order_by(Homework.due_date.desc())
            .limit(5)
            .all()
        )

        hw_ids = [h.id for h in homeworks]
        submitted_ids = set()
        if hw_ids:
            submissions = (
                db.query(HomeworkSubmission.homework_id)
                .filter(
                    HomeworkSubmission.homework_id.in_(hw_ids),
                    HomeworkSubmission.student_id == student_id,
                    HomeworkSubmission.is_deleted == False,  # noqa: E712
                )
                .all()
            )
            submitted_ids = {s[0] for s in submissions}

        items = []
        for h in homeworks:
            subj_name = getattr(h.subject, "subject_name", getattr(h.subject, "name", "Subject")) if h.subject else "Subject"
            items.append(
                HomeworkDashboardItem(
                    id=h.id,
                    title=h.title,
                    subject_name=subj_name,
                    due_date=str(h.due_date),
                    is_submitted=(h.id in submitted_ids),
                )
            )

        return items

    def get_student_upcoming_exams(self, db: Session, school_id: UUID, section_id: UUID | None) -> list[ExamDashboardItem]:
        if not section_id:
            return []

        from datetime import date
        from app.models.exam.exam_schedule import ExamSchedule

        schedules = (
            db.query(ExamSchedule)
            .filter(
                ExamSchedule.school_id == school_id,
                ExamSchedule.section_id == section_id,
                ExamSchedule.exam_date >= date.today(),
                ExamSchedule.is_deleted == False,  # noqa: E712
            )
            .order_by(ExamSchedule.exam_date.asc())
            .limit(5)
            .all()
        )

        items = []
        for s in schedules:
            exam_name = s.exam.name if s.exam else "Exam"
            subj_name = getattr(s.subject, "subject_name", getattr(s.subject, "name", "Subject")) if s.subject else "Subject"
            items.append(
                ExamDashboardItem(
                    id=s.id,
                    exam_name=exam_name,
                    subject_name=subj_name,
                    exam_date=str(s.exam_date),
                    start_time=str(s.start_time),
                    end_time=str(s.end_time),
                )
            )

        return items

    def get_unread_notifications_count(self, db: Session, school_id: UUID, user_id: UUID) -> int:
        from app.models.notification import Notification

        return (
            db.query(func.count(Notification.id))
            .filter(
                Notification.school_id == school_id,
                Notification.is_deleted == False,  # noqa: E712
            )
            .scalar()
            or 0
        )


dashboard_repository = DashboardRepository()

