from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import SectionStatus
from app.models.section import Section
from app.repositories.base import BaseRepository


class SectionRepository(BaseRepository[Section]):
    """
    Repository for Section operations.
    """

    def __init__(self) -> None:
        """
        Initialize SectionRepository with Section model.
        """
        super().__init__(Section)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_id_and_school(
        self,
        db: Session,
        section_id: UUID,
        school_id: UUID,
    ) -> Section | None:
        """
        Get active section by ID and school ID of its parent class.
        """
        from app.models.school_class import SchoolClass
        return db.scalar(
            select(Section)
            .join(SchoolClass, Section.school_class_id == SchoolClass.id)
            .where(
                Section.id == section_id,
                SchoolClass.school_id == school_id,
                Section.is_deleted.is_(False),
                SchoolClass.is_deleted.is_(False),
            )
        )

    def get_by_name(
        self,
        db: Session,
        school_class_id: UUID,
        name: str,
    ) -> Section | None:
        """
        Get a section by name within a school class.
        """
        return db.scalar(
            select(Section).where(
                Section.school_class_id == school_class_id,
                func.lower(Section.name) == name.lower(),
                Section.is_deleted.is_(False),
            )
        )

    def get_by_class(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> list[Section]:
        """
        Get all sections of a class.
        """
        return list(
            db.scalars(
                select(Section).where(
                    Section.school_class_id == school_class_id,
                    Section.is_deleted.is_(False),
                )
            )
        )

    def get_active_sections(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> list[Section]:
        """
        Get active sections of a class.
        """
        return list(
            db.scalars(
                select(Section).where(
                    Section.school_class_id == school_class_id,
                    Section.status == SectionStatus.ACTIVE,
                    Section.is_deleted.is_(False),
                )
            )
        )

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_name(
        self,
        db: Session,
        school_class_id: UUID,
        name: str,
    ) -> bool:
        """
        Check whether a section with the given name already exists.
        """
        return (
            self.get_by_name(
                db,
                school_class_id,
                name,
            )
            is not None
        )


section_repository = SectionRepository()