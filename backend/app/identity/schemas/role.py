from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class RoleBase(BaseModel):
    """
    Base schema for roles.
    """

    school_id: UUID | None = None

    name: str = Field(
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )


class RoleCreate(RoleBase):
    """
    Schema used to create a role.

    Note: is_system is intentionally excluded.
    System roles are managed by the platform only.
    """

    pass


class RoleUpdate(BaseModel):
    """
    Schema used to update a role.
    """

    name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )


class RoleResponse(RoleBase):
    """
    API response schema.
    """

    id: UUID

    is_system: bool

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class RoleFilter(BaseModel):
    """
    Filtering and pagination.
    """

    school_id: UUID | None = None

    name: str | None = None

    is_system: bool | None = None

    page: int = 1

    page_size: int = 10


class RoleListResponse(BaseModel):
    """
    Paginated response.
    """

    items: list[RoleResponse]

    total: int

    page: int

    page_size: int