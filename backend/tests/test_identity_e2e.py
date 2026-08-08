"""
End-to-end verification of the Identity module.

Covers the complete bootstrap → authentication → RBAC workflow:

  1.  Seeding state: tables have expected rows after seed_identity()
  2.  Bootstrap: first user can be created anonymously (0 active users)
  3.  Bootstrap: first user auto-receives School Admin role
  4.  Login: valid JWT access + refresh tokens returned
  5.  Login failures: invalid password, email, school code, inactive user
  6.  Token misuse: refresh token as access token, access token as refresh token, invalid token
  7.  /auth/me: returns authenticated user
  8.  Auth guard: protected endpoints reject anonymous requests
  9.  RBAC: School Admin (with user.create) can create users
  10. RBAC: user without user.create is rejected (403)
  11. Second-user: anonymous POST /users returns 401 after first user exists
  12. Users CRUD: GET /users, GET /users/{id}, PUT /users/{id}, DELETE /users/{id}
  13. Roles CRUD: POST /roles, GET /roles, GET /roles/{id}, PUT /roles/{id}, DELETE /roles/{id}
  14. Permissions API: GET /permissions, GET /permissions/{id}
  15. User-roles API: assign / list / remove role
  16. Role-permissions API: assign / list / remove permission
  17. Seed Endpoint: POST /identity/seed
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Register ALL SQLAlchemy models before metadata.create_all()
import app.database.models  # noqa: F401

from app.main import app as fastapi_app
from app.dependencies.database import get_db
from app.database.base import Base
from app.models.school.school import School
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.schemas.user import UserCreate
from app.identity.schemas.role import RoleCreate
from app.identity.services.user_service import identity_user_service
from app.identity.repositories import (
    identity_user_repository,
    role_repository,
    user_role_repository,
    permission_repository,
    role_permission_repository,
)

# ---------------------------------------------------------------------------
# Shared in-memory database fixture
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def engine():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)
    eng.dispose()


@pytest.fixture(scope="module")
def db_session(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="module")
def db(db_session):
    return db_session


@pytest.fixture(scope="module")
def client(engine):
    Session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        session = Session()
        try:
            yield session
        finally:
            session.close()

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()



# ---------------------------------------------------------------------------
# Shared test state (populated progressively across tests)
# ---------------------------------------------------------------------------

class State:
    school: School = None
    admin_user = None
    second_user = None
    inactive_user = None
    admin_access_token: str = ""
    admin_refresh_token: str = ""
    second_user_access_token: str = ""
    custom_role_id: str = ""


S = State()


def make_school(db, code="E2ETEST", name="E2E Test School") -> School:
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=code,
        address_line1="1 Test Ave",
        city="Testville",
        district="TestDistrict",
        state="TestState",
        country="India",
        postal_code="100001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


# ===========================================================================
# Test 1 – Seeding state
# ===========================================================================

def test_01_seed_identity_state(db, client):
    """After seeding, expected number of permissions and system roles exist."""
    summary = seed_identity(db)

    assert summary["permissions_created"] == 74
    assert summary["roles_created"] == 10
    assert summary["assignments_created"] > 0

    all_roles = role_repository.get_system_roles(db)
    role_names = {r.name for r in all_roles}
    assert "School Admin" in role_names
    assert "Super Admin" in role_names

    # Idempotency check
    summary2 = seed_identity(db)
    assert summary2["permissions_created"] == 0
    assert summary2["roles_created"] == 0


# ===========================================================================
# Test 2 – Bootstrap: first user created anonymously
# ===========================================================================

def test_02_bootstrap_first_user_created_anonymously(db, client):
    """POST /api/v1/users without auth must return 201 when identity_users is empty."""
    S.school = make_school(db)

    count = identity_user_repository.count_by_school(db, S.school.id)
    assert count == 0

    payload = {
        "school_id": str(S.school.id),
        "email": "admin@e2etest.edu",
        "password": "Str0ng!Pass1",
        "first_name": "Admin",
        "last_name": "User",
    }
    resp = client.post("/api/v1/users", json=payload)
    assert resp.status_code == 201

    data = resp.json()
    assert data["email"] == "admin@e2etest.edu"
    assert data["first_name"] == "Admin"


# ===========================================================================
# Test 3 – First user auto-receives School Admin role
# ===========================================================================

def test_03_first_user_receives_school_admin_role(db, client):
    """The first user of a school automatically gets the School Admin role."""
    S.admin_user = identity_user_repository.get_by_email(
        db, S.school.id, "admin@e2etest.edu"
    )
    assert S.admin_user is not None

    admin_role = role_repository.get_by_name(db, None, "School Admin")
    assert admin_role is not None

    roles = user_role_repository.get_roles(db, S.admin_user.id)
    assigned_role_ids = {r.role_id for r in roles}
    assert admin_role.id in assigned_role_ids


# ===========================================================================
# Test 4 – Login returns valid JWT tokens & Login Failures
# ===========================================================================

def test_04_login_success_and_failures(db, client):
    """Test successful login and login edge cases (invalid pass, email, school, inactive)."""
    # Invalid school code -> 400
    res_bad_school = client.post("/api/v1/auth/login", json={
        "school_code": "INVALID_CODE",
        "email": "admin@e2etest.edu",
        "password": "Str0ng!Pass1",
    })
    assert res_bad_school.status_code == 400

    # Invalid email -> 401
    res_bad_email = client.post("/api/v1/auth/login", json={
        "school_code": S.school.code,
        "email": "nonexistent@e2etest.edu",
        "password": "Str0ng!Pass1",
    })
    assert res_bad_email.status_code == 401

    # Invalid password -> 401
    res_bad_pass = client.post("/api/v1/auth/login", json={
        "school_code": S.school.code,
        "email": "admin@e2etest.edu",
        "password": "WrongPassword123!",
    })
    assert res_bad_pass.status_code == 401

    # Create inactive user directly in DB for testing
    inactive_u = identity_user_service.create_user(
        db,
        UserCreate(
            school_id=S.school.id,
            email="inactive@e2etest.edu",
            password="Str0ng!Pass1",
            first_name="Inactive",
        ),
    )
    inactive_u.is_active = False
    db.commit()
    S.inactive_user = inactive_u

    # Inactive user login -> 401
    res_inactive = client.post("/api/v1/auth/login", json={
        "school_code": S.school.code,
        "email": "inactive@e2etest.edu",
        "password": "Str0ng!Pass1",
    })
    assert res_inactive.status_code == 401

    # Successful login
    payload = {
        "school_code": S.school.code,
        "email": "admin@e2etest.edu",
        "password": "Str0ng!Pass1",
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200

    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"].lower() == "bearer"

    S.admin_access_token = data["access_token"]
    S.admin_refresh_token = data["refresh_token"]


# ===========================================================================
# Test 5 – Token misuse tests
# ===========================================================================

def test_05_token_misuse_scenarios(db, client):
    """Verify refresh token cannot be used as access token, vice versa, and forged tokens are rejected."""
    # Using Refresh Token as Bearer Auth Token -> 401
    res_refresh_as_access = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {S.admin_refresh_token}"},
    )
    assert res_refresh_as_access.status_code == 401

    # Using Access Token as Refresh Token -> 401
    res_access_as_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": S.admin_access_token},
    )
    assert res_access_as_refresh.status_code == 401

    # Invalid / Malformed Token -> 401
    res_invalid_token = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert res_invalid_token.status_code == 401

    # Forged Token (signed with WRONG_SECRET_KEY for a real existing user) -> 401
    admin_u = identity_user_repository.get_by_email(db, S.school.id, "admin@e2etest.edu")
    assert admin_u is not None
    from jose import jwt
    from datetime import datetime, timezone, timedelta
    now = datetime.now(timezone.utc)
    forged_payload = {
        "sub": str(admin_u.id),
        "school_id": str(S.school.id),
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=30),
    }
    forged_token = jwt.encode(forged_payload, "WRONG_SECRET_KEY_12345", algorithm="HS256")
    res_forged = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {forged_token}"},
    )
    assert res_forged.status_code == 401


# ===========================================================================
# Test 6 – /auth/me returns authenticated user
# ===========================================================================

def test_06_auth_me_returns_current_user(db, client):
    """GET /api/v1/auth/me must return the authenticated user's profile."""
    resp = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {S.admin_access_token}"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["email"] == "admin@e2etest.edu"


