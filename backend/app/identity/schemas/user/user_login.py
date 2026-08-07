from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserLogin(BaseModel):
    school_code: str = Field(
        ...,
        min_length=2,
        max_length=20,
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )