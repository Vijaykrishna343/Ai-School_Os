from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.enums import (
    AcademicYearStatus,
    BloodGroup,
    Gender,
    StudentStatus,
)
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
from app.common.enums.teacher import TeacherStatus
from app.database.common_model import CommonModel
from app.identity.models.user import IdentityUser
from app.models.academic_year.academic_year import AcademicYear
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
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher


@pytest.fixture(autouse=True)
def setup_library_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    yield


@pytest.fixture
def library_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Oakridge Public School A",
        code=f"LIB-SCH-A-{uuid.uuid4().hex[:4]}",
        address_line1="100 Library Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B (for tenant isolation)
    school_b = School(
        id=uuid.uuid4(),
        name="Oakridge Public School B",
        code=f"LIB-SCH-B-{uuid.uuid4().hex[:4]}",
        address_line1="200 Library Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    # Academic Year
    ay_a = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    ay_b = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add_all([ay_a, ay_b])
    db_session.flush()

    # Parents
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Ramesh Patel",
        primary_phone=f"98711{uuid.uuid4().hex[:5]}",
        email=f"ramesh.{uuid.uuid4().hex[:4]}@gmail.com",
        address_line1="123 Palm Grove",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Suresh Nair",
        primary_phone=f"98722{uuid.uuid4().hex[:5]}",
        email=f"suresh.{uuid.uuid4().hex[:4]}@gmail.com",
        address_line1="456 Palm Grove",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([parent_a, parent_b])
    db_session.flush()

    # Classes & Sections
    cls_a = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Grade 8",
        display_order=8,
    )
    cls_b = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="Grade 8",
        display_order=8,
    )
    db_session.add_all([cls_a, cls_b])
    db_session.flush()

    sec_a = Section(
        id=uuid.uuid4(),
        school_class_id=cls_a.id,
        name="Section A",
    )
    sec_b = Section(
        id=uuid.uuid4(),
        school_class_id=cls_b.id,
        name="Section B",
    )
    db_session.add_all([sec_a, sec_b])
    db_session.flush()

    # Students
    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        admission_number=f"ADM-LA-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="101",
        first_name="Aarav",
        last_name="Patel",
        date_of_birth=date(2012, 4, 10),
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        address_line1="123 Palm Grove",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    student_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        admission_number=f"ADM-LB-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="102",
        first_name="Diya",
        last_name="Nair",
        date_of_birth=date(2012, 6, 15),
        gender=Gender.FEMALE,
        blood_group=BloodGroup.A_POSITIVE,
        academic_year_id=ay_b.id,
        school_class_id=cls_b.id,
        section_id=sec_b.id,
        parent_id=parent_b.id,
        address_line1="456 Palm Grove",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add_all([student_a, student_b])
    db_session.flush()

    # Teachers
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id=f"EMP-LA-{uuid.uuid4().hex[:4]}",
        first_name="Meera",
        last_name="Sen",
        email=f"meera.{uuid.uuid4().hex[:4]}@school.com",
        phone=f"98711{uuid.uuid4().hex[:5]}",
        date_of_birth=date(1990, 3, 25),
        gender=Gender.FEMALE,
        joining_date=date(2022, 6, 1),
        qualification="M.Sc, B.Ed",
        address_line1="100 Library Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        employee_id=f"EMP-LB-{uuid.uuid4().hex[:4]}",
        first_name="Anil",
        last_name="Kapoor",
        email=f"anil.{uuid.uuid4().hex[:4]}@school.com",
        phone=f"98722{uuid.uuid4().hex[:5]}",
        date_of_birth=date(1988, 7, 12),
        gender=Gender.MALE,
        joining_date=date(2021, 6, 1),
        qualification="M.A, B.Ed",
        address_line1="200 Library Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([teacher_a, teacher_b])
    db_session.flush()

    # Identity Users (Librarians / Staff)
    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"librarian.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        first_name="Alice",
        last_name="Librarian",
        is_active=True,
    )
    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"librarian.b.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="$argon2id$v=19$m=65536,t=3,p=4$fakehash",
        first_name="Bob",
        last_name="Librarian",
        is_active=True,
    )
    db_session.add_all([user_a, user_b])
    db_session.flush()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "student_a": student_a,
        "student_b": student_b,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "user_a": user_a,
        "user_b": user_b,
    }


