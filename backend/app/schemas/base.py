from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    Base schema for all Pydantic models.

    Enables ORM/model validation for SQLAlchemy models.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class BaseResponseSchema(BaseSchema):
    """
    Common response fields shared by all entities.
    """

    id: UUID
    created_at: datetime
    updated_at: datetime


class UUIDResponseSchema(BaseSchema):
    """
    Generic schema for endpoints returning only an ID.
    """

    id: UUID


class PaginationResponseSchema(BaseSchema):
    """
    Common pagination metadata.
    """

    total: int
    page: int
    page_size: int
    total_pages: int