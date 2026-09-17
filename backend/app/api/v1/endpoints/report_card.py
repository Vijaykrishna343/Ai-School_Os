from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.common.authorization import enforce_relationship_access
from app.common.enums.report_card import ReportCardStatus
from app.common.exceptions import ForbiddenException
from app.dependencies import get_db, get_report_card_service
from app.identity.dependencies import require_permission
from app.identity.models import IdentityUser
from app.schemas.grading.report_card import (
    BatchReportCardBatchFinalizeRequest,
    BatchReportCardBatchFinalizeResponse,
    BatchReportCardBatchGenerateRequest,
    BatchReportCardBatchGenerateResponse,
    BatchReportCardPreviewRequest,
    BatchReportCardPreviewResponse,
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
    allowed_scope = enforce_relationship_access(
        db,
        school_id=current_user.school_id,
        current_user=current_user,
        target_student_id=None,
    )

    effective_student_ids: list[UUID] | None = None
    effective_student_id: UUID | None = None
    effective_status = card_status

    if isinstance(allowed_scope, list):
        if not allowed_scope:
            return ReportCardListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        # Parent persona: strictly restricted to PUBLISHED cards
        effective_status = ReportCardStatus.PUBLISHED
        if student_id is not None:
            if student_id in allowed_scope:
                effective_student_ids = [student_id]
            else:
                return ReportCardListResponse(
                    items=[],
                    total=0,
                    page=page,
                    page_size=page_size,
                    total_pages=0,
                )
        else:
            effective_student_ids = allowed_scope
    elif isinstance(allowed_scope, UUID):
        # Student persona: strictly restricted to PUBLISHED cards
        effective_status = ReportCardStatus.PUBLISHED
        if student_id is not None and student_id != allowed_scope:
            return ReportCardListResponse(
                items=[],
                total=0,
                page=page,
                page_size=page_size,
                total_pages=0,
            )
        effective_student_ids = [allowed_scope]
    else:
        effective_student_id = student_id

    filters = ReportCardFilter(
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        academic_term_id=academic_term_id,
        school_class_id=school_class_id,
        section_id=section_id,
        student_id=effective_student_id,
        student_ids=effective_student_ids,
        status=effective_status,
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

    allowed_scope = enforce_relationship_access(
        db,
        school_id=current_user.school_id,
        current_user=current_user,
        target_student_id=card.student_id,
    )

    # If Parent or Student, ensure report card is PUBLISHED
    if isinstance(allowed_scope, (list, UUID)) and card.status != ReportCardStatus.PUBLISHED:
        raise ForbiddenException("Report card is not yet published.")

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


@router.post(
    "/batch-preview",
    response_model=BatchReportCardPreviewResponse,
    status_code=status.HTTP_200_OK,
)
def preview_batch_report_cards(
    request_data: BatchReportCardPreviewRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.generate")),
    service: ReportCardService = Depends(get_report_card_service),
) -> BatchReportCardPreviewResponse:
    return service.preview_batch_report_cards(
        db,
        request_data=request_data,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/batch-generate-async",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Asynchronously Generate Section Report Cards",
)
def batch_generate_report_cards_async(
    request_data: BatchReportCardBatchGenerateRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.generate")),
) -> JSONResponse:
    from app.models.background_job import JobType
    from app.repositories.job_repository import job_repository
    from app.services.async_job_runner import async_job_runner

    job = job_repository.create_job(
        db=db,
        school_id=current_user.school_id,
        user_id=current_user.id,
        job_type=JobType.BATCH_REPORT_CARD_GEN,
        payload=request_data.model_dump(mode="json"),
    )
    db.commit()

    background_tasks.add_task(async_job_runner.process_job, current_user.school_id, job.id)

    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "success": True,
            "data": {
                "job_id": str(job.id),
                "status": job.status,
                "job_type": job.job_type,
            },
        },
    )


@router.post(
    "/batch-generate",
    response_model=BatchReportCardBatchGenerateResponse,
    status_code=status.HTTP_200_OK,
)
def batch_generate_report_cards(
    request_data: BatchReportCardBatchGenerateRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.generate")),
    service: ReportCardService = Depends(get_report_card_service),
) -> BatchReportCardBatchGenerateResponse:
    return service.batch_generate_report_cards(
        db,
        request_data=request_data,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/batch-finalize",
    response_model=BatchReportCardBatchFinalizeResponse,
    status_code=status.HTTP_200_OK,
)
def batch_finalize_report_cards(
    request_data: BatchReportCardBatchFinalizeRequest,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("report_card.finalize")),
    service: ReportCardService = Depends(get_report_card_service),
) -> BatchReportCardBatchFinalizeResponse:
    return service.batch_finalize_report_cards(
        db,
        request_data=request_data,
        current_user_id=current_user.id,
        current_school_id=current_user.school_id,
    )