# =============================================================================
# 1. LIBRARY ENTITY TESTS
# =============================================================================
def test_library_valid_creation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    lib = Library(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Central Senior Library",
        code="LIB-MAIN",
        description="Main campus library building",
        location="Block B, 2nd Floor",
        is_active=True,
    )
    db_session.add(lib)
    db_session.flush()

    assert lib.id is not None
    assert lib.school_id == school_a.id
    assert lib.name == "Central Senior Library"
    assert lib.code == "LIB-MAIN"
    assert lib.is_active is True


def test_library_tenant_scoped_code_uniqueness(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    school_b = library_fixture["school_b"]

    lib_a1 = Library(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Primary Library",
        code="LIB-01",
    )
    db_session.add(lib_a1)
    db_session.flush()

    # Duplicate code in same school fails
    lib_a2 = Library(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Junior Library",
        code="LIB-01",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(lib_a2)
            db_session.flush()

    # Same code in School B succeeds (tenant isolation)
    lib_b = Library(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="School B Main Library",
        code="LIB-01",
    )
    db_session.add(lib_b)
    db_session.flush()
    assert lib_b.id is not None
    assert lib_b.school_id == school_b.id


def test_library_soft_delete_recreation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    lib = Library(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Archived Library",
        code="LIB-ARCH",
        is_active=True,
    )
    db_session.add(lib)
    db_session.flush()

    lib.is_deleted = True
    db_session.flush()

    # Creating active library with same code succeeds after soft-delete
    lib_new = Library(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Replaced Library",
        code="LIB-ARCH",
        is_active=True,
    )
    db_session.add(lib_new)
    db_session.flush()
    assert lib_new.id != lib.id


# =============================================================================
# 2. BOOK CATEGORY TESTS
# =============================================================================
def test_category_valid_creation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    cat = BookCategory(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Science & Technology",
        code="SCI-TECH",
        description="Physics, Chemistry, Computer Science",
        is_active=True,
    )
    db_session.add(cat)
    db_session.flush()

    assert cat.id is not None
    assert cat.name == "Science & Technology"
    assert cat.code == "SCI-TECH"


def test_category_tenant_scoped_uniqueness(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    school_b = library_fixture["school_b"]

    cat_a = BookCategory(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Literature",
        code="LIT",
    )
    db_session.add(cat_a)
    db_session.flush()

    # Duplicate name in School A fails
    cat_a_dup = BookCategory(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Literature",
        code="LIT-2",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(cat_a_dup)
            db_session.flush()

    # Same category in School B succeeds
    cat_b = BookCategory(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="Literature",
        code="LIT",
    )
    db_session.add(cat_b)
    db_session.flush()
    assert cat_b.id is not None


# =============================================================================
# 3. BOOK CATALOG TESTS
# =============================================================================
def test_book_valid_creation_and_relationships(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    lib = Library(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Main Campus Library",
        code="LIB-MAIN-BK",
    )
    cat = BookCategory(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Mathematics",
        code="MATH",
    )
    db_session.add_all([lib, cat])
    db_session.flush()

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        library_id=lib.id,
        category_id=cat.id,
        title="Higher Engineering Mathematics",
        subtitle="Comprehensive Problem Sets",
        author="B.S. Grewal",
        publisher="Khanna Publishers",
        publication_year=2021,
        isbn="978-8174091955",
        edition="44th",
        language="English",
        description="Standard reference text for engineering mathematics",
        total_pages=1350,
        is_active=True,
    )
    db_session.add(book)
    db_session.flush()

    assert book.id is not None
    assert book.title == "Higher Engineering Mathematics"
    assert book.library.name == "Main Campus Library"
    assert book.category.name == "Mathematics"
    assert book.total_pages == 1350


def test_book_tenant_isolation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    school_b = library_fixture["school_b"]

    book_a = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Physics for Scientists",
        author="Serway & Jewett",
        isbn="978-1133947271",
    )
    book_b = Book(
        id=uuid.uuid4(),
        school_id=school_b.id,
        title="Physics for Scientists",
        author="Serway & Jewett",
        isbn="978-1133947271",
    )
    db_session.add_all([book_a, book_b])
    db_session.flush()

    books_school_a = db_session.scalars(select(Book).where(Book.school_id == school_a.id)).all()
    assert len(books_school_a) == 1
    assert books_school_a[0].id == book_a.id


# =============================================================================
# 4. BOOK COPY (ACCESSION) TESTS
# =============================================================================
def test_book_copy_valid_creation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Introduction to Algorithms",
        author="Cormen, Leiserson, Rivest, Stein",
        isbn="978-0262033848",
    )
    db_session.add(book)
    db_session.flush()

    copy1 = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="ACC-2026-0001",
        barcode="BAR-CLRS-01",
        status=BookCopyStatus.AVAILABLE,
        condition=BookCondition.NEW,
        shelf_location="CS-Rack-3",
        acquisition_date=date(2026, 6, 1),
        acquisition_price=Decimal("4500.00"),
        is_active=True,
    )
    copy2 = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="ACC-2026-0002",
        barcode="BAR-CLRS-02",
        status=BookCopyStatus.AVAILABLE,
        condition=BookCondition.GOOD,
        shelf_location="CS-Rack-3",
        acquisition_date=date(2026, 6, 1),
        acquisition_price=Decimal("4500.00"),
        is_active=True,
    )
    db_session.add_all([copy1, copy2])
    db_session.flush()

    assert copy1.id is not None
    assert copy2.id is not None
    assert copy1.accession_number == "ACC-2026-0001"
    assert copy1.acquisition_price == Decimal("4500.00")
    assert len(book.copies) == 2


