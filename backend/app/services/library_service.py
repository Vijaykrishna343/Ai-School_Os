from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

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
from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
    ValidationException,
)
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
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.schemas.library import (
    BookCategoryCreate,
    BookCategoryUpdate,
    BookCopyCreate,
    BookCopyUpdate,
    BookCreate,
    BookLoanCheckout,
    BookLoanRenew,
    BookLoanReturn,
    BookReservationCreate,
    BookUpdate,
    LibraryCreate,
    LibraryFineCreate,
    LibraryFineWaive,
    LibraryMemberCreate,
    LibraryMemberUpdate,
    LibrarySummaryResponse,
    LibraryUpdate,
)


class LibraryService:
    """
    Comprehensive service handling business logic, validation, and multi-tenant
    data management for the School ERP Library & Book Circulation Subsystem.
    """

    # =========================================================================
    # 1. LIBRARY MANAGEMENT
    # =========================================================================

    def create_library(
        self,
        db: Session,
        school_id: UUID,
        payload: LibraryCreate,
    ) -> Library:
        if payload.code:
            existing = db.scalars(
                select(Library).where(
                    Library.school_id == school_id,
                    Library.code == payload.code,
                    Library.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Library with code", payload.code)

        lib = Library(
            school_id=school_id,
            name=payload.name,
            code=payload.code,
            description=payload.description,
            location=payload.location,
            is_active=payload.is_active,
        )
        db.add(lib)
        db.commit()
        db.refresh(lib)
        return lib

    def get_library(
        self,
        db: Session,
        school_id: UUID,
        library_id: UUID,
    ) -> Library:
        lib = db.scalars(
            select(Library).where(
                Library.id == library_id,
                Library.school_id == school_id,
                Library.is_deleted.is_(False),
            )
        ).first()
        if not lib:
            raise NotFoundException("Library", str(library_id))
        return lib

    def list_libraries(
        self,
        db: Session,
        school_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Library], int, int]:
        stmt = select(Library).where(
            Library.school_id == school_id,
            Library.is_deleted.is_(False),
        )
        if is_active is not None:
            stmt = stmt.where(Library.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Library.name.ilike(term),
                    Library.code.ilike(term),
                    Library.location.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(Library.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    def update_library(
        self,
        db: Session,
        school_id: UUID,
        library_id: UUID,
        payload: LibraryUpdate,
    ) -> Library:
        lib = self.get_library(db=db, school_id=school_id, library_id=library_id)

        if payload.code is not None and payload.code != lib.code:
            existing = db.scalars(
                select(Library).where(
                    Library.school_id == school_id,
                    Library.code == payload.code,
                    Library.id != library_id,
                    Library.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Library with code", payload.code)
            lib.code = payload.code

        if payload.name is not None:
            lib.name = payload.name
        if payload.description is not None:
            lib.description = payload.description
        if payload.location is not None:
            lib.location = payload.location
        if payload.is_active is not None:
            lib.is_active = payload.is_active

        db.commit()
        db.refresh(lib)
        return lib

    def delete_library(
        self,
        db: Session,
        school_id: UUID,
        library_id: UUID,
    ) -> None:
        lib = self.get_library(db=db, school_id=school_id, library_id=library_id)
        lib.is_deleted = True
        lib.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 2. BOOK CATEGORY MANAGEMENT
    # =========================================================================

    def create_category(
        self,
        db: Session,
        school_id: UUID,
        payload: BookCategoryCreate,
    ) -> BookCategory:
        existing = db.scalars(
            select(BookCategory).where(
                BookCategory.school_id == school_id,
                BookCategory.name == payload.name,
                BookCategory.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Category with name", payload.name)

        cat = BookCategory(
            school_id=school_id,
            name=payload.name,
            code=payload.code,
            description=payload.description,
            is_active=payload.is_active,
        )
        db.add(cat)
        db.commit()
        db.refresh(cat)
        return cat

    def get_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
    ) -> BookCategory:
        cat = db.scalars(
            select(BookCategory).where(
                BookCategory.id == category_id,
                BookCategory.school_id == school_id,
                BookCategory.is_deleted.is_(False),
            )
        ).first()
        if not cat:
            raise NotFoundException("Book Category", str(category_id))
        return cat

    def list_categories(
        self,
        db: Session,
        school_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookCategory], int, int]:
        stmt = select(BookCategory).where(
            BookCategory.school_id == school_id,
            BookCategory.is_deleted.is_(False),
        )
        if is_active is not None:
            stmt = stmt.where(BookCategory.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    BookCategory.name.ilike(term),
                    BookCategory.code.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(BookCategory.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    def update_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
        payload: BookCategoryUpdate,
    ) -> BookCategory:
        cat = self.get_category(db=db, school_id=school_id, category_id=category_id)

        if payload.name is not None and payload.name != cat.name:
            existing = db.scalars(
                select(BookCategory).where(
                    BookCategory.school_id == school_id,
                    BookCategory.name == payload.name,
                    BookCategory.id != category_id,
                    BookCategory.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Category with name", payload.name)
            cat.name = payload.name

        if payload.code is not None:
            cat.code = payload.code
        if payload.description is not None:
            cat.description = payload.description
        if payload.is_active is not None:
            cat.is_active = payload.is_active

        db.commit()
        db.refresh(cat)
        return cat

    def delete_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
    ) -> None:
        cat = self.get_category(db=db, school_id=school_id, category_id=category_id)
        cat.is_deleted = True
        cat.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 3. BOOK CATALOG MANAGEMENT
    # =========================================================================

    def create_book(
        self,
        db: Session,
        school_id: UUID,
        payload: BookCreate,
    ) -> Book:
        if payload.library_id:
            lib = db.scalars(
                select(Library).where(
                    Library.id == payload.library_id,
                    Library.school_id == school_id,
                    Library.is_deleted.is_(False),
                )
            ).first()
            if not lib:
                raise NotFoundException("Library", str(payload.library_id))

        if payload.category_id:
            cat = db.scalars(
                select(BookCategory).where(
                    BookCategory.id == payload.category_id,
                    BookCategory.school_id == school_id,
                    BookCategory.is_deleted.is_(False),
                )
            ).first()
            if not cat:
                raise NotFoundException("Book Category", str(payload.category_id))

        book = Book(
            school_id=school_id,
            library_id=payload.library_id,
            category_id=payload.category_id,
            title=payload.title,
            subtitle=payload.subtitle,
            author=payload.author,
            publisher=payload.publisher,
            publication_year=payload.publication_year,
            isbn=payload.isbn,
            edition=payload.edition,
            language=payload.language,
            description=payload.description,
            total_pages=payload.total_pages,
            is_active=payload.is_active,
        )
        db.add(book)
        db.commit()
        db.refresh(book)
        return book

    def get_book(
        self,
        db: Session,
        school_id: UUID,
        book_id: UUID,
    ) -> Book:
        book = db.scalars(
            select(Book)
            .options(
                selectinload(Book.library),
                selectinload(Book.category),
                selectinload(Book.copies),
            )
            .where(
                Book.id == book_id,
                Book.school_id == school_id,
                Book.is_deleted.is_(False),
            )
        ).first()
        if not book:
            raise NotFoundException("Book", str(book_id))
        return book

    def list_books(
        self,
        db: Session,
        school_id: UUID,
        library_id: UUID | None = None,
        category_id: UUID | None = None,
        author: str | None = None,
        isbn: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Book], int, int]:
        stmt = select(Book).options(
            selectinload(Book.library),
            selectinload(Book.category),
            selectinload(Book.copies),
        ).where(
            Book.school_id == school_id,
            Book.is_deleted.is_(False),
        )
        if library_id:
            stmt = stmt.where(Book.library_id == library_id)
        if category_id:
            stmt = stmt.where(Book.category_id == category_id)
        if author:
            stmt = stmt.where(Book.author.ilike(f"%{author.strip()}%"))
        if isbn:
            stmt = stmt.where(Book.isbn == isbn.strip())
        if is_active is not None:
            stmt = stmt.where(Book.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    Book.title.ilike(term),
                    Book.subtitle.ilike(term),
                    Book.author.ilike(term),
                    Book.isbn.ilike(term),
                    Book.publisher.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(Book.title.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    def update_book(
        self,
        db: Session,
        school_id: UUID,
        book_id: UUID,
        payload: BookUpdate,
    ) -> Book:
        book = self.get_book(db=db, school_id=school_id, book_id=book_id)

        if payload.library_id is not None:
            if payload.library_id:
                lib = db.scalars(
                    select(Library).where(
                        Library.id == payload.library_id,
                        Library.school_id == school_id,
                        Library.is_deleted.is_(False),
                    )
                ).first()
                if not lib:
                    raise NotFoundException("Library", str(payload.library_id))
            book.library_id = payload.library_id

        if payload.category_id is not None:
            if payload.category_id:
                cat = db.scalars(
                    select(BookCategory).where(
                        BookCategory.id == payload.category_id,
                        BookCategory.school_id == school_id,
                        BookCategory.is_deleted.is_(False),
                    )
                ).first()
                if not cat:
                    raise NotFoundException("Book Category", str(payload.category_id))
            book.category_id = payload.category_id

        if payload.title is not None:
            book.title = payload.title
        if payload.subtitle is not None:
            book.subtitle = payload.subtitle
        if payload.author is not None:
            book.author = payload.author
        if payload.publisher is not None:
            book.publisher = payload.publisher
        if payload.publication_year is not None:
            book.publication_year = payload.publication_year
        if payload.isbn is not None:
            book.isbn = payload.isbn
        if payload.edition is not None:
            book.edition = payload.edition
        if payload.language is not None:
            book.language = payload.language
        if payload.description is not None:
            book.description = payload.description
        if payload.total_pages is not None:
            book.total_pages = payload.total_pages
        if payload.is_active is not None:
            book.is_active = payload.is_active

        db.commit()
        db.refresh(book)
        return book

    def delete_book(
        self,
        db: Session,
        school_id: UUID,
        book_id: UUID,
    ) -> None:
        book = self.get_book(db=db, school_id=school_id, book_id=book_id)
        book.is_deleted = True
        book.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 4. BOOK COPY (ACCESSION) MANAGEMENT
    # =========================================================================

    def create_book_copy(
        self,
        db: Session,
        school_id: UUID,
        payload: BookCopyCreate,
    ) -> BookCopy:
        book = db.scalars(
            select(Book).where(
                Book.id == payload.book_id,
                Book.school_id == school_id,
                Book.is_deleted.is_(False),
            )
        ).first()
        if not book:
            raise NotFoundException("Book", str(payload.book_id))

        existing = db.scalars(
            select(BookCopy).where(
                BookCopy.school_id == school_id,
                BookCopy.accession_number == payload.accession_number,
                BookCopy.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Book Copy accession number", payload.accession_number)

        copy = BookCopy(
            school_id=school_id,
            book_id=payload.book_id,
            accession_number=payload.accession_number,
            barcode=payload.barcode,
            rfid_tag=payload.rfid_tag,
            status=payload.status,
            condition=payload.condition,
            shelf_location=payload.shelf_location,
            acquisition_date=payload.acquisition_date,
            acquisition_price=payload.acquisition_price,
            is_active=payload.is_active,
        )
        db.add(copy)
        db.commit()
        db.refresh(copy)
        return copy

    def get_book_copy(
        self,
        db: Session,
        school_id: UUID,
        copy_id: UUID,
    ) -> BookCopy:
        copy = db.scalars(
            select(BookCopy)
            .options(selectinload(BookCopy.book))
            .where(
                BookCopy.id == copy_id,
                BookCopy.school_id == school_id,
                BookCopy.is_deleted.is_(False),
            )
        ).first()
        if not copy:
            raise NotFoundException("Book Copy", str(copy_id))
        return copy

    def list_book_copies(
        self,
        db: Session,
        school_id: UUID,
        book_id: UUID | None = None,
        status: BookCopyStatus | None = None,
        condition: BookCondition | None = None,
        shelf_location: str | None = None,
        search: str | None = None,
        is_active: bool | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookCopy], int, int]:
        stmt = select(BookCopy).options(
            selectinload(BookCopy.book)
        ).where(
            BookCopy.school_id == school_id,
            BookCopy.is_deleted.is_(False),
        )
        if book_id:
            stmt = stmt.where(BookCopy.book_id == book_id)
        if status:
            stmt = stmt.where(BookCopy.status == status)
        if condition:
            stmt = stmt.where(BookCopy.condition == condition)
        if shelf_location:
            stmt = stmt.where(BookCopy.shelf_location == shelf_location)
        if is_active is not None:
            stmt = stmt.where(BookCopy.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    BookCopy.accession_number.ilike(term),
                    BookCopy.barcode.ilike(term),
                    BookCopy.shelf_location.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(BookCopy.accession_number.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    def update_book_copy(
        self,
        db: Session,
        school_id: UUID,
        copy_id: UUID,
        payload: BookCopyUpdate,
    ) -> BookCopy:
        copy = self.get_book_copy(db=db, school_id=school_id, copy_id=copy_id)

        if payload.accession_number is not None and payload.accession_number != copy.accession_number:
            existing = db.scalars(
                select(BookCopy).where(
                    BookCopy.school_id == school_id,
                    BookCopy.accession_number == payload.accession_number,
                    BookCopy.id != copy_id,
                    BookCopy.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Book Copy accession number", payload.accession_number)
            copy.accession_number = payload.accession_number

        if payload.barcode is not None:
            copy.barcode = payload.barcode
        if payload.rfid_tag is not None:
            copy.rfid_tag = payload.rfid_tag
        if payload.status is not None:
            copy.status = payload.status
        if payload.condition is not None:
            copy.condition = payload.condition
        if payload.shelf_location is not None:
            copy.shelf_location = payload.shelf_location
        if payload.acquisition_date is not None:
            copy.acquisition_date = payload.acquisition_date
        if payload.acquisition_price is not None:
            copy.acquisition_price = payload.acquisition_price
        if payload.is_active is not None:
            copy.is_active = payload.is_active

        db.commit()
        db.refresh(copy)
        return copy

    def delete_book_copy(
        self,
        db: Session,
        school_id: UUID,
        copy_id: UUID,
    ) -> None:
        copy = self.get_book_copy(db=db, school_id=school_id, copy_id=copy_id)
        # Prevent deletion if active loan exists
        active_loan = db.scalars(
            select(BookLoan).where(
                BookLoan.school_id == school_id,
                BookLoan.book_copy_id == copy_id,
                BookLoan.status.in_([BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]),
                BookLoan.is_deleted.is_(False),
            )
        ).first()
        if active_loan:
            raise BadRequestException("Cannot delete book copy with an active circulation loan.")

        copy.is_deleted = True
        copy.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 5. LIBRARY MEMBER MANAGEMENT
    # =========================================================================

    def create_member(
        self,
        db: Session,
        school_id: UUID,
        payload: LibraryMemberCreate,
    ) -> LibraryMember:
        if payload.member_type == LibraryMemberType.STUDENT:
            if not payload.student_id:
                raise ValidationException("student_id is required for STUDENT member type.")
            student = db.scalars(
                select(Student).where(
                    Student.id == payload.student_id,
                    Student.school_id == school_id,
                    Student.is_deleted.is_(False),
                )
            ).first()
            if not student:
                raise NotFoundException("Student", str(payload.student_id))

            # Ensure student doesn't already have an active membership
            existing_student_member = db.scalars(
                select(LibraryMember).where(
                    LibraryMember.school_id == school_id,
                    LibraryMember.student_id == payload.student_id,
                    LibraryMember.is_deleted.is_(False),
                )
            ).first()
            if existing_student_member:
                raise AlreadyExistsException("Active library membership for student", str(payload.student_id))

        elif payload.member_type == LibraryMemberType.TEACHER:
            if not payload.teacher_id:
                raise ValidationException("teacher_id is required for TEACHER member type.")
            teacher = db.scalars(
                select(Teacher).where(
                    Teacher.id == payload.teacher_id,
                    Teacher.school_id == school_id,
                    Teacher.is_deleted.is_(False),
                )
            ).first()
            if not teacher:
                raise NotFoundException("Teacher", str(payload.teacher_id))

            existing_teacher_member = db.scalars(
                select(LibraryMember).where(
                    LibraryMember.school_id == school_id,
                    LibraryMember.teacher_id == payload.teacher_id,
                    LibraryMember.is_deleted.is_(False),
                )
            ).first()
            if existing_teacher_member:
                raise AlreadyExistsException("Active library membership for teacher", str(payload.teacher_id))

        elif payload.member_type == LibraryMemberType.STAFF:
            if not payload.user_id:
                raise ValidationException("user_id is required for STAFF member type.")
            user = db.scalars(
                select(IdentityUser).where(
                    IdentityUser.id == payload.user_id,
                    IdentityUser.school_id == school_id,
                    IdentityUser.is_deleted.is_(False),
                )
            ).first()
            if not user:
                raise NotFoundException("Staff User", str(payload.user_id))

        # Check card number uniqueness within school
        existing_card = db.scalars(
            select(LibraryMember).where(
                LibraryMember.school_id == school_id,
                LibraryMember.card_number == payload.card_number,
                LibraryMember.is_deleted.is_(False),
            )
        ).first()
        if existing_card:
            raise AlreadyExistsException("Library card number", payload.card_number)

        member = LibraryMember(
            school_id=school_id,
            member_type=payload.member_type,
            student_id=payload.student_id,
            teacher_id=payload.teacher_id,
            user_id=payload.user_id,
            card_number=payload.card_number,
            issue_date=payload.issue_date,
            expiry_date=payload.expiry_date,
            max_books_allowed=payload.max_books_allowed,
            status=payload.status,
            remarks=payload.remarks,
        )
        db.add(member)
        db.commit()
        db.refresh(member)
        return member

    def get_member(
        self,
        db: Session,
        school_id: UUID,
        member_id: UUID,
    ) -> LibraryMember:
        member = db.scalars(
            select(LibraryMember)
            .options(
                selectinload(LibraryMember.student),
                selectinload(LibraryMember.teacher),
                selectinload(LibraryMember.user),
                selectinload(LibraryMember.loans),
            )
            .where(
                LibraryMember.id == member_id,
                LibraryMember.school_id == school_id,
                LibraryMember.is_deleted.is_(False),
            )
        ).first()
        if not member:
            raise NotFoundException("Library Member", str(member_id))
        return member

    def list_members(
        self,
        db: Session,
        school_id: UUID,
        member_type: LibraryMemberType | None = None,
        status: LibraryMemberStatus | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LibraryMember], int, int]:
        stmt = select(LibraryMember).options(
            selectinload(LibraryMember.student),
            selectinload(LibraryMember.teacher),
            selectinload(LibraryMember.user),
            selectinload(LibraryMember.loans),
        ).where(
            LibraryMember.school_id == school_id,
            LibraryMember.is_deleted.is_(False),
        )
        if member_type:
            stmt = stmt.where(LibraryMember.member_type == member_type)
        if status:
            stmt = stmt.where(LibraryMember.status == status)
        if search:
            term = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    LibraryMember.card_number.ilike(term),
                    LibraryMember.remarks.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(LibraryMember.card_number.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    def update_member(
        self,
        db: Session,
        school_id: UUID,
        member_id: UUID,
        payload: LibraryMemberUpdate,
    ) -> LibraryMember:
        member = self.get_member(db=db, school_id=school_id, member_id=member_id)

        if payload.card_number is not None and payload.card_number != member.card_number:
            existing = db.scalars(
                select(LibraryMember).where(
                    LibraryMember.school_id == school_id,
                    LibraryMember.card_number == payload.card_number,
                    LibraryMember.id != member_id,
                    LibraryMember.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Library card number", payload.card_number)
            member.card_number = payload.card_number

        if payload.expiry_date is not None:
            member.expiry_date = payload.expiry_date
        if payload.max_books_allowed is not None:
            member.max_books_allowed = payload.max_books_allowed
        if payload.status is not None:
            member.status = payload.status
        if payload.remarks is not None:
            member.remarks = payload.remarks

        db.commit()
        db.refresh(member)
        return member

    def delete_member(
        self,
        db: Session,
        school_id: UUID,
        member_id: UUID,
    ) -> None:
        member = self.get_member(db=db, school_id=school_id, member_id=member_id)
        # Check if member has active loans
        active_loans = [
            loan for loan in member.loans
            if not loan.is_deleted and loan.status in [BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]
        ]
        if active_loans:
            raise BadRequestException("Cannot delete library member with active borrowed books.")

        member.is_deleted = True
        member.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 6. CIRCULATION (LOANS / CHECKOUT / RETURN / RENEW)
    # =========================================================================

    def checkout_book(
        self,
        db: Session,
        school_id: UUID,
        payload: BookLoanCheckout,
        issued_by_user_id: UUID | None = None,
    ) -> BookLoan:
        if payload.due_date < payload.issue_date:
            raise ValidationException("Due date must be on or after issue date.")

        # 1. Fetch & Validate Book Copy
        copy = db.scalars(
            select(BookCopy).where(
                BookCopy.id == payload.book_copy_id,
                BookCopy.school_id == school_id,
                BookCopy.is_deleted.is_(False),
            )
        ).first()
        if not copy:
            raise NotFoundException("Book Copy", str(payload.book_copy_id))
        if not copy.is_active or copy.status != BookCopyStatus.AVAILABLE:
            raise BadRequestException(f"Book copy is not available for checkout (current status: {copy.status.value}).")

        # 2. Fetch & Validate Member
        member = db.scalars(
            select(LibraryMember)
            .options(selectinload(LibraryMember.loans))
            .where(
                LibraryMember.id == payload.member_id,
                LibraryMember.school_id == school_id,
                LibraryMember.is_deleted.is_(False),
            )
        ).first()
        if not member:
            raise NotFoundException("Library Member", str(payload.member_id))
        if member.status != LibraryMemberStatus.ACTIVE:
            raise BadRequestException(f"Library member account is not active (current status: {member.status.value}).")
        if member.expiry_date and member.expiry_date < payload.issue_date:
            raise BadRequestException("Library membership has expired.")

        # 3. Check Borrowing Limit
        active_loans_count = sum(
            1 for loan in member.loans
            if not loan.is_deleted and loan.status in [BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]
        )
        if active_loans_count >= member.max_books_allowed:
            raise BadRequestException(
                f"Member has reached maximum borrowing limit ({member.max_books_allowed} books)."
            )

        # 4. Check for active loan on this copy (DB invariant)
        existing_loan = db.scalars(
            select(BookLoan).where(
                BookLoan.school_id == school_id,
                BookLoan.book_copy_id == copy.id,
                BookLoan.status.in_([BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]),
                BookLoan.is_deleted.is_(False),
            )
        ).first()
        if existing_loan:
            raise BadRequestException("This book copy is already issued in an active loan.")

        # 5. Create Loan & Update Copy Status
        loan = BookLoan(
            school_id=school_id,
            member_id=member.id,
            book_copy_id=copy.id,
            issue_date=payload.issue_date,
            due_date=payload.due_date,
            status=BookLoanStatus.ISSUED,
            issued_by_user_id=issued_by_user_id,
            remarks=payload.remarks,
        )
        copy.status = BookCopyStatus.ISSUED

        # If there is a fulfilled reservation for this member & book, mark fulfilled
        reservation = db.scalars(
            select(BookReservation).where(
                BookReservation.school_id == school_id,
                BookReservation.member_id == member.id,
                BookReservation.book_id == copy.book_id,
                BookReservation.status == BookReservationStatus.PENDING,
                BookReservation.is_deleted.is_(False),
            )
        ).first()
        if reservation:
            reservation.status = BookReservationStatus.FULFILLED

        db.add(loan)
        db.commit()
        db.refresh(loan)
        return loan

    def return_book(
        self,
        db: Session,
        school_id: UUID,
        loan_id: UUID,
        payload: BookLoanReturn,
        received_by_user_id: UUID | None = None,
    ) -> BookLoan:
        loan = db.scalars(
            select(BookLoan)
            .options(
                selectinload(BookLoan.book_copy),
                selectinload(BookLoan.member),
            )
            .where(
                BookLoan.id == loan_id,
                BookLoan.school_id == school_id,
                BookLoan.is_deleted.is_(False),
            )
        ).first()
        if not loan:
            raise NotFoundException("Book Loan", str(loan_id))

        if loan.status not in [BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]:
            raise BadRequestException(f"Loan is already returned or closed (current status: {loan.status.value}).")

        if payload.return_date < loan.issue_date:
            raise ValidationException("Return date cannot be earlier than loan issue date.")

        loan.return_date = payload.return_date
        loan.status = BookLoanStatus.RETURNED
        loan.received_by_user_id = received_by_user_id
        if payload.remarks:
            loan.remarks = (loan.remarks or "") + (" | " if loan.remarks else "") + payload.remarks

        if loan.book_copy:
            loan.book_copy.status = BookCopyStatus.AVAILABLE

        db.commit()
        db.refresh(loan)
        return loan

    def renew_loan(
        self,
        db: Session,
        school_id: UUID,
        loan_id: UUID,
        payload: BookLoanRenew,
    ) -> BookLoan:
        loan = db.scalars(
            select(BookLoan).where(
                BookLoan.id == loan_id,
                BookLoan.school_id == school_id,
                BookLoan.is_deleted.is_(False),
            )
        ).first()
        if not loan:
            raise NotFoundException("Book Loan", str(loan_id))

        if loan.status not in [BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]:
            raise BadRequestException(f"Cannot renew a closed or returned loan (current status: {loan.status.value}).")

        if payload.new_due_date <= loan.due_date:
            raise ValidationException("New due date must be after current due date.")

        if loan.renewal_count >= loan.max_renewals:
            raise BadRequestException(f"Maximum renewal limit reached ({loan.max_renewals} renewals).")

        loan.due_date = payload.new_due_date
        loan.renewal_count += 1
        loan.status = BookLoanStatus.ISSUED  # Reset from OVERDUE if renewed to future date
        if payload.remarks:
            loan.remarks = (loan.remarks or "") + (" | Renewal: " if loan.remarks else "Renewal: ") + payload.remarks

        db.commit()
        db.refresh(loan)
        return loan

    def get_loan(
        self,
        db: Session,
        school_id: UUID,
        loan_id: UUID,
    ) -> BookLoan:
        loan = db.scalars(
            select(BookLoan)
            .options(
                selectinload(BookLoan.member),
                selectinload(BookLoan.book_copy).selectinload(BookCopy.book),
            )
            .where(
                BookLoan.id == loan_id,
                BookLoan.school_id == school_id,
                BookLoan.is_deleted.is_(False),
            )
        ).first()
        if not loan:
            raise NotFoundException("Book Loan", str(loan_id))
        return loan

    def list_loans(
        self,
        db: Session,
        school_id: UUID,
        member_id: UUID | None = None,
        book_copy_id: UUID | None = None,
        status: BookLoanStatus | None = None,
        overdue_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookLoan], int, int]:
        stmt = select(BookLoan).options(
            selectinload(BookLoan.member),
            selectinload(BookLoan.book_copy).selectinload(BookCopy.book),
        ).where(
            BookLoan.school_id == school_id,
            BookLoan.is_deleted.is_(False),
        )
        if member_id:
            stmt = stmt.where(BookLoan.member_id == member_id)
        if book_copy_id:
            stmt = stmt.where(BookLoan.book_copy_id == book_copy_id)
        if status:
            stmt = stmt.where(BookLoan.status == status)
        if overdue_only:
            today = date.today()
            stmt = stmt.where(
                BookLoan.status == BookLoanStatus.ISSUED,
                BookLoan.due_date < today,
            )

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(BookLoan.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    # =========================================================================
    # 7. BOOK RESERVATIONS
    # =========================================================================

    def create_reservation(
        self,
        db: Session,
        school_id: UUID,
        payload: BookReservationCreate,
    ) -> BookReservation:
        # Validate Member
        member = db.scalars(
            select(LibraryMember).where(
                LibraryMember.id == payload.member_id,
                LibraryMember.school_id == school_id,
                LibraryMember.is_deleted.is_(False),
            )
        ).first()
        if not member:
            raise NotFoundException("Library Member", str(payload.member_id))
        if member.status != LibraryMemberStatus.ACTIVE:
            raise BadRequestException("Member account is not active.")

        # Validate Book
        book = db.scalars(
            select(Book).where(
                Book.id == payload.book_id,
                Book.school_id == school_id,
                Book.is_deleted.is_(False),
            )
        ).first()
        if not book:
            raise NotFoundException("Book", str(payload.book_id))

        if payload.expiry_date and payload.expiry_date < payload.reservation_date:
            raise ValidationException("Reservation expiry date must be on or after reservation date.")

        # Check existing pending reservation (DB constraint uq_pending_member_book_reservation)
        existing = db.scalars(
            select(BookReservation).where(
                BookReservation.school_id == school_id,
                BookReservation.member_id == payload.member_id,
                BookReservation.book_id == payload.book_id,
                BookReservation.status == BookReservationStatus.PENDING,
                BookReservation.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Pending reservation for member on this book")

        reservation = BookReservation(
            school_id=school_id,
            member_id=payload.member_id,
            book_id=payload.book_id,
            reservation_date=payload.reservation_date,
            expiry_date=payload.expiry_date,
            status=BookReservationStatus.PENDING,
        )
        db.add(reservation)
        db.commit()
        db.refresh(reservation)
        return reservation

    def cancel_reservation(
        self,
        db: Session,
        school_id: UUID,
        reservation_id: UUID,
    ) -> BookReservation:
        res = db.scalars(
            select(BookReservation).where(
                BookReservation.id == reservation_id,
                BookReservation.school_id == school_id,
                BookReservation.is_deleted.is_(False),
            )
        ).first()
        if not res:
            raise NotFoundException("Book Reservation", str(reservation_id))

        if res.status != BookReservationStatus.PENDING:
            raise BadRequestException(f"Only PENDING reservations can be cancelled (current status: {res.status.value}).")

        res.status = BookReservationStatus.CANCELLED
        db.commit()
        db.refresh(res)
        return res

    def get_reservation(
        self,
        db: Session,
        school_id: UUID,
        reservation_id: UUID,
    ) -> BookReservation:
        res = db.scalars(
            select(BookReservation)
            .options(
                selectinload(BookReservation.member),
                selectinload(BookReservation.book),
            )
            .where(
                BookReservation.id == reservation_id,
                BookReservation.school_id == school_id,
                BookReservation.is_deleted.is_(False),
            )
        ).first()
        if not res:
            raise NotFoundException("Book Reservation", str(reservation_id))
        return res

    def list_reservations(
        self,
        db: Session,
        school_id: UUID,
        member_id: UUID | None = None,
        book_id: UUID | None = None,
        status: BookReservationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[BookReservation], int, int]:
        stmt = select(BookReservation).options(
            selectinload(BookReservation.member),
            selectinload(BookReservation.book),
        ).where(
            BookReservation.school_id == school_id,
            BookReservation.is_deleted.is_(False),
        )
        if member_id:
            stmt = stmt.where(BookReservation.member_id == member_id)
        if book_id:
            stmt = stmt.where(BookReservation.book_id == book_id)
        if status:
            stmt = stmt.where(BookReservation.status == status)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(BookReservation.reservation_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    # =========================================================================
    # 8. LIBRARY FINES
    # =========================================================================

    def create_fine(
        self,
        db: Session,
        school_id: UUID,
        payload: LibraryFineCreate,
    ) -> LibraryFine:
        if payload.amount < Decimal("0.00"):
            raise ValidationException("Fine amount cannot be negative.")

        member = db.scalars(
            select(LibraryMember).where(
                LibraryMember.id == payload.member_id,
                LibraryMember.school_id == school_id,
                LibraryMember.is_deleted.is_(False),
            )
        ).first()
        if not member:
            raise NotFoundException("Library Member", str(payload.member_id))

        if payload.loan_id:
            loan = db.scalars(
                select(BookLoan).where(
                    BookLoan.id == payload.loan_id,
                    BookLoan.school_id == school_id,
                    BookLoan.is_deleted.is_(False),
                )
            ).first()
            if not loan:
                raise NotFoundException("Book Loan", str(payload.loan_id))

        fine = LibraryFine(
            school_id=school_id,
            loan_id=payload.loan_id,
            member_id=payload.member_id,
            amount=payload.amount,
            fine_reason=payload.fine_reason,
            status=payload.status,
        )
        db.add(fine)
        db.commit()
        db.refresh(fine)
        return fine

    def waive_fine(
        self,
        db: Session,
        school_id: UUID,
        fine_id: UUID,
        payload: LibraryFineWaive,
        waived_by_user_id: UUID | None = None,
    ) -> LibraryFine:
        fine = db.scalars(
            select(LibraryFine).where(
                LibraryFine.id == fine_id,
                LibraryFine.school_id == school_id,
                LibraryFine.is_deleted.is_(False),
            )
        ).first()
        if not fine:
            raise NotFoundException("Library Fine", str(fine_id))

        if fine.status in [LibraryFineStatus.PAID, LibraryFineStatus.WAIVED]:
            raise BadRequestException(f"Cannot waive fine that is already {fine.status.value}.")

        fine.status = LibraryFineStatus.WAIVED
        fine.waived_reason = payload.waived_reason
        fine.waived_by_user_id = waived_by_user_id
        db.commit()
        db.refresh(fine)
        return fine

    def get_fine(
        self,
        db: Session,
        school_id: UUID,
        fine_id: UUID,
    ) -> LibraryFine:
        fine = db.scalars(
            select(LibraryFine)
            .options(
                selectinload(LibraryFine.member),
                selectinload(LibraryFine.loan),
            )
            .where(
                LibraryFine.id == fine_id,
                LibraryFine.school_id == school_id,
                LibraryFine.is_deleted.is_(False),
            )
        ).first()
        if not fine:
            raise NotFoundException("Library Fine", str(fine_id))
        return fine

    def list_fines(
        self,
        db: Session,
        school_id: UUID,
        member_id: UUID | None = None,
        loan_id: UUID | None = None,
        status: LibraryFineStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[LibraryFine], int, int]:
        stmt = select(LibraryFine).options(
            selectinload(LibraryFine.member),
            selectinload(LibraryFine.loan),
        ).where(
            LibraryFine.school_id == school_id,
            LibraryFine.is_deleted.is_(False),
        )
        if member_id:
            stmt = stmt.where(LibraryFine.member_id == member_id)
        if loan_id:
            stmt = stmt.where(LibraryFine.loan_id == loan_id)
        if status:
            stmt = stmt.where(LibraryFine.status == status)

        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 1

        items = db.scalars(
            stmt.order_by(LibraryFine.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()
        return list(items), total, total_pages

    # =========================================================================
    # 9. LIBRARY SUMMARY / DERIVED OPERATIONAL ANALYTICS
    # =========================================================================

    def get_library_summary(
        self,
        db: Session,
        school_id: UUID,
    ) -> LibrarySummaryResponse:
        total_libraries = db.scalar(
            select(func.count(Library.id)).where(
                Library.school_id == school_id,
                Library.is_deleted.is_(False),
            )
        ) or 0

        total_books = db.scalar(
            select(func.count(Book.id)).where(
                Book.school_id == school_id,
                Book.is_deleted.is_(False),
            )
        ) or 0

        total_copies = db.scalar(
            select(func.count(BookCopy.id)).where(
                BookCopy.school_id == school_id,
                BookCopy.is_deleted.is_(False),
            )
        ) or 0

        available_copies = db.scalar(
            select(func.count(BookCopy.id)).where(
                BookCopy.school_id == school_id,
                BookCopy.status == BookCopyStatus.AVAILABLE,
                BookCopy.is_deleted.is_(False),
            )
        ) or 0

        issued_copies = db.scalar(
            select(func.count(BookCopy.id)).where(
                BookCopy.school_id == school_id,
                BookCopy.status == BookCopyStatus.ISSUED,
                BookCopy.is_deleted.is_(False),
            )
        ) or 0

        lost_or_damaged = db.scalar(
            select(func.count(BookCopy.id)).where(
                BookCopy.school_id == school_id,
                BookCopy.status.in_([BookCopyStatus.LOST, BookCopyStatus.DAMAGED]),
                BookCopy.is_deleted.is_(False),
            )
        ) or 0

        active_members = db.scalar(
            select(func.count(LibraryMember.id)).where(
                LibraryMember.school_id == school_id,
                LibraryMember.status == LibraryMemberStatus.ACTIVE,
                LibraryMember.is_deleted.is_(False),
            )
        ) or 0

        active_loans = db.scalar(
            select(func.count(BookLoan.id)).where(
                BookLoan.school_id == school_id,
                BookLoan.status.in_([BookLoanStatus.ISSUED, BookLoanStatus.OVERDUE]),
                BookLoan.is_deleted.is_(False),
            )
        ) or 0

        today = date.today()
        overdue_loans = db.scalar(
            select(func.count(BookLoan.id)).where(
                BookLoan.school_id == school_id,
                BookLoan.status == BookLoanStatus.ISSUED,
                BookLoan.due_date < today,
                BookLoan.is_deleted.is_(False),
            )
        ) or 0

        pending_reservations = db.scalar(
            select(func.count(BookReservation.id)).where(
                BookReservation.school_id == school_id,
                BookReservation.status == BookReservationStatus.PENDING,
                BookReservation.is_deleted.is_(False),
            )
        ) or 0

        pending_fines = db.scalar(
            select(func.coalesce(func.sum(LibraryFine.amount), Decimal("0.00"))).where(
                LibraryFine.school_id == school_id,
                LibraryFine.status == LibraryFineStatus.PENDING,
                LibraryFine.is_deleted.is_(False),
            )
        ) or Decimal("0.00")

        return LibrarySummaryResponse(
            total_libraries_count=total_libraries,
            total_books_count=total_books,
            total_copies_count=total_copies,
            available_copies_count=available_copies,
            issued_copies_count=issued_copies,
            lost_or_damaged_copies_count=lost_or_damaged,
            active_members_count=active_members,
            active_loans_count=active_loans,
            overdue_loans_count=overdue_loans,
            pending_reservations_count=pending_reservations,
            pending_fines_amount=pending_fines,
        )


library_service = LibraryService()
