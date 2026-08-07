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

    def __init__(self, model: type[ModelType]):
        self.model = model

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    def create(
        self,
        db: Session,
        obj: ModelType,
    ) -> ModelType:
        db.add(obj)
        db.commit()
        db.refresh(obj)
        return obj

    # ------------------------------------------------------------------
    # Get by Primary Key
    # ------------------------------------------------------------------

    def get(
        self,
        db: Session,
        obj_id: UUID,
    ) -> ModelType | None:
        return db.scalar(
            select(self.model).where(
                self.model.id == obj_id,
                self.model.is_deleted.is_(False),
            )
        )

    # Alias for consistency with identity repositories
    def get_by_id(
        self,
        db: Session,
        obj_id: UUID,
    ) -> ModelType | None:
        return self.get(db, obj_id)

    # ------------------------------------------------------------------
    # Get All
    # ------------------------------------------------------------------

    def get_all(
        self,
        db: Session,
    ) -> list[ModelType]:
        result = db.scalars(
            select(self.model).where(
                self.model.is_deleted.is_(False)
            )
        )
        return list(result)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(
        self,
        db: Session,
        obj: ModelType,
    ) -> ModelType:
        db.commit()
        db.refresh(obj)
        return obj

    # ------------------------------------------------------------------
    # Soft Delete
    # ------------------------------------------------------------------

    def delete(
        self,
        db: Session,
        obj: ModelType,
    ) -> None:
        obj.soft_delete()
        db.commit()

    # ------------------------------------------------------------------
    # Exists
    # ------------------------------------------------------------------

    def exists(
        self,
        db: Session,
        obj_id: UUID,
    ) -> bool:
        return self.get(db, obj_id) is not None

    # ------------------------------------------------------------------
    # Count
    # ------------------------------------------------------------------

    def count(
        self,
        db: Session,
    ) -> int:
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

    # ------------------------------------------------------------------
    # Pagination
    # ------------------------------------------------------------------

    def get_paginated(
        self,
        db: Session,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[ModelType], int, int]:
        """
        Returns:
            (
                items,
                total_records,
                total_pages
            )
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