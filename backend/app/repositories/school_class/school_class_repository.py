from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import SchoolClassStatus
from app.models.school_class import SchoolClass
from app.repositories.base import BaseRepository


class SchoolClassRepository(BaseRepository[SchoolClass]):
    """
    Repository for SchoolClass.
    """

    def __init__(self):
        super().__init__(SchoolClass)

    def get_by_name(
        self,
        db: Session,
        school_id: uuid.UUID,
        name: str,
    ) -> SchoolClass | None:
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
        school_id: uuid.UUID,
    ) -> list[SchoolClass]:
        stmt = (
            select(SchoolClass)
            .where(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted.is_(False),
            )
            .order_by(SchoolClass.display_order)
        )

        return list(db.scalars(stmt).all())

    def get_active_classes(
        self,
        db: Session,
        school_id: uuid.UUID,
    ) -> list[SchoolClass]:
        stmt = (
            select(SchoolClass)
            .where(
                SchoolClass.school_id == school_id,
                SchoolClass.status == SchoolClassStatus.ACTIVE,
                SchoolClass.is_deleted.is_(False),
            )
            .order_by(SchoolClass.display_order)
        )

        return list(db.scalars(stmt).all())

    def exists_by_name(
        self,
        db: Session,
        school_id: uuid.UUID,
        name: str,
        exclude_id: uuid.UUID | None = None,
    ) -> bool:
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