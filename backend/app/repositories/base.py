from math import ceil
from typing import Generic, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """
    Base repository providing reusable CRUD operations.
    """

    def __init__(self, model: type[ModelType]) -> None:
        """
        Initialize the base repository with the specified model type.
        """
        self.model = model

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create(
        self,
        db: Session,
        obj: ModelType,
    ) -> ModelType:
        """
        Add a new record to the database session and commit.
        """
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get(
        self,
        db: Session,
        obj_id: UUID,
    ) -> ModelType | None:
        """
        Retrieve an active record by ID.
        """
        return db.scalar(
            select(self.model).where(
                self.model.id == obj_id,
                self.model.is_deleted.is_(False),
            )
        )

    def get_by_id(
        self,
        db: Session,
        obj_id: UUID,
    ) -> ModelType | None:
        """
        Alias for get() to maintain consistency with identity repositories.
        """
        return self.get(db, obj_id)

    def get_by_id_and_school(
        self,
        db: Session,
        obj_id: UUID,
        school_id: UUID,
    ) -> ModelType | None:
        """
        Retrieve an active record by ID and school ID (tenant isolation).
        """
        return db.scalar(
            select(self.model).where(
                self.model.id == obj_id,
                self.model.school_id == school_id,
                self.model.is_deleted.is_(False),
            )
        )

    def get_all(
        self,
        db: Session,
    ) -> list[ModelType]:
        """
        Retrieve all active records for this model.
        """
        result = db.scalars(
            select(self.model).where(
                self.model.is_deleted.is_(False)
            )
        )
        return list(result)

    def get_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[ModelType], int, int]:
        """
        Retrieve paginated active records.

        Returns:
            (items, total_records, total_pages)
        """
        page = max(page, 1)
        page_size = max(page_size, 1)

        total = self.count(db)

        total_pages = (
            ceil(total / page_size)
            if total > 0
            else 0
        )

        result = db.scalars(
            select(self.model)
            .where(
                self.model.is_deleted.is_(False)
            )
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return (
            list(result),
            total,
            total_pages,
        )

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update(
        self,
        db: Session,
        obj: ModelType,
    ) -> ModelType:
        """
        Commit updates on a record and refresh its state.
        """
        db.commit()
        db.refresh(obj)
        return obj

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete(
        self,
        db: Session,
        obj: ModelType,
    ) -> None:
        """
        Perform a soft delete on a record and commit the change.
        """
        obj.soft_delete()
        db.commit()

    # ------------------------------------------------------------------
    # Existence & Count Methods
    # ------------------------------------------------------------------

    def exists(
        self,
        db: Session,
        obj_id: UUID,
    ) -> bool:
        """
        Check if an active record with the given ID exists.
        """
        return self.get(db, obj_id) is not None

    def count(
        self,
        db: Session,
    ) -> int:
        """
        Count total active records for this model.
        """
        return (
            db.scalar(
                select(func.count())
                .select_from(self.model)
                .where(
                    self.model.is_deleted.is_(False)
                )
            )
            or 0
        )