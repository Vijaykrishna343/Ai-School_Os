from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.parent import Parent
from app.repositories.base import BaseRepository


class ParentRepository(BaseRepository[Parent]):
    """
    Repository responsible for Parent database operations.
    """

    def __init__(self) -> None:
        """
        Initialize ParentRepository with Parent model.
        """
        super().__init__(Parent)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_phone(
        self,
        db: Session,
        phone: str,
    ) -> Parent | None:
        """
        Get active parent by primary phone.
        """
        return db.scalar(
            select(Parent).where(
                Parent.primary_phone == phone,
                Parent.is_deleted.is_(False),
            )
        )

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_phone(
        self,
        db: Session,
        phone: str,
    ) -> bool:
        """
        Check whether an active parent exists with the given primary phone.
        """
        return self.get_by_phone(db, phone) is not None


parent_repository = ParentRepository()