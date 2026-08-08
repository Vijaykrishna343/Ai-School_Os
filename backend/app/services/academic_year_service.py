from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.academic_year import AcademicYear
from app.repositories.academic_year import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.academic_year import (
    AcademicYearCreate,
    AcademicYearUpdate,
)

logger = get_logger(__name__)


class AcademicYearService:
    """
    Business logic for Academic Year operations.
    """

    def __init__(
        self,
        repository: AcademicYearRepository,
        school_repository: SchoolRepository,
    ) -> None:
        """
        Initialize AcademicYearService with repositories.
        """
        self.repository = repository
        self.school_repository = school_repository

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create_academic_year(
        self,
        db: Session,
        academic_year_data: AcademicYearCreate,
    ) -> AcademicYear:
        """
        Create a new academic year entity.
        """
        logger.info(
            "Creating academic year '%s' for school ID: %s",
            academic_year_data.name,
            academic_year_data.school_id,
        )

        school = self.school_repository.get(
            db,
            academic_year_data.school_id,
        )

        if school is None:
            logger.warning(
                "Validation failure: School ID '%s' not found for academic year creation",
                academic_year_data.school_id,
            )
            raise NotFoundException(
                "School",
                str(academic_year_data.school_id),
            )

        if self.repository.exists_by_name(
            db,
            academic_year_data.school_id,
            academic_year_data.name,
        ):
            logger.warning(
                "Validation failure: Academic year name '%s' already exists for school ID: %s",
                academic_year_data.name,
                academic_year_data.school_id,
            )
            raise AlreadyExistsException(
                "Academic Year",
                academic_year_data.name,
            )

        if academic_year_data.start_date >= academic_year_data.end_date:
            logger.warning("Validation failure: Start date >= end date")
            raise ValidationException(
                "Start date must be before end date."
            )

        if academic_year_data.is_current:
            current = self.repository.get_current(
                db,
                academic_year_data.school_id,
            )

            if current is not None:
                current.is_current = False
                self.repository.update(
                    db,
                    current,
                )

        academic_year = AcademicYear(
            **academic_year_data.model_dump()
        )

        created = self.repository.create(
            db,
            academic_year,
        )
        logger.info("Academic year '%s' created successfully with ID: %s", created.name, created.id)
        return created

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
    ) -> AcademicYear:
        """
        Get an academic year by ID or raise NotFoundException.
        """
        academic_year = self.repository.get(
            db,
            academic_year_id,
        )

        if academic_year is None:
            logger.warning("Validation failure: Academic Year ID '%s' not found", academic_year_id)
            raise NotFoundException(
                "Academic Year",
                str(academic_year_id),
            )

        return academic_year

    def get_all_academic_years(
        self,
        db: Session,
    ) -> list[AcademicYear]:
        """
        Get all academic years.
        """
        return self.repository.get_all(db)

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
        academic_year_data: AcademicYearUpdate,
    ) -> AcademicYear:
        """
        Update an academic year.
        """
        logger.info("Updating academic year ID: %s", academic_year_id)
        academic_year = self.get_academic_year(
            db,
            academic_year_id,
        )

        update_data = academic_year_data.model_dump(
            exclude_unset=True,
        )

        new_start_date = update_data.get(
            "start_date",
            academic_year.start_date,
        )

        new_end_date = update_data.get(
            "end_date",
            academic_year.end_date,
        )

        if new_start_date >= new_end_date:
            logger.warning("Validation failure: Start date >= end date for academic year ID: %s", academic_year_id)
            raise ValidationException(
                "Start date must be before end date."
            )

        if (
            "name" in update_data
            and update_data["name"] != academic_year.name
        ):
            if self.repository.exists_by_name(
                db,
                academic_year.school_id,
                update_data["name"],
            ):
                logger.warning(
                    "Validation failure: Academic year name '%s' already exists for school ID: %s",
                    update_data["name"],
                    academic_year.school_id,
                )
                raise AlreadyExistsException(
                    "Academic Year",
                    update_data["name"],
                )

        if update_data.get("is_current") is True:
            current = self.repository.get_current(
                db,
                academic_year.school_id,
            )

            if (
                current is not None
                and current.id != academic_year.id
            ):
                current.is_current = False
                self.repository.update(
                    db,
                    current,
                )

        for key, value in update_data.items():
            setattr(
                academic_year,
                key,
                value,
            )

        updated = self.repository.update(
            db,
            academic_year,
        )
        logger.info("Academic year ID: %s updated successfully", academic_year_id)
        return updated

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
    ) -> None:
        """
        Soft delete an academic year entity.
        """
        logger.info("Soft deleting academic year ID: %s", academic_year_id)
        academic_year = self.get_academic_year(
            db,
            academic_year_id,
        )

        self.repository.delete(
            db,
            academic_year,
        )
        logger.info("Academic year ID: %s soft deleted successfully", academic_year_id)


academic_year_service = AcademicYearService(
    repository=academic_year_repository,
    school_repository=school_repository,
)