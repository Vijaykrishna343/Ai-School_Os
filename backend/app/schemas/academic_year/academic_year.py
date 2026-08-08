from datetime import date
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums import AcademicYearStatus


class AcademicYearBase(BaseModel):
    """
    Shared fields for AcademicYear.
    """

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
    """
    Request body for creating an AcademicYear.
    """

    school_id: UUID


class AcademicYearUpdate(BaseModel):
    """
    Request body for updating an AcademicYear.
    """

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
    """
    API response representation for AcademicYear.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID


class AcademicYearListResponse(BaseModel):
    """
    Paginated API response representation for AcademicYear lists.
    """

    items: list[AcademicYearResponse]
    total: int
    page: int
    page_size: int
    total_pages: int

    model_config = ConfigDict(from_attributes=True)