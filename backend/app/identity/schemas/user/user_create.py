from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserCreate(BaseModel):
    school_id: UUID

    email: EmailStr

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    first_name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    last_name: str | None = Field(
        default=None,
        max_length=100,
    )

    phone: str | None = Field(
        default=None,
        max_length=20,
    )

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )