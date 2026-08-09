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
from app.models.exam.exam import Exam
from app.repositories.academic_year import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.exam.exam_repository import (
    ExamRepository,
    exam_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.exam.exam import (
    ExamCreate,
    ExamFilter,
    ExamListResponse,
    ExamResponse,
    ExamUpdate,
)

logger = get_logger(__name__)


class ExamService:
    """
    Business logic service for Exam operations.
    """

    def __init__(
        self,
        repository: ExamRepository,
        school_repo: SchoolRepository,
        academic_year_repo: AcademicYearRepository,
    ) -> None:
        self.repository = repository
        self.school_repository = school_repo
        self.academic_year_repository = academic_year_repo

    def create_exam(
        self,
        db: Session,
        exam_data: ExamCreate,
        current_school_id: UUID | None = None,
    ) -> Exam:
        """
        Create a new exam entity.
        Enforces tenant boundary, date ordering, entity existence, and name uniqueness.
        """
        if (
            current_school_id is not None
            and exam_data.school_id != current_school_id
        ):
            logger.warning(
                "Tenant mismatch: User school '%s' tried creating exam for school '%s'",
                current_school_id,
                exam_data.school_id,
            )
            raise ForbiddenException("Cannot create exam for another school.")

        school = self.school_repository.get(db, exam_data.school_id)
        if school is None:
            raise NotFoundException("School", str(exam_data.school_id))

        academic_year = self.academic_year_repository.get(
            db,
            exam_data.academic_year_id,
        )
        if academic_year is None:
            raise NotFoundException(
                "Academic Year",
                str(exam_data.academic_year_id),
            )
        if academic_year.school_id != exam_data.school_id:
            raise ValidationException(
                "Academic year must belong to the same school."
            )

        if exam_data.start_date > exam_data.end_date:
            raise ValidationException(
                "Exam start_date must be before or equal to end_date."
            )

        if self.repository.exists_by_name(
            db,
            exam_data.school_id,
            exam_data.academic_year_id,
            exam_data.name,
        ):
            raise AlreadyExistsException("Exam", exam_data.name)

        exam = Exam(**exam_data.model_dump())
        created = self.repository.create(db, exam)
        logger.info("Exam '%s' created successfully with ID: %s", created.name, created.id)
        return created

    def get_exam(
        self,
        db: Session,
        exam_id: UUID,
        school_id: UUID | None = None,
    ) -> Exam:
        """
        Get active exam by ID, optionally scoped to school_id tenant.
        """
        if school_id is not None:
            exam = self.repository.get_by_id_and_school(
                db,
                exam_id,
                school_id,
            )
        else:
            exam = self.repository.get(db, exam_id)

        if exam is None or exam.is_deleted:
            raise NotFoundException("Exam", str(exam_id))

        return exam

    def get_exams(
        self,
        db: Session,
        filters: ExamFilter,
    ) -> ExamListResponse:
        """
        Get paginated exams list matching filter parameters.
        """
        items, total = self.repository.list(db, filters)
        total_pages = (
            ceil(total / filters.page_size) if total > 0 else 0
        )
        return ExamListResponse(
            items=[ExamResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_exam(
        self,
        db: Session,
        exam_id: UUID,
        exam_data: ExamUpdate,
        school_id: UUID | None = None,
    ) -> Exam:
        """
        Update an existing exam.
        """
        exam = self.get_exam(db, exam_id, school_id=school_id)
        update_data = exam_data.model_dump(exclude_unset=True)

        new_start_date = update_data.get("start_date", exam.start_date)
        new_end_date = update_data.get("end_date", exam.end_date)
        if new_start_date > new_end_date:
            raise ValidationException(
                "Exam start_date must be before or equal to end_date."
            )

        if (
            "name" in update_data
            and update_data["name"] != exam.name
        ):
            if self.repository.exists_by_name(
                db,
                exam.school_id,
                exam.academic_year_id,
                update_data["name"],
            ):
                raise AlreadyExistsException("Exam", update_data["name"])

        for key, value in update_data.items():
            setattr(exam, key, value)

        updated = self.repository.update(db, exam)
        logger.info("Exam ID: %s updated successfully", exam_id)
        return updated

    def delete_exam(
        self,
        db: Session,
        exam_id: UUID,
        school_id: UUID | None = None,
    ) -> None:
        """
        Soft delete an exam.
        """
        exam = self.get_exam(db, exam_id, school_id=school_id)
        self.repository.delete(db, exam)
        logger.info("Exam ID: %s soft deleted successfully", exam_id)


exam_service = ExamService(
    repository=exam_repository,
    school_repo=school_repository,
    academic_year_repo=academic_year_repository,
)
