from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic_year import AcademicYear
from app.repositories.base import BaseRepository


class AcademicYearRepository(BaseRepository[AcademicYear]):
    """
    Repository responsible for AcademicYear database operations.
    """

    def __init__(self) -> None:
        """
        Initialize AcademicYearRepository with AcademicYear model.
        """
        super().__init__(AcademicYear)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_id_and_school(
        self,
        db: Session,
        academic_year_id: UUID,
        school_id: UUID,
    ) -> AcademicYear | None:
        """
        Retrieve an active academic year by ID and school ID.
        """
        return db.scalar(
            select(AcademicYear).where(
                AcademicYear.id == academic_year_id,
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
        )

    def get_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
    ) -> AcademicYear | None:
        """
        Retrieve an active academic year by school ID and name.
        """
        return db.scalar(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.name == name,
                AcademicYear.is_deleted.is_(False),
            )
        )

    def get_current(
        self,
        db: Session,
        school_id: UUID,
    ) -> AcademicYear | None:
        """
        Retrieve the current active academic year for a school.
        """
        return db.scalar(
            select(AcademicYear).where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_current.is_(True),
                AcademicYear.is_deleted.is_(False),
            )
        )

    def get_all_current_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[AcademicYear]:
        """
        Retrieve all academic years currently marked is_current=True for a school.
        """
        stmt = select(AcademicYear).where(
            AcademicYear.school_id == school_id,
            AcademicYear.is_current.is_(True),
            AcademicYear.is_deleted.is_(False),
        )
        return list(db.scalars(stmt))

    def get_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[AcademicYear]:
        """
        Retrieve all active academic years for a school ordered by start date descending.
        """
        result = db.scalars(
            select(AcademicYear)
            .where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
            .order_by(AcademicYear.start_date.desc())
        )

        return list(result)

    def get_paginated_by_school(
        self,
        db: Session,
        school_id: UUID,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[AcademicYear], int, int]:
        """
        Retrieve paginated active academic years for a school using DB-level offset and limit.

        Returns:
            (items, total_count, total_pages)
        """
        count_stmt = (
            select(func.count())
            .select_from(AcademicYear)
            .where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
        )
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        items_stmt = (
            select(AcademicYear)
            .where(
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted.is_(False),
            )
            .order_by(AcademicYear.start_date.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(db.scalars(items_stmt))
        total_pages = ceil(total / page_size) if total > 0 else 0

        return items, total, total_pages

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID,
        name: str,
    ) -> bool:
        """
        Check whether an active academic year exists with the specified name for a school.
        """
        return (
            self.get_by_name(
                db,
                school_id,
                name,
            )
            is not None
        )


academic_year_repository = AcademicYearRepository()