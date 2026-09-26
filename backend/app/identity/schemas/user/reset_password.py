from pydantic import BaseModel, ConfigDict, Field


class ResetPassword(BaseModel):
    token: str = Field(..., min_length=1)

    new_password: str = Field(
        ...,
        min_length=8,
        max_length=128,
    )

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class ResetPasswordResponse(BaseModel):
    success: bool = True
    message: str = "Password has been successfully reset. Please log in with your new password."