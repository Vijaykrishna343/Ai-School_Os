from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.authorization import enforce_relationship_access
from app.common.exceptions import ForbiddenException
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
from app.dependencies import get_db, get_library_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.models.library import (
    Book,
    BookCategory,
    BookCopy,
    BookLoan,
    BookReservation,
    Library,
    LibraryFine,
    LibraryMember,
)
from app.schemas.library import (
    BookCategoryCreate,
    BookCategoryListResponse,
    BookCategoryResponse,
    BookCategoryUpdate,
    BookCopyCreate,
    BookCopyListResponse,
    BookCopyResponse,
    BookCopyUpdate,
    BookCreate,
    BookListResponse,
    BookLoanCheckout,
    BookLoanListResponse,
    BookLoanRenew,
    BookLoanResponse,
    BookLoanReturn,
    BookReservationCreate,
    BookReservationListResponse,
    BookReservationResponse,
    BookResponse,
    BookUpdate,
    LibraryCreate,
    LibraryFineCreate,
    LibraryFineListResponse,
    LibraryFineResponse,
    LibraryFineWaive,
    LibraryListResponse,
    LibraryMemberCreate,
    LibraryMemberListResponse,
    LibraryMemberResponse,
    LibraryMemberUpdate,
    LibraryResponse,
    LibrarySummaryResponse,
    LibraryUpdate,
)
from app.services.library_service import LibraryService

router = APIRouter()


# =============================================================================
# 1. LIBRARY ENDPOINTS
# =============================================================================

