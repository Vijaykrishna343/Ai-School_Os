from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.models.section import Section
from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.section import (
    SectionRepository,
    section_repository,
)
from app.schemas.section.section import (
    SectionCreate,
    SectionResponse,
    SectionUpdate,
)
from app.services.base_service import BaseService

logger = get_logger(__name__)


class SectionService(BaseService[SectionRepository]):
    """
    Business logic for Sections.
    """

    def __init__(
        self,
        repository: SectionRepository,
        school_class_repository: SchoolClassRepository,
    ) -> None:
        """
        Initialize SectionService with repositories.
        """
        super().__init__(repository)
        self.school_class_repository = school_class_repository

    # ------------------------------------------------------------------
    # Private Validation Helpers
    # ------------------------------------------------------------------

    def _validate_school_class(
        self,
        db: Session,
        school_class_id: UUID,
        current_school_id: UUID | None = None,
    ):
        """
        Ensure the School Class exists or raise NotFoundException.
        """
        school_class = self.school_class_repository.get(
            db,
            school_class_id,
        )

        if school_class is None or (current_school_id is not None and school_class.school_id != current_school_id):
            logger.warning(
                "Validation failure: School Class ID '%s' not found",
                school_class_id,
            )
            raise NotFoundException(
                "School Class",
                str(school_class_id),
            )

        return school_class

    def _get_section_or_raise(
        self,
        db: Session,
        section_id: UUID,
        current_school_id: UUID | None = None,
    ) -> Section:
        """
        Retrieve a section by ID or raise NotFoundException.
        """
        section = self.repository.get_by_id_and_school(
            db,
            section_id,
            current_school_id,
        ) if current_school_id is not None else self.repository.get(db, section_id)

        if section is None:
            logger.warning("Validation failure: Section ID '%s' not found", section_id)
            raise NotFoundException(
                "Section",
                str(section_id),
            )

        return section

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create_section(
        self,
        db: Session,
        section_data: SectionCreate,
        current_school_id: UUID | None = None,
    ) -> SectionResponse:
        """
        Create a new section.
        """
        logger.info(
            "Creating section '%s' for school class ID: %s",
            section_data.name,
            section_data.school_class_id,
        )

        self._validate_school_class(
            db,
            section_data.school_class_id,
            current_school_id,
        )

        if self.repository.exists_by_name(
            db,
            section_data.school_class_id,
            section_data.name,
        ):
            logger.warning(
                "Validation failure: Section name '%s' already exists for school class ID: %s",
                section_data.name,
                section_data.school_class_id,
            )
            raise AlreadyExistsException(
                "Section",
                section_data.name,
            )

        section = self.repository.create(
            db,
            Section(
                **section_data.model_dump(),
            ),
        )

        logger.info(
            "Section '%s' created successfully with ID: %s",
            section.name,
            section.id,
        )
        return SectionResponse.model_validate(section)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_section(
        self,
        db: Session,
        section_id: UUID,
        current_school_id: UUID | None = None,
    ) -> SectionResponse:
        """
        Get a section by ID.
        """
        section = self._get_section_or_raise(
            db,
            section_id,
            current_school_id,
        )

        return SectionResponse.model_validate(section)

    def get_sections(
        self,
        db: Session,
        school_class_id: UUID,
        current_school_id: UUID | None = None,
    ) -> list[SectionResponse]:
        """
        Get all sections of a school class.
        """
        self._validate_school_class(
            db,
            school_class_id,
            current_school_id,
        )

        sections = self.repository.get_by_class(
            db,
            school_class_id,
        )

        return [
            SectionResponse.model_validate(section)
            for section in sections
        ]

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_section(
        self,
        db: Session,
        section_id: UUID,
        section_data: SectionUpdate,
        current_school_id: UUID | None = None,
    ) -> SectionResponse:
        """
        Update an existing section.
        """
        logger.info("Updating section ID: %s", section_id)
        section = self._get_section_or_raise(
            db,
            section_id,
            current_school_id,
        )

        update_data = section_data.model_dump(
            exclude_unset=True,
        )

        if (
            "name" in update_data
            and update_data["name"] != section.name
        ):
            if self.repository.exists_by_name(
                db,
                section.school_class_id,
                update_data["name"],
            ):
                logger.warning(
                    "Validation failure: Section name '%s' already exists for class ID: %s",
                    update_data["name"],
                    section.school_class_id,
                )
                raise AlreadyExistsException(
                    "Section",
                    update_data["name"],
                )

        for key, value in update_data.items():
            setattr(section, key, value)

        updated_section = self.repository.update(
            db,
            section,
        )

        logger.info("Section ID: %s updated successfully", section_id)
        return SectionResponse.model_validate(updated_section)

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete_section(
        self,
        db: Session,
        section_id: UUID,
        current_school_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a section entity.
        """
        logger.info("Soft deleting section ID: %s", section_id)
        section = self._get_section_or_raise(
            db,
            section_id,
            current_school_id,
        )

        self.repository.delete(
            db,
            section,
        )
        logger.info("Section ID: %s soft deleted successfully", section_id)


section_service = SectionService(
    repository=section_repository,
    school_class_repository=school_class_repository,
)