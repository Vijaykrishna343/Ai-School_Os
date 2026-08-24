import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import StudentStatus, Gender, AcademicYearStatus, TransferCertificateStatus
from app.main import app
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher, TeacherStatus
from app.models.student.student_certificate import StudentCertificate, CertificateType
from app.models.student.transfer_certificate import TransferCertificate
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.permission import IdentityPermission
from app.identity.models.user_role import IdentityUserRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_cert_security_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # Schools A and B
    school_a = School(
        name=f"Cert School A {s}", code=f"CSA_{s}",
        address_line1="123 Campus St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    school_b = School(
        name=f"Cert School B {s}", code=f"CSB_{s}",
        address_line1="456 Campus St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(school_id=school_a.id, name=f"2026-2027_{s}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    ay_b = AcademicYear(school_id=school_b.id, name=f"2026-2027_{s}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    class_10a = SchoolClass(school_id=school_a.id, name=f"10_{s}", display_order=1)
    class_10b = SchoolClass(school_id=school_b.id, name=f"10_{s}", display_order=1)
    db_session.add_all([class_10a, class_10b])
    db_session.commit()

    sec_10a = Section(school_class_id=class_10a.id, name="A")
    sec_10b = Section(school_class_id=class_10b.id, name="A")
    db_session.add_all([sec_10a, sec_10b])
    db_session.commit()

    # Roles
    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_principal = db_session.query(IdentityRole).filter_by(name="Principal").first()
    r_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_super = db_session.query(IdentityRole).filter_by(name="Super Admin").first()

    pwd = hash_password("Password@123")

    # Users
    u_admin = IdentityUser(email=f"admin_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin", last_name="A")
    u_principal = IdentityUser(email=f"principal_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Principal", last_name="A")
    u_teacher = IdentityUser(email=f"teacher_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Teacher", last_name="A")

    # Student 1: Email = student1_sec...
    u_student1 = IdentityUser(email=f"student1_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="One")
    # Student 2: Email = student2_sec...
    u_student2 = IdentityUser(email=f"student2_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="Two")
    # Student 3: Username = ADM_ST3...
    u_student3 = IdentityUser(username=f"ADM_ST3_{s}", email=f"student3_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Student", last_name="Three")

    # Parent 1: Linked to Student 1 and Student 2 (Email match)
    u_parent1 = IdentityUser(email=f"parent1_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="One")
    # Parent 2: Linked to Student 3 (Phone match)
    u_parent2 = IdentityUser(email=f"parent2_sec_{s}@school.com", phone="9876500001", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="Two")
    # Parent 3: Zero children
    u_parent3 = IdentityUser(email=f"parent3_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent", last_name="Three")

    u_super = IdentityUser(email=f"super_sec_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Super", last_name="Admin")
    u_admin_b = IdentityUser(email=f"admin_sec_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Admin", last_name="B")

    db_session.add_all([
        u_admin, u_principal, u_teacher,
        u_student1, u_student2, u_student3,
        u_parent1, u_parent2, u_parent3,
        u_super, u_admin_b
    ])
    db_session.commit()

    p_tc_view = db_session.query(IdentityPermission).filter_by(name="student.tc.view").first()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_principal.id, role_id=r_principal.id),
        IdentityUserRole(user_id=u_teacher.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_student1.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_student2.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_student3.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_parent1.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_parent2.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_parent3.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_super.id, role_id=r_super.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=r_admin.id),
    ])
    if p_tc_view:
        db_session.add_all([
            IdentityRolePermission(role_id=r_parent.id, permission_id=p_tc_view.id),
            IdentityRolePermission(role_id=r_student.id, permission_id=p_tc_view.id),
        ])
    db_session.commit()

    # Profiles
    p_prof1 = Parent(school_id=school_a.id, father_name="Parent One", email=u_parent1.email, primary_phone="9990001111", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    p_prof2 = Parent(school_id=school_a.id, father_name="Parent Two", primary_phone="9876500001", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    p_prof3 = Parent(school_id=school_a.id, father_name="Parent Three", email=u_parent3.email, primary_phone="9990003333", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    db_session.add_all([p_prof1, p_prof2, p_prof3])
    db_session.commit()

    st_prof1 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=class_10a.id, section_id=sec_10a.id,
        parent_id=p_prof1.id, admission_number=f"ADM_ST1_{s}", roll_number="1", first_name="Student", last_name="One",
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1),
        email=u_student1.email, status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof2 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=class_10a.id, section_id=sec_10a.id,
        parent_id=p_prof1.id, admission_number=f"ADM_ST2_{s}", roll_number="2", first_name="Student", last_name="Two",
        gender=Gender.FEMALE, date_of_birth=date(2011, 1, 1), admission_date=date(2026, 6, 1),
        email=u_student2.email, status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    st_prof3 = Student(
        school_id=school_a.id, academic_year_id=ay_a.id, school_class_id=class_10a.id, section_id=sec_10a.id,
        parent_id=p_prof2.id, admission_number=f"ADM_ST3_{s}", roll_number="3", first_name="Student", last_name="Three",
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1),
        email=u_student3.email, status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001"
    )
    db_session.add_all([st_prof1, st_prof2, st_prof3])
    db_session.commit()

    # Certificates
    cert_st1_bc = StudentCertificate(
        school_id=school_a.id, student_id=st_prof1.id, issued_by_id=u_admin.id,
        certificate_type=CertificateType.BONAFIDE, certificate_number=f"BC-{s}-0001",
        issued_date=date(2026, 7, 1), purpose="Passport Application", conduct="Good"
    )
    cert_st2_tc = StudentCertificate(
        school_id=school_a.id, student_id=st_prof2.id, issued_by_id=u_admin.id,
        certificate_type=CertificateType.TRANSFER_CERTIFICATE, certificate_number=f"TC-{s}-0001",
        issued_date=date(2026, 7, 2), reason_for_leaving="Relocation", conduct="Exemplary"
    )
    cert_st3_bc = StudentCertificate(
        school_id=school_a.id, student_id=st_prof3.id, issued_by_id=u_admin.id,
        certificate_type=CertificateType.BONAFIDE, certificate_number=f"BC-{s}-0002",
        issued_date=date(2026, 7, 3), purpose="Bank Account", conduct="Good"
    )
    db_session.add_all([cert_st1_bc, cert_st2_tc, cert_st3_bc])
    db_session.commit()

    # TransferCertificate (Promotion Service table)
    tc_st2 = TransferCertificate(
        school_id=school_a.id, student_id=st_prof2.id, academic_year_id=ay_a.id,
        tc_number=f"TC-PROM-{s}-001", issue_date=date(2026, 7, 2), leaving_date=date(2026, 7, 2),
        reason="Family Transfer", status=TransferCertificateStatus.ISSUED
    )
    db_session.add(tc_st2)
    db_session.commit()

    # Tokens
    tok_admin = jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id)
    tok_parent1 = jwt_manager.create_access_token(user_id=u_parent1.id, school_id=school_a.id)
    tok_parent2 = jwt_manager.create_access_token(user_id=u_parent2.id, school_id=school_a.id)
    tok_parent3 = jwt_manager.create_access_token(user_id=u_parent3.id, school_id=school_a.id)
    tok_student1 = jwt_manager.create_access_token(user_id=u_student1.id, school_id=school_a.id)
    tok_student2 = jwt_manager.create_access_token(user_id=u_student2.id, school_id=school_a.id)
    tok_student3 = jwt_manager.create_access_token(user_id=u_student3.id, school_id=school_a.id)
    tok_super = jwt_manager.create_access_token(user_id=u_super.id, school_id=school_a.id)
    tok_admin_b = jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b,
        "st_prof1": st_prof1, "st_prof2": st_prof2, "st_prof3": st_prof3,
        "cert_st1_bc": cert_st1_bc, "cert_st2_tc": cert_st2_tc, "cert_st3_bc": cert_st3_bc,
        "tc_st2": tc_st2,
        "tok_admin": tok_admin, "tok_parent1": tok_parent1, "tok_parent2": tok_parent2, "tok_parent3": tok_parent3,
        "tok_student1": tok_student1, "tok_student2": tok_student2, "tok_student3": tok_student3,
        "tok_super": tok_super, "tok_admin_b": tok_admin_b,
    }


# ============================================================================
# 1-9: Parent Relationship Security Tests
# ============================================================================

def test_01_parent_list_linked_child_certificates(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Parent 1 (linked to Student 1 & Student 2)
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    student_ids = {item["student_id"] for item in items}
    assert len(items) == 2
    assert str(d["st_prof1"].id) in student_ids
    assert str(d["st_prof2"].id) in student_ids
    assert str(d["st_prof3"].id) not in student_ids


def test_02_parent_cannot_list_unrelated_student_certificates(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Parent 1 attempting ?student_id=Student 3 -> 403 Forbidden
    res = client.get(f"/api/v1/certificates?student_id={d['st_prof3'].id}", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_03_parent_student_id_tampering_blocked(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates?student_id={d['st_prof3'].id}", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_04_parent_certificate_detail_linked_child_allowed(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Parent 1 accessing Student 1's Bonafide Cert
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["id"] == str(d["cert_st1_bc"].id)


def test_05_parent_certificate_detail_unrelated_child_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Parent 1 accessing Student 3's Cert -> 403 Forbidden
    res = client.get(f"/api/v1/certificates/{d['cert_st3_bc'].id}", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_06_parent_certificate_print_linked_child_allowed(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}/print", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "BONAFIDE CERTIFICATE" in res.text


def test_07_parent_certificate_print_unrelated_child_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st3_bc'].id}/print", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_08_multi_child_parent_sees_all_linked_child_certificates(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 2


def test_09_zero_child_parent_gets_empty_list(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_parent3']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 0
    assert res.json()["data"]["items"] == []


# ============================================================================
# 10-16: Student Self Security Tests
# ============================================================================

def test_10_student_lists_own_certificates(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == str(d["st_prof1"].id)


def test_11_student_cannot_list_peer_certificates(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates?student_id={d['st_prof2'].id}", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_12_student_student_id_tampering_blocked(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates?student_id={d['st_prof2'].id}", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_13_student_own_certificate_detail_allowed(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["id"] == str(d["cert_st1_bc"].id)


def test_14_student_peer_certificate_detail_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st2_tc'].id}", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_15_student_own_certificate_print_allowed(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}/print", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]


def test_16_student_peer_certificate_print_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st2_tc'].id}/print", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


# ============================================================================
# 17-20: Transfer Certificate History Security Tests
# ============================================================================

def test_17_parent_linked_child_transfer_history_allowed(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/students/{d['st_prof2'].id}/transfer-certificates", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 1


def test_18_parent_unrelated_transfer_history_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/students/{d['st_prof3'].id}/transfer-certificates", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_19_student_self_transfer_history_allowed(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/students/{d['st_prof2'].id}/transfer-certificates", headers={"Authorization": f"Bearer {d['tok_student2']}"})
    assert res.status_code == 200


def test_20_student_peer_transfer_history_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/students/{d['st_prof2'].id}/transfer-certificates", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


# ============================================================================
# 21-23: Cross-Tenant Isolation Security Tests
# ============================================================================

def test_21_cross_tenant_certificate_detail_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code == 404


def test_22_cross_tenant_certificate_print_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}/print", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code == 404


def test_23_cross_tenant_transfer_history_denied(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/students/{d['st_prof1'].id}/transfer-certificates", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res.status_code in (403, 404, 422)


# ============================================================================
# 24-27: Certificate Creation Security Tests
# ============================================================================

def test_24_parent_cannot_issue_tc(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    payload = {"reason_for_leaving": "Test", "conduct": "Good"}
    res = client.post(f"/api/v1/students/{d['st_prof1'].id}/certificates/tc", json=payload, headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_25_student_cannot_issue_tc(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    payload = {"reason_for_leaving": "Test", "conduct": "Good"}
    res = client.post(f"/api/v1/students/{d['st_prof1'].id}/certificates/tc", json=payload, headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


def test_26_parent_cannot_issue_bonafide(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    payload = {"purpose": "Test", "conduct": "Good"}
    res = client.post(f"/api/v1/students/{d['st_prof1'].id}/certificates/bonafide", json=payload, headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 403


def test_27_student_cannot_issue_bonafide(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    payload = {"purpose": "Test", "conduct": "Good"}
    res = client.post(f"/api/v1/students/{d['st_prof1'].id}/certificates/bonafide", json=payload, headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 403


# ============================================================================
# 28-30: Operational Staff & Admin Access Tests
# ============================================================================

def test_28_staff_certificate_creation_remains_functional(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    payload = {"purpose": "Higher Studies Verification", "conduct": "Exemplary"}
    res = client.post(f"/api/v1/students/{d['st_prof1'].id}/certificates/bonafide", json=payload, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 201
    assert res.json()["data"]["purpose"] == "Higher Studies Verification"


def test_29_staff_certificate_listing_remains_functional(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] >= 3


def test_30_super_admin_access_functional(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}", headers={"Authorization": f"Bearer {d['tok_super']}"})
    assert res.status_code == 200


# ============================================================================
# 31-35: Print Headers, Deletion & Filter Scope Tests
# ============================================================================

def test_31_certificate_print_security_headers_present(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}/print", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert "default-src 'none'" in res.headers.get("content-security-policy", "")


def test_32_deleted_certificate_cannot_be_accessed(client: TestClient, setup_cert_security_data, db_session: Session):
    d = setup_cert_security_data
    # Soft delete cert_st1_bc
    cert = db_session.get(StudentCertificate, d["cert_st1_bc"].id)
    cert.is_deleted = True
    db_session.commit()

    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}", headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 404


def test_33_certificate_type_filter_cannot_escape_scope(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Parent 1 filtering by type=BONAFIDE -> sees only Student 1's Bonafide
    res = client.get("/api/v1/certificates?type=BONAFIDE", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for item in items:
        assert item["student_id"] in (str(d["st_prof1"].id), str(d["st_prof2"].id))


def test_34_pagination_cannot_escape_scope(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get("/api/v1/certificates?page=1&page_size=10", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    assert res.json()["data"]["total"] == 2


def test_35_multi_child_parent_sees_only_linked_children_not_unrelated(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_parent1']}"})
    assert res.status_code == 200
    ids = [item["student_id"] for item in res.json()["data"]["items"]]
    assert str(d["st_prof3"].id) not in ids


# ============================================================================
# 36-40: Identity Resolution & Advanced Security Tests
# ============================================================================

def test_36_identity_resolution_using_parent_phone(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Parent 2 (phone match to Student 3)
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_parent2']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == str(d["st_prof3"].id)


def test_37_identity_resolution_using_secondary_parent_phone(client: TestClient, setup_cert_security_data, db_session: Session):
    d = setup_cert_security_data
    # Set secondary phone on Parent 3 to "9998887777" and link to Student 3
    p3 = db_session.get(Parent, d["st_prof3"].parent_id)
    p3.secondary_phone = "9998887777"
    db_session.commit()

    u_p_sec = IdentityUser(email=f"p_sec_{uuid.uuid4().hex[:6]}@school.com", phone="9998887777", password_hash=hash_password("Pass123!"), school_id=d["school_a"].id, first_name="P", last_name="Sec")
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    db_session.add(u_p_sec)
    db_session.commit()
    db_session.add(IdentityUserRole(user_id=u_p_sec.id, role_id=r_parent.id))
    db_session.commit()

    tok = jwt_manager.create_access_token(user_id=u_p_sec.id, school_id=d["school_a"].id)
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 200
    assert len(res.json()["data"]["items"]) == 1


def test_38_student_admission_number_identity_resolution(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Student 3 uses username = ADM_ST3
    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {d['tok_student3']}"})
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == str(d["st_prof3"].id)


def test_39_unknown_unsupported_role_fails_closed(client: TestClient, setup_cert_security_data, db_session: Session):
    d = setup_cert_security_data
    # User with no roles
    u_no_role = IdentityUser(email=f"norole_{uuid.uuid4().hex[:6]}@school.com", password_hash=hash_password("Pass123!"), school_id=d["school_a"].id, first_name="No", last_name="Role")
    db_session.add(u_no_role)
    db_session.commit()
    tok = jwt_manager.create_access_token(user_id=u_no_role.id, school_id=d["school_a"].id)

    res = client.get("/api/v1/certificates", headers={"Authorization": f"Bearer {tok}"})
    assert res.status_code == 403


def test_40_certificate_print_does_not_expose_unauthorized_student_data(client: TestClient, setup_cert_security_data):
    d = setup_cert_security_data
    # Student 1 requesting print for own cert
    res = client.get(f"/api/v1/certificates/{d['cert_st1_bc'].id}/print", headers={"Authorization": f"Bearer {d['tok_student1']}"})
    assert res.status_code == 200
    assert "Student One" in res.text
    assert "Student Three" not in res.text
