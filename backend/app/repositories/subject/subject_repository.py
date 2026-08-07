from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.subject.subject import Subject
from app.repositories.base import BaseRepository
from app.schemas.subject import (
    SubjectCreate,
    SubjectFilter,
    SubjectUpdate,
)


class SubjectRepository(BaseRepository[Subject]):
    """
    Repository responsible for Subject database operations.
    """

    def __init__(self):
        super().__init__(Subject)

    def create(
        self,
        db: Session,
        subject: SubjectCreate,
    ) -> Subject:
        db_subject = Subject(
            **subject.model_dump()
        )

        return super().create(
            db,
            db_subject,
        )

    def get_by_subject_code(
        self,
        db: Session,
        school_id: UUID,
        subject_code: str,
    ) -> Subject | None:
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

    def update(
        self,
        db: Session,
        db_subject: Subject,
        subject: SubjectUpdate,
    ) -> Subject:

        update_data = subject.model_dump(
            exclude_unset=True
        )

        for field, value in update_data.items():
            setattr(
                db_subject,
                field,
                value,
            )

        return super().update(
            db,
            db_subject,
        )

    def soft_delete(
        self,
        db: Session,
        db_subject: Subject,
    ) -> None:

        super().delete(
            db,
            db_subject,
        )

subject_repository = SubjectRepository()