def test_book_copy_accession_uniqueness(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    school_b = library_fixture["school_b"]

    book_a = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Concepts of Physics Vol 1",
        author="H.C. Verma",
    )
    book_b = Book(
        id=uuid.uuid4(),
        school_id=school_b.id,
        title="Concepts of Physics Vol 1",
        author="H.C. Verma",
    )
    db_session.add_all([book_a, book_b])
    db_session.flush()

    copy_a1 = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book_a.id,
        accession_number="HCV-001",
    )
    db_session.add(copy_a1)
    db_session.flush()

    # Duplicate accession in same school fails
    copy_a2 = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book_a.id,
        accession_number="HCV-001",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(copy_a2)
            db_session.flush()

    # Same accession in School B succeeds (tenant isolation)
    copy_b = BookCopy(
        id=uuid.uuid4(),
        school_id=school_b.id,
        book_id=book_b.id,
        accession_number="HCV-001",
    )
    db_session.add(copy_b)
    db_session.flush()
    assert copy_b.id is not None


def test_book_copy_negative_price_rejection(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Negative Price Test",
        author="Test Author",
    )
    db_session.add(book)
    db_session.flush()

    bad_copy = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="NEG-001",
        acquisition_price=Decimal("-150.00"),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(bad_copy)
            db_session.flush()


# =============================================================================
# 5. LIBRARY MEMBERSHIP TESTS
# =============================================================================
def test_student_and_teacher_membership_valid_creation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]
    teacher_a = library_fixture["teacher_a"]

    # Student Member
    mem_student = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-STUD-101",
        issue_date=date(2026, 6, 1),
        expiry_date=date(2027, 5, 31),
        max_books_allowed=3,
        status=LibraryMemberStatus.ACTIVE,
    )
    # Teacher Member
    mem_teacher = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.TEACHER,
        teacher_id=teacher_a.id,
        card_number="CARD-TEACH-201",
        issue_date=date(2026, 6, 1),
        expiry_date=date(2028, 5, 31),
        max_books_allowed=10,
        status=LibraryMemberStatus.ACTIVE,
    )
    db_session.add_all([mem_student, mem_teacher])
    db_session.flush()

    assert mem_student.id is not None
    assert mem_student.display_name == "Aarav Patel"
    assert mem_teacher.display_name == "Meera Sen"
    assert mem_student.max_books_allowed == 3
    assert mem_teacher.max_books_allowed == 10


