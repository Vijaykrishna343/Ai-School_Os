from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class PermissionBase(BaseModel):
    """
    Base schema.
    """

    name: str = Field(
        min_length=3,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=255,
    )

    module: str = Field(
        min_length=2,
        max_length=50,
    )

    action: str = Field(
        min_length=2,
        max_length=50,
    )


class PermissionCreate(PermissionBase):
    """
    Create schema.
    """

    pass


class PermissionUpdate(BaseModel):
    """
    Update schema.
    """

    name: str | None = None

    description: str | None = None

    module: str | None = None

    action: str | None = None


class PermissionResponse(PermissionBase):
    """
    Response schema.
    """

    id: UUID

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )


class PermissionFilter(BaseModel):
    """
    Filtering.
    """

    module: str | None = None

    action: str | None = None

    page: int = 1

    page_size: int = 10


class PermissionListResponse(BaseModel):
    """
    Paginated response.
    """

    items: list[PermissionResponse]

    total: int

    page: int

    page_size: int