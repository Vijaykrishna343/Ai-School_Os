from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.enums.subject import SubjectStatus


class SubjectFilter(BaseModel):
    school_id: UUID | None = None

    subject_name: str | None = None

    subject_code: str | None = None

    status: SubjectStatus | None = None

    is_optional: bool | None = None

    page: int = 1

    page_size: int = 10

    model_config = ConfigDict(
        from_attributes=True,
    )