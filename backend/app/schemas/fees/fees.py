from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.fees import (
    DiscountType,
    FeeCategory,
    FeeStructureStatus,
    PaymentMode,
    StudentFeeAssignmentStatus,
)


class FeeItemCreate(BaseModel):
    """
    Schema for creating/updating a fee item inside a fee structure.
    """

    category: FeeCategory
    name: str = Field(..., min_length=1, max_length=150)
    amount: Decimal = Field(..., ge=0)
    is_optional: bool = Field(default=False)
    order: int = Field(default=0)


class FeeItemResponse(BaseModel):
    """
    Response schema for a fee item.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fee_structure_id: UUID
    category: FeeCategory
    name: str
    amount: Decimal
    is_optional: bool
    order: int
    created_at: datetime
    updated_at: datetime


class FeeStructureCreate(BaseModel):
    """
    Request payload for creating a FeeStructure.
    """

    academic_year_id: UUID
    school_class_id: UUID | None = None
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    status: FeeStructureStatus = Field(default=FeeStructureStatus.DRAFT)
    items: list[FeeItemCreate] = Field(default_factory=list)


class FeeStructureUpdate(BaseModel):
    """
    Request payload for updating a FeeStructure.
    """

    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    school_class_id: UUID | None = None
    status: FeeStructureStatus | None = None
    items: list[FeeItemCreate] | None = None


class FeeStructureResponse(BaseModel):
    """
    Response schema for a FeeStructure.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    school_class_id: UUID | None
    name: str
    description: str | None
    status: FeeStructureStatus
    items: list[FeeItemResponse]
    created_at: datetime
    updated_at: datetime


class FeeStructureListResponse(BaseModel):
    """
    Paginated response schema for FeeStructure list.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[FeeStructureResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class StudentFeeItemCreate(BaseModel):
    """
    Request payload for creating/adding a student-specific fee item.
    """

    fee_item_id: UUID | None = None
    category: FeeCategory
    name: str = Field(..., min_length=1, max_length=150)
    amount: Decimal = Field(..., ge=0)
    is_optional: bool = Field(default=False)
    is_applicable: bool = Field(default=True)


class StudentFeeItemResponse(BaseModel):
    """
    Response schema for a student fee item.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_fee_assignment_id: UUID
    fee_item_id: UUID | None
    category: FeeCategory
    name: str
    amount: Decimal
    is_optional: bool
    is_applicable: bool
    created_at: datetime
    updated_at: datetime


class FeeDiscountCreate(BaseModel):
    """
    Request payload for adding a discount/concession to a student fee assignment.
    """

    discount_type: DiscountType
    name: str = Field(..., min_length=1, max_length=150)
    amount: Decimal = Field(..., gt=0)
    remarks: str | None = Field(default=None, max_length=255)


class FeeDiscountResponse(BaseModel):
    """
    Response schema for a discount.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    student_fee_assignment_id: UUID
    discount_type: DiscountType
    name: str
    amount: Decimal
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class StudentFeeAssignmentCreate(BaseModel):
    """
    Request payload for assigning a fee structure to a student.
    """

    academic_year_id: UUID
    student_id: UUID
    fee_structure_id: UUID
    due_date: date | None = None
    remarks: str | None = Field(default=None, max_length=255)
    custom_items: list[StudentFeeItemCreate] | None = None


class StudentFeeAssignmentResponse(BaseModel):
    """
    Response schema for a student fee assignment with calculated financial metrics.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    academic_year_id: UUID
    student_id: UUID
    fee_structure_id: UUID
    status: StudentFeeAssignmentStatus
    due_date: date | None
    remarks: str | None
    gross_amount: Decimal
    total_discounts: Decimal
    net_payable: Decimal
    total_paid: Decimal
    outstanding_due: Decimal
    student_fee_items: list[StudentFeeItemResponse]
    discounts: list[FeeDiscountResponse]
    created_at: datetime
    updated_at: datetime


class StudentFeeAssignmentListResponse(BaseModel):
    """
    Paginated response schema for student fee assignment list.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[StudentFeeAssignmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FeePaymentCreate(BaseModel):
    """
    Request payload for recording a fee payment.
    """

    student_fee_assignment_id: UUID
    amount: Decimal = Field(..., gt=0)
    payment_date: date
    payment_mode: PaymentMode
    reference_number: str | None = Field(default=None, max_length=100)
    remarks: str | None = Field(default=None, max_length=255)


class FeePaymentResponse(BaseModel):
    """
    Response schema for a recorded fee payment.
    """

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    student_fee_assignment_id: UUID
    receipt_number: str
    amount: Decimal
    payment_date: date
    payment_mode: PaymentMode
    reference_number: str | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class FeePaymentListResponse(BaseModel):
    """
    Paginated response schema for fee payments list.
    """

    model_config = ConfigDict(from_attributes=True)

    items: list[FeePaymentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class FeeReceiptResponse(BaseModel):
    """
    Response schema for a generated fee receipt.
    """

    model_config = ConfigDict(from_attributes=True)

    receipt_number: str
    school_id: UUID
    student_id: UUID
    student_fee_assignment_id: UUID
    payment_id: UUID
    payment_date: date
    payment_mode: PaymentMode
    reference_number: str | None
    amount: Decimal
    gross_amount: Decimal
    total_discounts: Decimal
    net_payable: Decimal
    total_paid: Decimal
    outstanding_due: Decimal
