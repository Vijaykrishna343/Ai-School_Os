from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.academic_year.progression_execution import (
    ProgressionExecution,
    ProgressionExecutionStatus,
)


class ProgressionExecutionRepository:
    """
    Repository for managing ProgressionExecution and ProgressionExecutionItem entities.
    """

    def create(
        self,
        db: Session,
        execution: ProgressionExecution,
    ) -> ProgressionExecution:
        db.add(execution)
        db.flush()
        return execution

    def update(
        self,
        db: Session,
        execution: ProgressionExecution,
    ) -> ProgressionExecution:
        db.flush()
        return execution

    def get_by_id_and_school(
        self,
        db: Session,
        execution_id: UUID,
        school_id: UUID,
    ) -> ProgressionExecution | None:
        stmt = (
            select(ProgressionExecution)
            .options(joinedload(ProgressionExecution.items))
            .where(
                ProgressionExecution.id == execution_id,
                ProgressionExecution.school_id == school_id,
                ProgressionExecution.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt)

    def get_by_school_and_idempotency_key(
        self,
        db: Session,
        school_id: UUID,
        idempotency_key: str,
    ) -> ProgressionExecution | None:
        stmt = (
            select(ProgressionExecution)
            .options(joinedload(ProgressionExecution.items))
            .where(
                ProgressionExecution.school_id == school_id,
                ProgressionExecution.idempotency_key == idempotency_key,
                ProgressionExecution.is_deleted.is_(False),
            )
        )
        return db.scalar(stmt)

    def get_active_for_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> ProgressionExecution | None:
        """
        Check if an active execution run exists for a school (PENDING or RUNNING).
        """
        stmt = (
            select(ProgressionExecution)
            .where(
                ProgressionExecution.school_id == school_id,
                ProgressionExecution.status.in_([
                    ProgressionExecutionStatus.PENDING,
                    ProgressionExecutionStatus.RUNNING,
                ]),
                ProgressionExecution.is_deleted.is_(False),
            )
            .limit(1)
        )
        return db.scalar(stmt)


progression_execution_repository = ProgressionExecutionRepository()
