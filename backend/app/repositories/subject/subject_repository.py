from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.subject.subject import Subject
from app.repositories.base import BaseRepository
from app.schemas.subject import (
    SubjectCreate,
    SubjectFilter,
)


class SubjectRepository(BaseRepository[Subject]):
    """
    Repository responsible for Subject database operations.
    """

    def __init__(self) -> None:
        """
        Initialize SubjectRepository with Subject model.
        """
        super().__init__(Subject)

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create(
        self,
        db: Session,
        subject: Subject | SubjectCreate,
    ) -> Subject:
        """
        Create a new Subject entity in the database.
        """
        if isinstance(subject, Subject):
            db_subject = subject
        else:
            db_subject = Subject(**subject.model_dump())

        return super().create(db, db_subject)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_subject_code(
        self,
        db: Session,
        school_id: UUID,
        subject_code: str,
    ) -> Subject | None:
        """
        Retrieve an active subject by school ID and subject code.
        """
        return db.scalar(
            select(Subject).where(
                Subject.school_id == school_id,
                Subject.subject_code == subject_code,
                Subject.is_deleted.is_(False),
            )
        )

    def get_by_subject_name(
        self,
        db: Session,
        school_id: UUID,
        subject_name: str,
    ) -> Subject | None:
        """
        Retrieve an active subject by school ID and subject name.
        """
        return db.scalar(
            select(Subject).where(
                Subject.school_id == school_id,
                Subject.subject_name == subject_name,
                Subject.is_deleted.is_(False),
            )
        )

    def list(
        self,
        db: Session,
        filters: SubjectFilter,
    ) -> tuple[list[Subject], int]:
        """
        List active subjects based on query filters and pagination parameters.
        """
        query = select(Subject).where(
            Subject.is_deleted.is_(False)
        )

        if filters.school_id:
            query = query.where(
                Subject.school_id == filters.school_id
            )

        if filters.subject_code:
            query = query.where(
                Subject.subject_code.ilike(
                    f"%{filters.subject_code}%"
                )
            )

        if filters.subject_name:
            query = query.where(
                Subject.subject_name.ilike(
                    f"%{filters.subject_name}%"
                )
            )

        if filters.status:
            query = query.where(
                Subject.status == filters.status
            )

        if filters.is_optional is not None:
            query = query.where(
                Subject.is_optional == filters.is_optional
            )

        total = db.scalar(
            select(func.count()).select_from(
                query.subquery()
            )
        ) or 0

        query = (
            query.order_by(
                Subject.subject_name
            )
            .offset(
                (filters.page - 1)
                * filters.page_size
            )
            .limit(filters.page_size)
        )

        return (
            list(db.scalars(query)),
            total,
        )

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update(
        self,
        db: Session,
        db_subject: Subject,
        subject: Any = None,
    ) -> Subject:
        """
        Update an existing Subject entity.
        """
        if subject is not None and hasattr(subject, "model_dump"):
            update_data = subject.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                setattr(db_subject, field, value)

        return super().update(db, db_subject)

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def soft_delete(
        self,
        db: Session,
        db_subject: Subject,
    ) -> None:
        """
        Soft delete a Subject entity.
        """
        super().delete(db, db_subject)


subject_repository = SubjectRepository()