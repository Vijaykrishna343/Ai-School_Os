from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr

from app.common.enums.parent import ParentRelationship


class ParentBase(BaseModel):
    father_name: str
    mother_name: str | None = None
    guardian_name: str | None = None

    relationship: ParentRelationship = ParentRelationship.FATHER

    primary_phone: str
    secondary_phone: str | None = None

    email: EmailStr | None = None

    occupation: str | None = None
    annual_income: Decimal | None = None

    address_line1: str
    address_line2: str | None = None

    city: str
    district: str
    state: str
    country: str = "India"
    postal_code: str

    school_id: UUID

    is_active: bool = True


class ParentCreate(ParentBase):
    pass


class ParentUpdate(BaseModel):
    father_name: str | None = None
    mother_name: str | None = None
    guardian_name: str | None = None

    relationship: ParentRelationship | None = None

    primary_phone: str | None = None
    secondary_phone: str | None = None

    email: EmailStr | None = None

    occupation: str | None = None
    annual_income: Decimal | None = None

    address_line1: str | None = None
    address_line2: str | None = None

    city: str | None = None
    district: str | None = None
    state: str | None = None
    country: str | None = None
    postal_code: str | None = None

    school_id: UUID | None = None

    is_active: bool | None = None


class ParentResponse(ParentBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    is_deleted: bool
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)