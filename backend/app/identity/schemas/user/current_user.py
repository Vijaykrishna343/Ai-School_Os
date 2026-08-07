from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class CurrentUser(BaseModel):
    id: UUID

    school_id: UUID

    email: str

    username: str | None

    first_name: str

    last_name: str | None

    is_active: bool

    is_verified: bool

    last_login: datetime | None

    model_config = ConfigDict(
        from_attributes=True,
    )