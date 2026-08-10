from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.enums import StudentStatus
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.exam.student_exam_result import StudentExamResult
from app.repositories.exam.exam_schedule_repository import (
    ExamScheduleRepository,
    exam_schedule_repository,
)
from app.repositories.exam.student_exam_result_repository import (
    StudentExamResultRepository,
    student_exam_result_repository,
)
from app.repositories.student.student_repository import (
    StudentRepository,
    student_repository,
)
from app.schemas.exam.student_exam_result import (
    StudentExamResultCreate,
    StudentExamResultFilter,
    StudentExamResultListResponse,
    StudentExamResultResponse,
    StudentExamResultUpdate,
)

logger = get_logger(__name__)


class StudentExamResultService:
    """
    Business logic service for StudentExamResult operations.
    """

    def __init__(
        self,
        repository: StudentExamResultRepository = student_exam_result_repository,
        exam_schedule_repo: ExamScheduleRepository = exam_schedule_repository,
        student_repo: StudentRepository = student_repository,
    ) -> None:
        self.repository = repository
        self.exam_schedule_repository = exam_schedule_repo
        self.student_repository = student_repo

    def create_student_exam_result(
        self,
        db: Session,
        result_data: StudentExamResultCreate,
        current_school_id: UUID | None = None,
    ) -> StudentExamResult:
        """
        Create a new student exam result.
        Enforces tenant boundary, entity relationships, status, marks validation, and duplicate prevention.
        """
        if not current_school_id:
            raise ValidationException(
                "Authenticated user is not associated with a school."
            )

        schedule = self.exam_schedule_repository.get(
            db, result_data.exam_schedule_id
        )
        if schedule is None or schedule.is_deleted:
            raise NotFoundException(
                "ExamSchedule", str(result_data.exam_schedule_id)
            )

        if schedule.school_id != current_school_id:
            raise ValidationException(
                "Exam schedule must belong to the user's school."
            )

        student = self.student_repository.get(db, result_data.student_id)
        if student is None or student.is_deleted:
            raise NotFoundException("Student", str(result_data.student_id))

        if student.school_id != current_school_id:
            raise ValidationException(
                "Student must belong to the user's school."
            )

        if student.status != StudentStatus.ACTIVE:
            raise ValidationException(
                f"Cannot record result for inactive student '{student.full_name}'."
            )

        if student.academic_year_id != schedule.academic_year_id:
            raise ValidationException(
                "Student must belong to the same academic year as the exam schedule."
            )

        if student.school_class_id != schedule.school_class_id:
            raise ValidationException(
                "Student must belong to the same class as the exam schedule."
            )

        if student.section_id != schedule.section_id:
            raise ValidationException(
                "Student must belong to the same section as the exam schedule."
            )

        if result_data.marks_obtained < 0:
            raise ValidationException("Marks obtained cannot be negative.")

        if result_data.marks_obtained > schedule.maximum_marks:
            raise ValidationException(
                "Marks obtained cannot exceed maximum marks of the exam schedule."
            )

        if self.repository.exists_active_result(
            db,
            exam_schedule_id=schedule.id,
            student_id=student.id,
        ):
            raise AlreadyExistsException(
                "StudentExamResult",
                f"exam_schedule_id={schedule.id}, student_id={student.id}",
            )

        result = StudentExamResult(**result_data.model_dump())
        created = self.repository.create(db, result)
        logger.info(
            "StudentExamResult created successfully with ID: %s", created.id
        )
        return created

    def get_student_exam_result(
        self,
        db: Session,
        result_id: UUID,
        school_id: UUID | None = None,
    ) -> StudentExamResult:
        """
        Get active student exam result by ID, optionally scoped to school_id.
        """
        if school_id is not None:
            result = self.repository.get_by_id_and_school(
                db,
                result_id,
                school_id,
            )
        else:
            result = self.repository.get(db, result_id)

        if result is None or result.is_deleted:
            raise NotFoundException("StudentExamResult", str(result_id))

        return result

    def get_student_exam_results(
        self,
        db: Session,
        filters: StudentExamResultFilter,
        school_id: UUID | None = None,
    ) -> StudentExamResultListResponse:
        """
        Get paginated student exam results matching filter parameters.
        Enforces tenant boundary using school_id.
        """
        if school_id is None:
            raise ValidationException(
                "School ID is required for tenant isolation."
            )

        filters.school_id = school_id


        items, total = self.repository.list(db, filters)
        total_pages = (
            ceil(total / filters.page_size) if total > 0 else 0
        )
        return StudentExamResultListResponse(
            items=[
                StudentExamResultResponse.model_validate(item)
                for item in items
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )


    def update_student_exam_result(
        self,
        db: Session,
        result_id: UUID,
        result_data: StudentExamResultUpdate,
        school_id: UUID | None = None,
    ) -> StudentExamResult:
        """
        Update an existing student exam result.
        """
        result = self.get_student_exam_result(db, result_id, school_id=school_id)
        update_data = result_data.model_dump(exclude_unset=True)

        if "marks_obtained" in update_data and update_data["marks_obtained"] is not None:
            new_marks = update_data["marks_obtained"]
            if new_marks < 0:
                raise ValidationException("Marks obtained cannot be negative.")

            schedule = self.exam_schedule_repository.get(
                db, result.exam_schedule_id
            )
            if schedule and new_marks > schedule.maximum_marks:
                raise ValidationException(
                    "Marks obtained cannot exceed maximum marks of the exam schedule."
                )

        for key, value in update_data.items():
            setattr(result, key, value)

        updated = self.repository.update(db, result)
        logger.info(
            "StudentExamResult ID: %s updated successfully", result_id
        )
        return updated

    def delete_student_exam_result(
        self,
        db: Session,
        result_id: UUID,
        school_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a student exam result.
        """
        result = self.get_student_exam_result(db, result_id, school_id=school_id)
        if current_user_id:
            result.deleted_by_user_id = current_user_id
        self.repository.delete(db, result)
        logger.info(
            "StudentExamResult ID: %s soft deleted successfully", result_id
        )


student_exam_result_service = StudentExamResultService(
    repository=student_exam_result_repository,
    exam_schedule_repo=exam_schedule_repository,
    student_repo=student_repository,
)
