from pydantic import BaseModel


class UserLogout(BaseModel):
    refresh_token: str | None = None


class UserLogoutResponse(BaseModel):
    message: str = "Logged out successfully"
