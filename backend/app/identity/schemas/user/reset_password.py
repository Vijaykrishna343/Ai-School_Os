from pydantic import BaseModel, ConfigDict, Field


class ResetPassword(BaseModel):
    token: str

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )