from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.common.enums.school import SchoolStatus


class SchoolBase(BaseModel):
    """
    Shared fields for School.
    """

    name: str
    code: str

    email: EmailStr | None = None
    phone: str | None = None

    website: str | None = None
    logo_url: str | None = None

    address_line1: str
    address_line2: str | None = None

    city: str
    district: str
    state: str
    country: str = "India"

    postal_code: str

    status: SchoolStatus = SchoolStatus.ACTIVE


class SchoolCreate(SchoolBase):
    """
    Request body for creating a school.
    """
    pass


class SchoolUpdate(BaseModel):
    """
    Request body for updating a school.
    """

    name: str | None = None
    email: EmailStr | None = None
    phone: str | None = None

    website: str | None = None
    logo_url: str | None = None

    address_line1: str | None = None
    address_line2: str | None = None

    city: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None

    postal_code: str | None = None

    status: SchoolStatus | None = None


class SchoolResponse(SchoolBase):
    """
    API response representation for School.
    """

    id: UUID

    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SchoolListResponse(BaseModel):
    """
    Paginated API response representation for School lists.
    """

    items: list[SchoolResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)