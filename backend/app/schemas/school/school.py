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
    subscription_tier: str = "STANDARD"

    max_students: int | None = None
    max_teachers: int | None = None

    trial_ends_at: datetime | None = None
    subscription_expires_at: datetime | None = None
    grace_period_ends_at: datetime | None = None
    suspended_at: datetime | None = None
    suspension_reason: str | None = None


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


class SchoolStatusUpdate(BaseModel):
    """
    Request body for updating school status (Super Admin only).
    """

    status: SchoolStatus
    suspension_reason: str | None = None


class SchoolSubscriptionUpdate(BaseModel):
    """
    Request body for updating school subscription details (Super Admin only).
    """

    subscription_tier: str = "STANDARD"
    max_students: int | None = None
    max_teachers: int | None = None
    trial_ends_at: datetime | None = None
    subscription_expires_at: datetime | None = None
    grace_period_ends_at: datetime | None = None


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