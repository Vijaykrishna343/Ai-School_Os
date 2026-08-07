from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.subject import SubjectStatus


class SubjectCreate(BaseModel):
    school_id: UUID

    subject_code: str = Field(
        ...,
        min_length=2,
        max_length=20,
        examples=["MAT101"],
    )

    subject_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
        examples=["Mathematics"],
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_optional: bool = False

    status: SubjectStatus = SubjectStatus.ACTIVE

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )