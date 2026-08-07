from pydantic import BaseModel, ConfigDict, EmailStr


class ForgotPassword(BaseModel):
    email: EmailStr

    model_config = ConfigDict(
        str_strip_whitespace=True,
    )