from pydantic import BaseModel


class UserLoginResponse(BaseModel):
    access_token: str

    refresh_token: str

    token_type: str = "Bearer"

    expires_in: int