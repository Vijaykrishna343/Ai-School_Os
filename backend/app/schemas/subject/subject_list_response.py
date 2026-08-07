from pydantic import BaseModel, ConfigDict

from app.schemas.subject.subject_response import SubjectResponse


class SubjectListResponse(BaseModel):
    items: list[SubjectResponse]

    total: int

    page: int

    page_size: int

    model_config = ConfigDict(
        from_attributes=True,
    )