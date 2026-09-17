from datetime import date, timedelta
from decimal import Decimal
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.common.enums import (
    AcademicYearStatus,
    BloodGroup,
    Gender,
    StudentStatus,
    TeacherStatus,
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
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
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
def setup_library_api_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def library_api_fixture(db_session):
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

    # Academic Years
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
    cls_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Grade 8", display_order=8)
    cls_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Grade 8", display_order=8)
    db_session.add_all([cls_a, cls_b])
    db_session.flush()

    sec_a = Section(id=uuid.uuid4(), school_class_id=cls_a.id, name="Section A")
    sec_b = Section(id=uuid.uuid4(), school_class_id=cls_b.id, name="Section B")
    db_session.add_all([sec_a, sec_b])
    db_session.flush()

    # Students
    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        admission_number=f"ADM-A-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="101",
        first_name="Aarav",
        last_name="Patel",
        date_of_birth=date(2012, 4, 10),
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
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
        academic_year_id=ay_b.id,
        school_class_id=cls_b.id,
        section_id=sec_b.id,
        parent_id=parent_b.id,
        admission_number=f"ADM-B-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="102",
        first_name="Diya",
        last_name="Nair",
        date_of_birth=date(2012, 6, 15),
        gender=Gender.FEMALE,
        blood_group=BloodGroup.A_POSITIVE,
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
        employee_id=f"EMP-A-{uuid.uuid4().hex[:4]}",
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
        employee_id=f"EMP-B-{uuid.uuid4().hex[:4]}",
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

    # Helper for Permissions
    def get_or_create_perm(name, action, module="library"):
        p = db_session.query(IdentityPermission).filter_by(name=name).first()
        if not p:
            p = IdentityPermission(
                id=uuid.uuid4(),
                name=name,
                action=action,
                module=module,
                description=f"{action} {module}",
            )
            db_session.add(p)
            db_session.flush()
        return p

    perm_view = get_or_create_perm("library.view", "view")
    perm_create = get_or_create_perm("library.create", "create")
    perm_update = get_or_create_perm("library.update", "update")
    perm_delete = get_or_create_perm("library.delete", "delete")
    perm_circulate = get_or_create_perm("library.circulate", "circulate")
    perm_manage = get_or_create_perm("library.manage", "manage")

    # Full Admin Role for School A
    admin_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Librarian Admin A {uuid.uuid4().hex[:4]}",
        description="Full Library Admin",
        permissions=[perm_view, perm_create, perm_update, perm_delete, perm_circulate, perm_manage],
    )
    # View-only Role for School A
    view_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Library Viewer A {uuid.uuid4().hex[:4]}",
        description="View only",
        permissions=[perm_view],
    )
    # Full Admin Role for School B
    admin_role_b = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name=f"Librarian Admin B {uuid.uuid4().hex[:4]}",
        description="Full Library Admin B",
        permissions=[perm_view, perm_create, perm_update, perm_delete, perm_circulate, perm_manage],
    )
    db_session.add_all([admin_role_a, view_role_a, admin_role_b])
    db_session.flush()

    # Users
    user_admin_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"admin.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Alice",
        last_name="Admin",
        is_active=True,
        roles=[admin_role_a],
    )
    user_viewer_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"viewer.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Victor",
        last_name="Viewer",
        is_active=True,
        roles=[view_role_a],
    )
    user_admin_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"admin.b.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Bob",
        last_name="Admin",
        is_active=True,
        roles=[admin_role_b],
    )
    user_inactive_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"inactive.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Ian",
        last_name="Inactive",
        is_active=False,
        roles=[admin_role_a],
    )
    db_session.add_all([user_admin_a, user_viewer_a, user_admin_b, user_inactive_a])
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
        "user_admin_a": user_admin_a,
        "user_viewer_a": user_viewer_a,
        "user_admin_b": user_admin_b,
        "user_inactive_a": user_inactive_a,
    }


def auth_client(user: IdentityUser) -> TestClient:
    fastapi_app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(fastapi_app)


