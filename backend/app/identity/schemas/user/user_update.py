from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserUpdate(BaseModel):
    email: EmailStr | None = None

    username: str | None = Field(
        default=None,
        min_length=3,
        max_length=100,
    )

    first_name: str | None = Field(
        default=None,
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

    is_active: bool | None = None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
    )