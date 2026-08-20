from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserResponse(BaseModel):
    id: UUID

    school_id: UUID

    email: str

    username: str | None

    first_name: str

    last_name: str | None

    phone: str | None

    is_active: bool

    status: str = "ACTIVE"

    suspended_at: datetime | None = None

    suspension_reason: str | None = None

    is_verified: bool

    last_login: datetime | None


    created_at: datetime

    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,
    )