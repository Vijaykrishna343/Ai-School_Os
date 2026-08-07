from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
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


class SectionService(BaseService[SectionRepository]):
    """
    Business logic for Sections.
    """

    def __init__(
        self,
        repository: SectionRepository,
        school_class_repository: SchoolClassRepository,
    ) -> None:
        super().__init__(repository)
        self.school_class_repository = school_class_repository

    # ==========================================================
    # Validation Helpers
    # ==========================================================

    def _validate_school_class(
        self,
        db: Session,
        school_class_id: UUID,
    ):
        """
        Ensure the School Class exists.
        """

        school_class = self.school_class_repository.get(
            db,
            school_class_id,
        )

        if school_class is None:
            raise NotFoundException(
                "School Class",
                str(school_class_id),
            )

        return school_class

    # ==========================================================
    # Create Section
    # ==========================================================

    def create_section(
        self,
        db: Session,
        section_data: SectionCreate,
    ) -> SectionResponse:
        """
        Create a new section.
        """

        # Validate School Class
        self._validate_school_class(
            db,
            section_data.school_class_id,
        )

        # Check duplicate section name within the class
        if self.repository.exists_by_name(
            db,
            section_data.school_class_id,
            section_data.name,
        ):
            raise AlreadyExistsException(
                "Section",
                section_data.name,
            )

        # Create Section
        section = self.repository.create(
            db,
            Section(
                **section_data.model_dump(),
            ),
        )

        return SectionResponse.model_validate(section)

    # ==========================================================
    # Get Section
    # ==========================================================

    def get_section(
        self,
        db: Session,
        section_id: UUID,
    ) -> SectionResponse:
        """
        Get a section by ID.
        """

        section = self.repository.get(
            db,
            section_id,
        )

        if section is None:
            raise NotFoundException(
                "Section",
                str(section_id),
            )

        return SectionResponse.model_validate(section)

    # ==========================================================
    # Get Sections by Class
    # ==========================================================

    def get_sections(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> list[SectionResponse]:
        """
        Get all sections of a school class.
        """

        self._validate_school_class(
            db,
            school_class_id,
        )

        sections = self.repository.get_by_class(
            db,
            school_class_id,
        )

        return [
            SectionResponse.model_validate(section)
            for section in sections
        ]

    # ==========================================================
    # Update Section
    # ==========================================================

    def update_section(
        self,
        db: Session,
        section_id: UUID,
        section_data: SectionUpdate,
    ) -> SectionResponse:
        """
        Update a section.
        """

        section = self.repository.get(
            db,
            section_id,
        )

        if section is None:
            raise NotFoundException(
                "Section",
                str(section_id),
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
                raise AlreadyExistsException(
                    "Section",
                    update_data["name"],
                )

        # Apply update fields to the entity before persisting
        for key, value in update_data.items():
            setattr(section, key, value)

        updated_section = self.repository.update(
            db,
            section,
        )

        return SectionResponse.model_validate(updated_section)

    # ==========================================================
    # Delete Section
    # ==========================================================

    def delete_section(
        self,
        db: Session,
        section_id: UUID,
    ) -> None:
        """
        Soft delete a section.
        """

        section = self.repository.get(
            db,
            section_id,
        )

        if section is None:
            raise NotFoundException(
                "Section",
                str(section_id),
            )

        self.repository.delete(
            db,
            section,
        )


section_service = SectionService(
    repository=section_repository,
    school_class_repository=school_class_repository,
)