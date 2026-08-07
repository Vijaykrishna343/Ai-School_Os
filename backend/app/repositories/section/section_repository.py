from __future__ import annotations

import uuid

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
        super().__init__(Section)

    def get_by_name(
        self,
        db: Session,
        school_class_id: uuid.UUID,
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

    def exists_by_name(
        self,
        db: Session,
        school_class_id: uuid.UUID,
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

    def get_by_class(
        self,
        db: Session,
        school_class_id: uuid.UUID,
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
            ).all()
        )

    def get_active_sections(
        self,
        db: Session,
        school_class_id: uuid.UUID,
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
            ).all()
        )

section_repository = SectionRepository()