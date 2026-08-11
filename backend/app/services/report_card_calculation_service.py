from datetime import date
from decimal import Decimal, ROUND_HALF_UP, ROUND_FLOOR, ROUND_CEILING
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums.exam import AssessmentType, AttemptType
from app.common.enums.report_card import CalculationMode, RetestPolicy, RoundingMode
from app.common.exceptions import ValidationException
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.grading.grade_scale import GradeScale
from app.models.student.student import Student
from app.services.attendance_aggregation_service import (
    AttendanceAggregationService,
    attendance_aggregation_service,
)

DECIMAL_ROUNDING_MAP = {
    RoundingMode.ROUND_HALF_UP: ROUND_HALF_UP,
    RoundingMode.ROUND_FLOOR: ROUND_FLOOR,
    RoundingMode.ROUND_CEIL: ROUND_CEILING,
}


class ReportCardCalculationService:
    def __init__(
        self,
        att_service: AttendanceAggregationService = attendance_aggregation_service,
    ) -> None:
        self.attendance_aggregation_service = att_service

    def calculate_student_evaluation(
        self,
        db: Session,
        student: Student,
        academic_year: AcademicYear,
        academic_term: AcademicTerm | None,
        grade_scale: GradeScale,
        evaluation_config: EvaluationConfig,
        preloaded_schedules: list[ExamSchedule] | None = None,
        preloaded_results: dict[tuple[UUID, UUID], list[StudentExamResult]] | None = None,
        preloaded_att_summary: dict[str, int | Decimal] | None = None,
    ) -> dict:
        school_id = student.school_id
        section_id = student.section_id
        dec_rounding = DECIMAL_ROUNDING_MAP.get(
            evaluation_config.rounding_mode, ROUND_HALF_UP
        )

        # 1. Fetch relevant exam schedules if not preloaded
        if preloaded_schedules is not None:
            schedules = [sch for sch in preloaded_schedules if sch.section_id == section_id]
        else:
            schedule_query = (
                select(ExamSchedule)
                .options(joinedload(ExamSchedule.exam), joinedload(ExamSchedule.subject))
                .join(Exam, ExamSchedule.exam_id == Exam.id)
                .where(
                    ExamSchedule.school_id == school_id,
                    ExamSchedule.academic_year_id == academic_year.id,
                    ExamSchedule.section_id == section_id,
                    ExamSchedule.is_deleted.is_(False),
                    Exam.is_deleted.is_(False),
                )
            )

            if academic_term:
                schedule_query = schedule_query.where(
                    (Exam.academic_term_id == academic_term.id)
                    | (
                        Exam.academic_term_id.is_(None)
                        & (Exam.start_date >= academic_term.start_date)
                        & (Exam.end_date <= academic_term.end_date)
                    )
                )

            schedules = list(db.scalars(schedule_query))

        # Weightage validation if WEIGHTED_ASSESSMENT_TYPE
        weightage_map: dict[AssessmentType, Decimal] = {}
        if evaluation_config.calculation_mode == CalculationMode.WEIGHTED_ASSESSMENT_TYPE:
            active_weightages = [
                w for w in evaluation_config.weightages if not w.is_deleted
            ]
            if not active_weightages:
                raise ValidationException("No assessment type weightages configured for evaluation config.")

            total_weight = sum(w.weightage_percentage for w in active_weightages)
            if total_weight != Decimal("100.00"):
                raise ValidationException(
                    f"Assessment type weightages must sum to 100%. Current sum: {total_weight}%"
                )

            weightage_map = {
                w.assessment_type: w.weightage_percentage for w in active_weightages
            }

        # Group schedules by subject_id
        subject_schedules: dict[UUID, list[ExamSchedule]] = {}
        for sch in schedules:
            subject_schedules.setdefault(sch.subject_id, []).append(sch)

        subject_items: list[dict] = []
        overall_max_marks = Decimal("0.00")
        overall_obtained_marks = Decimal("0.00")
        all_subjects_passed = True
        total_grade_points = Decimal("0.00")

        # Sort entries by min_percentage desc for matching
        scale_entries = sorted(
            [e for e in grade_scale.entries if not e.is_deleted],
            key=lambda x: x.min_percentage,
            reverse=True,
        )

        for subject_id, sch_list in subject_schedules.items():
            if not sch_list:
                continue

            first_sch = sch_list[0]
            subj_name = first_sch.subject.subject_name
            subj_code = first_sch.subject.subject_code

            subj_max = Decimal("0.00")
            subj_obtained = Decimal("0.00")

            if evaluation_config.calculation_mode == CalculationMode.SIMPLE_TOTAL:
                for sch in sch_list:
                    subj_max += sch.maximum_marks

                    if preloaded_results is not None:
                        results = preloaded_results.get((student.id, sch.id), [])
                    else:
                        results = list(
                            db.scalars(
                                select(StudentExamResult)
                                .options(
                                    joinedload(StudentExamResult.exam_schedule).joinedload(ExamSchedule.exam)
                                )
                                .where(
                                    StudentExamResult.exam_schedule_id == sch.id,
                                    StudentExamResult.student_id == student.id,
                                    StudentExamResult.is_deleted.is_(False),
                                )
                            )
                        )

                    if not results:
                        continue

                    chosen_result = self._select_result_by_policy(
                        results, evaluation_config.retest_policy
                    )
                    if chosen_result:
                        subj_obtained += chosen_result.marks_obtained

                if subj_max > 0:
                    subj_pct = (subj_obtained / subj_max * Decimal("100.00")).quantize(
                        Decimal("0.01"), rounding=dec_rounding
                    )
                else:
                    subj_pct = Decimal("0.00")

            else:  # WEIGHTED_ASSESSMENT_TYPE
                type_groups: dict[AssessmentType, list[tuple[ExamSchedule, StudentExamResult | None]]] = {}

                for sch in sch_list:
                    atype = sch.exam.assessment_type

                    if preloaded_results is not None:
                        results = preloaded_results.get((student.id, sch.id), [])
                    else:
                        results = list(
                            db.scalars(
                                select(StudentExamResult)
                                .options(
                                    joinedload(StudentExamResult.exam_schedule).joinedload(ExamSchedule.exam)
                                )
                                .where(
                                    StudentExamResult.exam_schedule_id == sch.id,
                                    StudentExamResult.student_id == student.id,
                                    StudentExamResult.is_deleted.is_(False),
                                )
                            )
                        )

                    chosen_result = (
                        self._select_result_by_policy(results, evaluation_config.retest_policy)
                        if results
                        else None
                    )
                    type_groups.setdefault(atype, []).append((sch, chosen_result))

                weighted_pct_sum = Decimal("0.00")
                total_weight_used = Decimal("0.00")

                for atype, items in type_groups.items():
                    if atype not in weightage_map:
                        raise ValidationException(
                            f"Missing weightage configuration for assessment type '{atype.value}'."
                        )

                    t_max = sum(sch.maximum_marks for sch, _ in items)
                    t_obt = sum(res.marks_obtained for _, res in items if res)
                    subj_max += t_max
                    subj_obtained += t_obt

                    if t_max > 0:
                        type_pct = (t_obt / t_max * Decimal("100.00"))
                        weight = weightage_map[atype]
                        weighted_pct_sum += type_pct * (weight / Decimal("100.00"))
                        total_weight_used += weight

                if total_weight_used > 0:
                    if total_weight_used < Decimal("100.00"):
                        subj_pct = (weighted_pct_sum * (Decimal("100.00") / total_weight_used)).quantize(
                            Decimal("0.01"), rounding=dec_rounding
                        )
                    else:
                        subj_pct = weighted_pct_sum.quantize(Decimal("0.01"), rounding=dec_rounding)
                else:
                    subj_pct = Decimal("0.00")

            # Grade matching
            matched_entry = self._match_grade_entry(scale_entries, subj_pct)
            grade_code = matched_entry.grade_code if matched_entry else "N/A"
            grade_point = matched_entry.grade_point if matched_entry else Decimal("0.00")
            is_pass = matched_entry.is_pass if matched_entry else True

            if not is_pass:
                all_subjects_passed = False

            total_grade_points += grade_point
            overall_max_marks += subj_max
            overall_obtained_marks += subj_obtained

            subject_items.append(
                {
                    "subject_id": subject_id,
                    "subject_name": subj_name,
                    "subject_code": subj_code,
                    "max_marks": subj_max,
                    "obtained_marks": subj_obtained,
                    "percentage": subj_pct,
                    "grade_code": grade_code,
                    "grade_point": grade_point,
                    "is_pass": is_pass,
                    "remarks": None,
                }
            )

        # Overall Percentage calculation
        if evaluation_config.calculation_mode == CalculationMode.WEIGHTED_ASSESSMENT_TYPE:
            if len(subject_items) > 0:
                overall_pct = (
                    sum(item["percentage"] for item in subject_items) / Decimal(len(subject_items))
                ).quantize(Decimal("0.01"), rounding=dec_rounding)
            else:
                overall_pct = Decimal("0.00")
        else:
            if overall_max_marks > 0:
                overall_pct = (
                    overall_obtained_marks / overall_max_marks * Decimal("100.00")
                ).quantize(Decimal("0.01"), rounding=dec_rounding)
            else:
                overall_pct = Decimal("0.00")

        overall_matched = self._match_grade_entry(scale_entries, overall_pct)
        overall_grade = overall_matched.grade_code if overall_matched else "N/A"
        overall_grade_point = (
            overall_matched.grade_point if overall_matched else Decimal("0.00")
        )

        gpa = None
        if evaluation_config.gpa_enabled and len(subject_items) > 0:
            gpa = (total_grade_points / Decimal(len(subject_items))).quantize(
                Decimal("0.01"), rounding=ROUND_HALF_UP
            )

        # Attendance calculation
        if preloaded_att_summary is not None:
            att_summary = preloaded_att_summary
        else:
            start_dt = academic_term.start_date if academic_term else academic_year.start_date
            end_dt = academic_term.end_date if academic_term else academic_year.end_date

            att_summary = self.attendance_aggregation_service.calculate_attendance_summary(
                db,
                school_id=school_id,
                section_id=section_id,
                student_id=student.id,
                start_date=start_dt,
                end_date=end_dt,
            )

        return {
            "total_max_marks": overall_max_marks,
            "total_obtained_marks": overall_obtained_marks,
            "percentage": overall_pct,
            "overall_grade": overall_grade,
            "overall_grade_point": overall_grade_point,
            "gpa": gpa,
            "is_passed": all_subjects_passed,
            "total_working_days": att_summary["total_working_days"],
            "present_days": att_summary["present_days"],
            "attendance_percentage": att_summary["attendance_percentage"],
            "items": subject_items,
        }

    def _select_result_by_policy(
        self,
        results: list[StudentExamResult],
        policy: RetestPolicy,
    ) -> StudentExamResult | None:
        if not results:
            return None
        if len(results) == 1:
            return results[0]

        if policy == RetestPolicy.BEST_ATTEMPT:
            return max(results, key=lambda r: r.marks_obtained)
        elif policy == RetestPolicy.LATEST_ATTEMPT:
            return max(results, key=lambda r: r.created_at)
        else:  # REPLACE_ORIGINAL
            # Prefer RETEST / MAKEUP if present
            retest_results = [
                r for r in results if r.exam_schedule and r.exam_schedule.exam.attempt_type != AttemptType.REGULAR
            ]
            if retest_results:
                return retest_results[-1]
            return results[-1]

    def _match_grade_entry(self, sorted_entries, percentage: Decimal):
        for entry in sorted_entries:
            if entry.min_percentage <= percentage <= entry.max_percentage:
                return entry
        return sorted_entries[-1] if sorted_entries else None


report_card_calculation_service = ReportCardCalculationService()
