from pydantic import BaseModel


class UserStatusUpdate(BaseModel):
    """
    Request body for updating user status (e.g. SUSPENDED, ACTIVE).
    """

    status: str
    suspension_reason: str | None = None