def test_member_card_number_uniqueness(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]
    teacher_a = library_fixture["teacher_a"]

    mem1 = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-DUP-01",
        issue_date=date(2026, 6, 1),
    )
    db_session.add(mem1)
    db_session.flush()

    # Duplicate card_number in same school fails
    mem2 = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.TEACHER,
        teacher_id=teacher_a.id,
        card_number="CARD-DUP-01",
        issue_date=date(2026, 6, 1),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(mem2)
            db_session.flush()


def test_member_single_active_membership_per_student(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]

    mem1 = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-ST-1",
        issue_date=date(2026, 6, 1),
    )
    db_session.add(mem1)
    db_session.flush()

    # Second active membership for same student fails partial unique index
    mem2 = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-ST-2",
        issue_date=date(2026, 6, 1),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(mem2)
            db_session.flush()


# =============================================================================
# 6. BOOK LOAN (CIRCULATION) TESTS & SINGLE ACTIVE LOAN INVARIANT
# =============================================================================
def test_loan_valid_issue_and_return(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]
    user_a = library_fixture["user_a"]

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Clean Code",
        author="Robert C. Martin",
    )
    db_session.add(book)
    db_session.flush()

    copy = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="CLN-001",
        status=BookCopyStatus.AVAILABLE,
    )
    member = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="MEM-CLN-01",
        issue_date=date(2026, 6, 1),
    )
    db_session.add_all([copy, member])
    db_session.flush()

    today = date(2026, 6, 1)
    due = today + timedelta(days=14)

    # Issue loan
    loan = BookLoan(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=member.id,
        book_copy_id=copy.id,
        issue_date=today,
        due_date=due,
        status=BookLoanStatus.ISSUED,
        issued_by_user_id=user_a.id,
    )
    copy.status = BookCopyStatus.ISSUED
    db_session.add(loan)
    db_session.flush()

    assert loan.id is not None
    assert loan.status == BookLoanStatus.ISSUED
    assert loan.due_date == due
    assert loan.member.display_name == "Aarav Patel"

    # Return book
    returned_date = today + timedelta(days=10)
    loan.return_date = returned_date
    loan.status = BookLoanStatus.RETURNED
    loan.received_by_user_id = user_a.id
    copy.status = BookCopyStatus.AVAILABLE
    db_session.flush()

    assert loan.status == BookLoanStatus.RETURNED
    assert loan.return_date == returned_date
    assert copy.status == BookCopyStatus.AVAILABLE


