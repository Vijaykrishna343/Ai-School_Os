from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.timetable import RoomType


class ClassroomBase(BaseModel):
    """
    Shared fields for Classroom.
    """

    room_number: str = Field(
        ...,
        min_length=1,
        max_length=30,
        examples=["101", "Lab-2"],
    )

    building_name: str | None = Field(
        default=None,
        max_length=100,
        examples=["Main Building"],
    )

    capacity: int = Field(default=40, ge=1)

    room_type: RoomType = Field(
        default=RoomType.CLASSROOM,
        examples=[RoomType.CLASSROOM],
    )


class ClassroomCreate(ClassroomBase):
    """
    Request payload for creating a Classroom.
    """

    school_id: UUID


class ClassroomUpdate(BaseModel):
    """
    Request payload for updating a Classroom.
    """

    room_number: str | None = Field(default=None, min_length=1, max_length=30)
    building_name: str | None = Field(default=None, max_length=100)
    capacity: int | None = Field(default=None, ge=1)
    room_type: RoomType | None = None


class ClassroomResponse(ClassroomBase):
    """
    API response representation for Classroom.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    created_at: datetime
    updated_at: datetime


class ClassroomListResponse(BaseModel):
    """
    Paginated API response representation for Classroom lists.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[ClassroomResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class ClassroomFilter(BaseModel):
    """
    Filter parameters for listing Classrooms.
    """

    school_id: UUID | None = None
    room_type: RoomType | None = None
    search: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=10, ge=1, le=100)
