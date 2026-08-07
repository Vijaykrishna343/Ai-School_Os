from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.models.parent import Parent
from app.repositories.parent import (
    ParentRepository,
    parent_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.parent import ParentCreate, ParentUpdate


class ParentService:
    """
    Business logic for Parent operations.
    """

    def __init__(
        self,
        repository: ParentRepository,
        school_repository: SchoolRepository,
    ):
        self.repository = repository
        self.school_repository = school_repository

    def create_parent(
        self,
        db: Session,
        parent_data: ParentCreate,
    ) -> Parent:

        school = self.school_repository.get(
            db,
            parent_data.school_id,
        )

        if school is None:
            raise NotFoundException(
                "School",
                str(parent_data.school_id),
            )

        if self.repository.exists_by_phone(
            db,
            parent_data.primary_phone,
        ):
            raise AlreadyExistsException(
                "Parent",
                parent_data.primary_phone,
            )

        parent = Parent(**parent_data.model_dump())

        return self.repository.create(db, parent)

    def get_parent(
        self,
        db: Session,
        parent_id: UUID,
    ) -> Parent:

        parent = self.repository.get(db, parent_id)

        if parent is None:
            raise NotFoundException(
                "Parent",
                str(parent_id),
            )

        return parent

    def get_all_parents(
        self,
        db: Session,
    ) -> list[Parent]:
        return self.repository.get_all(db)

    def update_parent(
        self,
        db: Session,
        parent_id: UUID,
        parent_data: ParentUpdate,
    ) -> Parent:

        parent = self.get_parent(db, parent_id)

        update_data = parent_data.model_dump(
            exclude_unset=True,
        )

        for key, value in update_data.items():
            setattr(parent, key, value)

        return self.repository.update(
            db,
            parent,
        )

    def delete_parent(
        self,
        db: Session,
        parent_id: UUID,
    ) -> None:

        parent = self.get_parent(db, parent_id)

        self.repository.delete(
            db,
            parent,
        )


parent_service = ParentService(
    repository=parent_repository,
    school_repository=school_repository,
)