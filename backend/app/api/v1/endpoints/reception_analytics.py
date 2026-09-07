from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_reception_analytics_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.visitor import ReceptionAnalyticsResponse
from app.services.reception_analytics_service import ReceptionAnalyticsService

router = APIRouter()


@router.get(
    "",
    response_model=ReceptionAnalyticsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Reception Analytics & Operational Reporting",
)
def get_reception_analytics(
    start_date: date | None = Query(
        default=None, description="Start date for analytics filter (YYYY-MM-DD)"
    ),
    end_date: date | None = Query(
        default=None, description="End date for analytics filter (YYYY-MM-DD)"
    ),
    current_user: IdentityUser = Depends(require_permission("reception.view")),
    db: Session = Depends(get_db),
    service: ReceptionAnalyticsService = Depends(get_reception_analytics_service),
) -> ReceptionAnalyticsResponse:
    """
    Returns aggregated metrics, daily activity trends, and operational statistics
    for reception desk activity, visitors, inquiries, and appointments.
    Strictly isolated by current_user.school_id.
    """
    return service.get_analytics(
        db=db,
        school_id=current_user.school_id,
        start_date=start_date,
        end_date=end_date,
    )
