from datetime import datetime, timezone
from decimal import Decimal
from math import ceil
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.common.enums.report_card import ReportCardStatus
from app.common.exceptions import (
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year.academic_year import AcademicYear
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.exam.student_exam_result import StudentExamResult
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.grading.grade_scale import GradeScale
from app.models.grading.report_card import ReportCard
from app.models.grading.report_card_item_snapshot import ReportCardItemSnapshot
from app.models.student.student import Student
from app.repositories.academic_term.academic_term_repository import (
    AcademicTermRepository,
    academic_term_repository,
)
from app.repositories.academic_year.academic_year_repository import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.grading.evaluation_config_repository import (
    EvaluationConfigRepository,
    evaluation_config_repository,
)
from app.repositories.grading.grade_scale_repository import (
    GradeScaleRepository,
    grade_scale_repository,
)
from app.repositories.grading.report_card_repository import (
    ReportCardRepository,
    report_card_repository,
)
from app.repositories.student.student_repository import (
    StudentRepository,
    student_repository,
)
from app.schemas.grading.report_card import (
    ReportCardFilter,
    ReportCardGenerateRequest,
    ReportCardListResponse,
    ReportCardRemarksUpdate,
    ReportCardResponse,
)
from app.services.report_card_calculation_service import (
    ReportCardCalculationService,
    report_card_calculation_service,
)

logger = get_logger(__name__)


class ReportCardService:
    def __init__(
        self,
        repository: ReportCardRepository = report_card_repository,
        calculation_service: ReportCardCalculationService = report_card_calculation_service,
        student_repo: StudentRepository = student_repository,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
        academic_term_repo: AcademicTermRepository = academic_term_repository,
        grade_scale_repo: GradeScaleRepository = grade_scale_repository,
        eval_config_repo: EvaluationConfigRepository = evaluation_config_repository,
    ) -> None:
        self.repository = repository
        self.calculation_service = calculation_service
        self.student_repository = student_repo
        self.academic_year_repository = academic_year_repo
        self.academic_term_repository = academic_term_repo
        self.grade_scale_repository = grade_scale_repo
        self.evaluation_config_repository = eval_config_repo

    def generate_report_cards(
        self,
        db: Session,
        request_data: ReportCardGenerateRequest,
        current_school_id: UUID | None = None,
    ) -> list[ReportCard]:
        if current_school_id and request_data.school_id != current_school_id:
            raise ForbiddenException("Cannot generate report cards for another school.")

        school_id = request_data.school_id
        ay = self.academic_year_repository.get(db, request_data.academic_year_id)
        if not ay or ay.school_id != school_id or ay.is_deleted:
            raise NotFoundException("Academic Year", str(request_data.academic_year_id))

        term = None
        if request_data.academic_term_id:
            term = self.academic_term_repository.get(db, request_data.academic_term_id)
            if not term or term.school_id != school_id or term.is_deleted:
                raise NotFoundException("Academic Term", str(request_data.academic_term_id))

        grade_scale = None
        if request_data.grade_scale_id:
            grade_scale = self.grade_scale_repository.get_by_id_and_school(
                db, request_data.grade_scale_id, school_id
            )
        else:
            grade_scale = self.grade_scale_repository.get_default_by_school(db, school_id)

        if not grade_scale:
            raise ValidationException("No active grade scale found for school.")

        eval_config = None
        if request_data.evaluation_config_id:
            eval_config = self.evaluation_config_repository.get_by_id_and_school(
                db, request_data.evaluation_config_id, school_id
            )
        else:
            eval_config = self.evaluation_config_repository.get_default_for_year(
                db, school_id, ay.id
            )

        if not eval_config:
            eval_config = EvaluationConfig(
                school_id=school_id,
                academic_year_id=ay.id,
                name="Default Evaluation Config",
                is_default=True,
            )
            db.add(eval_config)
            db.flush()

        # Identify target students
        students: list[Student] = []
        if request_data.student_id:
            student = self.student_repository.get_by_id(db, request_data.student_id)
            if student and student.school_id == school_id and not student.is_deleted:
                students.append(student)
        elif request_data.section_id:
            query = select(Student).where(
                Student.school_id == school_id,
                Student.section_id == request_data.section_id,
                Student.is_deleted.is_(False),
            )
            students = list(db.scalars(query))
        elif request_data.school_class_id:
            query = select(Student).where(
                Student.school_id == school_id,
                Student.school_class_id == request_data.school_class_id,
                Student.is_deleted.is_(False),
            )
            students = list(db.scalars(query))

        if not students:
            raise ValidationException("No eligible students found for report card generation.")

        student_ids = [s.id for s in students]
        section_ids = list({s.section_id for s in students})

        # 1. Batch fetch existing report cards
        existing_cards_stmt = select(ReportCard).where(
            ReportCard.school_id == school_id,
            ReportCard.academic_year_id == ay.id,
            ReportCard.student_id.in_(student_ids),
            ReportCard.is_deleted.is_(False),
        )
        if term:
            existing_cards_stmt = existing_cards_stmt.where(ReportCard.academic_term_id == term.id)
        else:
            existing_cards_stmt = existing_cards_stmt.where(ReportCard.academic_term_id.is_(None))

        existing_cards = list(db.scalars(existing_cards_stmt))
        existing_cards_map: dict[UUID, ReportCard] = {c.student_id: c for c in existing_cards}

        # Validate status of existing report cards
        for c in existing_cards:
            if c.status in [ReportCardStatus.FINALIZED, ReportCardStatus.PUBLISHED]:
                st = next((s for s in students if s.id == c.student_id), None)
                st_name = st.full_name if st else str(c.student_id)
                raise ValidationException(
                    f"Report card for student '{st_name}' is already {c.status.value} and cannot be regenerated."
                )

        # 2. Batch fetch relevant exam schedules
        schedule_query = (
            select(ExamSchedule)
            .options(joinedload(ExamSchedule.exam), joinedload(ExamSchedule.subject))
            .join(Exam, ExamSchedule.exam_id == Exam.id)
            .where(
                ExamSchedule.school_id == school_id,
                ExamSchedule.academic_year_id == ay.id,
                ExamSchedule.section_id.in_(section_ids),
                ExamSchedule.is_deleted.is_(False),
                Exam.is_deleted.is_(False),
            )
        )
        if term:
            schedule_query = schedule_query.where(
                (Exam.academic_term_id == term.id)
                | (
                    Exam.academic_term_id.is_(None)
                    & (Exam.start_date >= term.start_date)
                    & (Exam.end_date <= term.end_date)
                )
            )
        all_schedules = list(db.scalars(schedule_query))
        all_schedule_ids = [sch.id for sch in all_schedules]

        # 3. Batch fetch all StudentExamResults for students & schedules
        results_map: dict[tuple[UUID, UUID], list[StudentExamResult]] = {}
        if all_schedule_ids:
            results_stmt = (
                select(StudentExamResult)
                .options(joinedload(StudentExamResult.exam_schedule).joinedload(ExamSchedule.exam))
                .where(
                    StudentExamResult.student_id.in_(student_ids),
                    StudentExamResult.exam_schedule_id.in_(all_schedule_ids),
                    StudentExamResult.is_deleted.is_(False),
                )
            )
            all_results = list(db.scalars(results_stmt))
            for res in all_results:
                results_map.setdefault((res.student_id, res.exam_schedule_id), []).append(res)

        # 4. Batch fetch attendance summaries
        start_dt = term.start_date if term else ay.start_date
        end_dt = term.end_date if term else ay.end_date

        att_summaries_by_student: dict[UUID, dict[str, int | Decimal]] = {}
        for sec_id in section_ids:
            sec_student_ids = [s.id for s in students if s.section_id == sec_id]
            sec_summaries = self.calculation_service.attendance_aggregation_service.calculate_bulk_attendance_summaries(
                db,
                school_id=school_id,
                section_id=sec_id,
                student_ids=sec_student_ids,
                start_date=start_dt,
                end_date=end_dt,
            )
            att_summaries_by_student.update(sec_summaries)

        generated_cards: list[ReportCard] = []

        for student in students:
            existing = existing_cards_map.get(student.id)
            att_summary = att_summaries_by_student.get(
                student.id,
                {
                    "total_working_days": 0,
                    "present_days": 0,
                    "attendance_percentage": Decimal("0.00"),
                },
            )

            calc = self.calculation_service.calculate_student_evaluation(
                db,
                student=student,
                academic_year=ay,
                academic_term=term,
                grade_scale=grade_scale,
                evaluation_config=eval_config,
                preloaded_schedules=all_schedules,
                preloaded_results=results_map,
                preloaded_att_summary=att_summary,
            )

            if existing:
                existing.grade_scale_id = grade_scale.id
                existing.evaluation_config_id = eval_config.id
                existing.total_max_marks = calc["total_max_marks"]
                existing.total_obtained_marks = calc["total_obtained_marks"]
                existing.percentage = calc["percentage"]
                existing.overall_grade = calc["overall_grade"]
                existing.overall_grade_point = calc["overall_grade_point"]
                existing.gpa = calc["gpa"]
                existing.is_passed = calc["is_passed"]
                existing.total_working_days = calc["total_working_days"]
                existing.present_days = calc["present_days"]
                existing.attendance_percentage = calc["attendance_percentage"]

                existing.items.clear()
                for item_dict in calc["items"]:
                    existing.items.append(ReportCardItemSnapshot(**item_dict))

                updated = self.repository.update(db, existing)
                generated_cards.append(updated)
            else:
                card = ReportCard(
                    school_id=school_id,
                    academic_year_id=ay.id,
                    academic_term_id=term.id if term else None,
                    student_id=student.id,
                    school_class_id=student.school_class_id,
                    section_id=student.section_id,
                    grade_scale_id=grade_scale.id,
                    evaluation_config_id=eval_config.id,
                    status=ReportCardStatus.DRAFT,
                    total_max_marks=calc["total_max_marks"],
                    total_obtained_marks=calc["total_obtained_marks"],
                    percentage=calc["percentage"],
                    overall_grade=calc["overall_grade"],
                    overall_grade_point=calc["overall_grade_point"],
                    gpa=calc["gpa"],
                    is_passed=calc["is_passed"],
                    total_working_days=calc["total_working_days"],
                    present_days=calc["present_days"],
                    attendance_percentage=calc["attendance_percentage"],
                )
                for item_dict in calc["items"]:
                    card.items.append(ReportCardItemSnapshot(**item_dict))

                created = self.repository.create(db, card)
                generated_cards.append(created)

        logger.info(
            "Generated %d report cards for school ID: %s",
            len(generated_cards),
            school_id,
        )
        return generated_cards

    def get_report_card(
        self,
        db: Session,
        report_card_id: UUID,
        current_school_id: UUID | None = None,
    ) -> ReportCard:
        if current_school_id:
            card = self.repository.get_by_id_and_school(db, report_card_id, current_school_id)
        else:
            card = self.repository.get(db, report_card_id)

        if not card or card.is_deleted:
            raise NotFoundException("Report Card", str(report_card_id))
        return card

    def list_report_cards(
        self,
        db: Session,
        filters: ReportCardFilter,
        current_school_id: UUID | None = None,
    ) -> ReportCardListResponse:
        school_id = current_school_id or filters.school_id
        if not school_id:
            raise ValidationException("Authenticated user is not associated with a school.")

        items, total = self.repository.list_by_school(db, school_id, filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return ReportCardListResponse(
            items=[ReportCardResponse.model_validate(card) for card in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_remarks(
        self,
        db: Session,
        report_card_id: UUID,
        remarks_data: ReportCardRemarksUpdate,
        current_school_id: UUID | None = None,
    ) -> ReportCard:
        card = self.get_report_card(db, report_card_id, current_school_id)
        if remarks_data.teacher_remarks is not None:
            card.teacher_remarks = remarks_data.teacher_remarks
        if remarks_data.principal_remarks is not None:
            card.principal_remarks = remarks_data.principal_remarks

        return self.repository.update(db, card)

    def finalize_report_card(
        self,
        db: Session,
        report_card_id: UUID,
        current_user_id: UUID,
        current_school_id: UUID | None = None,
    ) -> ReportCard:
        card = self.get_report_card(db, report_card_id, current_school_id)
        if card.status != ReportCardStatus.DRAFT:
            raise ValidationException(f"Cannot finalize report card in status '{card.status.value}'.")

        card.status = ReportCardStatus.FINALIZED
        card.finalized_at = datetime.now(timezone.utc)
        card.finalized_by_user_id = current_user_id

        updated = self.repository.update(db, card)
        logger.info("Report card ID: %s finalized by user ID: %s", report_card_id, current_user_id)
        return updated

    def publish_report_card(
        self,
        db: Session,
        report_card_id: UUID,
        current_user_id: UUID,
        current_school_id: UUID | None = None,
    ) -> ReportCard:
        card = self.get_report_card(db, report_card_id, current_school_id)
        if card.status == ReportCardStatus.PUBLISHED:
            return card

        card.status = ReportCardStatus.PUBLISHED
        card.published_at = datetime.now(timezone.utc)
        card.published_by_user_id = current_user_id

        updated = self.repository.update(db, card)
        logger.info("Report card ID: %s published by user ID: %s", report_card_id, current_user_id)
        return updated


report_card_service = ReportCardService()
