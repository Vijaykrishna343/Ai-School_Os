from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.subject import SubjectStatus


class SubjectUpdate(BaseModel):
    subject_code: str | None = Field(
        default=None,
        min_length=2,
        max_length=20,
    )

    subject_name: str | None = Field(
        default=None,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    is_optional: bool | None = None

    status: SubjectStatus | None = None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )