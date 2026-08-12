from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_classroom_service, get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.timetable.classroom import (
    ClassroomCreate,
    ClassroomFilter,
    ClassroomListResponse,
    ClassroomResponse,
    ClassroomUpdate,
)
from app.common.enums.timetable import RoomType
from app.services.classroom_service import ClassroomService

router = APIRouter()


@router.post(
    "",
    response_model=ClassroomResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_classroom(
    classroom_data: ClassroomCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.create")),
    service: ClassroomService = Depends(get_classroom_service),
) -> ClassroomResponse:
    """
    Create a new Classroom for the tenant school.
    """
    created = service.create_classroom(
        db,
        classroom_data=classroom_data,
        current_school_id=current_user.school_id,
    )
    return ClassroomResponse.model_validate(created)


@router.get(
    "",
    response_model=ClassroomListResponse,
)
def list_classrooms(
    room_type: RoomType | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: ClassroomService = Depends(get_classroom_service),
) -> ClassroomListResponse:
    """
    List paginated Classrooms for the current school.
    """
    filters = ClassroomFilter(
        school_id=current_user.school_id,
        room_type=room_type,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.list_classrooms(
        db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/{classroom_id}",
    response_model=ClassroomResponse,
)
def get_classroom(
    classroom_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: ClassroomService = Depends(get_classroom_service),
) -> ClassroomResponse:
    """
    Get a specific Classroom by ID.
    """
    classroom = service.get_classroom(
        db,
        classroom_id=classroom_id,
        current_school_id=current_user.school_id,
    )
    return ClassroomResponse.model_validate(classroom)


@router.put(
    "/{classroom_id}",
    response_model=ClassroomResponse,
)
def update_classroom(
    classroom_id: UUID,
    classroom_data: ClassroomUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.update")),
    service: ClassroomService = Depends(get_classroom_service),
) -> ClassroomResponse:
    """
    Update an existing Classroom.
    """
    updated = service.update_classroom(
        db,
        classroom_id=classroom_id,
        classroom_data=classroom_data,
        current_school_id=current_user.school_id,
    )
    return ClassroomResponse.model_validate(updated)


@router.delete(
    "/{classroom_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_classroom(
    classroom_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.delete")),
    service: ClassroomService = Depends(get_classroom_service),
) -> None:
    """
    Soft delete a Classroom.
    """
    service.delete_classroom(
        db,
        classroom_id=classroom_id,
        current_school_id=current_user.school_id,
        current_user_id=current_user.id,
    )
