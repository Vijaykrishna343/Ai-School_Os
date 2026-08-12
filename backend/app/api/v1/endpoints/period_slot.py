from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_period_slot_service, get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.timetable.period_slot import (
    PeriodSlotCreate,
    PeriodSlotFilter,
    PeriodSlotListResponse,
    PeriodSlotResponse,
    PeriodSlotUpdate,
)
from app.common.enums.timetable import PeriodType
from app.services.period_slot_service import PeriodSlotService

router = APIRouter()


@router.post(
    "",
    response_model=PeriodSlotResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_period_slot(
    slot_data: PeriodSlotCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.create")),
    service: PeriodSlotService = Depends(get_period_slot_service),
) -> PeriodSlotResponse:
    """
    Create a new PeriodSlot for the tenant school.
    """
    created = service.create_period_slot(
        db,
        slot_data=slot_data,
        current_school_id=current_user.school_id,
    )
    return PeriodSlotResponse.model_validate(created)


@router.get(
    "",
    response_model=PeriodSlotListResponse,
)
def list_period_slots(
    period_type: PeriodType | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: PeriodSlotService = Depends(get_period_slot_service),
) -> PeriodSlotListResponse:
    """
    List paginated PeriodSlots for the current school.
    """
    filters = PeriodSlotFilter(
        school_id=current_user.school_id,
        period_type=period_type,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.list_period_slots(
        db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/{slot_id}",
    response_model=PeriodSlotResponse,
)
def get_period_slot(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.view")),
    service: PeriodSlotService = Depends(get_period_slot_service),
) -> PeriodSlotResponse:
    """
    Get a specific PeriodSlot by ID.
    """
    slot = service.get_period_slot(
        db,
        slot_id=slot_id,
        current_school_id=current_user.school_id,
    )
    return PeriodSlotResponse.model_validate(slot)


@router.put(
    "/{slot_id}",
    response_model=PeriodSlotResponse,
)
def update_period_slot(
    slot_id: UUID,
    slot_data: PeriodSlotUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.update")),
    service: PeriodSlotService = Depends(get_period_slot_service),
) -> PeriodSlotResponse:
    """
    Update an existing PeriodSlot.
    """
    updated = service.update_period_slot(
        db,
        slot_id=slot_id,
        slot_data=slot_data,
        current_school_id=current_user.school_id,
    )
    return PeriodSlotResponse.model_validate(updated)


@router.delete(
    "/{slot_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_period_slot(
    slot_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("timetable.delete")),
    service: PeriodSlotService = Depends(get_period_slot_service),
) -> None:
    """
    Soft delete a PeriodSlot.
    """
    service.delete_period_slot(
        db,
        slot_id=slot_id,
        current_school_id=current_user.school_id,
        current_user_id=current_user.id,
    )
