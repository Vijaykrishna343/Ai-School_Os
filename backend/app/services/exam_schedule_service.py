from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.exam.exam_schedule import ExamSchedule
from app.repositories.academic_year import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.exam.exam_repository import (
    ExamRepository,
    exam_repository,
)
from app.repositories.exam.exam_schedule_repository import (
    ExamScheduleRepository,
    exam_schedule_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.section import (
    SectionRepository,
    section_repository,
)
from app.repositories.subject import (
    SubjectRepository,
    subject_repository,
)
from app.schemas.exam.exam_schedule import (
    ExamScheduleCreate,
    ExamScheduleFilter,
    ExamScheduleListResponse,
    ExamScheduleResponse,
    ExamScheduleUpdate,
)

logger = get_logger(__name__)


class ExamScheduleService:
    """
    Business logic service for ExamSchedule operations.
    """

    def __init__(
        self,
        repository: ExamScheduleRepository,
        exam_repo: ExamRepository,
        school_repo: SchoolRepository,
        academic_year_repo: AcademicYearRepository,
        class_repo: SchoolClassRepository,
        section_repo: SectionRepository,
        subject_repo: SubjectRepository,
    ) -> None:
        self.repository = repository
        self.exam_repository = exam_repo
        self.school_repository = school_repo
        self.academic_year_repository = academic_year_repo
        self.school_class_repository = class_repo
        self.section_repository = section_repo
        self.subject_repository = subject_repo

    def create_exam_schedule(
        self,
        db: Session,
        schedule_data: ExamScheduleCreate,
        current_school_id: UUID | None = None,
    ) -> ExamSchedule:
        """
        Create a new exam schedule.
        Enforces tenant boundary, entity relationships, time boundaries, marks validation, and duplicate prevention.
        """
        if (
            current_school_id is not None
            and schedule_data.school_id != current_school_id
        ):
            logger.warning(
                "Tenant mismatch: User school '%s' tried creating exam schedule for school '%s'",
                current_school_id,
                schedule_data.school_id,
            )
            raise ForbiddenException(
                "Cannot create exam schedule for another school."
            )

        school = self.school_repository.get(db, schedule_data.school_id)
        if school is None:
            raise NotFoundException("School", str(schedule_data.school_id))

        academic_year = self.academic_year_repository.get(
            db,
            schedule_data.academic_year_id,
        )
        if academic_year is None:
            raise NotFoundException(
                "Academic Year",
                str(schedule_data.academic_year_id),
            )
        if academic_year.school_id != schedule_data.school_id:
            raise ValidationException(
                "Academic year must belong to the specified school."
            )

        exam = self.exam_repository.get(db, schedule_data.exam_id)
        if exam is None:
            raise NotFoundException("Exam", str(schedule_data.exam_id))
        if exam.school_id != schedule_data.school_id:
            raise ValidationException(
                "Exam must belong to the specified school."
            )
        if exam.academic_year_id != schedule_data.academic_year_id:
            raise ValidationException(
                "Exam must belong to the specified academic year."
            )

        school_class = self.school_class_repository.get(
            db,
            schedule_data.school_class_id,
        )
        if school_class is None:
            raise NotFoundException(
                "School Class",
                str(schedule_data.school_class_id),
            )
        if school_class.school_id != schedule_data.school_id:
            raise ValidationException(
                "Class must belong to the specified school."
            )

        section = self.section_repository.get(db, schedule_data.section_id)
        if section is None:
            raise NotFoundException("Section", str(schedule_data.section_id))
        if section.school_class_id != schedule_data.school_class_id:
            raise ValidationException(
                "Section must belong to the specified class."
            )

        subject = self.subject_repository.get(db, schedule_data.subject_id)
        if subject is None:
            raise NotFoundException("Subject", str(schedule_data.subject_id))
        if subject.school_id != schedule_data.school_id:
            raise ValidationException(
                "Subject must belong to the specified school."
            )

        if schedule_data.exam_date < exam.start_date or schedule_data.exam_date > exam.end_date:
            raise ValidationException(
                "Schedule exam_date must fall within the exam start_date and end_date."
            )

        if schedule_data.start_time >= schedule_data.end_time:
            raise ValidationException(
                "Schedule start_time must be before end_time."
            )

        if schedule_data.maximum_marks <= 0:
            raise ValidationException(
                "Maximum marks must be greater than zero."
            )

        if schedule_data.passing_marks < 0:
            raise ValidationException(
                "Passing marks cannot be negative."
            )

        if schedule_data.passing_marks > schedule_data.maximum_marks:
            raise ValidationException(
                "Passing marks cannot exceed maximum marks."
            )


        if self.repository.exists_active_schedule(
            db,
            exam_id=schedule_data.exam_id,
            section_id=schedule_data.section_id,
            subject_id=schedule_data.subject_id,
            exam_date=schedule_data.exam_date,
        ):
            raise AlreadyExistsException(
                "ExamSchedule",
                f"exam={schedule_data.exam_id}, section={schedule_data.section_id}, subject={schedule_data.subject_id}, date={schedule_data.exam_date}",
            )

        schedule = ExamSchedule(**schedule_data.model_dump())
        created = self.repository.create(db, schedule)
        logger.info("ExamSchedule created successfully with ID: %s", created.id)
        return created

    def get_exam_schedule(
        self,
        db: Session,
        schedule_id: UUID,
        school_id: UUID | None = None,
    ) -> ExamSchedule:
        """
        Get active exam schedule by ID, optionally scoped to school_id.
        """
        if school_id is not None:
            schedule = self.repository.get_by_id_and_school(
                db,
                schedule_id,
                school_id,
            )
        else:
            schedule = self.repository.get(db, schedule_id)

        if schedule is None or schedule.is_deleted:
            raise NotFoundException("ExamSchedule", str(schedule_id))

        return schedule

    def get_exam_schedules(
        self,
        db: Session,
        filters: ExamScheduleFilter,
    ) -> ExamScheduleListResponse:
        """
        Get paginated exam schedules matching filter parameters.
        """
        items, total = self.repository.list(db, filters)
        total_pages = (
            ceil(total / filters.page_size) if total > 0 else 0
        )
        return ExamScheduleListResponse(
            items=[ExamScheduleResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_exam_schedule(
        self,
        db: Session,
        schedule_id: UUID,
        schedule_data: ExamScheduleUpdate,
        school_id: UUID | None = None,
    ) -> ExamSchedule:
        """
        Update an existing exam schedule.
        """
        schedule = self.get_exam_schedule(db, schedule_id, school_id=school_id)
        update_data = schedule_data.model_dump(exclude_unset=True)

        new_start_time = update_data.get("start_time", schedule.start_time)
        new_end_time = update_data.get("end_time", schedule.end_time)
        if new_start_time >= new_end_time:
            raise ValidationException(
                "Schedule start_time must be before end_time."
            )

        new_max_marks = update_data.get("maximum_marks", schedule.maximum_marks)
        new_pass_marks = update_data.get("passing_marks", schedule.passing_marks)
        if new_pass_marks > new_max_marks:
            raise ValidationException(
                "Passing marks cannot exceed maximum marks."
            )

        new_date = update_data.get("exam_date", schedule.exam_date)
        if (
            new_date != schedule.exam_date
            and self.repository.exists_active_schedule(
                db,
                exam_id=schedule.exam_id,
                section_id=schedule.section_id,
                subject_id=schedule.subject_id,
                exam_date=new_date,
                exclude_schedule_id=schedule.id,
            )
        ):
            raise AlreadyExistsException(
                "ExamSchedule",
                f"exam={schedule.exam_id}, section={schedule.section_id}, subject={schedule.subject_id}, date={new_date}",
            )

        for key, value in update_data.items():
            setattr(schedule, key, value)

        updated = self.repository.update(db, schedule)
        logger.info("ExamSchedule ID: %s updated successfully", schedule_id)
        return updated

    def delete_exam_schedule(
        self,
        db: Session,
        schedule_id: UUID,
        school_id: UUID | None = None,
    ) -> None:
        """
        Soft delete an exam schedule.
        """
        schedule = self.get_exam_schedule(db, schedule_id, school_id=school_id)
        self.repository.delete(db, schedule)
        logger.info("ExamSchedule ID: %s soft deleted successfully", schedule_id)


exam_schedule_service = ExamScheduleService(
    repository=exam_schedule_repository,
    exam_repo=exam_repository,
    school_repo=school_repository,
    academic_year_repo=academic_year_repository,
    class_repo=school_class_repository,
    section_repo=section_repository,
    subject_repo=subject_repository,
)
