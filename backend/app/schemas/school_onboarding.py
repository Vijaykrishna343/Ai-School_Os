from __future__ import annotations

from datetime import date
from uuid import UUID
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminCredentialsInput(BaseModel):
    """
    Initial School Administrator credentials and details.
    """
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    username: str | None = Field(default=None, max_length=100)
    password: str = Field(..., min_length=8, max_length=128)
    phone: str | None = Field(default=None, max_length=20)


class AcademicYearInput(BaseModel):
    """
    Initial primary academic year configuration.
    """
    name: str = Field(..., min_length=1, max_length=30)
    start_date: date
    end_date: date
    is_current: bool = True


class ClassTemplateItem(BaseModel):
    """
    Optional class and section template item.
    """
    name: str = Field(..., min_length=1, max_length=30)
    display_order: int = Field(default=1, ge=1)
    create_default_section: bool = True
    default_section_name: str = Field(default="A", max_length=10)
    capacity: int = Field(default=40, ge=1, le=500)


class SchoolOnboardingRequest(BaseModel):
    """
    Payload for provisioning a new School Tenant.
    """
    name: str = Field(..., min_length=2, max_length=150)
    code: str = Field(..., min_length=2, max_length=20)
    email: EmailStr | None = None
    phone: str | None = Field(default=None, max_length=20)
    website: str | None = Field(default=None, max_length=255)
    logo_url: str | None = Field(default=None, max_length=500)

    address_line1: str = Field(..., min_length=1, max_length=255)
    address_line2: str | None = Field(default=None, max_length=255)
    city: str = Field(..., min_length=1, max_length=100)
    district: str = Field(..., min_length=1, max_length=100)
    state: str = Field(..., min_length=1, max_length=100)
    country: str = Field(default="India", max_length=100)
    postal_code: str = Field(..., min_length=1, max_length=10)

    subscription_tier: str = Field(default="STANDARD", max_length=50)
    max_students: int | None = Field(default=500, ge=1)
    max_teachers: int | None = Field(default=50, ge=1)

    admin: AdminCredentialsInput
    academic_year: AcademicYearInput
    class_templates: list[ClassTemplateItem] | None = None


class SchoolOnboardingResponse(BaseModel):
    """
    Safe response returned upon successful school tenant onboarding.
    Never exposes passwords, hashes, or secrets.
    """
    model_config = ConfigDict(from_attributes=True)

    school_id: UUID
    name: str
    code: str
    status: str
    subscription_tier: str
    admin_user_id: UUID
    admin_email: str
    admin_name: str
    academic_year_id: UUID
    academic_year_name: str
    roles_provisioned_count: int
    classes_provisioned_count: int
    message: str = "School tenant provisioned successfully."
