from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.models.school import School
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.school.school import (
    SchoolCreate,
    SchoolUpdate,
)
from app.services.base_service import BaseService

logger = get_logger(__name__)


class SchoolService(BaseService[SchoolRepository]):
    """
    Business logic for School operations.
    """

    def __init__(
        self,
        repository: SchoolRepository,
    ) -> None:
        """
        Initialize SchoolService with SchoolRepository.
        """
        super().__init__(repository)

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create_school(
        self,
        db: Session,
        school_data: SchoolCreate,
    ) -> School:
        """
        Create a new school entity.
        """
        logger.info("Creating new school with code: %s", school_data.code)

        if self.repository.exists_by_code(
            db,
            school_data.code,
        ):
            logger.warning("Validation failure: School code '%s' already exists", school_data.code)
            raise AlreadyExistsException(
                "School",
                school_data.code,
            )

        school = School(
            **school_data.model_dump()
        )

        created = self.repository.create(
            db,
            school,
        )
        logger.info("School created successfully with ID: %s", created.id)
        return created

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> School:
        """
        Get a school by ID or raise NotFoundException.
        """
        school = self.repository.get(
            db,
            school_id,
        )

        if school is None:
            logger.warning("Validation failure: School ID '%s' not found", school_id)
            raise NotFoundException(
                "School",
                str(school_id),
            )

        return school

    def get_all_schools(
        self,
        db: Session,
    ) -> list[School]:
        """
        Get all active schools.
        """
        return self.repository.get_all(db)

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_school(
        self,
        db: Session,
        school_id: UUID,
        school_data: SchoolUpdate,
    ) -> School:
        """
        Update an existing school.
        """
        logger.info("Updating school ID: %s", school_id)
        school = self.get_school(
            db,
            school_id,
        )

        update_data = school_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                school,
                key,
                value,
            )

        updated = self.repository.update(
            db,
            school,
        )
        logger.info("School ID: %s updated successfully", school_id)
        return updated

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> None:
        """
        Soft delete a school entity.
        """
        logger.info("Soft deleting school ID: %s", school_id)
        school = self.get_school(
            db,
            school_id,
        )

        self.repository.delete(
            db,
            school,
        )
        logger.info("School ID: %s soft deleted successfully", school_id)


school_service = SchoolService(repository=school_repository)