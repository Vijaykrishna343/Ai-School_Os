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
from app.models.academic_term.academic_term import AcademicTerm
from app.repositories.academic_term.academic_term_repository import (
    AcademicTermRepository,
    academic_term_repository,
)
from app.repositories.academic_year.academic_year_repository import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.schemas.academic_term.academic_term import (
    AcademicTermCreate,
    AcademicTermFilter,
    AcademicTermListResponse,
    AcademicTermResponse,
    AcademicTermUpdate,
)

logger = get_logger(__name__)


class AcademicTermService:
    """
    Business logic service for AcademicTerm operations.
    """

    def __init__(
        self,
        repository: AcademicTermRepository = academic_term_repository,
        school_repo: SchoolRepository = school_repository,
        academic_year_repo: AcademicYearRepository = academic_year_repository,
    ) -> None:
        self.repository = repository
        self.school_repository = school_repo
        self.academic_year_repository = academic_year_repo

    def create_academic_term(
        self,
        db: Session,
        term_data: AcademicTermCreate,
        current_school_id: UUID | None = None,
    ) -> AcademicTerm:
        """
        Create a new AcademicTerm under an AcademicYear.
        Validates tenant isolation, date boundaries, and name/code uniqueness.
        """
        if current_school_id is not None and term_data.school_id != current_school_id:
            raise ForbiddenException("Cannot create academic term for another school.")

        school = self.school_repository.get(db, term_data.school_id)
        if school is None or school.is_deleted:
            raise NotFoundException("School", str(term_data.school_id))

        academic_year = self.academic_year_repository.get(db, term_data.academic_year_id)
        if academic_year is None or academic_year.is_deleted:
            raise NotFoundException("Academic Year", str(term_data.academic_year_id))

        if academic_year.school_id != term_data.school_id:
            raise ValidationException("Academic year must belong to the same school.")

        if term_data.start_date > term_data.end_date:
            raise ValidationException("Term start_date must be before or equal to end_date.")

        if (
            term_data.start_date < academic_year.start_date
            or term_data.end_date > academic_year.end_date
        ):
            raise ValidationException(
                f"Term dates ({term_data.start_date} to {term_data.end_date}) must fall within "
                f"academic year boundaries ({academic_year.start_date} to {academic_year.end_date})."
            )

        if self.repository.exists_by_name(
            db, term_data.academic_year_id, term_data.name
        ):
            raise AlreadyExistsException("AcademicTerm name", term_data.name)

        if self.repository.exists_by_code(
            db, term_data.academic_year_id, term_data.code
        ):
            raise AlreadyExistsException("AcademicTerm code", term_data.code)

        term = AcademicTerm(
            school_id=term_data.school_id,
            academic_year_id=term_data.academic_year_id,
            name=term_data.name.strip(),
            code=term_data.code.strip().upper(),
            start_date=term_data.start_date,
            end_date=term_data.end_date,
            display_order=term_data.display_order,
            is_active=term_data.is_active,
        )

        created = self.repository.create(db, term)
        logger.info(
            "AcademicTerm '%s' (%s) created successfully with ID: %s",
            created.name,
            created.code,
            created.id,
        )
        return created

    def get_academic_term(
        self,
        db: Session,
        term_id: UUID,
        current_school_id: UUID | None = None,
    ) -> AcademicTerm:
        """
        Retrieve an active AcademicTerm by ID for the tenant school.
        """
        if current_school_id:
            term = self.repository.get_by_id_and_school(db, term_id, current_school_id)
        else:
            term = self.repository.get(db, term_id)

        if term is None or term.is_deleted:
            raise NotFoundException("AcademicTerm", str(term_id))

        return term

    def list_academic_terms(
        self,
        db: Session,
        filters: AcademicTermFilter,
        current_school_id: UUID | None = None,
    ) -> AcademicTermListResponse:
        """
        List paginated AcademicTerms for the tenant school.
        """
        school_id = current_school_id or filters.school_id
        if not school_id:
            raise ValidationException("Authenticated user is not associated with a school.")

        items, total = self.repository.list_by_school(db, school_id, filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return AcademicTermListResponse(
            items=[AcademicTermResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_academic_term(
        self,
        db: Session,
        term_id: UUID,
        term_data: AcademicTermUpdate,
        current_school_id: UUID | None = None,
    ) -> AcademicTerm:
        """
        Update an existing AcademicTerm.
        """
        term = self.get_academic_term(db, term_id, current_school_id)
        update_dict = term_data.model_dump(exclude_unset=True)

        academic_year = self.academic_year_repository.get(db, term.academic_year_id)

        new_start_date = update_dict.get("start_date", term.start_date)
        new_end_date = update_dict.get("end_date", term.end_date)

        if new_start_date > new_end_date:
            raise ValidationException("Term start_date must be before or equal to end_date.")

        if academic_year:
            if (
                new_start_date < academic_year.start_date
                or new_end_date > academic_year.end_date
            ):
                raise ValidationException(
                    f"Term dates ({new_start_date} to {new_end_date}) must fall within "
                    f"academic year boundaries ({academic_year.start_date} to {academic_year.end_date})."
                )

        if "name" in update_dict and update_dict["name"] is not None:
            new_name = update_dict["name"].strip()
            if new_name.lower() != term.name.lower() and self.repository.exists_by_name(
                db, term.academic_year_id, new_name, exclude_id=term_id
            ):
                raise AlreadyExistsException("AcademicTerm name", new_name)
            term.name = new_name

        if "code" in update_dict and update_dict["code"] is not None:
            new_code = update_dict["code"].strip().upper()
            if new_code != term.code and self.repository.exists_by_code(
                db, term.academic_year_id, new_code, exclude_id=term_id
            ):
                raise AlreadyExistsException("AcademicTerm code", new_code)
            term.code = new_code

        if "start_date" in update_dict:
            term.start_date = new_start_date
        if "end_date" in update_dict:
            term.end_date = new_end_date
        if "display_order" in update_dict and update_dict["display_order"] is not None:
            term.display_order = update_dict["display_order"]
        if "is_active" in update_dict and update_dict["is_active"] is not None:
            term.is_active = update_dict["is_active"]

        updated = self.repository.update(db, term)
        logger.info("AcademicTerm ID: %s updated successfully", term_id)
        return updated

    def delete_academic_term(
        self,
        db: Session,
        term_id: UUID,
        current_school_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> None:
        """
        Soft delete an AcademicTerm.
        """
        term = self.get_academic_term(db, term_id, current_school_id)
        if current_user_id:
            term.deleted_by_user_id = current_user_id

        self.repository.delete(db, term)
        logger.info("AcademicTerm ID: %s soft deleted successfully", term_id)


academic_term_service = AcademicTermService(
    repository=academic_term_repository,
    school_repo=school_repository,
    academic_year_repo=academic_year_repository,
)
