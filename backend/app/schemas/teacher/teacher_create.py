from datetime import date
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.common.enums.teacher import (
    BloodGroup,
    Gender,
    TeacherStatus,
)


class TeacherCreate(BaseModel):
    school_id: UUID

    first_name: str
    middle_name: str | None = None
    last_name: str

    gender: Gender
    blood_group: BloodGroup | None = None

    date_of_birth: date
    joining_date: date

    qualification: str
    specialization: str | None = None
    experience_years: int = 0

    phone: str
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

    status: TeacherStatus = TeacherStatus.ACTIVE

    model_config = ConfigDict(
        from_attributes=True,
    )