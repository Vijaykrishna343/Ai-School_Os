from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.report_card import ReportCardStatus
from app.dependencies import get_db, get_report_card_service
from app.identity.dependencies import require_permission
from app.identity.models import IdentityUser
from app.schemas.grading.report_card import (
    ReportCardFilter,
    ReportCardGenerateRequest,
    ReportCardListResponse,
    ReportCardRemarksUpdate,
    ReportCardResponse,
)
from app.services.report_card_service import ReportCardService

router = APIRouter()


@router.post(
    "/generate",
    response_model=list[ReportCardResponse],
    status_code=status.HTTP_201_CREATED,
)
def generate_report_cards(
    request_data: ReportCardGenerateRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.generate")),
    service: ReportCardService = Depends(get_report_card_service),
) -> list[ReportCardResponse]:
    cards = service.generate_report_cards(
        db,
        request_data=request_data,
        current_school_id=current_user.school_id,
    )
    return [ReportCardResponse.model_validate(c) for c in cards]


@router.get(
    "",
    response_model=ReportCardListResponse,
)
def list_report_cards(
    academic_year_id: UUID | None = Query(default=None),
    academic_term_id: UUID | None = Query(default=None),
    school_class_id: UUID | None = Query(default=None),
    section_id: UUID | None = Query(default=None),
    student_id: UUID | None = Query(default=None),
    card_status: ReportCardStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.view")),
    service: ReportCardService = Depends(get_report_card_service),
) -> ReportCardListResponse:
    filters = ReportCardFilter(
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        academic_term_id=academic_term_id,
        school_class_id=school_class_id,
        section_id=section_id,
        student_id=student_id,
        status=card_status,
        page=page,
        page_size=page_size,
    )
    return service.list_report_cards(
        db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/{report_card_id}",
    response_model=ReportCardResponse,
)
def get_report_card(
    report_card_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.view")),
    service: ReportCardService = Depends(get_report_card_service),
) -> ReportCardResponse:
    card = service.get_report_card(
        db,
        report_card_id=report_card_id,
        current_school_id=current_user.school_id,
    )
    return ReportCardResponse.model_validate(card)


@router.put(
    "/{report_card_id}/remarks",
    response_model=ReportCardResponse,
)
def update_report_card_remarks(
    report_card_id: UUID,
    remarks_data: ReportCardRemarksUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.edit_remarks")),
    service: ReportCardService = Depends(get_report_card_service),
) -> ReportCardResponse:
    updated = service.update_remarks(
        db,
        report_card_id=report_card_id,
        remarks_data=remarks_data,
        current_school_id=current_user.school_id,
    )
    return ReportCardResponse.model_validate(updated)


@router.put(
    "/{report_card_id}/finalize",
    response_model=ReportCardResponse,
)
def finalize_report_card(
    report_card_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.finalize")),
    service: ReportCardService = Depends(get_report_card_service),
) -> ReportCardResponse:
    finalized = service.finalize_report_card(
        db,
        report_card_id=report_card_id,
        current_user_id=current_user.id,
        current_school_id=current_user.school_id,
    )
    return ReportCardResponse.model_validate(finalized)


@router.put(
    "/{report_card_id}/publish",
    response_model=ReportCardResponse,
)
def publish_report_card(
    report_card_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.publish")),
    service: ReportCardService = Depends(get_report_card_service),
) -> ReportCardResponse:
    published = service.publish_report_card(
        db,
        report_card_id=report_card_id,
        current_user_id=current_user.id,
        current_school_id=current_user.school_id,
    )
    return ReportCardResponse.model_validate(published)
