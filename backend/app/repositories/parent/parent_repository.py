from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.parent import Parent
from app.repositories.base import BaseRepository


class ParentRepository(BaseRepository[Parent]):
    """
    Repository responsible for Parent database operations.
    """

    def __init__(self):
        super().__init__(Parent)

    def get_by_phone(
        self,
        db: Session,
        phone: str,
    ) -> Parent | None:
        return db.scalar(
            select(Parent).where(
                Parent.primary_phone == phone,
                Parent.is_deleted.is_(False),
            )
        )

    def exists_by_phone(
        self,
        db: Session,
        phone: str,
    ) -> bool:
        return self.get_by_phone(db, phone) is not None

parent_repository = ParentRepository()