def test_loan_single_active_loan_per_physical_copy(db_session, library_fixture):
    """
    Critical Invariant: One physical book copy CANNOT have multiple active loans (ISSUED or OVERDUE).
    """
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]
    teacher_a = library_fixture["teacher_a"]

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Single Copy Test Title",
        author="Author Test",
    )
    db_session.add(book)
    db_session.flush()

    copy = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="SGL-COPY-001",
        status=BookCopyStatus.AVAILABLE,
    )
    mem1 = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-SGL-1",
        issue_date=date(2026, 6, 1),
    )
    mem2 = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.TEACHER,
        teacher_id=teacher_a.id,
        card_number="CARD-SGL-2",
        issue_date=date(2026, 6, 1),
    )
    db_session.add_all([copy, mem1, mem2])
    db_session.flush()

    # Loan 1: Issue to mem1
    loan1 = BookLoan(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=mem1.id,
        book_copy_id=copy.id,
        issue_date=date(2026, 6, 1),
        due_date=date(2026, 6, 15),
        status=BookLoanStatus.ISSUED,
    )
    db_session.add(loan1)
    db_session.flush()

    # Loan 2: Attempt concurrent active issue on SAME copy to mem2 -> MUST fail partial unique index
    loan2 = BookLoan(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=mem2.id,
        book_copy_id=copy.id,
        issue_date=date(2026, 6, 2),
        due_date=date(2026, 6, 16),
        status=BookLoanStatus.ISSUED,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(loan2)
            db_session.flush()


def test_loan_due_date_check_constraint(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Check Constraint Book",
        author="Author",
    )
    db_session.add(book)
    db_session.flush()

    copy = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="CHK-001",
    )
    member = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-CHK-1",
        issue_date=date(2026, 6, 1),
    )
    db_session.add_all([copy, member])
    db_session.flush()

    # Due date before issue date fails check constraint
    bad_loan = BookLoan(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=member.id,
        book_copy_id=copy.id,
        issue_date=date(2026, 6, 15),
        due_date=date(2026, 6, 10),  # INVALID: due < issue
        status=BookLoanStatus.ISSUED,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(bad_loan)
            db_session.flush()


# =============================================================================
# 7. BOOK RESERVATION TESTS
# =============================================================================
def test_reservation_valid_and_single_pending_rule(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="The Design of Everyday Things",
        author="Don Norman",
    )
    db_session.add(book)
    db_session.flush()

    member = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-RES-1",
        issue_date=date(2026, 6, 1),
    )
    db_session.add(member)
    db_session.flush()

    res1 = BookReservation(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=member.id,
        book_id=book.id,
        reservation_date=date(2026, 6, 1),
        expiry_date=date(2026, 6, 8),
        status=BookReservationStatus.PENDING,
    )
    db_session.add(res1)
    db_session.flush()

    assert res1.id is not None
    assert res1.status == BookReservationStatus.PENDING

    # Attempt second pending reservation for same member and book -> fails unique constraint
    res2 = BookReservation(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=member.id,
        book_id=book.id,
        reservation_date=date(2026, 6, 2),
        status=BookReservationStatus.PENDING,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(res2)
            db_session.flush()


# =============================================================================
# 8. LIBRARY FINE TESTS
# =============================================================================
def test_fine_valid_creation_and_non_negative_check(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]
    user_a = library_fixture["user_a"]

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Domain-Driven Design",
        author="Eric Evans",
    )
    db_session.add(book)
    db_session.flush()

    copy = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="DDD-001",
    )
    member = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-DDD-1",
        issue_date=date(2026, 6, 1),
    )
    db_session.add_all([copy, member])
    db_session.flush()

    loan = BookLoan(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=member.id,
        book_copy_id=copy.id,
        issue_date=date(2026, 6, 1),
        due_date=date(2026, 6, 15),
        return_date=date(2026, 6, 25),  # 10 days overdue
        status=BookLoanStatus.OVERDUE,
    )
    db_session.add(loan)
    db_session.flush()

    fine = LibraryFine(
        id=uuid.uuid4(),
        school_id=school_a.id,
        loan_id=loan.id,
        member_id=member.id,
        amount=Decimal("50.00"),
        fine_reason=LibraryFineReason.OVERDUE,
        status=LibraryFineStatus.PENDING,
    )
    db_session.add(fine)
    db_session.flush()

    assert fine.id is not None
    assert fine.amount == Decimal("50.00")
    assert fine.status == LibraryFineStatus.PENDING

    # Waive fine
    fine.status = LibraryFineStatus.WAIVED
    fine.waived_reason = "Medical exemption granted"
    fine.waived_by_user_id = user_a.id
    db_session.flush()

    assert fine.status == LibraryFineStatus.WAIVED
    assert fine.waived_reason == "Medical exemption granted"
    assert fine.waived_by.first_name == "Alice"