# =============================================================================
# 1. LIBRARY CRUD & VALIDATION TESTS
# =============================================================================

def test_library_crud_and_validation(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    client = auth_client(user_a)

    # 1. Create Library
    create_payload = {
        "name": "Central Campus Library",
        "code": "LIB-CENTRAL",
        "description": "Main library facility",
        "location": "Building A, 2nd Floor",
        "is_active": True,
    }
    resp = client.post("/api/v1/library/libraries", json=create_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    lib_data = resp.json()
    assert lib_data["name"] == "Central Campus Library"
    assert lib_data["code"] == "LIB-CENTRAL"
    lib_id = lib_data["id"]

    # Duplicate code rejection
    dup_resp = client.post("/api/v1/library/libraries", json=create_payload)
    assert dup_resp.status_code == status.HTTP_409_CONFLICT

    # 2. Get Library
    get_resp = client.get(f"/api/v1/library/libraries/{lib_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["id"] == lib_id

    # 3. List Libraries
    list_resp = client.get("/api/v1/library/libraries")
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] >= 1
    assert any(item["id"] == lib_id for item in list_resp.json()["items"])

    # 4. Update Library
    upd_payload = {
        "name": "Central Library Renovated",
        "location": "Building A, 3rd Floor",
    }
    upd_resp = client.put(f"/api/v1/library/libraries/{lib_id}", json=upd_payload)
    assert upd_resp.status_code == status.HTTP_200_OK
    assert upd_resp.json()["name"] == "Central Library Renovated"
    assert upd_resp.json()["location"] == "Building A, 3rd Floor"

    # 5. Delete Library
    del_resp = client.delete(f"/api/v1/library/libraries/{lib_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT

    # Verify deleted
    get_del = client.get(f"/api/v1/library/libraries/{lib_id}")
    assert get_del.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# 2. BOOK CATEGORY CRUD TESTS
# =============================================================================

def test_category_crud_and_validation(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    client = auth_client(user_a)

    # 1. Create Category
    create_payload = {
        "name": "Computer Science",
        "code": "CS",
        "description": "Programming, Algorithms, AI",
        "is_active": True,
    }
    resp = client.post("/api/v1/library/categories", json=create_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    cat_id = resp.json()["id"]
    assert resp.json()["name"] == "Computer Science"

    # Duplicate name rejection
    dup_resp = client.post("/api/v1/library/categories", json=create_payload)
    assert dup_resp.status_code == status.HTTP_409_CONFLICT

    # 2. List Categories
    list_resp = client.get("/api/v1/library/categories?search=Computer")
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["id"] == cat_id

    # 3. Update Category
    upd_resp = client.put(f"/api/v1/library/categories/{cat_id}", json={"description": "Updated CS description"})
    assert upd_resp.status_code == status.HTTP_200_OK
    assert upd_resp.json()["description"] == "Updated CS description"

    # 4. Delete Category
    del_resp = client.delete(f"/api/v1/library/categories/{cat_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 3. BOOK CATALOG CRUD & RELATIONSHIPS
# =============================================================================

def test_book_crud_and_relationships(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    client = auth_client(user_a)

    # Create library & category first
    lib_resp = client.post("/api/v1/library/libraries", json={"name": "Science Library", "code": "SCI-LIB"})
    lib_id = lib_resp.json()["id"]

    cat_resp = client.post("/api/v1/library/categories", json={"name": "Mathematics", "code": "MATH"})
    cat_id = cat_resp.json()["id"]

    # 1. Create Book
    book_payload = {
        "library_id": lib_id,
        "category_id": cat_id,
        "title": "Clean Architecture",
        "subtitle": "A Craftsman's Guide to Software Structure",
        "author": "Robert C. Martin",
        "publisher": "Prentice Hall",
        "publication_year": 2017,
        "isbn": "978-0134494166",
        "edition": "1st",
        "language": "English",
        "description": "Essential architecture patterns and software design",
        "total_pages": 432,
        "is_active": True,
    }
    resp = client.post("/api/v1/library/books", json=book_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    book_data = resp.json()
    assert book_data["title"] == "Clean Architecture"
    assert book_data["library_name"] == "Science Library"
    assert book_data["category_name"] == "Mathematics"
    book_id = book_data["id"]

    # 2. Get Book
    get_resp = client.get(f"/api/v1/library/books/{book_id}")
    assert get_resp.status_code == status.HTTP_200_OK
    assert get_resp.json()["id"] == book_id

    # 3. List Books with filters
    list_resp = client.get("/api/v1/library/books?search=Martin&category_id=" + cat_id)
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["id"] == book_id

    # 4. Update Book
    upd_resp = client.put(f"/api/v1/library/books/{book_id}", json={"subtitle": "Updated Subtitle"})
    assert upd_resp.status_code == status.HTTP_200_OK
    assert upd_resp.json()["subtitle"] == "Updated Subtitle"

    # 5. Delete Book
    del_resp = client.delete(f"/api/v1/library/books/{book_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 4. BOOK COPY (PHYSICAL INVENTORY) TESTS
# =============================================================================

def test_book_copy_crud_and_accession_rules(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    client = auth_client(user_a)

    # Create book
    book_resp = client.post("/api/v1/library/books", json={"title": "Test Driven Development", "author": "Kent Beck"})
    book_id = book_resp.json()["id"]

    # 1. Create Copy 1
    copy1_payload = {
        "book_id": book_id,
        "accession_number": "TDD-ACC-001",
        "barcode": "BAR-TDD-01",
        "shelf_location": "Rack A1",
        "acquisition_price": "1200.50",
        "status": BookCopyStatus.AVAILABLE.value,
        "condition": BookCondition.NEW.value,
    }
    resp1 = client.post("/api/v1/library/copies", json=copy1_payload)
    assert resp1.status_code == status.HTTP_201_CREATED
    copy1_id = resp1.json()["id"]
    assert resp1.json()["accession_number"] == "TDD-ACC-001"
    assert resp1.json()["acquisition_price"] == "1200.50"
    assert resp1.json()["book_title"] == "Test Driven Development"

    # Duplicate accession in same school fails
    dup_resp = client.post("/api/v1/library/copies", json=copy1_payload)
    assert dup_resp.status_code == status.HTTP_409_CONFLICT

    # 2. List Copies
    list_resp = client.get(f"/api/v1/library/copies?book_id={book_id}")
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] == 1

    # 3. Update Copy
    upd_resp = client.put(f"/api/v1/library/copies/{copy1_id}", json={"condition": BookCondition.GOOD.value, "shelf_location": "Rack A2"})
    assert upd_resp.status_code == status.HTTP_200_OK
    assert upd_resp.json()["condition"] == BookCondition.GOOD.value
    assert upd_resp.json()["shelf_location"] == "Rack A2"

    # 4. Delete Copy
    del_resp = client.delete(f"/api/v1/library/copies/{copy1_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 5. LIBRARY MEMBER MANAGEMENT TESTS
# =============================================================================

def test_member_crud_and_validation(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    student_a = library_api_fixture["student_a"]
    teacher_a = library_api_fixture["teacher_a"]
    client = auth_client(user_a)

    # 1. Register Student Member
    student_member_payload = {
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_a.id),
        "card_number": "CARD-STUD-999",
        "issue_date": "2026-06-01",
        "max_books_allowed": 3,
        "status": LibraryMemberStatus.ACTIVE.value,
    }
    resp = client.post("/api/v1/library/members", json=student_member_payload)
    assert resp.status_code == status.HTTP_201_CREATED
    mem_data = resp.json()
    assert mem_data["card_number"] == "CARD-STUD-999"
    assert mem_data["display_name"] == "Aarav Patel"
    mem_id = mem_data["id"]

    # Duplicate active student member fails
    dup_student = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_a.id),
        "card_number": "CARD-STUD-998",
        "issue_date": "2026-06-01",
    })
    assert dup_student.status_code == status.HTTP_409_CONFLICT

    # 2. Register Teacher Member
    teacher_member_payload = {
        "member_type": LibraryMemberType.TEACHER.value,
        "teacher_id": str(teacher_a.id),
        "card_number": "CARD-TEACH-888",
        "issue_date": "2026-06-01",
        "max_books_allowed": 10,
    }
    resp_t = client.post("/api/v1/library/members", json=teacher_member_payload)
    assert resp_t.status_code == status.HTTP_201_CREATED
    assert resp_t.json()["display_name"] == "Meera Sen"

    # 3. List Members
    list_resp = client.get("/api/v1/library/members?member_type=STUDENT")
    assert list_resp.status_code == status.HTTP_200_OK
    assert list_resp.json()["total"] == 1
    assert list_resp.json()["items"][0]["id"] == mem_id

    # 4. Update Member
    upd_resp = client.put(f"/api/v1/library/members/{mem_id}", json={"max_books_allowed": 5, "remarks": "Honor Student"})
    assert upd_resp.status_code == status.HTTP_200_OK
    assert upd_resp.json()["max_books_allowed"] == 5
    assert upd_resp.json()["remarks"] == "Honor Student"

    # 5. Delete Member
    del_resp = client.delete(f"/api/v1/library/members/{mem_id}")
    assert del_resp.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 6. CIRCULATION LIFECYCLE (CHECKOUT, RETURN, RENEW)
# =============================================================================

def test_circulation_checkout_return_renew_lifecycle(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    student_a = library_api_fixture["student_a"]
    client = auth_client(user_a)

    # 1. Setup Book, Copy, Member
    book_resp = client.post("/api/v1/library/books", json={"title": "Designing Data-Intensive Applications", "author": "Martin Kleppmann"})
    book_id = book_resp.json()["id"]

    copy_resp = client.post("/api/v1/library/copies", json={
        "book_id": book_id,
        "accession_number": "DDIA-001",
    })
    copy_id = copy_resp.json()["id"]

    mem_resp = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_a.id),
        "card_number": "CARD-CIRC-1",
        "max_books_allowed": 2,
    })
    member_id = mem_resp.json()["id"]

    # 2. Checkout
    today = date.today()
    due = today + timedelta(days=14)
    checkout_payload = {
        "member_id": member_id,
        "book_copy_id": copy_id,
        "issue_date": str(today),
        "due_date": str(due),
        "remarks": "Semester loan",
    }
    loan_resp = client.post("/api/v1/library/loans/checkout", json=checkout_payload)
    assert loan_resp.status_code == status.HTTP_201_CREATED
    loan_data = loan_resp.json()
    loan_id = loan_data["id"]
    assert loan_data["status"] == BookLoanStatus.ISSUED.value
    assert loan_data["member_display_name"] == "Aarav Patel"
    assert loan_data["accession_number"] == "DDIA-001"

    # Verify copy status updated to ISSUED
    copy_check = client.get(f"/api/v1/library/copies/{copy_id}")
    assert copy_check.json()["status"] == BookCopyStatus.ISSUED.value

    # Attempting second checkout on same copy fails
    dup_loan = client.post("/api/v1/library/loans/checkout", json=checkout_payload)
    assert dup_loan.status_code == status.HTTP_400_BAD_REQUEST

    # Attempting to delete copy with active loan fails
    del_copy_fail = client.delete(f"/api/v1/library/copies/{copy_id}")
    assert del_copy_fail.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Renew Loan
    new_due = due + timedelta(days=7)
    renew_resp = client.post(f"/api/v1/library/loans/{loan_id}/renew", json={"new_due_date": str(new_due), "remarks": "Extended for exam"})
    assert renew_resp.status_code == status.HTTP_200_OK
    assert renew_resp.json()["renewal_count"] == 1
    assert renew_resp.json()["due_date"] == str(new_due)

    # 4. Return Loan
    return_payload = {
        "return_date": str(today + timedelta(days=5)),
        "remarks": "Returned in perfect condition",
    }
    return_resp = client.post(f"/api/v1/library/loans/{loan_id}/return", json=return_payload)
    assert return_resp.status_code == status.HTTP_200_OK
    assert return_resp.json()["status"] == BookLoanStatus.RETURNED.value
    assert return_resp.json()["return_date"] == str(today + timedelta(days=5))

    # Verify copy status reset to AVAILABLE
    copy_check2 = client.get(f"/api/v1/library/copies/{copy_id}")
    assert copy_check2.json()["status"] == BookCopyStatus.AVAILABLE.value

    # Repeated return fails
    repeated_return = client.post(f"/api/v1/library/loans/{loan_id}/return", json=return_payload)
    assert repeated_return.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# 7. BOOK RESERVATION TESTS
# =============================================================================

def test_reservation_lifecycle(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    student_a = library_api_fixture["student_a"]
    client = auth_client(user_a)

    book_resp = client.post("/api/v1/library/books", json={"title": "Structure and Interpretation of Computer Programs", "author": "Sussman"})
    book_id = book_resp.json()["id"]

    mem_resp = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_a.id),
        "card_number": "CARD-RES-99",
    })
    member_id = mem_resp.json()["id"]

    # 1. Create Reservation
    res_payload = {
        "member_id": member_id,
        "book_id": book_id,
        "reservation_date": str(date.today()),
        "expiry_date": str(date.today() + timedelta(days=7)),
    }
    res_resp = client.post("/api/v1/library/reservations", json=res_payload)
    assert res_resp.status_code == status.HTTP_201_CREATED
    res_id = res_resp.json()["id"]
    assert res_resp.json()["status"] == BookReservationStatus.PENDING.value
    assert res_resp.json()["book_title"] == "Structure and Interpretation of Computer Programs"

    # Duplicate pending reservation fails
    dup_res = client.post("/api/v1/library/reservations", json=res_payload)
    assert dup_res.status_code == status.HTTP_409_CONFLICT

    # 2. List Reservations
    list_res = client.get(f"/api/v1/library/reservations?member_id={member_id}")
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 1

    # 3. Cancel Reservation
    cancel_resp = client.post(f"/api/v1/library/reservations/{res_id}/cancel")
    assert cancel_resp.status_code == status.HTTP_200_OK
    assert cancel_resp.json()["status"] == BookReservationStatus.CANCELLED.value


# =============================================================================
# 8. LIBRARY FINE ASSESSMENT & WAIVER
# =============================================================================

def test_fine_assessment_and_waiver(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    student_a = library_api_fixture["student_a"]
    client = auth_client(user_a)

    # Setup Book, Copy, Member, Loan
    book_resp = client.post("/api/v1/library/books", json={"title": "Fine Test Title", "author": "Author F"})
    book_id = book_resp.json()["id"]

    copy_resp = client.post("/api/v1/library/copies", json={"book_id": book_id, "accession_number": "FINE-ACC-01"})
    copy_id = copy_resp.json()["id"]

    mem_resp = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_a.id),
        "card_number": "CARD-FINE-01",
    })
    member_id = mem_resp.json()["id"]

    loan_resp = client.post("/api/v1/library/loans/checkout", json={
        "member_id": member_id,
        "book_copy_id": copy_id,
        "due_date": str(date.today() + timedelta(days=7)),
    })
    loan_id = loan_resp.json()["id"]

    # 1. Create Fine
    fine_payload = {
        "loan_id": loan_id,
        "member_id": member_id,
        "amount": "150.00",
        "fine_reason": LibraryFineReason.OVERDUE.value,
        "status": LibraryFineStatus.PENDING.value,
    }
    fine_resp = client.post("/api/v1/library/fines", json=fine_payload)
    assert fine_resp.status_code == status.HTTP_201_CREATED
    fine_id = fine_resp.json()["id"]
    assert fine_resp.json()["amount"] == "150.00"
    assert fine_resp.json()["status"] == LibraryFineStatus.PENDING.value

    # Negative amount fails validation
    neg_payload = {
        "loan_id": loan_id,
        "member_id": member_id,
        "amount": "-50.00",
    }
    neg_resp = client.post("/api/v1/library/fines", json=neg_payload)
    assert neg_resp.status_code in [status.HTTP_422_UNPROCESSABLE_CONTENT, status.HTTP_400_BAD_REQUEST]

    # 2. List Fines
    list_fines = client.get(f"/api/v1/library/fines?member_id={member_id}")
    assert list_fines.status_code == status.HTTP_200_OK
    assert list_fines.json()["total"] == 1

    # 3. Waive Fine
    waive_resp = client.post(f"/api/v1/library/fines/{fine_id}/waive", json={"waived_reason": "Principal special approval"})
    assert waive_resp.status_code == status.HTTP_200_OK
    assert waive_resp.json()["status"] == LibraryFineStatus.WAIVED.value
    assert waive_resp.json()["waived_reason"] == "Principal special approval"

    # Repeated waiver fails
    rep_waive = client.post(f"/api/v1/library/fines/{fine_id}/waive", json={"waived_reason": "Another waive"})
    assert rep_waive.status_code == status.HTTP_400_BAD_REQUEST


# =============================================================================
# 9. OPERATIONAL SUMMARY / ANALYTICS
# =============================================================================

def test_library_operational_summary(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    student_a = library_api_fixture["student_a"]
    client = auth_client(user_a)

    # Setup 1 Library, 2 Books, 3 Copies, 1 Member, 1 Loan, 1 Fine
    lib_resp = client.post("/api/v1/library/libraries", json={"name": "Analytics Library", "code": "ANL-LIB"})
    book_resp = client.post("/api/v1/library/books", json={"title": "Book 1", "author": "Author 1"})
    book_id = book_resp.json()["id"]

    copy1_resp = client.post("/api/v1/library/copies", json={"book_id": book_id, "accession_number": "ANL-ACC-1"})
    copy2_resp = client.post("/api/v1/library/copies", json={"book_id": book_id, "accession_number": "ANL-ACC-2"})
    copy1_id = copy1_resp.json()["id"]

    mem_resp = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_a.id),
        "card_number": "CARD-ANL-1",
    })
    member_id = mem_resp.json()["id"]

    # Issue loan
    loan_resp = client.post("/api/v1/library/loans/checkout", json={
        "member_id": member_id,
        "book_copy_id": copy1_id,
        "due_date": str(date.today() + timedelta(days=7)),
    })
    loan_id = loan_resp.json()["id"]

    # Create pending fine
    client.post("/api/v1/library/fines", json={
        "loan_id": loan_id,
        "member_id": member_id,
        "amount": "75.50",
    })

    summary_resp = client.get("/api/v1/library/summary")
    assert summary_resp.status_code == status.HTTP_200_OK
    summary = summary_resp.json()
    assert summary["total_libraries_count"] >= 1
    assert summary["total_books_count"] >= 1
    assert summary["total_copies_count"] >= 2
    assert summary["available_copies_count"] >= 1
    assert summary["issued_copies_count"] >= 1
    assert summary["active_members_count"] >= 1
    assert summary["active_loans_count"] >= 1
    assert Decimal(str(summary["pending_fines_amount"])) >= Decimal("75.50")


