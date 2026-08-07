from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.school import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    """
    Repository responsible for School database operations.
    """

    def __init__(self):
        super().__init__(School)

    def get_by_code(
        self,
        db: Session,
        code: str,
    ) -> School | None:
        return db.scalar(
            select(School).where(
                School.code == code,
                School.is_deleted.is_(False),
            )
        )

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> School | None:
        return db.scalar(
            select(School).where(
                School.email == email,
                School.is_deleted.is_(False),
            )
        )

    def exists_by_code(
        self,
        db: Session,
        code: str,
    ) -> bool:
        return self.get_by_code(
            db,
            code,
        ) is not None

school_repository = SchoolRepository()