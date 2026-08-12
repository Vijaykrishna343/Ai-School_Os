from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_timetable_entry_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.timetable.timetable_entry import (
    TimetableEntryDetailResponse,
    TimetableEntryUpdate,
)
from app.services.timetable_entry_service import TimetableEntryService

router = APIRouter()


@router.put(
    "/{entry_id}",
    response_model=TimetableEntryDetailResponse,
)
def update_timetable_entry(
    entry_id: UUID,
    entry_data: TimetableEntryUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.update")),
    service: TimetableEntryService = Depends(get_timetable_entry_service),
) -> TimetableEntryDetailResponse:
    """
    Update an existing TimetableEntry.
    """
    updated = service.update_entry(
        db,
        entry_id=entry_id,
        entry_data=entry_data,
        current_school_id=current_user.school_id,
    )
    return TimetableEntryDetailResponse.model_validate(updated)


@router.delete(
    "/{entry_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_timetable_entry(
    entry_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.delete")),
    service: TimetableEntryService = Depends(get_timetable_entry_service),
) -> None:
    """
    Soft delete a TimetableEntry.
    """
    service.delete_entry(
        db,
        entry_id=entry_id,
        current_school_id=current_user.school_id,
    )
