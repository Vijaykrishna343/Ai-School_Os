from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, EmailStr

from app.common.enums.teacher import (
    BloodGroup,
    Gender,
    TeacherStatus,
)


class TeacherUpdate(BaseModel):
    first_name: str | None = None
    middle_name: str | None = None
    last_name: str | None = None

    gender: Gender | None = None
    blood_group: BloodGroup | None = None

    date_of_birth: date | None = None
    joining_date: date | None = None

    qualification: str | None = None
    specialization: str | None = None
    experience_years: int | None = None

    phone: str | None = None
    email: EmailStr | None = None
    emergency_contact: str | None = None

    profile_photo_url: str | None = None

    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    salary: Decimal | None = None
    remarks: str | None = None

    status: TeacherStatus | None = None

    model_config = ConfigDict(
        from_attributes=True,
    )