# =============================================================================
# 10. CROSS-TENANT STRICT ISOLATION AUDIT
# =============================================================================

def test_cross_tenant_isolation_security(library_api_fixture):
    user_a = library_api_fixture["user_admin_a"]
    user_b = library_api_fixture["user_admin_b"]
    student_b = library_api_fixture["student_b"]

    client = TestClient(fastapi_app)

    # 1. School A creates library, book, copy, member
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    lib_a = client.post("/api/v1/library/libraries", json={"name": "School A Lib", "code": "SA-LIB"}).json()
    book_a = client.post("/api/v1/library/books", json={"title": "School A Title", "author": "Author A"}).json()
    copy_a = client.post("/api/v1/library/copies", json={"book_id": book_a["id"], "accession_number": "SA-ACC-1"}).json()
    mem_a = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(library_api_fixture["student_a"].id),
        "card_number": "SA-CARD-1",
    }).json()

    # 2. Switch to School B
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b

    # School B cannot read School A records
    assert client.get(f"/api/v1/library/libraries/{lib_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/library/books/{book_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/library/copies/{copy_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client.get(f"/api/v1/library/members/{mem_a['id']}").status_code == status.HTTP_404_NOT_FOUND

    # School B cannot update or delete School A records
    assert client.put(f"/api/v1/library/libraries/{lib_a['id']}", json={"name": "Hacked Lib"}).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/library/libraries/{lib_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client.put(f"/api/v1/library/books/{book_a['id']}", json={"title": "Hacked Title"}).status_code == status.HTTP_404_NOT_FOUND
    assert client.delete(f"/api/v1/library/books/{book_a['id']}").status_code == status.HTTP_404_NOT_FOUND

    # School B cannot create Copy referencing School A book
    bad_copy = client.post("/api/v1/library/copies", json={"book_id": book_a["id"], "accession_number": "SB-ACC-X"})
    assert bad_copy.status_code == status.HTTP_404_NOT_FOUND

    # School B cannot register Member referencing School A student
    bad_mem = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(library_api_fixture["student_a"].id),
        "card_number": "SB-CARD-X",
    })
    assert bad_mem.status_code == status.HTTP_404_NOT_FOUND

    # School B cannot checkout School A copy
    mem_b = client.post("/api/v1/library/members", json={
        "member_type": LibraryMemberType.STUDENT.value,
        "student_id": str(student_b.id),
        "card_number": "SB-CARD-1",
    }).json()
    bad_checkout = client.post("/api/v1/library/loans/checkout", json={
        "member_id": mem_b["id"],
        "book_copy_id": copy_a["id"],
        "due_date": str(date.today() + timedelta(days=14)),
    })
    assert bad_checkout.status_code == status.HTTP_404_NOT_FOUND


