from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserFilter(BaseModel):
    school_id: UUID | None = None

    email: str | None = None

    username: str | None = None

    first_name: str | None = None

    is_active: bool | None = None

    page: int = 1

    page_size: int = 10

    model_config = ConfigDict(
        from_attributes=True,
    )