# ===========================================================================
# Test 7 – Protected endpoints reject anonymous requests
# ===========================================================================

@pytest.mark.parametrize("method,url,body", [
    ("get",    "/api/v1/auth/me",            None),
    ("get",    "/api/v1/users",              None),
    ("get",    "/api/v1/users/" + str(uuid.uuid4()), None),
    ("put",    "/api/v1/users/" + str(uuid.uuid4()), {"first_name": "x"}),
    ("delete", "/api/v1/users/" + str(uuid.uuid4()), None),
    ("get",    "/api/v1/roles",              None),
    ("get",    "/api/v1/permissions",        None),
])
def test_07_protected_endpoints_reject_anonymous(method, url, body, client):
    """Each protected endpoint must return 401 or 403 when no token is provided."""
    func = getattr(client, method)
    kwargs = {}
    if body:
        kwargs["json"] = body

    resp = func(url, **kwargs)
    assert resp.status_code in (401, 403)


# ===========================================================================
# Test 8 – RBAC: School Admin can create a second user
# ===========================================================================

def test_08_school_admin_can_create_second_user(db, client):
    """A user with user.create permission can create other users."""
    payload = {
        "school_id": str(S.school.id),
        "email": "teacher@e2etest.edu",
        "password": "Str0ng!Pass2",
        "first_name": "Teacher",
        "last_name": "One",
    }
    resp = client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {S.admin_access_token}"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "teacher@e2etest.edu"

    S.second_user = identity_user_repository.get_by_email(
        db, S.school.id, "teacher@e2etest.edu"
    )
    assert S.second_user is not None