# =============================================================================
# 11. RBAC PERMISSION & INACTIVE USER TESTS
# =============================================================================

def test_rbac_permission_boundaries(library_api_fixture):
    viewer_a = library_api_fixture["user_viewer_a"]
    client_viewer = auth_client(viewer_a)

    # Viewer has library.view, but NOT library.create, library.update, library.delete, library.circulate, library.manage
    # GET succeeds
    assert client_viewer.get("/api/v1/library/libraries").status_code == status.HTTP_200_OK
    assert client_viewer.get("/api/v1/library/books").status_code == status.HTTP_200_OK

    # POST / PUT / DELETE denied with 403
    assert client_viewer.post("/api/v1/library/libraries", json={"name": "Fail Lib"}).status_code == status.HTTP_403_FORBIDDEN
    assert client_viewer.post("/api/v1/library/books", json={"title": "Fail Book", "author": "A"}).status_code == status.HTTP_403_FORBIDDEN
    assert client_viewer.post("/api/v1/library/copies", json={"book_id": str(uuid.uuid4()), "accession_number": "X"}).status_code == status.HTTP_403_FORBIDDEN
    assert client_viewer.post("/api/v1/library/members", json={"member_type": "STUDENT", "student_id": str(uuid.uuid4()), "card_number": "X"}).status_code == status.HTTP_403_FORBIDDEN
    assert client_viewer.post("/api/v1/library/loans/checkout", json={"member_id": str(uuid.uuid4()), "book_copy_id": str(uuid.uuid4()), "due_date": "2026-06-30"}).status_code == status.HTTP_403_FORBIDDEN
    assert client_viewer.post("/api/v1/library/fines", json={"member_id": str(uuid.uuid4()), "amount": "100.00"}).status_code == status.HTTP_403_FORBIDDEN


def test_inactive_user_rejection(library_api_fixture):
    from app.identity.security.jwt_manager import jwt_manager
    inactive_user = library_api_fixture["user_inactive_a"]
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(fastapi_app)

    token = jwt_manager.create_access_token(
        user_id=inactive_user.id, school_id=inactive_user.school_id
    )
    resp = client.get("/api/v1/library/libraries", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == status.HTTP_401_UNAUTHORIZED

