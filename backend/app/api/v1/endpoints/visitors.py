from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.visitor import VisitorStatus
from app.dependencies import get_db, get_visitor_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.visitor import (
    VisitorCheckOut,
    VisitorCreate,
    VisitorListResponse,
    VisitorResponse,
)
from app.services.visitor_service import VisitorService

router = APIRouter()


@router.post(
    "/check-in",
    response_model=VisitorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Check In Campus Visitor",
)
def check_in_visitor(
    data: VisitorCreate,
    current_user: IdentityUser = Depends(require_permission("visitors.checkin")),
    db: Session = Depends(get_db),
    service: VisitorService = Depends(get_visitor_service),
) -> VisitorResponse:
    """
    Registers and checks in a visitor for the current authenticated user's school.
    Server-generates check-in timestamp and tenant-unique gate pass number.
    """
    user_role = current_user.roles[0].name if current_user.roles else "User"
    return service.check_in_visitor(
        db=db,
        current_school_id=current_user.school_id,
        data=data,
        current_user=current_user,
        user_role=user_role,
    )


@router.post(
    "/{id}/check-out",
    response_model=VisitorResponse,
    status_code=status.HTTP_200_OK,
    summary="Check Out Active Visitor",
)
def check_out_visitor(
    id: UUID,
    payload: VisitorCheckOut | None = None,
    current_user: IdentityUser = Depends(require_permission("visitors.checkout")),
    db: Session = Depends(get_db),
    service: VisitorService = Depends(get_visitor_service),
) -> VisitorResponse:
    """
    Checks out an active visitor.
    Enforces state machine transitions and server-generates checkout timestamp.
    """
    user_role = current_user.roles[0].name if current_user.roles else "User"
    remarks = payload.remarks if payload else None
    return service.check_out_visitor(
        db=db,
        visitor_id=id,
        current_school_id=current_user.school_id,
        remarks=remarks,
        current_user=current_user,
        user_role=user_role,
    )


@router.get(
    "",
    response_model=VisitorListResponse,
    summary="List Campus Visitors",
)
def list_visitors(
    status: VisitorStatus | None = Query(default=None, description="Filter by visitor status"),
    search: str | None = Query(default=None, description="Search by name, phone, pass number, or purpose"),
    start_date: date | None = Query(default=None, description="Filter by check-in start date (YYYY-MM-DD)"),
    end_date: date | None = Query(default=None, description="Filter by check-in end date (YYYY-MM-DD)"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("visitors.view")),
    db: Session = Depends(get_db),
    service: VisitorService = Depends(get_visitor_service),
) -> VisitorListResponse:
    """
    List paginated visitors for the current authenticated user's school.
    Protects PII by omitting sensitive ID proof numbers in list view summaries.
    """
    return service.list_visitors(
        db=db,
        current_school_id=current_user.school_id,
        status=status,
        search=search,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=VisitorResponse,
    summary="Get Visitor Details by ID",
)
def get_visitor(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("visitors.view")),
    db: Session = Depends(get_db),
    service: VisitorService = Depends(get_visitor_service),
) -> VisitorResponse:
    """
    Retrieve detailed visitor information for an authorized single-record view.
    """
    return service.get_visitor(
        db=db,
        visitor_id=id,
        current_school_id=current_user.school_id,
    )
