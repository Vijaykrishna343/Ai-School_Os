from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.models.parent import Parent
from app.repositories.parent import (
    ParentRepository,
    parent_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.parent import ParentCreate, ParentUpdate

logger = get_logger(__name__)


class ParentService:
    """
    Business logic for Parent operations.
    """

    def __init__(
        self,
        repository: ParentRepository,
        school_repository: SchoolRepository,
    ) -> None:
        """
        Initialize ParentService with repositories.
        """
        self.repository = repository
        self.school_repository = school_repository

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create_parent(
        self,
        db: Session,
        parent_data: ParentCreate,
    ) -> Parent:
        """
        Create a new parent record after validating school existence and phone uniqueness.
        """
        logger.info(
            "Creating parent '%s %s' for school ID: %s",
            parent_data.father_name or parent_data.mother_name or "Parent",
            parent_data.guardian_name or "",
            parent_data.school_id,
        )

        school = self.school_repository.get(
            db,
            parent_data.school_id,
        )

        if school is None:
            logger.warning(
                "Validation failure: School ID '%s' not found for parent creation",
                parent_data.school_id,
            )
            raise NotFoundException(
                "School",
                str(parent_data.school_id),
            )

        if self.repository.exists_by_phone(
            db,
            parent_data.primary_phone,
        ):
            logger.warning(
                "Validation failure: Parent phone '%s' already exists",
                parent_data.primary_phone,
            )
            raise AlreadyExistsException(
                "Parent",
                parent_data.primary_phone,
            )

        parent = Parent(**parent_data.model_dump())

        created = self.repository.create(db, parent)
        logger.info("Parent created successfully with ID: %s", created.id)
        return created

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_parent(
        self,
        db: Session,
        parent_id: UUID,
    ) -> Parent:
        """
        Retrieve a parent record by ID or raise NotFoundException.
        """
        parent = self.repository.get(db, parent_id)

        if parent is None:
            logger.warning("Validation failure: Parent ID '%s' not found", parent_id)
            raise NotFoundException(
                "Parent",
                str(parent_id),
            )

        return parent

    def get_all_parents(
        self,
        db: Session,
    ) -> list[Parent]:
        """
        Retrieve all active parent records.
        """
        return self.repository.get_all(db)

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_parent(
        self,
        db: Session,
        parent_id: UUID,
        parent_data: ParentUpdate,
    ) -> Parent:
        """
        Update an existing parent record.
        """
        logger.info("Updating parent ID: %s", parent_id)
        parent = self.get_parent(db, parent_id)

        update_data = parent_data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(parent, key, value)

        updated = self.repository.update(
            db,
            parent,
        )
        logger.info("Parent ID: %s updated successfully", parent_id)
        return updated

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete_parent(
        self,
        db: Session,
        parent_id: UUID,
    ) -> None:
        """
        Soft delete a parent record.
        """
        logger.info("Soft deleting parent ID: %s", parent_id)
        parent = self.get_parent(db, parent_id)

        self.repository.delete(
            db,
            parent,
        )
        logger.info("Parent ID: %s soft deleted successfully", parent_id)


parent_service = ParentService(
    repository=parent_repository,
    school_repository=school_repository,
)