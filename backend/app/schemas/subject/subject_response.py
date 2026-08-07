from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.enums.subject import SubjectStatus


class SubjectResponse(BaseModel):
    id: UUID

    school_id: UUID

    subject_code: str

    subject_name: str

    description: str | None

    is_optional: bool

    status: SubjectStatus

    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )