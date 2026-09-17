from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.admissions import (
    AdmissionApplicationStatus,
    AdmissionCycleStatus,
    ApplicantStatus,
)
from app.dependencies import get_admissions_service, get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.admissions import (
    AdmissionApplicationCreate,
    AdmissionApplicationListResponse,
    AdmissionApplicationResponse,
    AdmissionApplicationUpdate,
    AdmissionCycleCreate,
    AdmissionCycleListResponse,
    AdmissionCycleResponse,
    AdmissionCycleUpdate,
    AdmissionDecisionCreate,
    AdmissionDecisionListResponse,
    AdmissionDecisionResponse,
    ApplicantCreate,
    ApplicantListResponse,
    ApplicantResponse,
    ApplicantUpdate,
    ApplicationReviewRequest,
    ApplicationStatusHistoryListResponse,
    ApplicationStatusHistoryResponse,
    ApplicationSubmitRequest,
    ApplicationWithdrawRequest,
)
from app.services.admissions_service import AdmissionsService

router = APIRouter()


# =============================================================================
# 1. ADMISSION CYCLES ENDPOINTS
# =============================================================================

@router.post(
    "/cycles",
    response_model=AdmissionCycleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admission cycle",
)
def create_admission_cycle(
    payload: AdmissionCycleCreate,
    current_user: IdentityUser = Depends(require_permission("admissions.create")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionCycleResponse:
    cycle = service.create_cycle(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return AdmissionCycleResponse.model_validate(cycle)


@router.get(
    "/cycles",
    response_model=AdmissionCycleListResponse,
    summary="List admission cycles",
)
def list_admission_cycles(
    academic_year_id: UUID | None = Query(default=None, description="Filter by academic year"),
    status: AdmissionCycleStatus | None = Query(default=None, description="Filter by cycle status"),
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name or code"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionCycleListResponse:
    items, total, total_pages = service.list_cycles(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        status=status,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return AdmissionCycleListResponse(
        items=[AdmissionCycleResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/cycles/{cycle_id}",
    response_model=AdmissionCycleResponse,
    summary="Get admission cycle by ID",
)
def get_admission_cycle(
    cycle_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionCycleResponse:
    cycle = service.get_cycle(
        db=db,
        school_id=current_user.school_id,
        cycle_id=cycle_id,
    )
    return AdmissionCycleResponse.model_validate(cycle)


@router.put(
    "/cycles/{cycle_id}",
    response_model=AdmissionCycleResponse,
    summary="Update admission cycle",
)
def update_admission_cycle(
    cycle_id: UUID,
    payload: AdmissionCycleUpdate,
    current_user: IdentityUser = Depends(require_permission("admissions.update")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionCycleResponse:
    cycle = service.update_cycle(
        db=db,
        school_id=current_user.school_id,
        cycle_id=cycle_id,
        payload=payload,
    )
    return AdmissionCycleResponse.model_validate(cycle)


@router.delete(
    "/cycles/{cycle_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete admission cycle",
)
def delete_admission_cycle(
    cycle_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.delete")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> None:
    service.delete_cycle(
        db=db,
        school_id=current_user.school_id,
        cycle_id=cycle_id,
    )


# =============================================================================
# 2. APPLICANTS / PROSPECTS ENDPOINTS
# =============================================================================

@router.post(
    "/applicants",
    response_model=ApplicantResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create applicant / prospect",
)
def create_applicant(
    payload: ApplicantCreate,
    current_user: IdentityUser = Depends(require_permission("admissions.create")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> ApplicantResponse:
    applicant = service.create_applicant(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return ApplicantResponse.model_validate(applicant)


@router.get(
    "/applicants",
    response_model=ApplicantListResponse,
    summary="List applicants / prospects",
)
def list_applicants(
    admission_cycle_id: UUID | None = Query(default=None, description="Filter by admission cycle"),
    status: ApplicantStatus | None = Query(default=None, description="Filter by applicant status"),
    search: str | None = Query(default=None, description="Search by name, number, contact"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> ApplicantListResponse:
    items, total, total_pages = service.list_applicants(
        db=db,
        school_id=current_user.school_id,
        admission_cycle_id=admission_cycle_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return ApplicantListResponse(
        items=[ApplicantResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/applicants/{applicant_id}",
    response_model=ApplicantResponse,
    summary="Get applicant by ID",
)
def get_applicant(
    applicant_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> ApplicantResponse:
    applicant = service.get_applicant(
        db=db,
        school_id=current_user.school_id,
        applicant_id=applicant_id,
    )
    return ApplicantResponse.model_validate(applicant)


@router.put(
    "/applicants/{applicant_id}",
    response_model=ApplicantResponse,
    summary="Update applicant",
)
def update_applicant(
    applicant_id: UUID,
    payload: ApplicantUpdate,
    current_user: IdentityUser = Depends(require_permission("admissions.update")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> ApplicantResponse:
    applicant = service.update_applicant(
        db=db,
        school_id=current_user.school_id,
        applicant_id=applicant_id,
        payload=payload,
    )
    return ApplicantResponse.model_validate(applicant)


@router.delete(
    "/applicants/{applicant_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete applicant",
)
def delete_applicant(
    applicant_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.delete")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> None:
    service.delete_applicant(
        db=db,
        school_id=current_user.school_id,
        applicant_id=applicant_id,
    )


# =============================================================================
# 3. ADMISSION APPLICATIONS ENDPOINTS
# =============================================================================

@router.post(
    "/applications",
    response_model=AdmissionApplicationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create admission application",
)
def create_admission_application(
    payload: AdmissionApplicationCreate,
    current_user: IdentityUser = Depends(require_permission("admissions.create")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationResponse:
    application = service.create_application(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return AdmissionApplicationResponse.model_validate(application)


@router.get(
    "/applications",
    response_model=AdmissionApplicationListResponse,
    summary="List admission applications",
)
def list_admission_applications(
    admission_cycle_id: UUID | None = Query(default=None, description="Filter by cycle"),
    applicant_id: UUID | None = Query(default=None, description="Filter by applicant"),
    academic_year_id: UUID | None = Query(default=None, description="Filter by academic year"),
    target_class_id: UUID | None = Query(default=None, description="Filter by target class"),
    status: AdmissionApplicationStatus | None = Query(default=None, description="Filter by status"),
    search: str | None = Query(default=None, description="Search by application number or remarks"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationListResponse:
    items, total, total_pages = service.list_applications(
        db=db,
        school_id=current_user.school_id,
        admission_cycle_id=admission_cycle_id,
        applicant_id=applicant_id,
        academic_year_id=academic_year_id,
        target_class_id=target_class_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return AdmissionApplicationListResponse(
        items=[AdmissionApplicationResponse.model_validate(app) for app in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/applications/{application_id}",
    response_model=AdmissionApplicationResponse,
    summary="Get admission application by ID",
)
def get_admission_application(
    application_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationResponse:
    application = service.get_application(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
    )
    return AdmissionApplicationResponse.model_validate(application)


@router.put(
    "/applications/{application_id}",
    response_model=AdmissionApplicationResponse,
    summary="Update admission application",
)
def update_admission_application(
    application_id: UUID,
    payload: AdmissionApplicationUpdate,
    current_user: IdentityUser = Depends(require_permission("admissions.update")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationResponse:
    application = service.update_application(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
        payload=payload,
    )
    return AdmissionApplicationResponse.model_validate(application)


@router.post(
    "/applications/{application_id}/submit",
    response_model=AdmissionApplicationResponse,
    summary="Submit admission application",
)
def submit_admission_application(
    application_id: UUID,
    payload: ApplicationSubmitRequest | None = None,
    current_user: IdentityUser = Depends(require_permission("admissions.update")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationResponse:
    application = service.submit_application(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
        user_id=current_user.id,
        payload=payload,
    )
    return AdmissionApplicationResponse.model_validate(application)


@router.post(
    "/applications/{application_id}/review",
    response_model=AdmissionApplicationResponse,
    summary="Mark application under review",
)
def review_admission_application(
    application_id: UUID,
    payload: ApplicationReviewRequest | None = None,
    current_user: IdentityUser = Depends(require_permission("admissions.review")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationResponse:
    application = service.start_review_application(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
        user_id=current_user.id,
        payload=payload,
    )
    return AdmissionApplicationResponse.model_validate(application)


@router.post(
    "/applications/{application_id}/decision",
    response_model=AdmissionDecisionResponse,
    summary="Record decision for application",
)
def record_admission_decision(
    application_id: UUID,
    payload: AdmissionDecisionCreate,
    current_user: IdentityUser = Depends(require_permission("admissions.review")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionDecisionResponse:
    _, decision = service.record_decision(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
        user_id=current_user.id,
        payload=payload,
    )
    return AdmissionDecisionResponse.model_validate(decision)


@router.post(
    "/applications/{application_id}/withdraw",
    response_model=AdmissionApplicationResponse,
    summary="Withdraw admission application",
)
def withdraw_admission_application(
    application_id: UUID,
    payload: ApplicationWithdrawRequest,
    current_user: IdentityUser = Depends(require_permission("admissions.update")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionApplicationResponse:
    application = service.withdraw_application(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
        user_id=current_user.id,
        payload=payload,
    )
    return AdmissionApplicationResponse.model_validate(application)


# =============================================================================
# 4. STATUS HISTORY & DECISIONS AUDIT
# =============================================================================

@router.get(
    "/applications/{application_id}/history",
    response_model=ApplicationStatusHistoryListResponse,
    summary="Get application status transition history",
)
def get_application_history(
    application_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> ApplicationStatusHistoryListResponse:
    history = service.get_application_history(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
    )
    return ApplicationStatusHistoryListResponse(
        items=[ApplicationStatusHistoryResponse.model_validate(h) for h in history],
        total=len(history),
    )


@router.get(
    "/applications/{application_id}/decisions",
    response_model=AdmissionDecisionListResponse,
    summary="Get application decisions",
)
def get_application_decisions(
    application_id: UUID,
    current_user: IdentityUser = Depends(require_permission("admissions.view")),
    db: Session = Depends(get_db),
    service: AdmissionsService = Depends(get_admissions_service),
) -> AdmissionDecisionListResponse:
    decisions = service.get_application_decisions(
        db=db,
        school_id=current_user.school_id,
        application_id=application_id,
    )
    return AdmissionDecisionListResponse(
        items=[AdmissionDecisionResponse.model_validate(d) for d in decisions],
        total=len(decisions),
    )
