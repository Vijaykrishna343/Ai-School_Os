from datetime import datetime, time
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.common.enums.timetable import PeriodType


class PeriodSlotBase(BaseModel):
    """
    Shared fields for PeriodSlot.
    """

    name: str = Field(
        ...,
        min_length=1,
        max_length=50,
        examples=["Period 1", "Lunch Break"],
    )

    period_type: PeriodType = Field(
        default=PeriodType.REGULAR,
        examples=[PeriodType.REGULAR],
    )

    start_time: time = Field(..., examples=["08:30:00"])
    end_time: time = Field(..., examples=["09:15:00"])

    display_order: int = Field(..., ge=1)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time >= self.end_time:
            raise ValueError("start_time must be before end_time.")
        return self


class PeriodSlotCreate(PeriodSlotBase):
    """
    Request payload for creating a PeriodSlot.
    """

    school_id: UUID


class PeriodSlotUpdate(BaseModel):
    """
    Request payload for updating a PeriodSlot.
    """

    name: str | None = Field(default=None, min_length=1, max_length=50)
    period_type: PeriodType | None = None
    start_time: time | None = None
    end_time: time | None = None
    display_order: int | None = Field(default=None, ge=1)

    @model_validator(mode="after")
    def validate_time_range(self):
        if self.start_time is not None and self.end_time is not None:
            if self.start_time >= self.end_time:
                raise ValueError("start_time must be before end_time.")
        return self


class PeriodSlotResponse(PeriodSlotBase):
    """
    API response representation for PeriodSlot.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    created_at: datetime
    updated_at: datetime


class PeriodSlotListResponse(BaseModel):
    """
    Paginated API response representation for PeriodSlot lists.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[PeriodSlotResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class PeriodSlotFilter(BaseModel):
    """
    Filter parameters for listing PeriodSlots.
    """

    school_id: UUID | None = None
    period_type: PeriodType | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
