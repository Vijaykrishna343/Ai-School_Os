from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.library import (
    BookCondition,
    BookCopyStatus,
    BookLoanStatus,
    BookReservationStatus,
    LibraryFineReason,
    LibraryFineStatus,
    LibraryMemberStatus,
    LibraryMemberType,
)


# =============================================================================
# 1. LIBRARY SCHEMAS
# =============================================================================

class LibraryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None)
    location: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)


class LibraryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None)
    location: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class LibraryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    code: str | None = None
    description: str | None = None
    location: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class LibraryListResponse(BaseModel):
    items: list[LibraryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 2. BOOK CATEGORY SCHEMAS
# =============================================================================

class BookCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)


class BookCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None, max_length=255)
    is_active: bool | None = Field(default=None)


class BookCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    code: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BookCategoryListResponse(BaseModel):
    items: list[BookCategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 3. BOOK CATALOG SCHEMAS
# =============================================================================

class BookCreate(BaseModel):
    library_id: UUID | None = Field(default=None)
    category_id: UUID | None = Field(default=None)
    title: str = Field(..., min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    publication_year: int | None = Field(default=None, ge=1000, le=2100)
    isbn: str | None = Field(default=None, max_length=30)
    edition: str | None = Field(default=None, max_length=50)
    language: str = Field(default="English", max_length=50)
    description: str | None = Field(default=None)
    total_pages: int | None = Field(default=None, gt=0)
    is_active: bool = Field(default=True)


class BookUpdate(BaseModel):
    library_id: UUID | None = Field(default=None)
    category_id: UUID | None = Field(default=None)
    title: str | None = Field(default=None, min_length=1, max_length=255)
    subtitle: str | None = Field(default=None, max_length=255)
    author: str | None = Field(default=None, min_length=1, max_length=255)
    publisher: str | None = Field(default=None, max_length=255)
    publication_year: int | None = Field(default=None, ge=1000, le=2100)
    isbn: str | None = Field(default=None, max_length=30)
    edition: str | None = Field(default=None, max_length=50)
    language: str | None = Field(default=None, max_length=50)
    description: str | None = Field(default=None)
    total_pages: int | None = Field(default=None, gt=0)
    is_active: bool | None = Field(default=None)


class BookResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    library_id: UUID | None = None
    category_id: UUID | None = None
    title: str
    subtitle: str | None = None
    author: str
    publisher: str | None = None
    publication_year: int | None = None
    isbn: str | None = None
    edition: str | None = None
    language: str
    description: str | None = None
    total_pages: int | None = None
    is_active: bool
    library_name: str | None = None
    category_name: str | None = None
    total_copies_count: int = 0
    available_copies_count: int = 0
    created_at: datetime
    updated_at: datetime


class BookListResponse(BaseModel):
    items: list[BookResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 4. BOOK COPY SCHEMAS
# =============================================================================

class BookCopyCreate(BaseModel):
    book_id: UUID = Field(...)
    accession_number: str = Field(..., min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    rfid_tag: str | None = Field(default=None, max_length=100)
    status: BookCopyStatus = Field(default=BookCopyStatus.AVAILABLE)
    condition: BookCondition = Field(default=BookCondition.GOOD)
    shelf_location: str | None = Field(default=None, max_length=100)
    acquisition_date: date | None = Field(default=None)
    acquisition_price: Decimal | None = Field(default=None, ge=0)
    is_active: bool = Field(default=True)


class BookCopyUpdate(BaseModel):
    accession_number: str | None = Field(default=None, min_length=1, max_length=100)
    barcode: str | None = Field(default=None, max_length=100)
    rfid_tag: str | None = Field(default=None, max_length=100)
    status: BookCopyStatus | None = Field(default=None)
    condition: BookCondition | None = Field(default=None)
    shelf_location: str | None = Field(default=None, max_length=100)
    acquisition_date: date | None = Field(default=None)
    acquisition_price: Decimal | None = Field(default=None, ge=0)
    is_active: bool | None = Field(default=None)


class BookCopyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    book_id: UUID
    accession_number: str
    barcode: str | None = None
    rfid_tag: str | None = None
    status: BookCopyStatus
    condition: BookCondition
    shelf_location: str | None = None
    acquisition_date: date | None = None
    acquisition_price: Decimal | None = None
    is_active: bool
    book_title: str | None = None
    book_author: str | None = None
    created_at: datetime
    updated_at: datetime


class BookCopyListResponse(BaseModel):
    items: list[BookCopyResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 5. LIBRARY MEMBER SCHEMAS
# =============================================================================

class LibraryMemberCreate(BaseModel):
    member_type: LibraryMemberType = Field(default=LibraryMemberType.STUDENT)
    student_id: UUID | None = Field(default=None)
    teacher_id: UUID | None = Field(default=None)
    user_id: UUID | None = Field(default=None)
    card_number: str = Field(..., min_length=1, max_length=100)
    issue_date: date = Field(default_factory=date.today)
    expiry_date: date | None = Field(default=None)
    max_books_allowed: int = Field(default=3, ge=1, le=50)
    status: LibraryMemberStatus = Field(default=LibraryMemberStatus.ACTIVE)
    remarks: str | None = Field(default=None, max_length=255)


class LibraryMemberUpdate(BaseModel):
    card_number: str | None = Field(default=None, min_length=1, max_length=100)
    expiry_date: date | None = Field(default=None)
    max_books_allowed: int | None = Field(default=None, ge=1, le=50)
    status: LibraryMemberStatus | None = Field(default=None)
    remarks: str | None = Field(default=None, max_length=255)


class LibraryMemberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    member_type: LibraryMemberType
    student_id: UUID | None = None
    teacher_id: UUID | None = None
    user_id: UUID | None = None
    card_number: str
    issue_date: date
    expiry_date: date | None = None
    max_books_allowed: int
    status: LibraryMemberStatus
    remarks: str | None = None
    display_name: str | None = None
    active_loans_count: int = 0
    created_at: datetime
    updated_at: datetime


class LibraryMemberListResponse(BaseModel):
    items: list[LibraryMemberResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 6. BOOK LOAN / CIRCULATION SCHEMAS
# =============================================================================

class BookLoanCheckout(BaseModel):
    member_id: UUID = Field(...)
    book_copy_id: UUID = Field(...)
    issue_date: date = Field(default_factory=date.today)
    due_date: date = Field(...)
    remarks: str | None = Field(default=None)


class BookLoanReturn(BaseModel):
    return_date: date = Field(default_factory=date.today)
    remarks: str | None = Field(default=None)


class BookLoanRenew(BaseModel):
    new_due_date: date = Field(...)
    remarks: str | None = Field(default=None)


class BookLoanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    member_id: UUID
    book_copy_id: UUID
    issue_date: date
    due_date: date
    return_date: date | None = None
    renewal_count: int
    max_renewals: int
    status: BookLoanStatus
    issued_by_user_id: UUID | None = None
    received_by_user_id: UUID | None = None
    remarks: str | None = None
    member_display_name: str | None = None
    member_card_number: str | None = None
    book_title: str | None = None
    accession_number: str | None = None
    created_at: datetime
    updated_at: datetime


class BookLoanListResponse(BaseModel):
    items: list[BookLoanResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 7. BOOK RESERVATION SCHEMAS
# =============================================================================

class BookReservationCreate(BaseModel):
    member_id: UUID = Field(...)
    book_id: UUID = Field(...)
    reservation_date: date = Field(default_factory=date.today)
    expiry_date: date | None = Field(default=None)


class BookReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    member_id: UUID
    book_id: UUID
    reservation_date: date
    expiry_date: date | None = None
    status: BookReservationStatus
    member_display_name: str | None = None
    book_title: str | None = None
    created_at: datetime
    updated_at: datetime


class BookReservationListResponse(BaseModel):
    items: list[BookReservationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 8. LIBRARY FINE SCHEMAS
# =============================================================================

class LibraryFineCreate(BaseModel):
    loan_id: UUID | None = Field(default=None)
    member_id: UUID = Field(...)
    amount: Decimal = Field(..., ge=0)
    fine_reason: LibraryFineReason = Field(default=LibraryFineReason.OVERDUE)
    status: LibraryFineStatus = Field(default=LibraryFineStatus.PENDING)


class LibraryFineWaive(BaseModel):
    waived_reason: str = Field(..., min_length=1, max_length=255)


class LibraryFineResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    loan_id: UUID | None = None
    member_id: UUID
    amount: Decimal
    fine_reason: LibraryFineReason
    status: LibraryFineStatus
    paid_date: date | None = None
    waived_reason: str | None = None
    waived_by_user_id: UUID | None = None
    member_display_name: str | None = None
    created_at: datetime
    updated_at: datetime


class LibraryFineListResponse(BaseModel):
    items: list[LibraryFineResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 9. LIBRARY SUMMARY / ANALYTICS SCHEMAS
# =============================================================================

class LibrarySummaryResponse(BaseModel):
    total_libraries_count: int = 0
    total_books_count: int = 0
    total_copies_count: int = 0
    available_copies_count: int = 0
    issued_copies_count: int = 0
    lost_or_damaged_copies_count: int = 0
    active_members_count: int = 0
    active_loans_count: int = 0
    overdue_loans_count: int = 0
    pending_reservations_count: int = 0
    pending_fines_amount: Decimal = Decimal("0.00")
