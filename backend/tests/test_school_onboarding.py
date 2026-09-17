"""
Unit & Integration Tests for School Tenant Onboarding & Provisioning Wizard — Phase 30.5
"""
import uuid
from datetime import date, timedelta
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session

from app.common.enums import AcademicYearStatus, SchoolClassStatus, SectionStatus
from app.common.enums.school import SchoolStatus
from app.identity.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import (
    identity_user_repository,
    permission_repository,
    role_repository,
    user_role_repository,
)
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password, verify_password
from app.identity.seeders import seed_identity
from app.models.academic_year.academic_year import AcademicYear
from app.models.audit_log import AuditLog
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.schemas.school_onboarding import (
    AcademicYearInput,
    AdminCredentialsInput,
    ClassTemplateItem,
    SchoolOnboardingRequest,
)
from app.services.school_onboarding_service import school_onboarding_service


def setup_super_admin(db: Session) -> tuple[IdentityUser, str]:
    """Create a test super admin and return (user, auth_header)."""
    seed_identity(db)
    school = School(
        id=uuid.uuid4(),
        name=f"Platform School {uuid.uuid4().hex[:4]}",
        code=f"PLT_{uuid.uuid4().hex[:4].upper()}",
        address_line1="1 Platform Way",
        city="City",
        district="District",
        state="State",
        country="India",
        postal_code="560001",
    )
    db.add(school)
    db.commit()

    super_admin = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"superadmin_{uuid.uuid4().hex[:6]}@platform.com",
        username=f"superadmin_{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("SuperSecurePass123!"),
        first_name="Platform",
        last_name="Admin",
        is_active=True,
    )
    db.add(super_admin)
    db.commit()
    db.refresh(super_admin)

    # Assign Super Admin role
    super_role = role_repository.get_by_name(db, None, "Super Admin")
    if not super_role:
        super_role = IdentityRole(
            id=uuid.uuid4(),
            school_id=None,
            name="Super Admin",
            description="Super Administrator",
            is_system=True,
        )
        db.add(super_role)
        db.commit()

    user_role_repository.assign_role(db, super_admin.id, super_role.id)
    db.commit()
    db.refresh(super_admin)

    token = jwt_manager.create_access_token(user_id=super_admin.id, school_id=school.id)
    return super_admin, f"Bearer {token}"


def setup_regular_school_user(db: Session) -> tuple[IdentityUser, str]:
    """Create a regular school-level user and return (user, auth_header)."""
    seed_identity(db)
    school = School(
        id=uuid.uuid4(),
        name=f"Existing School {uuid.uuid4().hex[:4]}",
        code=f"EXS_{uuid.uuid4().hex[:4].upper()}",
        address_line1="123 Existing Way",
        city="City",
        district="District",
        state="State",
        country="India",
        postal_code="560001",
    )
    db.add(school)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"user_{uuid.uuid4().hex[:6]}@school.com",
        username=f"user_{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("RegularPass123!"),
        first_name="Regular",
        last_name="Teacher",
        is_active=True,
    )
    db.add(user)
    db.commit()

    # Assign Teacher role (not Super Admin)
    teacher_role = role_repository.get_by_name(db, None, "Teacher")
    if teacher_role:
        user_role_repository.assign_role(db, user.id, teacher_role.id)
        db.commit()
    db.refresh(user)

    token = jwt_manager.create_access_token(user_id=user.id, school_id=school.id)
    return user, f"Bearer {token}"


def test_onboarding_unauthenticated(client: TestClient):
    """Unauthenticated requests must be rejected with HTTP 401."""
    payload = {
        "name": "Unauthorized Academy",
        "code": "UNAUTH_01",
        "address_line1": "123 Nowhere St",
        "city": "Metropolis",
        "district": "Metro",
        "state": "State",
        "postal_code": "100001",
        "admin": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@unauth.com",
            "password": "Password123!",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2026-06-01",
            "end_date": "2027-04-30",
        },
    }
    response = client.post("/api/v1/schools/onboarding", json=payload)
    assert response.status_code == 401


