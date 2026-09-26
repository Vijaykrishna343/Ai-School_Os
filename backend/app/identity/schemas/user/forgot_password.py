from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ForgotPassword(BaseModel):
    email: EmailStr
    school_code: Optional[str] = Field(None, max_length=50, description="Optional school code to resolve tenant ambiguity")

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )


class ForgotPasswordResponse(BaseModel):
    success: bool = True
    message: str = "If an account with that email exists, password reset instructions have been sent."