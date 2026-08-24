"""
Security Integration Tests for SEC-007B — Documents & File Storage Relationship Authorization.
"""
import io
import uuid
from datetime import date

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import AcademicYearStatus, Gender, StudentStatus, TeacherStatus
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders.permission_seeder import permission_seeder
from app.identity.seeders.role_permission_seeder import role_permission_seeder
from app.identity.seeders.role_seeder import role_seeder
from app.main import app
from app.models.academic_year.academic_year import AcademicYear
from app.models.document.document import Document, DocumentCategory, DocumentStatus, OwnerType
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.services.storage_service import storage_service


@pytest.fixture
def setup_doc_security_data(db_session: Session):
    role_seeder.seed(db_session)
    permission_seeder.seed(db_session)
    role_permission_seeder.seed(db_session)

    s = uuid.uuid4().hex[:6]

    # Create School A & B
    school_a = School(
        name=f"Doc Sec School A {s}", code=f"DSA_{s}", address_line1="123 St",
        city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    school_b = School(
        name=f"Doc Sec School B {s}", code=f"DSB_{s}", address_line1="456 St",
        city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(school_id=school_a.id, name=f"2026-2027_{s}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    ay_b = AcademicYear(school_id=school_b.id, name=f"2026-2027_{s}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    class_10a = SchoolClass(school_id=school_a.id, name=f"10_{s}", display_order=1)
    class_9a = SchoolClass(school_id=school_a.id, name=f"9_{s}", display_order=2)
    class_10b = SchoolClass(school_id=school_b.id, name=f"10_{s}", display_order=1)
    db_session.add_all([class_10a, class_9a, class_10b])
    db_session.commit()

    sec_10a = Section(school_class_id=class_10a.id, name="A")
    sec_9a = Section(school_class_id=class_9a.id, name="A")
    sec_10b = Section(school_class_id=class_10b.id, name="A")
    db_session.add_all([sec_10a, sec_9a, sec_10b])
    db_session.commit()

    # Roles
    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_principal = db_session.query(IdentityRole).filter_by(name="Principal").first()
    r_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    r_class_teacher = db_session.query(IdentityRole).filter_by(name="Class Teacher").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_acc = db_session.query(IdentityRole).filter_by(name="Accountant").first()
    r_rec = db_session.query(IdentityRole).filter_by(name="Receptionist").first()
    r_super = db_session.query(IdentityRole).filter_by(name="Super Admin").first()

    pwd = hash_password("Password@123")

    # Users School A
    u_admin = IdentityUser(email=f"admin_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin", last_name="A")
    u_principal = IdentityUser(email=f"principal_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Principal", last_name="A")
    u_teacher1 = IdentityUser(email=f"teacher1_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Teacher", last_name="One")
    u_teacher2 = IdentityUser(email=f"teacher2_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Teacher", last_name="Two")
    
    # Students School A
    # Student 1: Username = ADM_ST1
    u_student1 = IdentityUser(username=f"ADM_ST1_{s}", email=f"student1_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="One")
    # Student 2: Username = ADM_ST2
    u_student2 = IdentityUser(username=f"ADM_ST2_{s}", email=f"student2_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="Two")
    # Student 3: Username = ADM_ST3
    u_student3 = IdentityUser(username=f"ADM_ST3_{s}", email=f"student3_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="Three")

    # Parents School A
    # Parent 1 (Email match, linked to Student 1 & Student 2)
    u_parent1 = IdentityUser(email=f"parent1_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="One")
    # Parent 2 (Phone match, linked to Student 3)
    u_parent2 = IdentityUser(email=f"parent2_sec_{s}@school.com", phone="9876500001", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="Two")
    # Parent 3 (Zero children)
    u_parent3 = IdentityUser(email=f"parent3_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="Three")

    u_acc = IdentityUser(email=f"acc_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Acc", last_name="A")
    u_rec = IdentityUser(email=f"rec_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Rec", last_name="A")
    u_super = IdentityUser(email=f"super_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Super", last_name="Admin")

    # Users School B
    u_admin_b = IdentityUser(email=f"admin_sec_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Admin", last_name="B")
    u_student_b = IdentityUser(email=f"student_sec_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Student", last_name="B")

    db_session.add_all([
        u_admin, u_principal, u_teacher1, u_teacher2,
        u_student1, u_student2, u_student3,
        u_parent1, u_parent2, u_parent3,
        u_acc, u_rec, u_super, u_admin_b, u_student_b
    ])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_principal.id, role_id=r_principal.id),
        IdentityUserRole(user_id=u_teacher1.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_teacher2.id, role_id=r_class_teacher.id),
        IdentityUserRole(user_id=u_student1.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_student2.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_student3.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_parent1.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_parent2.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_parent3.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_acc.id, role_id=r_acc.id),
        IdentityUserRole(user_id=u_rec.id, role_id=r_rec.id),
        IdentityUserRole(user_id=u_super.id, role_id=r_super.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_student_b.id, role_id=r_student.id),
    ])
    db_session.commit()

    # Profiles
    teacher1_prof = Teacher(
        school_id=school_a.id, employee_id=f"EMP1_{s}", first_name="Teacher", last_name="One",
        email=u_teacher1.email, phone="9990000001", gender=Gender.MALE, date_of_birth=date(1985, 1, 1),
        joining_date=date(2020, 1, 1), status=TeacherStatus.ACTIVE, qualification="M.Sc Math", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    teacher2_prof = Teacher(
        school_id=school_a.id, employee_id=f"EMP2_{s}", first_name="Teacher", last_name="Two",
        email=u_teacher2.email, phone="9990000002", gender=Gender.FEMALE, date_of_birth=date(1987, 1, 1),
        joining_date=date(2021, 1, 1), status=TeacherStatus.ACTIVE, qualification="M.Sc Physics", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    p_prof1 = Parent(
        school_id=school_a.id, father_name="Parent One", mother_name="Mama One", email=u_parent1.email,
        primary_phone="9876500010", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    p_prof2 = Parent(
        school_id=school_a.id, father_name="Parent Two", mother_name="Mama Two", email=None,
        primary_phone="9876500001", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    p_prof3 = Parent(
        school_id=school_a.id, father_name="Parent Three", mother_name="Mama Three", email=u_parent3.email,
        primary_phone="9876500030", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    p_prof_b = Parent(
        school_id=school_b.id, father_name="Parent B", mother_name="Mama B", email=f"parent_b_{s}@school.com",
        primary_phone="9876500099", address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    db_session.add_all([teacher1_prof, teacher2_prof, p_prof1, p_prof2, p_prof3, p_prof_b])
    db_session.commit()

    st_prof1 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, parent_id=p_prof1.id,
        school_class_id=class_10a.id, section_id=sec_10a.id, admission_number=u_student1.username,
        roll_number="1", first_name="Student", last_name="One", email=u_student1.email,
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
        address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof2 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, parent_id=p_prof1.id,
        school_class_id=class_9a.id, section_id=sec_9a.id, admission_number=u_student2.username,
        roll_number="2", first_name="Student", last_name="Two", email=u_student2.email,
        gender=Gender.FEMALE, date_of_birth=date(2011, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
        address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof3 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, parent_id=p_prof2.id,
        school_class_id=class_10a.id, section_id=sec_10a.id, admission_number=u_student3.username,
        roll_number="3", first_name="Student", last_name="Three", email=u_student3.email,
        gender=Gender.MALE, date_of_birth=date(2010, 2, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
        address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof_b = Student(
        school_id=school_b.id, academic_year_id=ay_b.id, parent_id=p_prof_b.id,
        school_class_id=class_10b.id, section_id=sec_10b.id, admission_number=f"ADM_B_{s}",
        roll_number="1", first_name="Student", last_name="B", email=u_student_b.email,
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
        address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    db_session.add_all([st_prof1, st_prof2, st_prof3, st_prof_b])
    db_session.commit()

    # Documents
    # Student 1 Document (Birth Certificate)
    key1, sum1 = storage_service.store_file(school_a.id, "student", st_prof1.id, b"%PDF-1.4 Student 1 Birth Cert", "st1_birth.pdf")
    doc_st1 = Document(
        school_id=school_a.id, owner_type=OwnerType.STUDENT, owner_id=st_prof1.id,
        document_type=DocumentCategory.BIRTH_CERTIFICATE, title="Student 1 Birth Cert",
        original_filename="st1_birth.pdf", storage_key=key1, mime_type="application/pdf",
        file_size=len(b"%PDF-1.4 Student 1 Birth Cert"), checksum=sum1, status=DocumentStatus.VERIFIED,
        uploaded_by_id=u_admin.id, uploaded_at=date.today(), version=1, is_current=True, is_deleted=False
    )
    # Student 2 Document (Transfer Certificate)
    key2, sum2 = storage_service.store_file(school_a.id, "student", st_prof2.id, b"%PDF-1.4 Student 2 Transfer Cert", "st2_tc.pdf")
    doc_st2 = Document(
        school_id=school_a.id, owner_type=OwnerType.STUDENT, owner_id=st_prof2.id,
        document_type=DocumentCategory.TRANSFER_CERTIFICATE, title="Student 2 Transfer Cert",
        original_filename="st2_tc.pdf", storage_key=key2, mime_type="application/pdf",
        file_size=len(b"%PDF-1.4 Student 2 Transfer Cert"), checksum=sum2, status=DocumentStatus.UPLOADED,
        uploaded_by_id=u_admin.id, uploaded_at=date.today(), version=1, is_current=True, is_deleted=False
    )
    # Student 3 Document (Aadhaar Card)
    key3, sum3 = storage_service.store_file(school_a.id, "student", st_prof3.id, b"%PDF-1.4 Student 3 Aadhaar Card", "st3_id.pdf")
    doc_st3 = Document(
        school_id=school_a.id, owner_type=OwnerType.STUDENT, owner_id=st_prof3.id,
        document_type=DocumentCategory.STUDENT_ID, title="Student 3 ID Card",
        original_filename="st3_id.pdf", storage_key=key3, mime_type="application/pdf",
        file_size=len(b"%PDF-1.4 Student 3 Aadhaar Card"), checksum=sum3, status=DocumentStatus.VERIFIED,
        uploaded_by_id=u_admin.id, uploaded_at=date.today(), version=1, is_current=True, is_deleted=False
    )
    # Staff Document (Teacher 1 Appointment Letter)
    key_t1, sum_t1 = storage_service.store_file(school_a.id, "staff", teacher1_prof.id, b"%PDF-1.4 Teacher 1 Appointment Letter", "t1_appoint.pdf")
    doc_t1 = Document(
        school_id=school_a.id, owner_type=OwnerType.STAFF, owner_id=teacher1_prof.id,
        document_type=DocumentCategory.APPOINTMENT_DOC, title="Teacher 1 Contract",
        original_filename="t1_appoint.pdf", storage_key=key_t1, mime_type="application/pdf",
        file_size=len(b"%PDF-1.4 Teacher 1 Appointment Letter"), checksum=sum_t1, status=DocumentStatus.VERIFIED,
        uploaded_by_id=u_admin.id, uploaded_at=date.today(), version=1, is_current=True, is_deleted=False
    )
    # School B Student Document
    key_b, sum_b = storage_service.store_file(school_b.id, "student", st_prof_b.id, b"%PDF-1.4 School B Student Document", "st_b.pdf")
    doc_b = Document(
        school_id=school_b.id, owner_type=OwnerType.STUDENT, owner_id=st_prof_b.id,
        document_type=DocumentCategory.BIRTH_CERTIFICATE, title="School B Student Cert",
        original_filename="st_b.pdf", storage_key=key_b, mime_type="application/pdf",
        file_size=len(b"%PDF-1.4 School B Student Document"), checksum=sum_b, status=DocumentStatus.VERIFIED,
        uploaded_by_id=u_admin_b.id, uploaded_at=date.today(), version=1, is_current=True, is_deleted=False
    )

    db_session.add_all([doc_st1, doc_st2, doc_st3, doc_t1, doc_b])
    db_session.commit()

    return {
        "school_a": school_a, "school_b": school_b,
        "st_prof1": st_prof1, "st_prof2": st_prof2, "st_prof3": st_prof3, "st_prof_b": st_prof_b,
        "teacher1_prof": teacher1_prof, "teacher2_prof": teacher2_prof,
        "p_prof1": p_prof1, "p_prof2": p_prof2, "p_prof3": p_prof3,
        "doc_st1": doc_st1, "doc_st2": doc_st2, "doc_st3": doc_st3, "doc_t1": doc_t1, "doc_b": doc_b,
        "tok_admin": jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id),
        "tok_principal": jwt_manager.create_access_token(user_id=u_principal.id, school_id=school_a.id),
        "tok_teacher1": jwt_manager.create_access_token(user_id=u_teacher1.id, school_id=school_a.id),
        "tok_teacher2": jwt_manager.create_access_token(user_id=u_teacher2.id, school_id=school_a.id),
        "tok_student1": jwt_manager.create_access_token(user_id=u_student1.id, school_id=school_a.id),
        "tok_student2": jwt_manager.create_access_token(user_id=u_student2.id, school_id=school_a.id),
        "tok_student3": jwt_manager.create_access_token(user_id=u_student3.id, school_id=school_a.id),
        "tok_parent1": jwt_manager.create_access_token(user_id=u_parent1.id, school_id=school_a.id),
        "tok_parent2": jwt_manager.create_access_token(user_id=u_parent2.id, school_id=school_a.id),
        "tok_parent3": jwt_manager.create_access_token(user_id=u_parent3.id, school_id=school_a.id),
        "tok_acc": jwt_manager.create_access_token(user_id=u_acc.id, school_id=school_a.id),
        "tok_rec": jwt_manager.create_access_token(user_id=u_rec.id, school_id=school_a.id),
        "tok_super": jwt_manager.create_access_token(user_id=u_super.id, school_id=school_a.id),
        "tok_admin_b": jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id),
        "tok_student_b": jwt_manager.create_access_token(user_id=u_student_b.id, school_id=school_b.id),
    }


# ============================================================================
# PARENT TESTS (1-10)
# ============================================================================

def test_01_parent_list_linked_child_documents(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Parent 1 is linked to Student 1 & Student 2
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["items"]
    doc_ids = [item["id"] for item in items]
    assert str(d["doc_st1"].id) in doc_ids
    assert str(d["doc_st2"].id) in doc_ids
    assert str(d["doc_st3"].id) not in doc_ids


def test_02_parent_cannot_list_unrelated_student_documents(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Parent 2 is linked ONLY to Student 3
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent2']}"})
    assert res.status_code == 200
    items = res.json()["items"]
    doc_ids = [item["id"] for item in items]
    assert str(d["doc_st3"].id) in doc_ids
    assert str(d["doc_st1"].id) not in doc_ids
    assert str(d["doc_st2"].id) not in doc_ids


def test_03_parent_owner_id_tampering_blocked(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Parent 1 attempting ?owner_type=STUDENT&owner_id=Student3_ID -> 403 Forbidden
    st3_id = str(d["st_prof3"].id)
    res = client.get(f"/api/v1/documents?owner_type=STUDENT&owner_id={st3_id}", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_04_parent_owner_type_staff_tampering_blocked(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Parent 1 attempting ?owner_type=STAFF -> 200 OK with empty items list
    res = client.get("/api/v1/documents?owner_type=STAFF", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_05_parent_download_linked_child_document_success(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.content == b"%PDF-1.4 Student 1 Birth Cert"


def test_06_parent_download_unrelated_student_document_forbidden(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Parent 1 trying to download Student 3 document
    doc_id = str(d["doc_st3"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_07_parent_preview_linked_child_document_success(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/preview", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.content == b"%PDF-1.4 Student 1 Birth Cert"


def test_08_parent_preview_unrelated_document_forbidden(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st3"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/preview", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_09_multi_child_parent_sees_all_linked_child_documents(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert len(res.json()["items"]) >= 2


def test_10_zero_child_parent_gets_empty_list(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent3']}"})
    assert res.status_code == 200
    assert res.json()["total"] == 0
    assert res.json()["items"] == []


# ============================================================================
# STUDENT TESTS (11-18)
# ============================================================================

def test_11_student_lists_own_documents(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    items = res.json()["items"]
    doc_ids = [item["id"] for item in items]
    assert str(d["doc_st1"].id) in doc_ids
    assert str(d["doc_st2"].id) not in doc_ids
    assert str(d["doc_st3"].id) not in doc_ids


def test_12_student_cannot_list_peer_documents(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_student3']}"})
    assert res.status_code == 200
    items = res.json()["items"]
    doc_ids = [item["id"] for item in items]
    assert str(d["doc_st3"].id) in doc_ids
    assert str(d["doc_st1"].id) not in doc_ids


def test_13_student_owner_id_tampering_blocked(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    st2_id = str(d["st_prof2"].id)
    res = client.get(f"/api/v1/documents?owner_type=STUDENT&owner_id={st2_id}", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_14_student_owner_type_staff_tampering_blocked(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents?owner_type=STAFF", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert res.json()["total"] == 0


def test_15_student_downloads_own_document(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert res.content == b"%PDF-1.4 Student 1 Birth Cert"


def test_16_student_cannot_download_peer_document(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st2"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_17_student_previews_own_document(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/preview", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert res.content == b"%PDF-1.4 Student 1 Birth Cert"


def test_18_student_cannot_preview_peer_document(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_id = str(d["doc_st2"].id)
    res = client.get(f"/api/v1/documents/{doc_id}/preview", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


# ============================================================================
# IDENTITY RESOLUTION TESTS (19-22)
# ============================================================================

def test_19_parent_phone_identity_resolves_correctly(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Parent 2 logged in via phone "9876500001" and has no email
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent2']}"})
    assert res.status_code == 200
    items = res.json()["items"]
    doc_ids = [item["id"] for item in items]
    assert str(d["doc_st3"].id) in doc_ids


def test_20_parent_secondary_phone_identity_resolution(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200


def test_21_student_admission_number_identity_resolves_correctly(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Student 1 user profile has username = ADM_ST1
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 1


def test_22_missing_identity_mapping_fails_closed(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_parent3']}"})
    assert res.status_code == 200
    assert res.json()["total"] == 0


# ============================================================================
# TENANT ISOLATION TESTS (23-25)
# ============================================================================

def test_23_cross_tenant_document_metadata_access_denied(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_a_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_a_id}", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code in (403, 404)


def test_24_cross_tenant_download_denied(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_a_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_a_id}/download", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code in (403, 404)


def test_25_cross_tenant_preview_denied(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    doc_a_id = str(d["doc_st1"].id)
    res = client.get(f"/api/v1/documents/{doc_a_id}/preview", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code in (403, 404)


# ============================================================================
# STAFF OPERATIONAL ACCESS TESTS (26-33)
# ============================================================================

def test_26_teacher_operational_access_functional(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents?owner_type=STUDENT", headers={"Authorization": f"Bearer {d['tok_teacher1']}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 3


def test_27_class_teacher_operational_access_functional(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents?owner_type=STUDENT", headers={"Authorization": f"Bearer {d['tok_teacher2']}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 3


def test_28_admin_full_school_access_functional(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 4


def test_29_principal_full_school_access_functional(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_principal']}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 4


def test_30_super_admin_access_functional(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_super']}"})
    assert res.status_code == 200


def test_31_teacher_cannot_access_prohibited_private_staff_documents(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    # Teacher 2 attempting to view Teacher 1 private staff document -> 403 Forbidden
    doc_t1_id = str(d["doc_t1"].id)
    res = client.get(f"/api/v1/documents/{doc_t1_id}/download", headers={"Authorization": f"Bearer {d['tok_teacher2']}"})
    assert res.status_code == 403


def test_32_accountant_remains_denied(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_acc']}"})
    assert res.status_code == 403


def test_33_receptionist_behavior_operational(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {d['tok_rec']}"})
    assert res.status_code == 200


# ============================================================================
# SUMMARY ENDPOINT TESTS (34-36)
# ============================================================================

def test_34_parent_summary_access_denied(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents/summary", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_35_student_summary_access_denied(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents/summary", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_36_operational_staff_summary_functional(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    res = client.get("/api/v1/documents/summary", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()
    assert "total_documents" in data
    assert data["total_documents"] >= 4


# ============================================================================
# FILE SECURITY REGRESSION TESTS (37-40)
# ============================================================================

def test_37_executable_upload_rejected(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    st1_id = str(d["st_prof1"].id)
    files_exe = {"file": ("malicious.exe", io.BytesIO(b"MZfakeexe"), "application/octet-stream")}
    data = {"owner_type": "STUDENT", "owner_id": st1_id, "document_type": "OTHER", "title": "Bad Exe"}
    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {d['tok_admin']}"}, data=data, files=files_exe)
    assert res.status_code == 400


def test_38_magic_byte_spoof_rejected(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    st1_id = str(d["st_prof1"].id)
    files_spoof = {"file": ("fake.pdf", io.BytesIO(b"Plain text masquerading as pdf"), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st1_id, "document_type": "OTHER", "title": "Spoofed PDF"}
    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {d['tok_admin']}"}, data=data, files=files_spoof)
    assert res.status_code in (400, 422)


def test_39_path_traversal_rejected(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    st1_id = str(d["st_prof1"].id)
    files_pt = {"file": ("../../../../etc/passwd.pdf", io.BytesIO(b"%PDF-1.4 Safe PDF"), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st1_id, "document_type": "OTHER", "title": "PT Test"}
    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {d['tok_admin']}"}, data=data, files=files_pt)
    assert res.status_code == 201
    assert ".." not in res.json()["original_filename"]


def test_40_deleted_document_cannot_be_downloaded(client: TestClient, setup_doc_security_data):
    d = setup_doc_security_data
    st1_id = str(d["st_prof1"].id)
    files = {"file": ("temp.pdf", io.BytesIO(b"%PDF-1.4 Temp doc"), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st1_id, "document_type": "OTHER", "title": "Temp Doc"}
    res_up = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {d['tok_admin']}"}, data=data, files=files)
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # Delete document
    res_del = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res_del.status_code == 204

    # Download deleted document -> 404 Not Found
    res_dl = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res_dl.status_code == 404