# ===========================================================================
# Test 9 – RBAC: user without user.create is rejected (403)
# ===========================================================================

def test_09_user_without_permission_gets_403(db, client):
    """A user without user.create must receive 403 when trying to create another user."""
    S.second_user_access_token = jwt_manager.create_access_token(
        S.second_user.id,
        S.school.id,
    )

    payload = {
        "school_id": str(S.school.id),
        "email": "another@e2etest.edu",
        "password": "Str0ng!Pass3",
        "first_name": "Another",
    }
    resp = client.post(
        "/api/v1/users",
        json=payload,
        headers={"Authorization": f"Bearer {S.second_user_access_token}"},
    )
    assert resp.status_code == 403


# ===========================================================================
# Test 10 – Anonymous POST /users returns 401 after first user exists
# ===========================================================================

def test_10_anonymous_create_user_rejected_when_users_exist(db, client):
    """Once at least one active user exists, anonymous POST /api/v1/users returns 401."""
    payload = {
        "school_id": str(S.school.id),
        "email": "intruder@e2etest.edu",
        "password": "Str0ng!Pass4",
        "first_name": "Intruder",
    }
    resp = client.post("/api/v1/users", json=payload)
    assert resp.status_code in (401, 403)


# ===========================================================================
# Test 11 – Refresh token returns new tokens
# ===========================================================================

def test_11_refresh_token_returns_new_tokens(db, client):
    """POST /api/v1/auth/refresh must issue new tokens from a valid refresh token."""
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": S.admin_refresh_token},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data


# ===========================================================================
# Test 12 – Users CRUD Endpoints
# ===========================================================================

