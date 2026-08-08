from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.school_class import SchoolClass
from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.school_class import (
    SchoolClassCreate,
    SchoolClassUpdate,
)

logger = get_logger(__name__)


class SchoolClassService:
    """
    Business logic for School Class operations.
    """

    def __init__(
        self,
        repository: SchoolClassRepository,
        school_repository: SchoolRepository,
    ) -> None:
        """
        Initialize SchoolClassService with repositories.
        """
        self.repository = repository
        self.school_repository = school_repository

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create_school_class(
        self,
        db: Session,
        school_class_data: SchoolClassCreate,
    ) -> SchoolClass:
        """
        Create a new school class.
        """
        logger.info(
            "Creating school class '%s' for school ID: %s",
            school_class_data.name,
            school_class_data.school_id,
        )

        school = self.school_repository.get(
            db,
            school_class_data.school_id,
        )

        if school is None:
            logger.warning(
                "Validation failure: School ID '%s' not found for class creation",
                school_class_data.school_id,
            )
            raise NotFoundException(
                "School",
                str(school_class_data.school_id),
            )

        if self.repository.exists_by_name(
            db,
            school_class_data.school_id,
            school_class_data.name,
        ):
            logger.warning(
                "Validation failure: School class name '%s' already exists for school ID: %s",
                school_class_data.name,
                school_class_data.school_id,
            )
            raise AlreadyExistsException(
                "School Class",
                school_class_data.name,
            )

        if school_class_data.display_order <= 0:
            logger.warning("Validation failure: Display order <= 0")
            raise ValidationException(
                "Display order must be greater than zero."
            )

        school_class = SchoolClass(
            **school_class_data.model_dump()
        )

        created = self.repository.create(
            db,
            school_class,
        )
        logger.info("School class '%s' created successfully with ID: %s", created.name, created.id)
        return created

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_school_class(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> SchoolClass:
        """
        Get school class by ID or raise NotFoundException.
        """
        school_class = self.repository.get(
            db,
            school_class_id,
        )

        if school_class is None:
            logger.warning("Validation failure: School Class ID '%s' not found", school_class_id)
            raise NotFoundException(
                "School Class",
                str(school_class_id),
            )

        return school_class

    def get_all_school_classes(
        self,
        db: Session,
    ) -> list[SchoolClass]:
        """
        Get all school classes.
        """
        return self.repository.get_all(db)

    def get_school_classes_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[SchoolClass]:
        """
        Get all active classes of a school.
        """
        school = self.school_repository.get(
            db,
            school_id,
        )

        if school is None:
            logger.warning("Validation failure: School ID '%s' not found", school_id)
            raise NotFoundException(
                "School",
                str(school_id),
            )

        return self.repository.get_by_school(
            db,
            school_id,
        )

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_school_class(
        self,
        db: Session,
        school_class_id: UUID,
        school_class_data: SchoolClassUpdate,
    ) -> SchoolClass:
        """
        Update an existing school class.
        """
        logger.info("Updating school class ID: %s", school_class_id)
        school_class = self.get_school_class(
            db,
            school_class_id,
        )

        update_data = school_class_data.model_dump(
            exclude_unset=True,
        )

        if (
            "name" in update_data
            and update_data["name"] != school_class.name
        ):
            if self.repository.exists_by_name(
                db,
                school_class.school_id,
                update_data["name"],
            ):
                logger.warning(
                    "Validation failure: Class name '%s' already exists for school ID: %s",
                    update_data["name"],
                    school_class.school_id,
                )
                raise AlreadyExistsException(
                    "School Class",
                    update_data["name"],
                )

        if (
            "display_order" in update_data
            and update_data["display_order"] <= 0
        ):
            logger.warning("Validation failure: Display order <= 0 for class ID: %s", school_class_id)
            raise ValidationException(
                "Display order must be greater than zero."
            )

        for key, value in update_data.items():
            setattr(
                school_class,
                key,
                value,
            )

        updated = self.repository.update(
            db,
            school_class,
        )
        logger.info("School class ID: %s updated successfully", school_class_id)
        return updated

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete_school_class(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> None:
        """
        Soft delete a school class entity.
        """
        logger.info("Soft deleting school class ID: %s", school_class_id)
        school_class = self.get_school_class(
            db,
            school_class_id,
        )

        self.repository.delete(
            db,
            school_class,
        )
        logger.info("School class ID: %s soft deleted successfully", school_class_id)


school_class_service = SchoolClassService(
    repository=school_class_repository,
    school_repository=school_repository,
)