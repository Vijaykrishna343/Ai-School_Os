"""
Teacher Classroom Command Cockpit Service — Phase 30.3
Aggregates daily schedule, attendance status, homework tasks, exams, and alerts for teachers.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from uuid import UUID

from sqlalchemy import and_, case, desc, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.common.enums import AttendanceStatus, TeacherStatus
from app.common.enums.timetable import DayOfWeek, TimetableStatus
from app.models.homework.homework import HomeworkStatus
from app.models.academic_year.academic_year import AcademicYear
from app.models.attendance.attendance import Attendance
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.homework.homework import Homework
from app.models.homework.homework_submission import HomeworkSubmission
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.models.timetable.period_slot import PeriodSlot
from app.models.timetable.teacher_substitution import TeacherSubstitution
from app.models.timetable.timetable import Timetable
from app.models.timetable.timetable_entry import TimetableEntry
from app.schemas.teacher_cockpit import (
    CockpitAlertItem,
    CockpitAttendanceSection,
    CockpitExamItem,
    CockpitHomeworkItem,
    CockpitMetricsSummary,
    CockpitQuickActions,
    CockpitScheduleEntry,
    CurrentAndNextClass,
    TeacherCockpitResponse,
    TeacherProfileHeader,
)


class TeacherCockpitService:
    """
    Teacher Classroom Command Cockpit Service.
    Tenant-isolated, high-performance operational aggregation.
    """

    WEEKDAY_MAP = {
        0: DayOfWeek.MONDAY,
        1: DayOfWeek.TUESDAY,
        2: DayOfWeek.WEDNESDAY,
        3: DayOfWeek.THURSDAY,
        4: DayOfWeek.FRIDAY,
        5: DayOfWeek.SATURDAY,
        6: DayOfWeek.SUNDAY,
    }

    def _resolve_teacher(
        self,
        db: Session,
        school_id: UUID,
        user_id: UUID,
        user_email: str,
    ) -> Optional[Teacher]:
        """Find active Teacher entity for given user in current school tenant."""
        stmt = (
            select(Teacher)
            .where(
                Teacher.school_id == school_id,
                Teacher.is_deleted.is_(False),
                or_(
                    Teacher.email == user_email,
                    Teacher.id == user_id,
                ),
            )
        )
        return db.execute(stmt).scalars().first()

    def get_cockpit_data(
        self,
        db: Session,
        school_id: UUID,
        current_user_id: UUID,
        current_user_email: str,
        current_user_name: str,
        user_permissions: Optional[List[str]] = None,
        target_date: Optional[date] = None,
    ) -> TeacherCockpitResponse:
        """
        Produce consolidated operational response for teacher command cockpit.
        """
        eval_date = target_date or date.today()
        current_dow = self.WEEKDAY_MAP.get(eval_date.weekday(), DayOfWeek.MONDAY)
        now_time = datetime.now().time()
        permissions = set(user_permissions or [])

        # 1. School Information
        school = db.execute(
            select(School).where(School.id == school_id, School.is_deleted.is_(False))
        ).scalars().first()
        school_name = school.name if school else "School"

        # 2. Teacher Profile Resolution
        teacher = self._resolve_teacher(db, school_id, current_user_id, current_user_email)

        if teacher:
            teacher_header = TeacherProfileHeader(
                teacher_id=teacher.id,
                first_name=teacher.first_name,
                last_name=teacher.last_name or "",
                full_name=teacher.full_name,
                employee_id=teacher.employee_id,
                email=teacher.email,
                phone=teacher.phone,
                qualification=teacher.qualification,
                specialization=teacher.specialization,
                school_id=school_id,
                school_name=school_name,
            )
            teacher_id = teacher.id
        else:
            # Fallback for Admin / Staff previewing cockpit
            name_parts = current_user_name.split(" ", 1)
            first_name = name_parts[0]
            last_name = name_parts[1] if len(name_parts) > 1 else ""
            teacher_header = TeacherProfileHeader(
                teacher_id=None,
                first_name=first_name,
                last_name=last_name,
                full_name=current_user_name,
                employee_id=None,
                email=current_user_email,
                phone=None,
                qualification=None,
                specialization=None,
                school_id=school_id,
                school_name=school_name,
            )
            teacher_id = None

        # 3. Timetable & Schedule Aggregation
        today_schedule: List[CockpitScheduleEntry] = []
        assigned_section_ids: Set[UUID] = set()
        assigned_subject_ids: Set[UUID] = set()
        assigned_class_ids: Set[UUID] = set()

        if teacher_id is not None:
            # 3.1 Get active substitutions for today
            sub_q = (
                select(TeacherSubstitution)
                .options(
                    joinedload(TeacherSubstitution.original_teacher),
                    joinedload(TeacherSubstitution.substitute_teacher),
                )
                .where(
                    TeacherSubstitution.school_id == school_id,
                    TeacherSubstitution.substitution_date == eval_date,
                    TeacherSubstitution.is_deleted.is_(False),
                )
            )
            active_subs = db.execute(sub_q).scalars().all()
            
            # Map entry_id -> substitution
            subs_by_entry: Dict[UUID, TeacherSubstitution] = {
                s.timetable_entry_id: s for s in active_subs
            }

            # 3.2 Get regular timetable entries for teacher on today's day of week
            regular_entries_q = (
                select(TimetableEntry)
                .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
                .join(PeriodSlot, TimetableEntry.period_slot_id == PeriodSlot.id)
                .join(Subject, TimetableEntry.subject_id == Subject.id)
                .join(SchoolClass, Timetable.school_class_id == SchoolClass.id)
                .outerjoin(Section, Timetable.section_id == Section.id)
                .outerjoin(Classroom, TimetableEntry.classroom_id == Classroom.id)
                .options(
                    joinedload(TimetableEntry.period_slot),
                    joinedload(TimetableEntry.subject),
                    joinedload(TimetableEntry.timetable).joinedload(Timetable.school_class),
                    joinedload(TimetableEntry.timetable).joinedload(Timetable.section),
                    joinedload(TimetableEntry.classroom),
                )
                .where(
                    Timetable.school_id == school_id,
                    Timetable.is_deleted.is_(False),
                    Timetable.status == TimetableStatus.PUBLISHED,
                    TimetableEntry.is_deleted.is_(False),
                    TimetableEntry.day_of_week == current_dow,
                    TimetableEntry.teacher_id == teacher_id,
                )
            )
            regular_entries = db.execute(regular_entries_q).scalars().all()

            # 3.3 Get substitution entries where this teacher is assigned as substitute today
            sub_entry_ids = [
                s.timetable_entry_id for s in active_subs if s.substitute_teacher_id == teacher_id
            ]
            sub_entries: List[TimetableEntry] = []
            if sub_entry_ids:
                sub_q2 = (
                    select(TimetableEntry)
                    .join(Timetable, TimetableEntry.timetable_id == Timetable.id)
                    .join(PeriodSlot, TimetableEntry.period_slot_id == PeriodSlot.id)
                    .join(Subject, TimetableEntry.subject_id == Subject.id)
                    .join(SchoolClass, Timetable.school_class_id == SchoolClass.id)
                    .outerjoin(Section, Timetable.section_id == Section.id)
                    .outerjoin(Classroom, TimetableEntry.classroom_id == Classroom.id)
                    .options(
                        joinedload(TimetableEntry.period_slot),
                        joinedload(TimetableEntry.subject),
                        joinedload(TimetableEntry.timetable).joinedload(Timetable.school_class),
                        joinedload(TimetableEntry.timetable).joinedload(Timetable.section),
                        joinedload(TimetableEntry.classroom),
                        joinedload(TimetableEntry.teacher),
                    )
                    .where(
                        Timetable.school_id == school_id,
                        Timetable.is_deleted.is_(False),
                        TimetableEntry.is_deleted.is_(False),
                        TimetableEntry.id.in_(sub_entry_ids),
                    )
                )
                sub_entries = db.execute(sub_q2).scalars().all()

            # Process all valid entries for today
            raw_schedule: List[Tuple[TimetableEntry, bool, Optional[TeacherSubstitution]]] = []

            for entry in regular_entries:
                sub = subs_by_entry.get(entry.id)
                # If someone else is substituting for this teacher today, skip
                if sub and sub.substitute_teacher_id != teacher_id:
                    continue
                raw_schedule.append((entry, False, None))

            for entry in sub_entries:
                sub = subs_by_entry.get(entry.id)
                raw_schedule.append((entry, True, sub))

            # Deduplicate by entry ID
            seen_entry_ids = set()
            for entry, is_sub, sub_record in raw_schedule:
                if entry.id in seen_entry_ids:
                    continue
                seen_entry_ids.add(entry.id)

                slot = entry.period_slot
                slot_num = getattr(slot, "display_order", 0) if slot else 0
                slot_name = slot.name if (slot and hasattr(slot, "name") and slot.name) else f"Period {slot_num}"
                start_str = slot.start_time.strftime("%H:%M") if (slot and slot.start_time) else "00:00"
                end_str = slot.end_time.strftime("%H:%M") if (slot and slot.end_time) else "00:00"
                p_type = str(slot.period_type.value) if (slot and hasattr(slot.period_type, "value")) else str(getattr(slot, "period_type", "REGULAR"))

                tt = entry.timetable
                class_id = tt.school_class_id if tt else entry.timetable_id
                class_name = tt.school_class.name if (tt and tt.school_class) else "Class"
                section_id = tt.section_id if tt else None
                section_name = tt.section.name if (tt and tt.section) else None

                assigned_class_ids.add(class_id)
                if section_id:
                    assigned_section_ids.add(section_id)
                if entry.subject_id:
                    assigned_subject_ids.add(entry.subject_id)

                # Determine slot status
                slot_status = "UPCOMING"
                if slot and slot.start_time and slot.end_time:
                    if now_time > slot.end_time:
                        slot_status = "COMPLETED"
                    elif slot.start_time <= now_time <= slot.end_time:
                        slot_status = "IN_PROGRESS"
                    else:
                        slot_status = "UPCOMING"

                orig_teacher_id = None
                orig_teacher_name = None
                if is_sub and sub_record and sub_record.original_teacher:
                    orig_teacher_id = sub_record.original_teacher_id
                    orig_teacher_name = sub_record.original_teacher.full_name

                today_schedule.append(
                    CockpitScheduleEntry(
                        timetable_entry_id=entry.id,
                        timetable_id=entry.timetable_id,
                        period_slot_id=entry.period_slot_id,
                        slot_number=slot_num,
                        slot_name=slot_name,
                        start_time=start_str,
                        end_time=end_str,
                        period_type=p_type,
                        subject_id=entry.subject_id,
                        subject_name=entry.subject.subject_name if entry.subject else "Subject",
                        subject_code=entry.subject.subject_code if entry.subject else "SUB",
                        school_class_id=class_id,
                        class_name=class_name,
                        section_id=section_id,
                        section_name=section_name,
                        classroom_id=entry.classroom_id,
                        room_number=entry.classroom.room_number if entry.classroom else None,
                        building=entry.classroom.building_name if entry.classroom else None,
                        is_substitution=is_sub,
                        original_teacher_id=orig_teacher_id,
                        original_teacher_name=orig_teacher_name,
                        status=slot_status,
                        attendance_marked=False,  # Enriched below
                    )
                )

            # Sort schedule by slot number or start time
            today_schedule.sort(key=lambda s: (s.slot_number, s.start_time))

        # 4. Attendance Roster Status for Today
        attendance_roster: List[CockpitAttendanceSection] = []
        pending_attendance_count = 0

        if assigned_section_ids:
            # Query section details
            sections_q = (
                select(Section)
                .join(SchoolClass, Section.school_class_id == SchoolClass.id)
                .options(joinedload(Section.school_class))
                .where(
                    Section.id.in_(assigned_section_ids),
                    Section.is_deleted.is_(False),
                )
            )
            sections_list = db.execute(sections_q).scalars().all()

            # Query attendance aggregated counts for these sections today
            att_counts_q = (
                select(
                    Attendance.section_id,
                    func.count(Attendance.id).label("total_records"),
                    func.count(case((Attendance.status == AttendanceStatus.PRESENT, 1))).label("present_cnt"),
                    func.count(case((Attendance.status == AttendanceStatus.ABSENT, 1))).label("absent_cnt"),
                    func.count(case((Attendance.status == AttendanceStatus.LATE, 1))).label("late_cnt"),
                    func.count(case((Attendance.status == AttendanceStatus.HALF_DAY, 1))).label("half_day_cnt"),
                )
                .where(
                    Attendance.school_id == school_id,
                    Attendance.section_id.in_(assigned_section_ids),
                    Attendance.attendance_date == eval_date,
                    Attendance.is_deleted.is_(False),
                )
                .group_by(Attendance.section_id)
            )
            att_counts = {r.section_id: r for r in db.execute(att_counts_q).all()}

            # Query total active students in these sections
            stu_counts_q = (
                select(
                    Student.section_id,
                    func.count(Student.id).label("total_students"),
                )
                .where(
                    Student.school_id == school_id,
                    Student.section_id.in_(assigned_section_ids),
                    Student.is_deleted.is_(False),
                )
                .group_by(Student.section_id)
            )
            stu_counts = {r.section_id: r.total_students for r in db.execute(stu_counts_q).all()}

            for sec in sections_list:
                sec_att = att_counts.get(sec.id)
                total_stu = stu_counts.get(sec.id, 0)
                
                if sec_att and sec_att.total_records > 0:
                    is_marked = True
                    prs = sec_att.present_cnt or 0
                    abs_cnt = sec_att.absent_cnt or 0
                    lt_cnt = sec_att.late_cnt or 0
                    hd_cnt = sec_att.half_day_cnt or 0
                    tot_rec = sec_att.total_records or 1
                    pct = round(((prs + (hd_cnt * 0.5)) / tot_rec) * 100.0, 1)
                else:
                    is_marked = False
                    pending_attendance_count += 1
                    prs, abs_cnt, lt_cnt, hd_cnt, pct = 0, 0, 0, 0, 0.0

                attendance_roster.append(
                    CockpitAttendanceSection(
                        school_class_id=sec.school_class_id,
                        class_name=sec.school_class.name if sec.school_class else "Class",
                        section_id=sec.id,
                        section_name=sec.name,
                        is_marked=is_marked,
                        total_students=total_stu,
                        present_count=prs,
                        absent_count=abs_cnt,
                        late_count=lt_cnt,
                        half_day_count=hd_cnt,
                        attendance_pct=pct,
                    )
                )

            # Update attendance_marked flags in today's schedule items
            marked_section_ids = {sec_id for sec_id, r in att_counts.items() if r.total_records > 0}
            for entry_item in today_schedule:
                if entry_item.section_id in marked_section_ids:
                    entry_item.attendance_marked = True
                    sec_att = att_counts.get(entry_item.section_id)
                    if sec_att:
                        entry_item.attendance_stats = {
                            "present": sec_att.present_cnt or 0,
                            "absent": sec_att.absent_cnt or 0,
                            "late": sec_att.late_cnt or 0,
                        }

        # 5. Current & Next Class Determination
        current_class: Optional[CockpitScheduleEntry] = None
        next_class: Optional[CockpitScheduleEntry] = None

        for item in today_schedule:
            if item.status == "IN_PROGRESS" and current_class is None:
                current_class = item
            elif item.status == "UPCOMING" and next_class is None:
                next_class = item

        # 6. Homework Overview
        homework_overview: List[CockpitHomeworkItem] = []
        pending_homework_reviews_count = 0
        active_homework_count = 0

        if teacher_id is not None:
            hw_q = (
                select(Homework)
                .options(
                    joinedload(Homework.subject),
                    joinedload(Homework.school_class),
                    joinedload(Homework.section),
                )
                .where(
                    Homework.school_id == school_id,
                    Homework.teacher_id == teacher_id,
                    Homework.is_deleted.is_(False),
                )
                .order_by(desc(Homework.assigned_date), desc(Homework.created_at))
                .limit(10)
            )
            hw_list = db.execute(hw_q).scalars().all()
            hw_ids = [h.id for h in hw_list]

            # Query submission counts
            subm_stats: Dict[UUID, Tuple[int, int]] = {}
            if hw_ids:
                subm_q = (
                    select(
                        HomeworkSubmission.homework_id,
                        func.count(HomeworkSubmission.id).label("total_submissions"),
                        func.count(case((HomeworkSubmission.status == "GRADED", 1))).label("graded_submissions"),
                    )
                    .where(
                        HomeworkSubmission.homework_id.in_(hw_ids),
                        HomeworkSubmission.is_deleted.is_(False),
                    )
                    .group_by(HomeworkSubmission.homework_id)
                )
                for r in db.execute(subm_q).all():
                    subm_stats[r.homework_id] = (r.total_submissions or 0, r.graded_submissions or 0)

            for hw in hw_list:
                tot_subm, graded_subm = subm_stats.get(hw.id, (0, 0))
                pending_review = max(0, tot_subm - graded_subm)
                if hw.status == HomeworkStatus.PUBLISHED or hw.status == "PUBLISHED":
                    active_homework_count += 1
                pending_homework_reviews_count += pending_review

                hw_status_str = hw.status.value if hasattr(hw.status, "value") else str(hw.status)
                homework_overview.append(
                    CockpitHomeworkItem(
                        homework_id=hw.id,
                        title=hw.title,
                        description=hw.description,
                        subject_name=hw.subject.subject_name if hw.subject else "Subject",
                        class_name=hw.school_class.name if hw.school_class else "Class",
                        section_name=hw.section.name if hw.section else None,
                        assigned_date=hw.assigned_date.strftime("%Y-%m-%d") if hw.assigned_date else "",
                        due_date=hw.due_date.strftime("%Y-%m-%d") if hw.due_date else "",
                        status=hw_status_str,
                        total_submissions=tot_subm,
                        graded_submissions=graded_subm,
                        pending_review_count=pending_review,
                    )
                )

        # 7. Upcoming Exams
        upcoming_exams: List[CockpitExamItem] = []
        if assigned_subject_ids or assigned_class_ids:
            exam_q = (
                select(ExamSchedule)
                .join(Exam, ExamSchedule.exam_id == Exam.id)
                .join(Subject, ExamSchedule.subject_id == Subject.id)
                .join(SchoolClass, ExamSchedule.school_class_id == SchoolClass.id)
                .outerjoin(Section, ExamSchedule.section_id == Section.id)
                .options(
                    joinedload(ExamSchedule.exam),
                    joinedload(ExamSchedule.subject),
                    joinedload(ExamSchedule.school_class),
                    joinedload(ExamSchedule.section),
                )
                .where(
                    ExamSchedule.school_id == school_id,
                    ExamSchedule.is_deleted.is_(False),
                    ExamSchedule.exam_date >= eval_date,
                    ExamSchedule.exam_date <= (eval_date + timedelta(days=21)),
                    or_(
                        ExamSchedule.subject_id.in_(assigned_subject_ids) if assigned_subject_ids else False,
                        ExamSchedule.school_class_id.in_(assigned_class_ids) if assigned_class_ids else False,
                    ),
                )
                .order_by(ExamSchedule.exam_date, ExamSchedule.start_time)
                .limit(6)
            )
            exam_scheds = db.execute(exam_q).scalars().all()
            sched_ids = [s.id for s in exam_scheds]

            # Results entered counts
            res_stats: Dict[UUID, int] = {}
            if sched_ids:
                res_q = (
                    select(
                        StudentExamResult.exam_schedule_id,
                        func.count(StudentExamResult.id).label("res_count"),
                    )
                    .where(
                        StudentExamResult.exam_schedule_id.in_(sched_ids),
                        StudentExamResult.is_deleted.is_(False),
                    )
                    .group_by(StudentExamResult.exam_schedule_id)
                )
                for r in db.execute(res_q).all():
                    res_stats[r.exam_schedule_id] = r.res_count or 0

            for es in exam_scheds:
                res_cnt = res_stats.get(es.id, 0)
                sec_id = es.section_id
                tot_students = stu_counts.get(sec_id, 30) if sec_id else 30
                
                grading_st = "NOT_STARTED"
                if res_cnt >= tot_students and tot_students > 0:
                    grading_st = "COMPLETED"
                elif res_cnt > 0:
                    grading_st = "IN_PROGRESS"

                upcoming_exams.append(
                    CockpitExamItem(
                        exam_id=es.exam_id,
                        exam_name=es.exam.name if es.exam else "Exam",
                        exam_schedule_id=es.id,
                        subject_name=es.subject.subject_name if es.subject else "Subject",
                        class_name=es.school_class.name if es.school_class else "Class",
                        section_name=es.section.name if es.section else None,
                        exam_date=es.exam_date.strftime("%Y-%m-%d") if es.exam_date else "",
                        start_time=es.start_time.strftime("%H:%M") if es.start_time else "",
                        end_time=es.end_time.strftime("%H:%M") if es.end_time else "",
                        max_marks=float(es.maximum_marks or 100),
                        passing_marks=float(es.passing_marks or 35),
                        results_entered_count=res_cnt,
                        total_students_count=tot_students,
                        grading_status=grading_st,
                    )
                )

        # 8. Actionable Alerts
        alerts: List[CockpitAlertItem] = []
        alert_idx = 1

        # 8.1 Unmarked attendance alert
        unmarked_sections = [sec for sec in attendance_roster if not sec.is_marked]
        if unmarked_sections:
            sec_names = ", ".join(f"{s.class_name}-{s.section_name}" for s in unmarked_sections[:3])
            alerts.append(
                CockpitAlertItem(
                    id=f"alert-{alert_idx}",
                    severity="WARNING",
                    title="Attendance Not Marked",
                    message=f"Attendance pending for today in: {sec_names}.",
                    category="ATTENDANCE",
                    action_route="/app/attendance",
                )
            )
            alert_idx += 1

        # 8.2 Submissions review alert
        if pending_homework_reviews_count > 0:
            alerts.append(
                CockpitAlertItem(
                    id=f"alert-{alert_idx}",
                    severity="INFO",
                    title="Homework Submissions Pending",
                    message=f"{pending_homework_reviews_count} student homework submissions awaiting grading.",
                    category="HOMEWORK",
                    action_route="/app/homework",
                )
            )
            alert_idx += 1

        # 8.3 Substitution alert
        subs_today = [item for item in today_schedule if item.is_substitution]
        if subs_today:
            alerts.append(
                CockpitAlertItem(
                    id=f"alert-{alert_idx}",
                    severity="URGENT",
                    title="Substitution Assigned Today",
                    message=f"You are assigned to cover {len(subs_today)} class(es) today as a substitute.",
                    category="TIMETABLE",
                    action_route="/app/timetable",
                )
            )
            alert_idx += 1

        # 8.4 Upcoming exam alert within 3 days
        imminent_exams = [
            e for e in upcoming_exams
            if 0 <= (datetime.strptime(e.exam_date, "%Y-%m-%d").date() - eval_date).days <= 3
        ]
        if imminent_exams:
            alerts.append(
                CockpitAlertItem(
                    id=f"alert-{alert_idx}",
                    severity="INFO",
                    title="Upcoming Examination Soon",
                    message=f"{imminent_exams[0].exam_name} ({imminent_exams[0].subject_name}) is scheduled for {imminent_exams[0].exam_date}.",
                    category="EXAM",
                    action_route="/app/exams",
                )
            )
            alert_idx += 1

        # 9. Quick Actions Capabilities
        is_super = "*" in permissions
        quick_actions = CockpitQuickActions(
            can_mark_attendance=is_super or "attendance.create" in permissions or "attendance.update" in permissions,
            can_manage_homework=is_super or "homework.create" in permissions or "homework.view" in permissions,
            can_enter_marks=is_super or "marks.create" in permissions or "marks.update" in permissions,
            can_view_timetable=is_super or "timetable.view" in permissions,
            can_apply_leave=is_super or "staff_leave.create" in permissions or "staff_leave.view" in permissions,
        )

        # 10. Summary Metrics
        completed_classes = sum(1 for item in today_schedule if item.status == "COMPLETED")
        summary = CockpitMetricsSummary(
            total_classes_today=len(today_schedule),
            completed_classes_today=completed_classes,
            pending_attendance_count=pending_attendance_count,
            active_homework_count=active_homework_count,
            pending_homework_reviews_count=pending_homework_reviews_count,
            upcoming_exams_count=len(upcoming_exams),
            active_alerts_count=len(alerts),
        )

        return TeacherCockpitResponse(
            today_date=eval_date.strftime("%Y-%m-%d"),
            day_of_week=current_dow.value if hasattr(current_dow, "value") else str(current_dow),
            teacher=teacher_header,
            summary=summary,
            current_and_next=CurrentAndNextClass(
                current_class=current_class,
                next_class=next_class,
            ),
            today_schedule=today_schedule,
            attendance_roster=attendance_roster,
            homework_overview=homework_overview,
            upcoming_exams=upcoming_exams,
            alerts=alerts,
            quick_actions=quick_actions,
        )


teacher_cockpit_service = TeacherCockpitService()
