from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import SectionStatus


class SectionBase(BaseModel):
    """
    Base schema for Section.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=10,
        examples=["A"],
    )

    room_number: str | None = Field(
        default=None,
        max_length=20,
        examples=["101"],
    )

    capacity: int = Field(
        default=40,
        ge=1,
        examples=[40],
    )

    status: SectionStatus = SectionStatus.ACTIVE


class SectionCreate(SectionBase):
    """
    Schema for creating a section.
    """

    school_class_id: UUID


class SectionUpdate(BaseModel):
    """
    Schema for updating a section.
    """

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=10,
    )

    room_number: str | None = Field(
        default=None,
        max_length=20,
    )

    capacity: int | None = Field(
        default=None,
        ge=1,
    )

    status: SectionStatus | None = None


class SectionResponse(SectionBase):
    """
    Schema returned to clients for Section.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: UUID
    school_class_id: UUID


class SectionListResponse(BaseModel):
    """
    Paginated API response representation for Section lists.
    """

    items: list[SectionResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)