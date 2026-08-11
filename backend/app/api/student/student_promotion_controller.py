"""
Student Promotion, Retention, Academic Year Transition, and Transfer Certificate Endpoints.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Path, status
from sqlalchemy.orm import Session

from app.common.responses.api_response import ApiResponse
from app.dependencies.database import get_db
from app.dependencies.services import get_student_promotion_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.student.promotion_schema import (
    BulkPromotionResultResponse,
    BulkStudentPromotionRequest,
    BulkStudentRetentionRequest,
    StudentEnrollmentHistoryListResponse,
    StudentEnrollmentHistoryResponse,
    StudentPromotionRequest,
    StudentRetentionRequest,
    TransferCertificateCreate,
    TransferCertificateListResponse,
    TransferCertificateResponse,
)
from app.services.student.student_promotion_service import StudentPromotionService

router = APIRouter()


@router.get(
    "/{student_id}/enrollments",
    response_model=dict,
    summary="Get Student Enrollment History",
    dependencies=[Depends(require_permission("student.view"))],
)
def get_student_enrollments(
    student_id: UUID = Path(..., description="Student ID"),
    current_user: IdentityUser = Depends(require_permission("student.view")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Retrieve all historical enrollment records for a student.
    """
    enrollments = service.get_student_enrollments(
        db=db,
        student_id=student_id,
        current_school_id=current_user.school_id,
    )

    items = [
        StudentEnrollmentHistoryResponse.model_validate(e).model_dump(mode="json")
        for e in enrollments
    ]

    return ApiResponse.success(
        data=StudentEnrollmentHistoryListResponse(
            student_id=student_id,
            enrollments=[StudentEnrollmentHistoryResponse.model_validate(e) for e in enrollments],
            total=len(enrollments),
        ).model_dump(mode="json"),
        message="Student enrollment history retrieved successfully.",
    )


@router.post(
    "/{student_id}/promote",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Promote Single Student",
)
def promote_student(
    request: StudentPromotionRequest,
    student_id: UUID = Path(..., description="Student ID"),
    current_user: IdentityUser = Depends(require_permission("student.promote")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Promote a single student to a new academic year, class, and section.
    """
    history = service.promote_student(
        db=db,
        student_id=student_id,
        data=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=StudentEnrollmentHistoryResponse.model_validate(history).model_dump(
            mode="json"
        ),
        message="Student promoted successfully.",
    )


@router.post(
    "/{student_id}/retain",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Retain Single Student",
)
def retain_student(
    request: StudentRetentionRequest,
    student_id: UUID = Path(..., description="Student ID"),
    current_user: IdentityUser = Depends(require_permission("student.retain")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Retain a single student in their current class/section for a new academic year.
    """
    history = service.retain_student(
        db=db,
        student_id=student_id,
        data=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=StudentEnrollmentHistoryResponse.model_validate(history).model_dump(
            mode="json"
        ),
        message="Student retained successfully.",
    )


@router.post(
    "/promote/bulk",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Bulk Promote Students",
)
def bulk_promote_students(
    request: BulkStudentPromotionRequest,
    current_user: IdentityUser = Depends(require_permission("student.promote")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Promote multiple students in a single operation.
    """
    result = service.bulk_promote_students(
        db=db,
        data=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=result.model_dump(mode="json"),
        message="Bulk student promotion processed successfully.",
    )


@router.post(
    "/retain/bulk",
    response_model=dict,
    status_code=status.HTTP_200_OK,
    summary="Bulk Retain Students",
)
def bulk_retain_students(
    request: BulkStudentRetentionRequest,
    current_user: IdentityUser = Depends(require_permission("student.retain")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Retain multiple students in a single operation.
    """
    result = service.bulk_retain_students(
        db=db,
        data=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=result.model_dump(mode="json"),
        message="Bulk student retention processed successfully.",
    )


@router.post(
    "/{student_id}/transfer-certificate",
    response_model=dict,
    status_code=status.HTTP_201_CREATED,
    summary="Issue Transfer Certificate",
)
def issue_transfer_certificate(
    request: TransferCertificateCreate,
    student_id: UUID = Path(..., description="Student ID"),
    current_user: IdentityUser = Depends(require_permission("student.tc.create")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Issue a Transfer Certificate (TC) for a student and update status to TRANSFERRED.
    """
    tc = service.issue_transfer_certificate(
        db=db,
        student_id=student_id,
        data=request,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=TransferCertificateResponse.model_validate(tc).model_dump(mode="json"),
        message="Transfer Certificate issued successfully.",
    )


@router.get(
    "/{student_id}/transfer-certificates",
    response_model=dict,
    summary="Get Student Transfer Certificates",
)
def get_student_transfer_certificates(
    student_id: UUID = Path(..., description="Student ID"),
    current_user: IdentityUser = Depends(require_permission("student.tc.view")),
    db: Session = Depends(get_db),
    service: StudentPromotionService = Depends(get_student_promotion_service),
) -> dict[str, object]:
    """
    Get all Transfer Certificates issued for a student.
    """
    tcs = service.get_student_transfer_certificates(
        db=db,
        student_id=student_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        data=TransferCertificateListResponse(
            student_id=student_id,
            certificates=[TransferCertificateResponse.model_validate(t) for t in tcs],
            total=len(tcs),
        ).model_dump(mode="json"),
        message="Transfer Certificates retrieved successfully.",
    )
