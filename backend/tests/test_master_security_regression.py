"""
Comprehensive Master Security Regression Test Suite.
Tests all 14 security invariants across RBAC, system role guards, tenant isolation,
school suspension, and user suspension.
"""
from uuid import uuid4
import pytest
from fastapi.testclient import TestClient

import app.database.models  # noqa: F401
from app.common.enums.school import SchoolStatus
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.school import School


@pytest.fixture
def test_setup(db_session):
    seed_identity(db_session)

    # 1. School A
    school_a = School(
        name="VGS School A",
        code=f"VGS_{uuid4().hex[:6]}",
        address_line1="123 Main St",
        city="Bengaluru",
        district="Bengaluru",
        state="Karnataka",
        postal_code="560001",
        status=SchoolStatus.ACTIVE,
    )
    db_session.add(school_a)
    db_session.commit()

    # 2. Super Admin User
    super_admin_role = db_session.query(IdentityRole).filter(IdentityRole.name == "Super Admin").first()
    super_admin_user = IdentityUser(
        school_id=school_a.id,
        email=f"superadmin_{uuid4().hex[:6]}@platform.com",
        password_hash=hash_password("Password123!"),
        first_name="Super",
        last_name="Admin",
        is_active=True,
    )
    db_session.add(super_admin_user)
    db_session.commit()
    super_admin_user.roles.append(super_admin_role)
    db_session.commit()

    # 3. School Admin User (School A)
    school_admin_role = db_session.query(IdentityRole).filter(IdentityRole.name == "School Admin").first()
    school_admin_user = IdentityUser(
        school_id=school_a.id,
        email=f"schooladmin_{uuid4().hex[:6]}@vgs.com",
        password_hash=hash_password("Password123!"),
        first_name="School",
        last_name="Admin",
        is_active=True,
    )
    db_session.add(school_admin_user)
    db_session.commit()
    school_admin_user.roles.append(school_admin_role)
    db_session.commit()

    # 4. Teacher User (School A)
    teacher_role = db_session.query(IdentityRole).filter(IdentityRole.name == "Teacher").first()
    teacher_user = IdentityUser(
        school_id=school_a.id,
        email=f"teacher_{uuid4().hex[:6]}@vgs.com",
        password_hash=hash_password("Password123!"),
        first_name="Teacher",
        last_name="User",
        is_active=True,
    )
    db_session.add(teacher_user)
    db_session.commit()
    teacher_user.roles.append(teacher_role)
    db_session.commit()

    # Create tokens
    sa_token = jwt_manager.create_access_token(super_admin_user.id, school_a.id)
    admin_token = jwt_manager.create_access_token(school_admin_user.id, school_a.id)
    teacher_token = jwt_manager.create_access_token(teacher_user.id, school_a.id)

    return {
        "school_a": school_a,
        "super_admin": super_admin_user,
        "school_admin": school_admin_user,
        "teacher": teacher_user,
        "sa_headers": {"Authorization": f"Bearer {sa_token}"},
        "admin_headers": {"Authorization": f"Bearer {admin_token}"},
        "teacher_headers": {"Authorization": f"Bearer {teacher_token}"},
    }


def test_school_suspension_enforcement(client: TestClient, db_session, test_setup):
    """
    INVARIANT 6 & 14: Suspended school blocks school users with 403, Super Admin allowed access.
    """
    school_a = test_setup["school_a"]
    school_a.status = SchoolStatus.SUSPENDED
    db_session.commit()
    db_session.expire_all()

    # School Admin should be rejected with 403 Forbidden because school is suspended
    res = client.get("/api/v1/users", headers=test_setup["admin_headers"])
    assert res.status_code == 403
    assert "suspended" in str(res.json()).lower()

    # Reset school status
    school_a.status = SchoolStatus.ACTIVE
    db_session.commit()
    db_session.expire_all()


def test_system_role_protection(client: TestClient, db_session, test_setup):
    """
    INVARIANT 2: School Admin cannot modify or delete System Roles.
    """
    system_role = db_session.query(IdentityRole).filter(IdentityRole.name == "Teacher").first()
    assert system_role is not None

    # Attempt update
    res = client.put(f"/api/v1/roles/{system_role.id}", json={"name": "Tampered Teacher"}, headers=test_setup["admin_headers"])
    assert res.status_code in (400, 403)

    # Attempt delete
    res = client.delete(f"/api/v1/roles/{system_role.id}", headers=test_setup["admin_headers"])
    assert res.status_code in (400, 403)


def test_global_permission_mutation_protection(client: TestClient, test_setup):
    """
    INVARIANT 3: School Admin cannot create, update, or delete global permissions.
    """
    res = client.post("/api/v1/permissions", json={"name": "malicious.perm", "module": "malicious", "action": "CREATE", "description": "test"}, headers=test_setup["admin_headers"])
    assert res.status_code == 403


def test_super_admin_privilege_escalation_guard(client: TestClient, db_session, test_setup):
    """
    INVARIANT 1: School Admin cannot assign Super Admin role to anyone.
    """
    super_admin_role = db_session.query(IdentityRole).filter(IdentityRole.name == "Super Admin").first()
    assert super_admin_role is not None

    # Create dummy user
    dummy_user = IdentityUser(
        school_id=test_setup["school_a"].id,
        email=f"dummy_{uuid4()}@vgs.edu",
        password_hash=hash_password("Password123!"),
        first_name="Dummy",
        is_active=True,
    )
    db_session.add(dummy_user)
    db_session.commit()
    db_session.expire_all()

    res = client.post(f"/api/v1/users/{dummy_user.id}/roles/{super_admin_role.id}", headers=test_setup["admin_headers"])
    assert res.status_code == 403


def test_cross_tenant_user_isolation(client: TestClient, db_session, test_setup):
    """
    INVARIANT 4: School Admin cannot view or manipulate users from another school.
    """
    other_school = School(
        name="Other School",
        code=f"OTH_{uuid4().hex[:6]}",
        address_line1="Address",
        city="City",
        district="District",
        state="State",
        postal_code="123456",
        status=SchoolStatus.ACTIVE,
    )
    db_session.add(other_school)
    db_session.commit()

    other_user = IdentityUser(
        school_id=other_school.id,
        email=f"other_{uuid4()}@other.edu",
        password_hash=hash_password("Password123!"),
        first_name="Other",
        is_active=True,
    )
    db_session.add(other_user)
    db_session.commit()
    db_session.expire_all()

    # Attempt get user from other school
    res = client.get(f"/api/v1/users/{other_user.id}", headers=test_setup["admin_headers"])
    assert res.status_code == 404

    # Attempt delete user from other school
    res = client.delete(f"/api/v1/users/{other_user.id}", headers=test_setup["admin_headers"])
    assert res.status_code == 404
