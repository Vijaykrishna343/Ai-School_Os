from __future__ import annotations

from typing import Any, Generic, TypeVar
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import NotFoundException
from app.repositories.base import BaseRepository

RepositoryType = TypeVar(
    "RepositoryType",
    bound=BaseRepository,
)


class BaseService(Generic[RepositoryType]):
    """
    Base service for all business services.

    Provides common helper methods shared by every service.
    """

    def __init__(
        self,
        repository: RepositoryType,
    ) -> None:
        """
        Initialize the base service with a repository instance.
        """
        self.repository = repository

    def get_by_id(
        self,
        db: Session,
        obj_id: UUID,
        resource_name: str,
    ) -> Any:
        """
        Retrieve an entity by ID or raise NotFoundException.
        """
        obj = self.repository.get(
            db,
            obj_id,
        )

        if obj is None:
            raise NotFoundException(resource_name, str(obj_id))

        return obj

    def delete(
        self,
        db: Session,
        obj_id: UUID,
        resource_name: str,
    ) -> None:
        """
        Soft delete an entity by ID.
        """
        obj = self.get_by_id(
            db,
            obj_id,
            resource_name,
        )

        self.repository.delete(
            db,
            obj,
        )