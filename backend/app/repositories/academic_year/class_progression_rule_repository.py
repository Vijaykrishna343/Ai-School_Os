from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic_year import ClassProgressionRule
from app.repositories.base import BaseRepository


class ClassProgressionRuleRepository(BaseRepository[ClassProgressionRule]):
    """
    Repository for ClassProgressionRule database operations.
    """

    def __init__(self) -> None:
        super().__init__(ClassProgressionRule)

    def get_by_id_and_school(
        self,
        db: Session,
        rule_id: UUID,
        school_id: UUID,
    ) -> ClassProgressionRule | None:
        """
        Retrieve an active class progression rule by ID and school_id.
        """
        return db.scalar(
            select(ClassProgressionRule).where(
                ClassProgressionRule.id == rule_id,
                ClassProgressionRule.school_id == school_id,
                ClassProgressionRule.is_deleted.is_(False),
            )
        )

    def get_by_source_class(
        self,
        db: Session,
        school_id: UUID,
        source_class_id: UUID,
    ) -> ClassProgressionRule | None:
        """
        Retrieve an active progression rule for a specific source class.
        """
        return db.scalar(
            select(ClassProgressionRule).where(
                ClassProgressionRule.school_id == school_id,
                ClassProgressionRule.source_class_id == source_class_id,
                ClassProgressionRule.is_deleted.is_(False),
            )
        )

    def get_all_active_for_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[ClassProgressionRule]:
        """
        Retrieve all active progression rules for a school.
        """
        stmt = select(ClassProgressionRule).where(
            ClassProgressionRule.school_id == school_id,
            ClassProgressionRule.is_deleted.is_(False),
        )
        return list(db.scalars(stmt))

    def get_paginated_by_school(
        self,
        db: Session,
        school_id: UUID,
        source_class_id: UUID | None = None,
        target_class_id: UUID | None = None,
        is_terminal: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[ClassProgressionRule], int, int]:
        """
        Retrieve paginated active progression rules with optional filters.

        Returns:
            (items, total_count, total_pages)
        """
        conditions = [
            ClassProgressionRule.school_id == school_id,
            ClassProgressionRule.is_deleted.is_(False),
        ]

        if source_class_id is not None:
            conditions.append(ClassProgressionRule.source_class_id == source_class_id)
        if target_class_id is not None:
            conditions.append(ClassProgressionRule.target_class_id == target_class_id)
        if is_terminal is not None:
            conditions.append(ClassProgressionRule.is_terminal == is_terminal)

        count_stmt = (
            select(func.count())
            .select_from(ClassProgressionRule)
            .where(*conditions)
        )
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        items_stmt = (
            select(ClassProgressionRule)
            .where(*conditions)
            .offset(offset)
            .limit(page_size)
        )
        items = list(db.scalars(items_stmt))
        total_pages = ceil(total / page_size) if total > 0 else 0

        return items, total, total_pages


class_progression_rule_repository = ClassProgressionRuleRepository()
