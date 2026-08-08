from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.school import School
from app.repositories.base import BaseRepository


class SchoolRepository(BaseRepository[School]):
    """
    Repository responsible for School database operations.
    """

    def __init__(self) -> None:
        """
        Initialize SchoolRepository with School model.
        """
        super().__init__(School)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_code(
        self,
        db: Session,
        code: str,
    ) -> School | None:
        """
        Retrieve an active school entity by its unique school code.
        """
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
        """
        Retrieve an active school entity by its contact email address.
        """
        return db.scalar(
            select(School).where(
                School.email == email,
                School.is_deleted.is_(False),
            )
        )

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_code(
        self,
        db: Session,
        code: str,
    ) -> bool:
        """
        Check whether an active school entity exists with the specified code.
        """
        return self.get_by_code(
            db,
            code,
        ) is not None


school_repository = SchoolRepository()