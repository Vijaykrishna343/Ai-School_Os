from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import SchoolClassStatus
from app.models.school_class import SchoolClass
from app.repositories.base import BaseRepository


class SchoolClassRepository(BaseRepository[SchoolClass]):
    """
    Repository responsible for SchoolClass database operations.
    """

    def __init__(self) -> None:
        """
        Initialize SchoolClassRepository with SchoolClass model.
        """
        super().__init__(SchoolClass)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
    ) -> SchoolClass | None:
        """
        Retrieve a school class by name (case-insensitive) for a specific school.
        """
        stmt = (
            select(SchoolClass)
            .where(
                SchoolClass.school_id == school_id,
                func.lower(SchoolClass.name) == name.lower(),
                SchoolClass.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[SchoolClass]:
        """
        Retrieve all active classes for a school ordered by display order.
        """
        stmt = (
            select(SchoolClass)
            .where(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted.is_(False),
            )
            .order_by(SchoolClass.display_order)
        )

        return list(db.scalars(stmt))

    def get_active_classes(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[SchoolClass]:
        """
        Retrieve active classes with status ACTIVE for a school ordered by display order.
        """
        stmt = (
            select(SchoolClass)
            .where(
                SchoolClass.school_id == school_id,
                SchoolClass.status == SchoolClassStatus.ACTIVE,
                SchoolClass.is_deleted.is_(False),
            )
            .order_by(SchoolClass.display_order)
        )

        return list(db.scalars(stmt))

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if a class with the given name exists in a school, optionally excluding an ID.
        """
        stmt = (
            select(SchoolClass)
            .where(
                SchoolClass.school_id == school_id,
                func.lower(SchoolClass.name) == name.lower(),
                SchoolClass.is_deleted.is_(False),
            )
        )

        if exclude_id is not None:
            stmt = stmt.where(
                SchoolClass.id != exclude_id,
            )

        return db.scalar(stmt) is not None


school_class_repository = SchoolClassRepository()