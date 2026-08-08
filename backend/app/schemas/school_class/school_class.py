from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import SchoolClassStatus


class SchoolClassBase(BaseModel):
    """
    Shared fields for SchoolClass.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=30,
        examples=["Class 1"],
    )

    display_order: int = Field(
        ...,
        gt=0,
        examples=[1],
    )

    status: SchoolClassStatus = SchoolClassStatus.ACTIVE


class SchoolClassCreate(SchoolClassBase):
    """
    Request body for creating a SchoolClass.
    """

    school_id: UUID


class SchoolClassUpdate(BaseModel):
    """
    Request body for updating a SchoolClass.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=30,
    )

    display_order: int | None = Field(
        default=None,
        gt=0,
    )

    status: SchoolClassStatus | None = None


class SchoolClassResponse(SchoolClassBase):
    """
    API response representation for SchoolClass.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    school_id: UUID


class SchoolClassListResponse(BaseModel):
    """
    Paginated API response representation for SchoolClass lists.
    """

    items: list[SchoolClassResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)