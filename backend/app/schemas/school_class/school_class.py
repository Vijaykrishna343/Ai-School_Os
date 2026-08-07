import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import SchoolClassStatus


class SchoolClassBase(BaseModel):
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
    school_id: uuid.UUID


class SchoolClassUpdate(BaseModel):
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
    model_config = ConfigDict(
        from_attributes=True,
    )

    id: uuid.UUID
    school_id: uuid.UUID