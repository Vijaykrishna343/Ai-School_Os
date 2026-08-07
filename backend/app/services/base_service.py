from __future__ import annotations

from typing import Generic, TypeVar
from uuid import UUID

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
    ):
        self.repository = repository

    def get_by_id(
        self,
        db,
        obj_id: UUID,
        resource_name: str,
    ):
        """
        Retrieve an entity or raise NotFoundException.
        """

        obj = self.repository.get(
            db,
            obj_id,
        )

        if obj is None:
            raise NotFoundException(resource_name)

        return obj

    def delete(
        self,
        db,
        obj_id: UUID,
        resource_name: str,
    ) -> None:
        """
        Soft delete an entity.
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