def test_onboarding_unauthorized_non_super_admin(client: TestClient, db_session: Session):
    """School-level non-super-admin users must be rejected with HTTP 403."""
    _, auth_header = setup_regular_school_user(db_session)

    payload = {
        "name": "Forbidden Academy",
        "code": "FORBID_01",
        "address_line1": "123 Forbidden Way",
        "city": "Metropolis",
        "district": "Metro",
        "state": "State",
        "postal_code": "100001",
        "admin": {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@forbid.com",
            "password": "Password123!",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2026-06-01",
            "end_date": "2027-04-30",
        },
    }
    response = client.post(
        "/api/v1/schools/onboarding",
        json=payload,
        headers={"Authorization": auth_header},
    )
    assert response.status_code == 403


def test_onboarding_success_platform_super_admin(client: TestClient, db_session: Session):
    """Super Admin provisions complete school tenant with roles, admin, academic year, and classes."""
    _, auth_header = setup_super_admin(db_session)
    suffix = uuid.uuid4().hex[:6].upper()
    code = f"DPS_{suffix}"
    admin_email = f"principal_{suffix.lower()}@dpsglobal.edu"
    raw_password = "SuperSecretAdminPassword123!"

    payload = {
        "name": f"Delhi Public Global School {suffix}",
        "code": code,
        "email": f"contact_{suffix.lower()}@dpsglobal.edu",
        "phone": "9876543210",
        "address_line1": "Sector 21 Knowledge Park",
        "city": "Noida",
        "district": "Gautam Buddha Nagar",
        "state": "Uttar Pradesh",
        "country": "India",
        "postal_code": "201301",
        "subscription_tier": "PREMIUM",
        "max_students": 1200,
        "max_teachers": 100,
        "admin": {
            "first_name": "Rajesh",
            "last_name": "Sharma",
            "email": admin_email,
            "username": f"rajesh_{suffix.lower()}",
            "password": raw_password,
            "phone": "9876543211",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
            "is_current": True,
        },
        "class_templates": [
            {"name": "Nursery", "display_order": 1, "create_default_section": True, "default_section_name": "A", "capacity": 30},
            {"name": "Class 1", "display_order": 2, "create_default_section": True, "default_section_name": "A", "capacity": 40},
            {"name": "Class 2", "display_order": 3, "create_default_section": True, "default_section_name": "A", "capacity": 40},
        ],
    }

    response = client.post(
        "/api/v1/schools/onboarding",
        json=payload,
        headers={"Authorization": auth_header},
    )

    assert response.status_code == 201
    res_data = response.json()
    assert res_data["success"] is True
    data = res_data["data"]

    # Credential safety: No passwords or hashes returned in response
    assert "password" not in data
    assert "password_hash" not in data
    assert raw_password not in str(data)

    # Safe summary verification
    assert data["name"] == f"Delhi Public Global School {suffix}"
    assert data["code"] == code
    assert data["admin_email"] == admin_email
    assert data["academic_year_name"] == "2026-2027"
    assert data["roles_provisioned_count"] >= 10
    assert data["classes_provisioned_count"] == 3

    school_id = uuid.UUID(data["school_id"])
    admin_user_id = uuid.UUID(data["admin_user_id"])
    academic_year_id = uuid.UUID(data["academic_year_id"])

    # Database state verification
    db = db_session
    # 1. School
    school_db = db.query(School).filter(School.id == school_id).first()
    assert school_db is not None
    assert school_db.code == code
    assert school_db.status == SchoolStatus.ACTIVE

    # 2. Administrator User
    admin_db = db.query(IdentityUser).filter(IdentityUser.id == admin_user_id).first()
    assert admin_db is not None
    assert admin_db.school_id == school_id
    assert admin_db.email == admin_email
    assert admin_db.is_active is True
    assert verify_password(raw_password, admin_db.password_hash) is True
    assert raw_password not in admin_db.password_hash

    # 3. Roles and Permission Matrix
    tenant_roles = db.query(IdentityRole).filter(IdentityRole.school_id == school_id).all()
    assert len(tenant_roles) >= 10
    role_names = {r.name for r in tenant_roles}
    assert "School Admin" in role_names
    assert "Teacher" in role_names
    assert "Principal" in role_names
    assert "Parent" in role_names
    assert "Student" in role_names

    # Check that School Admin role was assigned to admin user
    school_admin_role = next(r for r in tenant_roles if r.name == "School Admin")
    user_roles = user_role_repository.get_roles(db, admin_db.id)
    assert school_admin_role.id in [r.role_id for r in user_roles]

    # Check that permissions are attached to School Admin role
    admin_perms = school_admin_role.permissions
    assert len(admin_perms) > 0

    # 4. Academic Year
    ay_db = db.query(AcademicYear).filter(AcademicYear.id == academic_year_id).first()
    assert ay_db is not None
    assert ay_db.school_id == school_id
    assert ay_db.name == "2026-2027"
    assert ay_db.is_current is True

    # 5. Classes and Sections
    classes_db = db.query(SchoolClass).filter(SchoolClass.school_id == school_id).all()
    assert len(classes_db) == 3
    class_names = {c.name for c in classes_db}
    assert "Nursery" in class_names
    assert "Class 1" in class_names
    assert "Class 2" in class_names

    for sc in classes_db:
        sections = db.query(Section).filter(Section.school_class_id == sc.id).all()
        assert len(sections) == 1
        assert sections[0].name == "A"

    # 6. Safe Audit Log
    audit_entry = db.query(AuditLog).filter(
        AuditLog.school_id == school_id,
        AuditLog.action == "TENANT_PROVISIONED",
    ).first()
    assert audit_entry is not None
    assert raw_password not in audit_entry.details


