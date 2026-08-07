import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import AcademicYearStatus


class AcademicYearBase(BaseModel):
    name: str = Field(
        ...,
        min_length=4,
        max_length=30,
        examples=["2026-2027"],
    )

    start_date: date
    end_date: date

    status: AcademicYearStatus = AcademicYearStatus.UPCOMING

    is_current: bool = False


class AcademicYearCreate(AcademicYearBase):
    school_id: uuid.UUID


class AcademicYearUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=4,
        max_length=30,
    )

    start_date: date | None = None
    end_date: date | None = None

    status: AcademicYearStatus | None = None

    is_current: bool | None = None


class AcademicYearResponse(AcademicYearBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    school_id: uuid.UUID