@router.get(
    "/libraries",
    response_model=LibraryListResponse,
    summary="List libraries",
)
def list_libraries(
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name, code, or location"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryListResponse:
    items, total, total_pages = service.list_libraries(
        db=db,
        school_id=current_user.school_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return LibraryListResponse(
        items=[LibraryResponse.model_validate(lib) for lib in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/libraries",
    response_model=LibraryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a library",
)
def create_library(
    payload: LibraryCreate,
    current_user: IdentityUser = Depends(require_permission("library.create")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    lib = service.create_library(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return LibraryResponse.model_validate(lib)


@router.get(
    "/libraries/{library_id}",
    response_model=LibraryResponse,
    summary="Get library details",
)
def get_library(
    library_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    lib = service.get_library(
        db=db,
        school_id=current_user.school_id,
        library_id=library_id,
    )
    return LibraryResponse.model_validate(lib)


@router.put(
    "/libraries/{library_id}",
    response_model=LibraryResponse,
    summary="Update library",
)
def update_library(
    library_id: UUID,
    payload: LibraryUpdate,
    current_user: IdentityUser = Depends(require_permission("library.update")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryResponse:
    lib = service.update_library(
        db=db,
        school_id=current_user.school_id,
        library_id=library_id,
        payload=payload,
    )
    return LibraryResponse.model_validate(lib)


@router.delete(
    "/libraries/{library_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete library",
)
def delete_library(
    library_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.delete")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> None:
    service.delete_library(
        db=db,
        school_id=current_user.school_id,
        library_id=library_id,
    )


# =============================================================================
# 2. BOOK CATEGORY ENDPOINTS
# =============================================================================

@router.get(
    "/categories",
    response_model=BookCategoryListResponse,
    summary="List book categories",
)
def list_categories(
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name or code"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCategoryListResponse:
    items, total, total_pages = service.list_categories(
        db=db,
        school_id=current_user.school_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return BookCategoryListResponse(
        items=[BookCategoryResponse.model_validate(cat) for cat in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/categories",
    response_model=BookCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create book category",
)
def create_category(
    payload: BookCategoryCreate,
    current_user: IdentityUser = Depends(require_permission("library.create")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCategoryResponse:
    cat = service.create_category(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return BookCategoryResponse.model_validate(cat)


@router.get(
    "/categories/{category_id}",
    response_model=BookCategoryResponse,
    summary="Get book category details",
)
def get_category(
    category_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCategoryResponse:
    cat = service.get_category(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
    )
    return BookCategoryResponse.model_validate(cat)


@router.put(
    "/categories/{category_id}",
    response_model=BookCategoryResponse,
    summary="Update book category",
)
def update_category(
    category_id: UUID,
    payload: BookCategoryUpdate,
    current_user: IdentityUser = Depends(require_permission("library.update")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCategoryResponse:
    cat = service.update_category(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
        payload=payload,
    )
    return BookCategoryResponse.model_validate(cat)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book category",
)
def delete_category(
    category_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.delete")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> None:
    service.delete_category(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
    )


# =============================================================================
# 3. BOOK CATALOG ENDPOINTS
# =============================================================================

def _serialize_book(book: Book) -> BookResponse:
    resp = BookResponse.model_validate(book)
    resp.library_name = book.library.name if book.library else None
    resp.category_name = book.category.name if book.category else None
    if hasattr(book, "copies") and book.copies:
        active_copies = [c for c in book.copies if not c.is_deleted]
        resp.total_copies_count = len(active_copies)
        resp.available_copies_count = sum(1 for c in active_copies if c.status == BookCopyStatus.AVAILABLE)
    return resp


@router.get(
    "/books",
    response_model=BookListResponse,
    summary="List books in catalog",
)
def list_books(
    library_id: UUID | None = Query(default=None, description="Filter by library ID"),
    category_id: UUID | None = Query(default=None, description="Filter by category ID"),
    author: str | None = Query(default=None, description="Filter by author name"),
    isbn: str | None = Query(default=None, description="Filter by exact ISBN"),
    search: str | None = Query(default=None, description="Search by title, subtitle, author, ISBN, or publisher"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookListResponse:
    items, total, total_pages = service.list_books(
        db=db,
        school_id=current_user.school_id,
        library_id=library_id,
        category_id=category_id,
        author=author,
        isbn=isbn,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return BookListResponse(
        items=[_serialize_book(b) for b in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/books",
    response_model=BookResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add book to catalog",
)
def create_book(
    payload: BookCreate,
    current_user: IdentityUser = Depends(require_permission("library.create")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookResponse:
    book = service.create_book(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return _serialize_book(book)


@router.get(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="Get book details",
)
def get_book(
    book_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookResponse:
    book = service.get_book(
        db=db,
        school_id=current_user.school_id,
        book_id=book_id,
    )
    return _serialize_book(book)


@router.put(
    "/books/{book_id}",
    response_model=BookResponse,
    summary="Update book",
)
def update_book(
    book_id: UUID,
    payload: BookUpdate,
    current_user: IdentityUser = Depends(require_permission("library.update")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookResponse:
    book = service.update_book(
        db=db,
        school_id=current_user.school_id,
        book_id=book_id,
        payload=payload,
    )
    return _serialize_book(book)


@router.delete(
    "/books/{book_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book from catalog",
)
def delete_book(
    book_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.delete")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> None:
    service.delete_book(
        db=db,
        school_id=current_user.school_id,
        book_id=book_id,
    )


# =============================================================================
# 4. BOOK COPY (PHYSICAL INVENTORY) ENDPOINTS
# =============================================================================

def _serialize_copy(copy: BookCopy) -> BookCopyResponse:
    resp = BookCopyResponse.model_validate(copy)
    if copy.book:
        resp.book_title = copy.book.title
        resp.book_author = copy.book.author
    return resp


@router.get(
    "/copies",
    response_model=BookCopyListResponse,
    summary="List book copies (accessions)",
)
def list_book_copies(
    book_id: UUID | None = Query(default=None, description="Filter by book ID"),
    status: BookCopyStatus | None = Query(default=None, description="Filter by copy status"),
    condition: BookCondition | None = Query(default=None, description="Filter by physical condition"),
    shelf_location: str | None = Query(default=None, description="Filter by shelf location"),
    search: str | None = Query(default=None, description="Search by accession number, barcode, shelf location"),
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCopyListResponse:
    items, total, total_pages = service.list_book_copies(
        db=db,
        school_id=current_user.school_id,
        book_id=book_id,
        status=status,
        condition=condition,
        shelf_location=shelf_location,
        search=search,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )
    return BookCopyListResponse(
        items=[_serialize_copy(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/copies",
    response_model=BookCopyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a book copy",
)
def create_book_copy(
    payload: BookCopyCreate,
    current_user: IdentityUser = Depends(require_permission("library.create")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCopyResponse:
    copy = service.create_book_copy(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return _serialize_copy(copy)


@router.get(
    "/copies/{copy_id}",
    response_model=BookCopyResponse,
    summary="Get book copy details",
)
def get_book_copy(
    copy_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCopyResponse:
    copy = service.get_book_copy(
        db=db,
        school_id=current_user.school_id,
        copy_id=copy_id,
    )
    return _serialize_copy(copy)


@router.put(
    "/copies/{copy_id}",
    response_model=BookCopyResponse,
    summary="Update book copy",
)
def update_book_copy(
    copy_id: UUID,
    payload: BookCopyUpdate,
    current_user: IdentityUser = Depends(require_permission("library.update")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookCopyResponse:
    copy = service.update_book_copy(
        db=db,
        school_id=current_user.school_id,
        copy_id=copy_id,
        payload=payload,
    )
    return _serialize_copy(copy)


@router.delete(
    "/copies/{copy_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete book copy",
)
def delete_book_copy(
    copy_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.delete")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> None:
    service.delete_book_copy(
        db=db,
        school_id=current_user.school_id,
        copy_id=copy_id,
    )


# =============================================================================
# 5. LIBRARY MEMBER ENDPOINTS
# =============================================================================

def _serialize_member(member: LibraryMember) -> LibraryMemberResponse:
    resp = LibraryMemberResponse.model_validate(member)
    resp.display_name = member.display_name
    if hasattr(member, "loans") and member.loans:
        resp.active_loans_count = sum(
            1 for loan in member.loans
            if not loan.is_deleted and loan.status in [BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]
        )
    return resp


@router.get(
    "/members",
    response_model=LibraryMemberListResponse,
    summary="List library members",
)
def list_members(
    member_type: LibraryMemberType | None = Query(default=None, description="Filter by member type"),
    status: LibraryMemberStatus | None = Query(default=None, description="Filter by member status"),
    search: str | None = Query(default=None, description="Search by card number or remarks"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryMemberListResponse:
    items, total, total_pages = service.list_members(
        db=db,
        school_id=current_user.school_id,
        member_type=member_type,
        status=status,
        search=search,
        page=page,
        page_size=page_size,
    )
    return LibraryMemberListResponse(
        items=[_serialize_member(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/members",
    response_model=LibraryMemberResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register library member",
)
def create_member(
    payload: LibraryMemberCreate,
    current_user: IdentityUser = Depends(require_permission("library.manage")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryMemberResponse:
    member = service.create_member(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return _serialize_member(member)


@router.get(
    "/members/{member_id}",
    response_model=LibraryMemberResponse,
    summary="Get library member details",
)
def get_member(
    member_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryMemberResponse:
    member = service.get_member(
        db=db,
        school_id=current_user.school_id,
        member_id=member_id,
    )
    return _serialize_member(member)


@router.put(
    "/members/{member_id}",
    response_model=LibraryMemberResponse,
    summary="Update library member",
)
def update_member(
    member_id: UUID,
    payload: LibraryMemberUpdate,
    current_user: IdentityUser = Depends(require_permission("library.manage")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryMemberResponse:
    member = service.update_member(
        db=db,
        school_id=current_user.school_id,
        member_id=member_id,
        payload=payload,
    )
    return _serialize_member(member)


@router.delete(
    "/members/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete library member",
)
def delete_member(
    member_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.manage")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> None:
    service.delete_member(
        db=db,
        school_id=current_user.school_id,
        member_id=member_id,
    )


# =============================================================================
# 6. CIRCULATION (LOAN CHECKOUT / RETURN / RENEW) ENDPOINTS
# =============================================================================

def _serialize_loan(loan: BookLoan) -> BookLoanResponse:
    resp = BookLoanResponse.model_validate(loan)
    if loan.member:
        resp.member_display_name = loan.member.display_name
        resp.member_card_number = loan.member.card_number
    if loan.book_copy:
        resp.accession_number = loan.book_copy.accession_number
        if loan.book_copy.book:
            resp.book_title = loan.book_copy.book.title
    return resp


@router.post(
    "/loans/checkout",
    response_model=BookLoanResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Issue book copy to member",
)
def checkout_book(
    payload: BookLoanCheckout,
    current_user: IdentityUser = Depends(require_permission("library.circulate")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookLoanResponse:
    loan = service.checkout_book(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        issued_by_user_id=current_user.id,
    )
    return _serialize_loan(loan)


@router.post(
    "/loans/{loan_id}/return",
    response_model=BookLoanResponse,
    summary="Return issued book copy",
)
def return_book(
    loan_id: UUID,
    payload: BookLoanReturn,
    current_user: IdentityUser = Depends(require_permission("library.circulate")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookLoanResponse:
    loan = service.return_book(
        db=db,
        school_id=current_user.school_id,
        loan_id=loan_id,
        payload=payload,
        received_by_user_id=current_user.id,
    )
    return _serialize_loan(loan)


@router.post(
    "/loans/{loan_id}/renew",
    response_model=BookLoanResponse,
    summary="Renew active book loan",
)
def renew_loan(
    loan_id: UUID,
    payload: BookLoanRenew,
    current_user: IdentityUser = Depends(require_permission("library.circulate")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookLoanResponse:
    loan = service.renew_loan(
        db=db,
        school_id=current_user.school_id,
        loan_id=loan_id,
        payload=payload,
    )
    return _serialize_loan(loan)


@router.get(
    "/loans",
    response_model=BookLoanListResponse,
    summary="List circulation loans",
)
def list_loans(
    member_id: UUID | None = Query(default=None, description="Filter by member ID"),
    book_copy_id: UUID | None = Query(default=None, description="Filter by book copy ID"),
    status: BookLoanStatus | None = Query(default=None, description="Filter by loan status"),
    overdue_only: bool = Query(default=False, description="Filter only overdue loans"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookLoanListResponse:
    allowed_scope = enforce_relationship_access(
        db,
        school_id=current_user.school_id,
        current_user=current_user,
        target_student_id=None,
    )

    effective_member_id = member_id

    if isinstance(allowed_scope, list):
        # Parent Persona
        if not allowed_scope:
            return BookLoanListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)
        allowed_members = db.scalars(
            select(LibraryMember).where(
                LibraryMember.school_id == current_user.school_id,
                LibraryMember.student_id.in_(allowed_scope),
                LibraryMember.is_deleted == False,
            )
        ).all()
        allowed_member_ids = [m.id for m in allowed_members]
        if not allowed_member_ids:
            return BookLoanListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)
        if member_id is not None:
            if member_id not in allowed_member_ids:
                return BookLoanListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)
            effective_member_id = member_id
        else:
            effective_member_id = allowed_member_ids[0]
    elif isinstance(allowed_scope, UUID):
        # Student Persona
        student_member = db.scalar(
            select(LibraryMember).where(
                LibraryMember.school_id == current_user.school_id,
                LibraryMember.student_id == allowed_scope,
                LibraryMember.is_deleted == False,
            )
        )
        if not student_member:
            return BookLoanListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)
        if member_id is not None and member_id != student_member.id:
            return BookLoanListResponse(items=[], total=0, page=page, page_size=page_size, total_pages=0)
        effective_member_id = student_member.id

    items, total, total_pages = service.list_loans(
        db=db,
        school_id=current_user.school_id,
        member_id=effective_member_id,
        book_copy_id=book_copy_id,
        status=status,
        overdue_only=overdue_only,
        page=page,
        page_size=page_size,
    )
    return BookLoanListResponse(
        items=[_serialize_loan(loan) for loan in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/loans/{loan_id}",
    response_model=BookLoanResponse,
    summary="Get loan details",
)
def get_loan(
    loan_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookLoanResponse:
    loan = service.get_loan(
        db=db,
        school_id=current_user.school_id,
        loan_id=loan_id,
    )

    allowed_scope = enforce_relationship_access(
        db,
        school_id=current_user.school_id,
        current_user=current_user,
        target_student_id=None,
    )

    if isinstance(allowed_scope, list):
        if not loan.member or loan.member.student_id not in allowed_scope:
            raise ForbiddenException("Access denied.")
    elif isinstance(allowed_scope, UUID):
        if not loan.member or loan.member.student_id != allowed_scope:
            raise ForbiddenException("Access denied.")

    return _serialize_loan(loan)


# =============================================================================
# 7. BOOK RESERVATIONS ENDPOINTS
# =============================================================================

def _serialize_reservation(res: BookReservation) -> BookReservationResponse:
    resp = BookReservationResponse.model_validate(res)
    if res.member:
        resp.member_display_name = res.member.display_name
    if res.book:
        resp.book_title = res.book.title
    return resp


@router.post(
    "/reservations",
    response_model=BookReservationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Place a book reservation",
)
def create_reservation(
    payload: BookReservationCreate,
    current_user: IdentityUser = Depends(require_permission("library.circulate")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookReservationResponse:
    res = service.create_reservation(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return _serialize_reservation(res)


@router.post(
    "/reservations/{reservation_id}/cancel",
    response_model=BookReservationResponse,
    summary="Cancel a book reservation",
)
def cancel_reservation(
    reservation_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.circulate")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookReservationResponse:
    res = service.cancel_reservation(
        db=db,
        school_id=current_user.school_id,
        reservation_id=reservation_id,
    )
    return _serialize_reservation(res)


@router.get(
    "/reservations",
    response_model=BookReservationListResponse,
    summary="List book reservations",
)
def list_reservations(
    member_id: UUID | None = Query(default=None, description="Filter by member ID"),
    book_id: UUID | None = Query(default=None, description="Filter by book ID"),
    status: BookReservationStatus | None = Query(default=None, description="Filter by reservation status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookReservationListResponse:
    items, total, total_pages = service.list_reservations(
        db=db,
        school_id=current_user.school_id,
        member_id=member_id,
        book_id=book_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return BookReservationListResponse(
        items=[_serialize_reservation(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/reservations/{reservation_id}",
    response_model=BookReservationResponse,
    summary="Get reservation details",
)
def get_reservation(
    reservation_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> BookReservationResponse:
    res = service.get_reservation(
        db=db,
        school_id=current_user.school_id,
        reservation_id=reservation_id,
    )
    return _serialize_reservation(res)


# =============================================================================
# 8. LIBRARY FINES ENDPOINTS
# =============================================================================

def _serialize_fine(fine: LibraryFine) -> LibraryFineResponse:
    resp = LibraryFineResponse.model_validate(fine)
    if fine.member:
        resp.member_display_name = fine.member.display_name
    return resp


@router.post(
    "/fines",
    response_model=LibraryFineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assess/create a library fine",
)
def create_fine(
    payload: LibraryFineCreate,
    current_user: IdentityUser = Depends(require_permission("library.manage")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryFineResponse:
    fine = service.create_fine(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return _serialize_fine(fine)


@router.post(
    "/fines/{fine_id}/waive",
    response_model=LibraryFineResponse,
    summary="Waive a library fine",
)
def waive_fine(
    fine_id: UUID,
    payload: LibraryFineWaive,
    current_user: IdentityUser = Depends(require_permission("library.manage")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryFineResponse:
    fine = service.waive_fine(
        db=db,
        school_id=current_user.school_id,
        fine_id=fine_id,
        payload=payload,
        waived_by_user_id=current_user.id,
    )
    return _serialize_fine(fine)


@router.get(
    "/fines",
    response_model=LibraryFineListResponse,
    summary="List library fines",
)
def list_fines(
    member_id: UUID | None = Query(default=None, description="Filter by member ID"),
    loan_id: UUID | None = Query(default=None, description="Filter by loan ID"),
    status: LibraryFineStatus | None = Query(default=None, description="Filter by fine status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryFineListResponse:
    items, total, total_pages = service.list_fines(
        db=db,
        school_id=current_user.school_id,
        member_id=member_id,
        loan_id=loan_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return LibraryFineListResponse(
        items=[_serialize_fine(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/fines/{fine_id}",
    response_model=LibraryFineResponse,
    summary="Get library fine details",
)
def get_fine(
    fine_id: UUID,
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibraryFineResponse:
    fine = service.get_fine(
        db=db,
        school_id=current_user.school_id,
        fine_id=fine_id,
    )
    return _serialize_fine(fine)


# =============================================================================
# 9. LIBRARY SUMMARY / OPERATIONAL ANALYTICS
# =============================================================================

@router.get(
    "/summary",
    response_model=LibrarySummaryResponse,
    summary="Get library operational summary analytics",
)
def get_library_summary(
    current_user: IdentityUser = Depends(require_permission("library.view")),
    db: Session = Depends(get_db),
    service: LibraryService = Depends(get_library_service),
) -> LibrarySummaryResponse:
    return service.get_library_summary(
        db=db,
        school_id=current_user.school_id,
    )