def test_onboarding_atomic_rollback_on_failure(client: TestClient, db_session: Session):
    """Simulated validation/database failure must roll back entire transaction (zero orphans)."""
    _, auth_header = setup_super_admin(db_session)
    suffix = uuid.uuid4().hex[:6].upper()
    code = f"FAIL_{suffix}"
    admin_email = f"fail_{suffix.lower()}@school.edu"

    # Invalid payload: start_date is AFTER end_date
    payload = {
        "name": f"Fail School {suffix}",
        "code": code,
        "address_line1": "123 Rollback St",
        "city": "City",
        "district": "District",
        "state": "State",
        "postal_code": "560001",
        "admin": {
            "first_name": "Test",
            "last_name": "Admin",
            "email": admin_email,
            "password": "Password123!",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2027-04-01",  # Invalid: start > end
            "end_date": "2026-03-31",
            "is_current": True,
        },
    }

    response = client.post(
        "/api/v1/schools/onboarding",
        json=payload,
        headers={"Authorization": auth_header},
    )

    assert response.status_code in (400, 422)

    # Ensure zero orphan records in DB
    db = db_session
    assert db.query(School).filter(School.code == code).first() is None
    assert db.query(IdentityUser).filter(IdentityUser.email == admin_email).first() is None


def test_onboarding_duplicate_school_code_conflict(client: TestClient, db_session: Session):
    """Repeated school code submission must return HTTP 409 conflict."""
    _, auth_header = setup_super_admin(db_session)
    suffix = uuid.uuid4().hex[:6].upper()
    code = f"DUP_{suffix}"

    payload = {
        "name": f"Duplicate School {suffix}",
        "code": code,
        "address_line1": "123 Main St",
        "city": "City",
        "district": "District",
        "state": "State",
        "postal_code": "560001",
        "admin": {
            "first_name": "Admin",
            "last_name": "One",
            "email": f"admin1_{suffix.lower()}@dup.edu",
            "password": "Password123!",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
    }

    # First attempt -> 201 Created
    res1 = client.post("/api/v1/schools/onboarding", json=payload, headers={"Authorization": auth_header})
    assert res1.status_code == 201

    # Second attempt with same code -> 409 Conflict
    payload_dup = dict(payload)
    payload_dup["admin"] = {
        "first_name": "Admin",
        "last_name": "Two",
        "email": f"admin2_{suffix.lower()}@dup.edu",
        "password": "Password123!",
    }
    res2 = client.post("/api/v1/schools/onboarding", json=payload_dup, headers={"Authorization": auth_header})
    assert res2.status_code == 409


def test_onboarding_duplicate_admin_email_conflict(client: TestClient, db_session: Session):
    """Repeated admin email submission must return HTTP 409 conflict."""
    _, auth_header = setup_super_admin(db_session)
    suffix = uuid.uuid4().hex[:6].upper()
    admin_email = f"shared_admin_{suffix.lower()}@test.edu"

    payload1 = {
        "name": f"School Alpha {suffix}",
        "code": f"ALP_{suffix}",
        "address_line1": "123 Alpha St",
        "city": "City",
        "district": "District",
        "state": "State",
        "postal_code": "560001",
        "admin": {
            "first_name": "Admin",
            "last_name": "Alpha",
            "email": admin_email,
            "password": "Password123!",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
    }

    res1 = client.post("/api/v1/schools/onboarding", json=payload1, headers={"Authorization": auth_header})
    assert res1.status_code == 201

    payload2 = {
        "name": f"School Beta {suffix}",
        "code": f"BET_{suffix}",
        "address_line1": "123 Beta St",
        "city": "City",
        "district": "District",
        "state": "State",
        "postal_code": "560001",
        "admin": {
            "first_name": "Admin",
            "last_name": "Beta",
            "email": admin_email,  # Duplicate admin email
            "password": "Password123!",
        },
        "academic_year": {
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
    }

    res2 = client.post("/api/v1/schools/onboarding", json=payload2, headers={"Authorization": auth_header})
    assert res2.status_code == 409


def test_onboarding_tenant_isolation(client: TestClient, db_session: Session):
    """Provisioning multiple schools must maintain strict tenant isolation across all entities."""
    _, auth_header = setup_super_admin(db_session)
    suffix1 = uuid.uuid4().hex[:4].upper()
    suffix2 = uuid.uuid4().hex[:4].upper()

    req1 = {
        "name": f"Tenant School 1 {suffix1}",
        "code": f"T1_{suffix1}",
        "address_line1": "123 Road A",
        "city": "City A",
        "district": "District A",
        "state": "State A",
        "postal_code": "560001",
        "admin": {"first_name": "A1", "last_name": "L1", "email": f"a1_{suffix1.lower()}@t1.com", "password": "Password123!"},
        "academic_year": {"name": "2026-2027", "start_date": "2026-06-01", "end_date": "2027-04-30"},
        "class_templates": [{"name": "Grade 1", "display_order": 1, "create_default_section": True, "default_section_name": "A", "capacity": 30}],
    }
    req2 = {
        "name": f"Tenant School 2 {suffix2}",
        "code": f"T2_{suffix2}",
        "address_line1": "456 Road B",
        "city": "City B",
        "district": "District B",
        "state": "State B",
        "postal_code": "560002",
        "admin": {"first_name": "A2", "last_name": "L2", "email": f"a2_{suffix2.lower()}@t2.com", "password": "Password123!"},
        "academic_year": {"name": "2026-2027", "start_date": "2026-06-01", "end_date": "2027-04-30"},
        "class_templates": [{"name": "Grade 1", "display_order": 1, "create_default_section": True, "default_section_name": "B", "capacity": 35}],
    }

    res1 = client.post("/api/v1/schools/onboarding", json=req1, headers={"Authorization": auth_header})
    res2 = client.post("/api/v1/schools/onboarding", json=req2, headers={"Authorization": auth_header})

    assert res1.status_code == 201
    assert res2.status_code == 201

    s1_id = uuid.UUID(res1.json()["data"]["school_id"])
    s2_id = uuid.UUID(res2.json()["data"]["school_id"])
    assert s1_id != s2_id

    db = db_session
    # Check users
    u1 = db.query(IdentityUser).filter(IdentityUser.school_id == s1_id).all()
    u2 = db.query(IdentityUser).filter(IdentityUser.school_id == s2_id).all()
    assert {u.id for u in u1}.isdisjoint({u.id for u in u2})

    # Check roles
    r1 = db.query(IdentityRole).filter(IdentityRole.school_id == s1_id).all()
    r2 = db.query(IdentityRole).filter(IdentityRole.school_id == s2_id).all()
    assert {r.id for r in r1}.isdisjoint({r.id for r in r2})

    # Check academic years
    ay1 = db.query(AcademicYear).filter(AcademicYear.school_id == s1_id).all()
    ay2 = db.query(AcademicYear).filter(AcademicYear.school_id == s2_id).all()
    assert {ay.id for ay in ay1}.isdisjoint({ay.id for ay in ay2})

    # Check classes
    c1 = db.query(SchoolClass).filter(SchoolClass.school_id == s1_id).all()
    c2 = db.query(SchoolClass).filter(SchoolClass.school_id == s2_id).all()
    assert {c.id for c in c1}.isdisjoint({c.id for c in c2})
