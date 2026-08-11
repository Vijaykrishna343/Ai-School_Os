from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class AcademicTermBase(BaseModel):
    """
    Shared fields for AcademicTerm.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["Term 1", "Semester 1"],
    )

    code: str = Field(
        ...,
        min_length=1,
        max_length=20,
        examples=["TERM1", "SEM1"],
    )

    start_date: date
    end_date: date

    display_order: int = Field(default=1, ge=1)
    is_active: bool = Field(default=True)


class AcademicTermCreate(AcademicTermBase):
    """
    Request payload for creating an AcademicTerm.
    """

    school_id: UUID
    academic_year_id: UUID


class AcademicTermUpdate(BaseModel):
    """
    Request payload for updating an AcademicTerm.
    """

    name: str | None = Field(default=None, min_length=1, max_length=50)
    code: str | None = Field(default=None, min_length=1, max_length=20)

    start_date: date | None = None
    end_date: date | None = None

    display_order: int | None = Field(default=None, ge=1)
    is_active: bool | None = None


class AcademicTermResponse(AcademicTermBase):
    """
    API response representation for AcademicTerm.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    created_at: datetime
    updated_at: datetime


class AcademicTermListResponse(BaseModel):
    """
    Paginated API response representation for AcademicTerm lists.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[AcademicTermResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class AcademicTermFilter(BaseModel):
    """
    Filter parameters for listing AcademicTerms.
    """

    school_id: UUID | None = None
    academic_year_id: UUID | None = None
    is_active: bool | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
