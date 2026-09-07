from datetime import date
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.visitor import HostType, ReceptionInquiryStatus
from app.dependencies import get_db, get_reception_inquiry_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.visitor import (
    ReceptionInquiryCreate,
    ReceptionInquiryListResponse,
    ReceptionInquiryResponse,
    ReceptionInquiryUpdate,
)
from app.services.reception_inquiry_service import ReceptionInquiryService

router = APIRouter()


@router.post(
    "",
    response_model=ReceptionInquiryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Reception Inquiry / Appointment",
)
def create_inquiry(
    data: ReceptionInquiryCreate,
    current_user: IdentityUser = Depends(require_permission("reception.create")),
    db: Session = Depends(get_db),
    service: ReceptionInquiryService = Depends(get_reception_inquiry_service),
) -> ReceptionInquiryResponse:
    """
    Logs a new front-desk reception inquiry or appointment.
    Enforces tenant isolation, host & visitor linkage validation, and initial status server rules.
    """
    user_role = current_user.roles[0].name if current_user.roles else "User"
    return service.create_inquiry(
        db=db,
        current_school_id=current_user.school_id,
        data=data,
        current_user=current_user,
        user_role=user_role,
    )


@router.get(
    "",
    response_model=ReceptionInquiryListResponse,
    summary="List Reception Inquiries",
)
def list_inquiries(
    status: ReceptionInquiryStatus | None = Query(
        default=None, description="Filter by inquiry status"
    ),
    start_date: date | None = Query(
        default=None, description="Filter by creation start date (YYYY-MM-DD)"
    ),
    end_date: date | None = Query(
        default=None, description="Filter by creation end date (YYYY-MM-DD)"
    ),
    appointment_date: date | None = Query(
        default=None, description="Filter by appointment date (YYYY-MM-DD)"
    ),
    visitor_id: UUID | None = Query(
        default=None, description="Filter by linked visitor ID"
    ),
    host_type: HostType | None = Query(
        default=None, description="Filter by host type (TEACHER, STAFF, STUDENT)"
    ),
    host_id: UUID | None = Query(
        default=None, description="Filter by host entity ID"
    ),
    search: str | None = Query(
        default=None, description="Search by contact name, phone, or subject"
    ),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("reception.view")),
    db: Session = Depends(get_db),
    service: ReceptionInquiryService = Depends(get_reception_inquiry_service),
) -> ReceptionInquiryListResponse:
    """
    Lists paginated reception inquiries for the current authenticated user's school.
    Excludes soft-deleted records and enforces multi-tenant isolation.
    """
    return service.list_inquiries(
        db=db,
        current_school_id=current_user.school_id,
        status=status,
        start_date=start_date,
        end_date=end_date,
        appointment_date=appointment_date,
        visitor_id=visitor_id,
        host_type=host_type,
        host_id=host_id,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{id}",
    response_model=ReceptionInquiryResponse,
    summary="Get Reception Inquiry Details",
)
def get_inquiry(
    id: UUID,
    current_user: IdentityUser = Depends(require_permission("reception.view")),
    db: Session = Depends(get_db),
    service: ReceptionInquiryService = Depends(get_reception_inquiry_service),
) -> ReceptionInquiryResponse:
    """
    Retrieves detailed reception inquiry record by ID.
    Enforces tenant isolation.
    """
    return service.get_inquiry(
        db=db,
        inquiry_id=id,
        current_school_id=current_user.school_id,
    )


@router.patch(
    "/{id}",
    response_model=ReceptionInquiryResponse,
    summary="Update Reception Inquiry",
)
def update_inquiry(
    id: UUID,
    data: ReceptionInquiryUpdate,
    current_user: IdentityUser = Depends(require_permission("reception.update")),
    db: Session = Depends(get_db),
    service: ReceptionInquiryService = Depends(get_reception_inquiry_service),
) -> ReceptionInquiryResponse:
    """
    Updates an existing reception inquiry record.
    Enforces state machine transitions, host/visitor linkage re-validation, and audit logging.
    """
    user_role = current_user.roles[0].name if current_user.roles else "User"
    return service.update_inquiry(
        db=db,
        inquiry_id=id,
        current_school_id=current_user.school_id,
        data=data,
        current_user=current_user,
        user_role=user_role,
    )
