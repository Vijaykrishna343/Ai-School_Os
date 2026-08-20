"""
Integration tests for Phase 24 — Secure Student & Staff Document Management.
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


@pytest.fixture
def setup_document_data(db_session: Session):
    role_seeder.seed(db_session)
    permission_seeder.seed(db_session)
    role_permission_seeder.seed(db_session)

    suffix = uuid.uuid4().hex[:6]

    # Create School A & B
    school_a = School(
        name=f"Doc School A {suffix}",
        code=f"DSA_{suffix}",
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    school_b = School(
        name=f"Doc School B {suffix}",
        code=f"DSB_{suffix}",
        address_line1="456 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(
        school_id=school_a.id,
        name=f"2026-2027_{suffix}",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    ay_b = AcademicYear(
        school_id=school_b.id,
        name=f"2026-2027_{suffix}",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    class_a = SchoolClass(school_id=school_a.id, name=f"Class 10_{suffix}", display_order=1)
    class_b = SchoolClass(school_id=school_b.id, name=f"Class 10_{suffix}", display_order=1)
    db_session.add_all([class_a, class_b])
    db_session.commit()

    sec_a = Section(school_class_id=class_a.id, name="A")
    sec_b = Section(school_class_id=class_b.id, name="A")
    db_session.add_all([sec_a, sec_b])
    db_session.commit()

    # Roles
    role_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    role_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    role_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    role_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    role_acc = db_session.query(IdentityRole).filter_by(name="Accountant").first()

    pwd = hash_password("Password@123")

    # Users
    u_admin_a = IdentityUser(email=f"admin_doc_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin", last_name="A")
    u_teacher_a = IdentityUser(email=f"teacher_doc_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Alice", last_name="Teacher")
    u_student_a = IdentityUser(email=f"student_doc_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Charlie", last_name="Student")
    u_parent_a = IdentityUser(email=f"parent_doc_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Papa", last_name="A")
    u_acc_a = IdentityUser(email=f"acc_doc_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Acc", last_name="A")

    u_admin_b = IdentityUser(email=f"admin_doc_b_{suffix}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Admin", last_name="B")
    u_student_b = IdentityUser(email=f"student_doc_b_{suffix}@school.com", password_hash=pwd, school_id=school_b.id, first_name="David", last_name="Student")

    db_session.add_all([u_admin_a, u_teacher_a, u_student_a, u_parent_a, u_acc_a, u_admin_b, u_student_b])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin_a.id, role_id=role_admin.id),
        IdentityUserRole(user_id=u_teacher_a.id, role_id=role_teacher.id),
        IdentityUserRole(user_id=u_student_a.id, role_id=role_student.id),
        IdentityUserRole(user_id=u_parent_a.id, role_id=role_parent.id),
        IdentityUserRole(user_id=u_acc_a.id, role_id=role_acc.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=role_admin.id),
        IdentityUserRole(user_id=u_student_b.id, role_id=role_student.id),
    ])
    db_session.commit()

    # Teacher & Parent Profiles
    t_a = Teacher(
        school_id=school_a.id, employee_id=f"EMP_{suffix}",
        first_name="Alice", last_name="Teacher", email=u_teacher_a.email, phone="9998887771",
        gender=Gender.FEMALE, date_of_birth=date(1990, 1, 1), joining_date=date(2020, 6, 1), status=TeacherStatus.ACTIVE,
        qualification="M.Sc Math", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    p_a = Parent(
        school_id=school_a.id, father_name="Papa", mother_name="Mama",
        email=u_parent_a.email, primary_phone="9876543210", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    db_session.add_all([t_a, p_a])
    db_session.commit()

    # Students
    st_a = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, parent_id=p_a.id,
        school_class_id=class_a.id, section_id=sec_a.id, admission_number=f"ADM_{suffix}",
        roll_number="1", first_name="Charlie", last_name="Student", email=u_student_a.email,
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
        address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    st_b = Student(
        school_id=school_b.id, academic_year_id=ay_b.id,
        school_class_id=class_b.id, section_id=sec_b.id, admission_number=f"ADM_B_{suffix}",
        roll_number="1", first_name="David", last_name="Student", email=u_student_b.email,
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
        address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    db_session.add_all([st_a, st_b])
    db_session.commit()

    # Tokens
    tok_admin_a = jwt_manager.create_access_token(user_id=u_admin_a.id, school_id=school_a.id)
    tok_teacher_a = jwt_manager.create_access_token(user_id=u_teacher_a.id, school_id=school_a.id)
    tok_student_a = jwt_manager.create_access_token(user_id=u_student_a.id, school_id=school_a.id)
    tok_parent_a = jwt_manager.create_access_token(user_id=u_parent_a.id, school_id=school_a.id)
    tok_acc_a = jwt_manager.create_access_token(user_id=u_acc_a.id, school_id=school_a.id)
    tok_admin_b = jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b,
        "st_a": st_a, "st_b": st_b, "t_a": t_a, "p_a": p_a,
        "tok_admin_a": tok_admin_a, "tok_teacher_a": tok_teacher_a,
        "tok_student_a": tok_student_a, "tok_parent_a": tok_parent_a,
        "tok_acc_a": tok_acc_a, "tok_admin_b": tok_admin_b,
    }


def test_01_document_upload_download_preview_lifecycle(client: TestClient, setup_document_data):
    d = setup_document_data
    tok = d["tok_admin_a"]
    st_id = str(d["st_a"].id)

    # Valid PDF file content (starts with magic bytes %PDF-)
    pdf_bytes = b"%PDF-1.4 Fake PDF document contents for testing document vault upload."
    files = {"file": ("birth_certificate.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {
        "owner_type": "STUDENT",
        "owner_id": st_id,
        "document_type": "BIRTH_CERTIFICATE",
        "title": "Charlie Birth Certificate",
    }

    # Upload PDF
    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok}"}, data=data, files=files)
    assert res.status_code == 201, res.text
    doc_json = res.json()
    doc_id = doc_json["id"]
    assert doc_json["title"] == "Charlie Birth Certificate"
    assert doc_json["status"] == "UPLOADED"
    assert doc_json["checksum"] is not None
    assert doc_json["version"] == 1

    # List documents
    res = client.get(f"/api/v1/documents?owner_type=STUDENT&owner_id={st_id}", headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 200
    assert res.json()["total"] >= 1

    # Authenticated Download
    res_dl = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tok}"})
    assert res_dl.status_code == 200
    assert "attachment" in res_dl.headers.get("Content-Disposition", "")
    assert res_dl.headers.get("X-Content-Type-Options") == "nosniff"
    assert res_dl.content == pdf_bytes

    # Authenticated Preview
    res_prev = client.get(f"/api/v1/documents/{doc_id}/preview", headers={"Authorization": f"Bearer {tok}"})
    assert res_prev.status_code == 200
    assert "inline" in res_prev.headers.get("Content-Disposition", "")
    assert res_prev.headers.get("X-Content-Type-Options") == "nosniff"
    assert res_prev.content == pdf_bytes


def test_02_file_validation_and_security(client: TestClient, setup_document_data):
    d = setup_document_data
    tok = d["tok_admin_a"]
    st_id = str(d["st_a"].id)

    # 1. Executable file extension rejection (.exe)
    files_exe = {"file": ("malicious.exe", io.BytesIO(b"MZfakeexe"), "application/octet-stream")}
    data = {"owner_type": "STUDENT", "owner_id": st_id, "document_type": "OTHER", "title": "Bad File"}
    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok}"}, data=data, files=files_exe)
    assert res.status_code == 400
    assert "extension" in res.json()["detail"].lower()

    # 2. Magic bytes validation failure (text file renamed to .pdf)
    files_spoof = {"file": ("fake.pdf", io.BytesIO(b"Hello world text content"), "application/pdf")}
    res_spoof = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok}"}, data=data, files=files_spoof)
    assert res_spoof.status_code == 400 or res_spoof.status_code == 422

    # 3. Path traversal filename sanitization
    pdf_bytes = b"%PDF-1.4 Safe PDF content"
    files_pt = {"file": ("../../../../etc/passwd.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    res_pt = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok}"}, data=data, files=files_pt)
    assert res_pt.status_code == 201
    assert "passwd" in res_pt.json()["original_filename"]
    assert ".." not in res_pt.json()["original_filename"]


def test_03_rbac_and_accountant_denial(client: TestClient, setup_document_data):
    d = setup_document_data
    tok_acc = d["tok_acc_a"]
    st_id = str(d["st_a"].id)

    # Accountant role attempting to list documents -> 403 Forbidden
    res = client.get("/api/v1/documents", headers={"Authorization": f"Bearer {tok_acc}"})
    assert res.status_code == 403

    # Accountant role attempting to upload -> 403 Forbidden
    pdf_bytes = b"%PDF-1.4 Fake PDF"
    files = {"file": ("doc.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st_id, "document_type": "OTHER", "title": "Acc Upload"}
    res_up = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok_acc}"}, data=data, files=files)
    assert res_up.status_code == 403


def test_04_parent_child_relationship_authorization(client: TestClient, setup_document_data):
    d = setup_document_data
    tok_admin = d["tok_admin_a"]
    tok_parent_a = d["tok_parent_a"]
    st_a_id = str(d["st_a"].id)
    st_b_id = str(d["st_b"].id)

    # Admin uploads document for Student A
    pdf_bytes = b"%PDF-1.4 Child A document"
    files = {"file": ("child_a_cert.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st_a_id, "document_type": "BIRTH_CERTIFICATE", "title": "Child A Cert"}
    res_up = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok_admin}"}, data=data, files=files)
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # Parent A downloads Child A document -> 200 OK
    res_dl = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tok_parent_a}"})
    assert res_dl.status_code == 200

    # Parent A attempting to upload document for unrelated Student B -> 403 Forbidden
    data_unrelated = {"owner_type": "STUDENT", "owner_id": st_b_id, "document_type": "OTHER", "title": "Unrelated Upload"}
    res_unrel = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok_parent_a}"}, data=data_unrelated, files=files)
    assert res_unrel.status_code == 403


def test_05_tenant_isolation(client: TestClient, setup_document_data):
    d = setup_document_data
    tok_admin_a = d["tok_admin_a"]
    tok_admin_b = d["tok_admin_b"]
    st_a_id = str(d["st_a"].id)

    # Admin School A uploads document
    pdf_bytes = b"%PDF-1.4 School A doc"
    files = {"file": ("school_a.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st_a_id, "document_type": "STUDENT_ID", "title": "School A ID"}
    res_up = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok_admin_a}"}, data=data, files=files)
    assert res_up.status_code == 201
    doc_id = res_up.json()["id"]

    # Admin School B attempts to get / download School A document -> 404 or 403
    res_b_get = client.get(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {tok_admin_b}"})
    assert res_b_get.status_code in (403, 404)

    res_b_dl = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tok_admin_b}"})
    assert res_b_dl.status_code in (403, 404)


def test_06_verification_rejection_and_versioning(client: TestClient, setup_document_data):
    d = setup_document_data
    tok = d["tok_admin_a"]
    st_id = str(d["st_a"].id)

    pdf_bytes_v1 = b"%PDF-1.4 Original Version 1 document content"
    files_v1 = {"file": ("v1.pdf", io.BytesIO(pdf_bytes_v1), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st_id, "document_type": "ADMISSION_DOC", "title": "Admission Form"}

    # Upload v1
    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok}"}, data=data, files=files_v1)
    assert res.status_code == 201
    doc_v1 = res.json()
    doc_id = doc_v1["id"]

    # Verify document
    res_vf = client.post(f"/api/v1/documents/{doc_id}/verify", headers={"Authorization": f"Bearer {tok}"})
    assert res_vf.status_code == 200
    assert res_vf.json()["status"] == "VERIFIED"

    # Reject document
    res_rj = client.post(f"/api/v1/documents/{doc_id}/reject", headers={"Authorization": f"Bearer {tok}"}, json={"rejection_reason": "Blurry copy provided."})
    assert res_rj.status_code == 200
    assert res_rj.json()["status"] == "REJECTED"
    assert res_rj.json()["rejection_reason"] == "Blurry copy provided."

    # Replace document (Version 2)
    pdf_bytes_v2 = b"%PDF-1.4 Replaced Version 2 document content"
    files_v2 = {"file": ("v2.pdf", io.BytesIO(pdf_bytes_v2), "application/pdf")}
    res_rp = client.post(f"/api/v1/documents/{doc_id}/replace", headers={"Authorization": f"Bearer {tok}"}, files=files_v2)
    assert res_rp.status_code == 200
    doc_v2 = res_rp.json()
    assert doc_v2["version"] == 2
    assert doc_v2["is_current"] is True


def test_07_soft_deletion(client: TestClient, setup_document_data):
    d = setup_document_data
    tok = d["tok_admin_a"]
    st_id = str(d["st_a"].id)

    pdf_bytes = b"%PDF-1.4 Soft Delete Test Document"
    files = {"file": ("delete_me.pdf", io.BytesIO(pdf_bytes), "application/pdf")}
    data = {"owner_type": "STUDENT", "owner_id": st_id, "document_type": "OTHER", "title": "Delete Me"}

    res = client.post("/api/v1/documents/upload", headers={"Authorization": f"Bearer {tok}"}, data=data, files=files)
    assert res.status_code == 201
    doc_id = res.json()["id"]

    # Delete
    res_del = client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {tok}"})
    assert res_del.status_code == 204

    # Download deleted file -> 404 Not Found
    res_dl = client.get(f"/api/v1/documents/{doc_id}/download", headers={"Authorization": f"Bearer {tok}"})
    assert res_dl.status_code == 404
