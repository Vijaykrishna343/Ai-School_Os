import uuid

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

    school_class_id: uuid.UUID


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
    Schema returned to clients.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    school_class_id: uuid.UUID