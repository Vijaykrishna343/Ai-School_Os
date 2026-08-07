from pydantic import BaseModel

from .user_response import UserResponse


class UserListResponse(BaseModel):
    items: list[UserResponse]

    total: int

    page: int

    page_size: int