def test_fine_negative_amount_rejection(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    student_a = library_fixture["student_a"]

    book = Book(
        id=uuid.uuid4(),
        school_id=school_a.id,
        title="Fine Negative Test Book",
        author="Author",
    )
    db_session.add(book)
    db_session.flush()

    copy = BookCopy(
        id=uuid.uuid4(),
        school_id=school_a.id,
        book_id=book.id,
        accession_number="FNE-001",
    )
    member = LibraryMember(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_type=LibraryMemberType.STUDENT,
        student_id=student_a.id,
        card_number="CARD-FNE-1",
        issue_date=date(2026, 6, 1),
    )
    db_session.add_all([copy, member])
    db_session.flush()

    loan = BookLoan(
        id=uuid.uuid4(),
        school_id=school_a.id,
        member_id=member.id,
        book_copy_id=copy.id,
        issue_date=date(2026, 6, 1),
        due_date=date(2026, 6, 15),
        status=BookLoanStatus.ISSUED,
    )
    db_session.add(loan)
    db_session.flush()

    # Negative fine amount fails check constraint
    bad_fine = LibraryFine(
        id=uuid.uuid4(),
        school_id=school_a.id,
        loan_id=loan.id,
        member_id=member.id,
        amount=Decimal("-25.00"),
        fine_reason=LibraryFineReason.OVERDUE,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(bad_fine)
            db_session.flush()


# =============================================================================
# 9. CROSS-TENANT STRICT ISOLATION AUDIT
# =============================================================================
def test_cross_tenant_library_isolation(db_session, library_fixture):
    school_a = library_fixture["school_a"]
    school_b = library_fixture["school_b"]

    lib_a = Library(id=uuid.uuid4(), school_id=school_a.id, name="Lib A", code="LA")
    lib_b = Library(id=uuid.uuid4(), school_id=school_b.id, name="Lib B", code="LB")
    cat_a = BookCategory(id=uuid.uuid4(), school_id=school_a.id, name="Cat A", code="CA")
    cat_b = BookCategory(id=uuid.uuid4(), school_id=school_b.id, name="Cat B", code="CB")
    book_a = Book(id=uuid.uuid4(), school_id=school_a.id, title="Book A", author="Author A", library_id=lib_a.id, category_id=cat_a.id)
    book_b = Book(id=uuid.uuid4(), school_id=school_b.id, title="Book B", author="Author B", library_id=lib_b.id, category_id=cat_b.id)
    copy_a = BookCopy(id=uuid.uuid4(), school_id=school_a.id, book_id=book_a.id, accession_number="ACC-A1")
    copy_b = BookCopy(id=uuid.uuid4(), school_id=school_b.id, book_id=book_b.id, accession_number="ACC-B1")
    mem_a = LibraryMember(id=uuid.uuid4(), school_id=school_a.id, member_type=LibraryMemberType.STUDENT, student_id=library_fixture["student_a"].id, card_number="CARD-A1", issue_date=date(2026, 6, 1))
    mem_b = LibraryMember(id=uuid.uuid4(), school_id=school_b.id, member_type=LibraryMemberType.STUDENT, student_id=library_fixture["student_b"].id, card_number="CARD-B1", issue_date=date(2026, 6, 1))

    db_session.add_all([lib_a, lib_b, cat_a, cat_b, book_a, book_b, copy_a, copy_b, mem_a, mem_b])
    db_session.flush()

    # Verify querying School A strictly returns only School A entities
    a_libs = db_session.scalars(select(Library).where(Library.school_id == school_a.id)).all()
    a_books = db_session.scalars(select(Book).where(Book.school_id == school_a.id)).all()
    a_copies = db_session.scalars(select(BookCopy).where(BookCopy.school_id == school_a.id)).all()
    a_members = db_session.scalars(select(LibraryMember).where(LibraryMember.school_id == school_a.id)).all()

    assert len(a_libs) == 1
    assert a_libs[0].id == lib_a.id
    assert len(a_books) == 1
    assert a_books[0].id == book_a.id
    assert len(a_copies) == 1
    assert a_copies[0].id == copy_a.id
    assert len(a_members) == 1
    assert a_members[0].id == mem_a.id