def test_12_users_crud_endpoints(db, client):
    """Verify GET /users, GET /users/{id}, PUT /users/{id}, DELETE /users/{id}."""
    headers = {"Authorization": f"Bearer {S.admin_access_token}"}

    # Create a temporary user specifically for CRUD testing
    temp_user_resp = client.post(
        "/api/v1/users",
        json={
            "school_id": str(S.school.id),
            "email": "crud_temp@e2etest.edu",
            "password": "Str0ng!Pass1",
            "first_name": "CRUDTemp",
        },
        headers=headers,
    )
    assert temp_user_resp.status_code == 201
    temp_user_id = temp_user_resp.json()["id"]

    # List users
    res_list = client.get("/api/v1/users", headers=headers)
    assert res_list.status_code == 200
    assert res_list.json()["total"] >= 2

    # Get user
    res_get = client.get(f"/api/v1/users/{temp_user_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == temp_user_id

    # Update user
    res_put = client.put(
        f"/api/v1/users/{temp_user_id}",
        json={"first_name": "UpdatedName"},
        headers=headers,
    )
    assert res_put.status_code == 200
    assert res_put.json()["first_name"] == "UpdatedName"

    # Delete temporary user
    res_del = client.delete(f"/api/v1/users/{temp_user_id}", headers=headers)
    assert res_del.status_code == 204


# ===========================================================================
# Test 13 – Roles CRUD Endpoints
# ===========================================================================

def test_13_roles_crud_endpoints(db, client):
    """Verify POST /roles, GET /roles, GET /roles/{id}, PUT /roles/{id}, DELETE /roles/{id}."""
    headers = {"Authorization": f"Bearer {S.admin_access_token}"}

    # Create Role
    res_create = client.post(
        "/api/v1/roles",
        json={
            "school_id": str(S.school.id),
            "name": "CRUD Test Role",
            "description": "Test role for CRUD",
        },
        headers=headers,
    )
    assert res_create.status_code == 201
    role_id = res_create.json()["id"]

    # List Roles
    res_list = client.get(f"/api/v1/roles?school_id={S.school.id}", headers=headers)
    assert res_list.status_code == 200

    # Get Role
    res_get = client.get(f"/api/v1/roles/{role_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "CRUD Test Role"

    # Update Role
    res_update = client.put(
        f"/api/v1/roles/{role_id}",
        json={"name": "Updated Role Name"},
        headers=headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated Role Name"

    # Delete Role
    res_del = client.delete(f"/api/v1/roles/{role_id}", headers=headers)
    assert res_del.status_code == 204


# ===========================================================================
# Test 14 – Permissions Endpoints
# ===========================================================================

def test_14_permissions_endpoints(db, client):
    """Verify GET /permissions, GET /permissions/{id}."""
    headers = {"Authorization": f"Bearer {S.admin_access_token}"}

    res_list = client.get("/api/v1/permissions", headers=headers)
    assert res_list.status_code == 200
    perms = res_list.json()
    assert len(perms) >= 74

    first_perm_id = perms[0]["id"]
    res_get = client.get(f"/api/v1/permissions/{first_perm_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == first_perm_id


# ===========================================================================
# Test 15 – User-roles API: assign / list / remove
# ===========================================================================

def test_15_user_roles_api_assign_list_remove(db, client):
    """Verify the /users/{id}/roles API works end-to-end."""
    teacher_role = role_repository.get_by_name(db, None, "Teacher")
    assert teacher_role is not None

    role_id = str(teacher_role.id)
    user_id = str(S.second_user.id)
    headers = {"Authorization": f"Bearer {S.admin_access_token}"}

    # Assign role
    resp_assign = client.post(
        f"/api/v1/users/{user_id}/roles/{role_id}",
        headers=headers,
    )
    assert resp_assign.status_code == 201

    # List roles
    resp_list = client.get(
        f"/api/v1/users/{user_id}/roles",
        headers=headers,
    )
    assert resp_list.status_code == 200
    assigned_role_ids = [r["role_id"] for r in resp_list.json()]
    assert role_id in assigned_role_ids

    # Remove role
    resp_remove = client.delete(
        f"/api/v1/users/{user_id}/roles/{role_id}",
        headers=headers,
    )
    assert resp_remove.status_code == 204


# ===========================================================================
# Test 16 – Role-permissions API: assign / list / remove
# ===========================================================================

def test_16_role_permissions_api_assign_list_remove(db, client):
    """Verify the /roles/{id}/permissions API works end-to-end."""
    headers = {"Authorization": f"Bearer {S.admin_access_token}"}

    custom_role_resp = client.post(
        "/api/v1/roles",
        json={
            "school_id": str(S.school.id),
            "name": "E2E Perm Role",
            "description": "Test role for perm assignment",
        },
        headers=headers,
    )
    assert custom_role_resp.status_code == 201
    role_id = custom_role_resp.json()["id"]

    perms = permission_repository.get_all(db)
    target_perm = next((p for p in perms if p.name == "user.view"), None)
    assert target_perm is not None
    perm_id = str(target_perm.id)

    # Assign permission
    resp_assign = client.post(
        f"/api/v1/roles/{role_id}/permissions/{perm_id}",
        headers=headers,
    )
    assert resp_assign.status_code == 201

    # List permissions
    resp_list = client.get(
        f"/api/v1/roles/{role_id}/permissions",
        headers=headers,
    )
    assert resp_list.status_code == 200
    perm_ids = [p["permission_id"] for p in resp_list.json()]
    assert perm_id in perm_ids

    # Remove permission
    resp_remove = client.delete(
        f"/api/v1/roles/{role_id}/permissions/{perm_id}",
        headers=headers,
    )
    assert resp_remove.status_code == 204


# ===========================================================================
# Test 17 – Seed API Endpoint
# ===========================================================================

def test_17_seed_identity_api_endpoint(db, client):
    """POST /api/v1/identity/seed allows seeding via API for permission.create holders."""
    headers = {"Authorization": f"Bearer {S.admin_access_token}"}
    res_seed = client.post("/api/v1/identity/seed", headers=headers)
    assert res_seed.status_code == 200
    data = res_seed.json()
    assert "permissions_created" in data
    assert "roles_created" in data
