from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.student.student_certificate import CertificateType
from app.schemas.student.student_certificate import (
    StudentCertificateCreateTC,
    StudentCertificateCreateBonafide,
)
from app.services.student_certificate_service import student_certificate_service

router = APIRouter()


@router.post("/students/{student_id}/certificates/tc", summary="Issue Transfer Certificate (TC)", status_code=status.HTTP_201_CREATED)
def issue_transfer_certificate(
    student_id: UUID,
    body: StudentCertificateCreateTC,
    current_user: IdentityUser = Depends(require_permission("student.tc.create")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = student_certificate_service.issue_transfer_certificate(
        db,
        school_id=current_user.school_id,
        student_id=student_id,
        data=body,
        issuer=current_user,
    )
    return ApiResponse.success(
        message="Transfer Certificate issued successfully.",
        data=result.model_dump(mode="json"),
    )


@router.post("/students/{student_id}/certificates/bonafide", summary="Issue Bonafide Certificate", status_code=status.HTTP_201_CREATED)
def issue_bonafide_certificate(
    student_id: UUID,
    body: StudentCertificateCreateBonafide,
    current_user: IdentityUser = Depends(require_permission("student.certificate.create")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = student_certificate_service.issue_bonafide_certificate(
        db,
        school_id=current_user.school_id,
        student_id=student_id,
        data=body,
        issuer=current_user,
    )
    return ApiResponse.success(
        message="Bonafide Certificate issued successfully.",
        data=result.model_dump(mode="json"),
    )


@router.get("/certificates", summary="List Certificate History")
def list_certificates(
    certificate_type: CertificateType | None = Query(default=None, alias="type"),
    student_id: UUID | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("student.tc.view")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = student_certificate_service.list_certificates(
        db,
        school_id=current_user.school_id,
        certificate_type=certificate_type,
        student_id=student_id,
        page=page,
        page_size=page_size,
    )
    return ApiResponse.success(
        message="Certificates history retrieved successfully.",
        data=result.model_dump(mode="json"),
    )


@router.get("/certificates/{certificate_id}", summary="Get Certificate Details")
def get_certificate(
    certificate_id: UUID,
    current_user: IdentityUser = Depends(require_permission("student.tc.view")),
    db: Session = Depends(get_db),
) -> dict[str, object]:
    result = student_certificate_service.get_certificate(
        db,
        school_id=current_user.school_id,
        certificate_id=certificate_id,
    )
    return ApiResponse.success(
        message="Certificate details retrieved successfully.",
        data=result.model_dump(mode="json"),
    )


@router.get("/certificates/{certificate_id}/print", summary="Get Certificate Print View", response_class=HTMLResponse)
def get_certificate_print_view(
    certificate_id: UUID,
    current_user: IdentityUser = Depends(require_permission("student.tc.view")),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    html_content = student_certificate_service.get_printable_html(
        db,
        school_id=current_user.school_id,
        certificate_id=certificate_id,
    )
    return HTMLResponse(content=html_content, status_code=status.HTTP_200_OK)
