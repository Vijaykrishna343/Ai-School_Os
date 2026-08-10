from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.fees import (
    FeeStructureStatus,
    PaymentMode,
    StudentFeeAssignmentStatus,
)
from app.dependencies import get_db, get_fee_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.fees.fees import (
    FeeDiscountCreate,
    FeePaymentCreate,
    FeePaymentListResponse,
    FeePaymentResponse,
    FeeReceiptResponse,
    FeeStructureCreate,
    FeeStructureListResponse,
    FeeStructureResponse,
    FeeStructureUpdate,
    StudentFeeAssignmentCreate,
    StudentFeeAssignmentListResponse,
    StudentFeeAssignmentResponse,
    StudentFeeItemCreate,
)
from app.services.fee_service import FeeService

router = APIRouter()


# ------------------------------------------------------------------
# Fee Structures
# ------------------------------------------------------------------


@router.post(
    "/structures",
    response_model=FeeStructureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Fee Structure",
)
def create_fee_structure(
    structure: FeeStructureCreate,
    current_user: IdentityUser = Depends(require_permission("fees.create")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeeStructureResponse:
    """
    Create a new Fee Structure for the current authenticated user's school.
    """
    created = service.create_fee_structure(
        db=db,
        data=structure,
        current_school_id=current_user.school_id,
    )
    active_items = [item for item in created.items if not item.is_deleted]
    return FeeStructureResponse(
        id=created.id,
        school_id=created.school_id,
        academic_year_id=created.academic_year_id,
        school_class_id=created.school_class_id,
        name=created.name,
        description=created.description,
        status=created.status,
        items=active_items,
        created_at=created.created_at,
        updated_at=created.updated_at,
    )


@router.get(
    "/structures",
    response_model=FeeStructureListResponse,
    summary="List Fee Structures",
)
def list_fee_structures(
    academic_year_id: UUID | None = Query(default=None),
    school_class_id: UUID | None = Query(default=None),
    status: FeeStructureStatus | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeeStructureListResponse:
    """
    List paginated Fee Structures scoped to current user's school.
    """
    return service.list_fee_structures(
        db=db,
        current_school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/structures/{structure_id}",
    response_model=FeeStructureResponse,
    summary="Get Fee Structure by ID",
)
def get_fee_structure(
    structure_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeeStructureResponse:
    """
    Retrieve Fee Structure details by ID.
    """
    structure = service.get_fee_structure(
        db=db,
        structure_id=structure_id,
        current_school_id=current_user.school_id,
    )
    active_items = [item for item in structure.items if not item.is_deleted]
    return FeeStructureResponse(
        id=structure.id,
        school_id=structure.school_id,
        academic_year_id=structure.academic_year_id,
        school_class_id=structure.school_class_id,
        name=structure.name,
        description=structure.description,
        status=structure.status,
        items=active_items,
        created_at=structure.created_at,
        updated_at=structure.updated_at,
    )


@router.put(
    "/structures/{structure_id}",
    response_model=FeeStructureResponse,
    summary="Update Fee Structure",
)
def update_fee_structure(
    structure_id: UUID,
    structure: FeeStructureUpdate,
    current_user: IdentityUser = Depends(require_permission("fees.update")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeeStructureResponse:
    """
    Update an existing Fee Structure.
    """
    updated = service.update_fee_structure(
        db=db,
        structure_id=structure_id,
        data=structure,
        current_school_id=current_user.school_id,
    )
    active_items = [item for item in updated.items if not item.is_deleted]
    return FeeStructureResponse(
        id=updated.id,
        school_id=updated.school_id,
        academic_year_id=updated.academic_year_id,
        school_class_id=updated.school_class_id,
        name=updated.name,
        description=updated.description,
        status=updated.status,
        items=active_items,
        created_at=updated.created_at,
        updated_at=updated.updated_at,
    )


@router.delete(
    "/structures/{structure_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Fee Structure",
)
def delete_fee_structure(
    structure_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.delete")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> None:
    """
    Soft delete a Fee Structure and its items.
    """
    service.delete_fee_structure(
        db=db,
        structure_id=structure_id,
        current_school_id=current_user.school_id,
    )


# ------------------------------------------------------------------
# Student Fee Assignments
# ------------------------------------------------------------------


@router.post(
    "/assignments",
    response_model=StudentFeeAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign Fee Structure to Student",
)
def assign_fee_structure(
    assignment: StudentFeeAssignmentCreate,
    current_user: IdentityUser = Depends(require_permission("fees.create")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentResponse:
    """
    Assign a Fee Structure to a student for an academic year.
    """
    return service.assign_fee_structure(
        db=db,
        data=assignment,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/assignments",
    response_model=StudentFeeAssignmentListResponse,
    summary="List Student Fee Assignments",
)
def list_student_fee_assignments(
    academic_year_id: UUID | None = Query(default=None),
    student_id: UUID | None = Query(default=None),
    fee_structure_id: UUID | None = Query(default=None),
    status: StudentFeeAssignmentStatus | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentListResponse:
    """
    List paginated Student Fee Assignments scoped to current user's school.
    """
    return service.list_assignments(
        db=db,
        current_school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        student_id=student_id,
        fee_structure_id=fee_structure_id,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/assignments/{assignment_id}",
    response_model=StudentFeeAssignmentResponse,
    summary="Get Student Fee Assignment by ID",
)
def get_student_fee_assignment(
    assignment_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentResponse:
    """
    Retrieve details of a Student Fee Assignment.
    """
    return service.get_assignment(
        db=db,
        assignment_id=assignment_id,
        current_school_id=current_user.school_id,
    )


@router.delete(
    "/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Student Fee Assignment",
)
def delete_student_fee_assignment(
    assignment_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.delete")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> None:
    """
    Soft delete a Student Fee Assignment.
    """
    service.delete_assignment(
        db=db,
        assignment_id=assignment_id,
        current_school_id=current_user.school_id,
    )


# ------------------------------------------------------------------
# Student Fee Items & Discounts
# ------------------------------------------------------------------


@router.post(
    "/assignments/{assignment_id}/items",
    response_model=StudentFeeAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Custom Student Fee Item",
)
def add_student_fee_item(
    assignment_id: UUID,
    item: StudentFeeItemCreate,
    current_user: IdentityUser = Depends(require_permission("fees.update")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentResponse:
    """
    Add a student-specific fee item (such as transportation or optional charges).
    """
    return service.add_student_fee_item(
        db=db,
        assignment_id=assignment_id,
        data=item,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/assignments/{assignment_id}/discounts",
    response_model=StudentFeeAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Discount / Concession",
)
def add_fee_discount(
    assignment_id: UUID,
    discount: FeeDiscountCreate,
    current_user: IdentityUser = Depends(require_permission("fees.update")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentResponse:
    """
    Apply a discount/concession to a student's fee assignment.
    """
    return service.add_discount(
        db=db,
        assignment_id=assignment_id,
        data=discount,
        current_school_id=current_user.school_id,
    )


@router.delete(
    "/assignments/{assignment_id}/discounts/{discount_id}",
    response_model=StudentFeeAssignmentResponse,
    summary="Remove Discount / Concession",
)
def remove_fee_discount(
    assignment_id: UUID,
    discount_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.update")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentResponse:
    """
    Remove a discount/concession from a student's fee assignment and recalculate status.
    """
    return service.remove_discount(
        db=db,
        assignment_id=assignment_id,
        discount_id=discount_id,
        current_school_id=current_user.school_id,
    )


@router.post(
    "/assignments/{assignment_id}/cancel",
    response_model=StudentFeeAssignmentResponse,
    summary="Cancel Student Fee Assignment",
)
def cancel_student_fee_assignment(
    assignment_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.update")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> StudentFeeAssignmentResponse:
    """
    Cancel a Student Fee Assignment if no active payment records exist.
    """
    return service.cancel_assignment(
        db=db,
        assignment_id=assignment_id,
        current_school_id=current_user.school_id,
    )


# ------------------------------------------------------------------
# Payments & Receipts
# ------------------------------------------------------------------


@router.post(
    "/payments",
    response_model=FeePaymentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record Fee Payment",
)
def record_payment(
    payment: FeePaymentCreate,
    current_user: IdentityUser = Depends(require_permission("fees.create")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeePaymentResponse:
    """
    Record a payment towards a student's fee assignment and generate a unique receipt number.
    """
    return service.record_payment(
        db=db,
        data=payment,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/payments",
    response_model=FeePaymentListResponse,
    summary="List Fee Payments",
)
def list_fee_payments(
    assignment_id: UUID | None = Query(default=None),
    payment_mode: PaymentMode | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeePaymentListResponse:
    """
    List paginated fee payments for current user's school.
    """
    items, total = service.payment_repo.list_payments(
        db=db,
        school_id=current_user.school_id,
        assignment_id=assignment_id,
        payment_mode=payment_mode,
        page=page,
        page_size=page_size,
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return FeePaymentListResponse(
        items=[FeePaymentResponse.model_validate(p) for p in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/payments/{payment_id}",
    response_model=FeePaymentResponse,
    summary="Get Fee Payment by ID",
)
def get_fee_payment(
    payment_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeePaymentResponse:
    """
    Retrieve payment details by payment ID.
    """
    return service.get_payment(
        db=db,
        payment_id=payment_id,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/payments/{payment_id}/receipt",
    response_model=FeeReceiptResponse,
    summary="Get Payment Receipt",
)
def get_payment_receipt(
    payment_id: UUID,
    current_user: IdentityUser = Depends(require_permission("fees.view")),
    db: Session = Depends(get_db),
    service: FeeService = Depends(get_fee_service),
) -> FeeReceiptResponse:
    """
    Generate and retrieve the receipt representation for a successful payment.
    """
    return service.get_receipt(
        db=db,
        payment_id=payment_id,
        current_school_id=current_user.school_id,
    )
