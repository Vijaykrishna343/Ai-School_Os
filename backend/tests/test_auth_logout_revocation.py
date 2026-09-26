"""
Tests for Phase B: Logout + Refresh-Token Revocation
Covers:
- Login session recording (jti, user_id, school_id, token_hash)
- Valid refresh token rotation and old session revocation
- Access token rejected at refresh endpoint
- Expired and malformed refresh tokens rejected
- Unknown jti rejected
- Revoked refresh token rejected
- Authenticated logout revokes refresh session
- Repeated logout idempotency
- Cross-user and cross-tenant revocation forbidden
- Replay attack prevention (post-logout and post-rotation)
"""

import uuid
from datetime import datetime, timedelta, timezone
from jose import jwt
import pytest
from sqlalchemy.orm import Session

from app.common.enums.identity.token_type import TokenType
from app.core.config import settings
from app.identity.models.refresh_token import IdentityRefreshToken
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.repositories import identity_refresh_token_repository
from app.identity.security.jwt_config import jwt_settings
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.models.school import School


@pytest.fixture
def auth_fixture_data(db_session: Session):
    """Seed two distinct schools and users for testing authentication and tenant isolation."""
    # School A
    sch_a_id = uuid.uuid4()
    school_a = School(
        id=sch_a_id,
        name="Revocation School A",
        code=f"REV_SCH_A_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_a_id,
        email="user_a@revocation.com",
        password_hash=hash_password("Password123!"),
        first_name="User",
        last_name="A",
        is_active=True,
    )

    # School B (Different Tenant)
    sch_b_id = uuid.uuid4()
    school_b = School(
        id=sch_b_id,
        name="Revocation School B",
        code=f"REV_SCH_B_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="456 Secondary St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500002",
    )
    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_b_id,
        email="user_b@revocation.com",
        password_hash=hash_password("Password123!"),
        first_name="User",
        last_name="B",
        is_active=True,
    )

    # User A2 in School A (Same Tenant, Different User)
    user_a2 = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_a_id,
        email="user_a2@revocation.com",
        password_hash=hash_password("Password123!"),
        first_name="User",
        last_name="A2",
        is_active=True,
    )

    db_session.add_all([school_a, user_a, school_b, user_b, user_a2])
    db_session.commit()

    return {
        "school_a": school_a,
        "user_a": user_a,
        "school_b": school_b,
        "user_b": user_b,
        "user_a2": user_a2,
    }


def test_01_login_creates_refresh_session(client, db_session: Session, auth_fixture_data):
    """Successful login must record an active refresh session in the database."""
    data = auth_fixture_data
    payload = {
        "school_code": data["school_a"].code,
        "email": "user_a@revocation.com",
        "password": "Password123!",
    }
    resp = client.post("/api/v1/auth/login", json=payload)
    assert resp.status_code == 200
    res_data = resp.json()
    assert "access_token" in res_data
    assert "refresh_token" in res_data

    # Verify token payload
    decoded = jwt_manager.decode_token(res_data["refresh_token"])
    jti = decoded["jti"]
    assert jti is not None

    # Verify session record in DB
    session = identity_refresh_token_repository.get_by_jti(db_session, jti)
    assert session is not None
    assert session.user_id == data["user_a"].id
    assert session.school_id == data["school_a"].id
    assert session.is_revoked is False
    assert session.expires_at > datetime.now(timezone.utc)


def test_02_valid_refresh_token_rotates_and_revokes_previous(client, db_session: Session, auth_fixture_data):
    """POST /auth/refresh must issue new tokens, revoke the old session, and register the new session."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    )
    tokens = login_resp.json()
    old_refresh_token = tokens["refresh_token"]
    old_jti = jwt_manager.decode_token(old_refresh_token)["jti"]

    # Refresh
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": old_refresh_token},
    )
    assert refresh_resp.status_code == 200
    new_tokens = refresh_resp.json()
    assert "access_token" in new_tokens
    assert "refresh_token" in new_tokens
    new_refresh_token = new_tokens["refresh_token"]
    assert new_refresh_token != old_refresh_token

    new_jti = jwt_manager.decode_token(new_refresh_token)["jti"]
    assert new_jti != old_jti

    # Verify old session is now revoked with reason REFRESH_ROTATION
    old_session = identity_refresh_token_repository.get_by_jti(db_session, old_jti)
    assert old_session.is_revoked is True
    assert old_session.revocation_reason == "REFRESH_ROTATION"
    assert old_session.revoked_at is not None

    # Verify new session is active
    new_session = identity_refresh_token_repository.get_by_jti(db_session, new_jti)
    assert new_session.is_revoked is False
    assert new_session.user_id == data["user_a"].id


def test_03_access_token_rejected_at_refresh_endpoint(client, auth_fixture_data):
    """Access token must not be accepted at /auth/refresh."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    )
    access_token = login_resp.json()["access_token"]

    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": access_token},
    )
    assert resp.status_code == 401
    assert "Refresh token required" in resp.text


def test_04_expired_refresh_token_rejected(client, db_session: Session, auth_fixture_data):
    """Expired refresh token must be rejected."""
    data = auth_fixture_data
    now = datetime.now(timezone.utc) - timedelta(days=10)
    expired_payload = {
        "sub": str(data["user_a"].id),
        "school_id": str(data["school_a"].id),
        "type": TokenType.REFRESH.value,
        "iat": now,
        "exp": now + timedelta(hours=1),
        "jti": str(uuid.uuid4()),
    }
    expired_token = jwt.encode(
        expired_payload,
        jwt_settings.SECRET_KEY,
        algorithm=jwt_settings.ALGORITHM,
    )

    # Even if in DB or not, signature/exp verification rejects it
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": expired_token},
    )
    assert resp.status_code == 401


def test_05_malformed_refresh_token_rejected(client):
    """Malformed or non-JWT string must be rejected."""
    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "not.a.valid.jwt.token"},
    )
    assert resp.status_code == 401


def test_06_unknown_jti_refresh_token_rejected(client, auth_fixture_data):
    """Validly signed refresh token with unknown JTI not registered in DB must be rejected."""
    data = auth_fixture_data
    now = datetime.now(timezone.utc)
    unknown_payload = {
        "sub": str(data["user_a"].id),
        "school_id": str(data["school_a"].id),
        "type": TokenType.REFRESH.value,
        "iat": now,
        "exp": now + timedelta(days=7),
        "jti": str(uuid.uuid4()),  # Unrecorded in DB
    }
    token = jwt.encode(
        unknown_payload,
        jwt_settings.SECRET_KEY,
        algorithm=jwt_settings.ALGORITHM,
    )

    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token},
    )
    assert resp.status_code == 401
    assert "Refresh token session not found" in resp.text


def test_07_revoked_refresh_token_rejected(client, db_session: Session, auth_fixture_data):
    """Manually revoked refresh session must be rejected upon refresh attempt."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    )
    refresh_token = login_resp.json()["refresh_token"]
    jti = jwt_manager.decode_token(refresh_token)["jti"]

    # Explicitly revoke session in DB
    session = identity_refresh_token_repository.get_by_jti(db_session, jti)
    identity_refresh_token_repository.revoke_session(db_session, session, reason="ADMIN_TERMINATION")

    resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert resp.status_code == 401
    assert "Refresh token has been revoked" in resp.text


def test_08_authenticated_logout_revokes_session(client, db_session: Session, auth_fixture_data):
    """Calling POST /auth/logout with token must revoke the session server-side."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    )
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]
    jti = jwt_manager.decode_token(refresh_token)["jti"]

    # Perform logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200
    assert logout_resp.json()["message"] == "Logged out successfully"

    # Verify DB state
    session = identity_refresh_token_repository.get_by_jti(db_session, jti)
    assert session.is_revoked is True
    assert session.revocation_reason == "USER_LOGOUT"
    assert session.revoked_at is not None

    # Verify token cannot be used to refresh
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert refresh_resp.status_code == 401
    assert "Refresh token has been revoked" in refresh_resp.text


def test_09_repeated_logout_is_idempotent(client, auth_fixture_data):
    """Calling logout repeatedly on already revoked or empty payload must succeed safely."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    )
    tokens = login_resp.json()
    access_token = tokens["access_token"]
    refresh_token = tokens["refresh_token"]

    # First logout
    r1 = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert r1.status_code == 200

    # Second logout (already revoked)
    r2 = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert r2.status_code == 200

    # Logout with no payload
    r3 = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={},
    )
    assert r3.status_code == 200


def test_10_unauthenticated_logout_rejected(client):
    """POST /auth/logout without credentials must return 401."""
    resp = client.post("/api/v1/auth/logout", json={})
    assert resp.status_code == 401


def test_11_cross_user_revocation_forbidden(client, auth_fixture_data):
    """User A cannot revoke User A2's refresh token (Same Tenant, Different User)."""
    data = auth_fixture_data
    # Login User A
    login_a = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    ).json()

    # Login User A2
    login_a2 = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a2@revocation.com",
            "password": "Password123!",
        },
    ).json()

    # User A tries to revoke User A2's refresh token
    resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_a['access_token']}"},
        json={"refresh_token": login_a2["refresh_token"]},
    )
    assert resp.status_code == 403
    assert "Cannot revoke a session belonging to another user" in resp.text


def test_12_cross_tenant_revocation_forbidden(client, auth_fixture_data):
    """User A in School A cannot revoke User B's token in School B (Cross-Tenant)."""
    data = auth_fixture_data
    # Login User A (School A)
    login_a = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    ).json()

    # Login User B (School B)
    login_b = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_b"].code,
            "email": "user_b@revocation.com",
            "password": "Password123!",
        },
    ).json()

    # User A tries to revoke User B's refresh token
    resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_a['access_token']}"},
        json={"refresh_token": login_b["refresh_token"]},
    )
    assert resp.status_code == 403
    assert "Cannot revoke a session belonging to another" in resp.text


def test_13_replay_attack_post_logout_rejected(client, auth_fixture_data):
    """Replay sequence: login -> obtain refresh token -> logout -> attempt refresh with old token -> must fail."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    ).json()

    access_token = login_resp["access_token"]
    refresh_token = login_resp["refresh_token"]

    # Logout
    logout_resp = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {access_token}"},
        json={"refresh_token": refresh_token},
    )
    assert logout_resp.status_code == 200

    # Attacker attempts to reuse the refresh token
    replay_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert replay_resp.status_code == 401
    assert "revoked" in replay_resp.text.lower()


def test_14_replay_attack_post_rotation_rejected(client, auth_fixture_data):
    """Replay sequence: login -> refresh token A rotated to token B -> reuse token A -> must fail."""
    data = auth_fixture_data
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@revocation.com",
            "password": "Password123!",
        },
    ).json()

    token_a = login_resp["refresh_token"]

    # Rotate Token A -> Token B
    refresh_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_a},
    )
    assert refresh_resp.status_code == 200
    token_b = refresh_resp.json()["refresh_token"]
    assert token_a != token_b

    # Attempt to replay Token A
    replay_resp = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_a},
    )
    assert replay_resp.status_code == 401
    assert "revoked" in replay_resp.text.lower()

    # Token B should still be valid and usable
    valid_refresh = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": token_b},
    )
    assert valid_refresh.status_code == 200


def test_15_concurrent_refresh_rotation_atomic_race_closed(engine):
    """
    Concurrency Security Verification:
    When two concurrent requests on distinct DB connections attempt to rotate the SAME original refresh token simultaneously:
    - Exactly ONE request must succeed (returns new access + refresh token).
    - The other request MUST fail with UnauthorizedException (HTTP 401: revoked).
    - The original token session must be marked is_revoked=True with reason 'REFRESH_ROTATION'.
    """
    import concurrent.futures
    import threading
    import uuid
    from sqlalchemy.orm import sessionmaker
    from app.common.exceptions import UnauthorizedException
    from app.identity.models.user import IdentityUser
    from app.identity.schemas.user.refresh_token import RefreshToken
    from app.identity.schemas.user.user_login import UserLogin
    from app.identity.security.password import hash_password
    from app.identity.services.authentication_service import authentication_service
    from app.models.school.school import School

    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    # Setup dedicated test data committed directly to the engine
    setup_session = TestSession()
    sch_id = uuid.uuid4()
    school = School(
        id=sch_id,
        name="Concurrent Test School",
        code=f"CONC_SCH_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="123 Concurrency Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_id,
        email="concurrent_user@revocation.com",
        password_hash=hash_password("Password123!"),
        first_name="Conc",
        last_name="User",
        is_active=True,
    )
    setup_session.add(school)
    setup_session.add(user)
    setup_session.commit()

    # Login to create active refresh token session
    login_result = authentication_service.login(
        db=setup_session,
        credentials=UserLogin(
            school_code=school.code,
            email="concurrent_user@revocation.com",
            password="Password123!",
        ),
    )
    orig_refresh_token = login_result.refresh_token
    setup_session.close()

    barrier = threading.Barrier(2)

    def run_concurrent_refresh():
        s = TestSession()
        try:
            barrier.wait()
            res = authentication_service.refresh_token(
                db=s,
                data=RefreshToken(refresh_token=orig_refresh_token),
            )
            return {"success": True, "data": res}
        except UnauthorizedException as exc:
            return {"success": False, "error": str(exc.detail)}
        finally:
            s.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_concurrent_refresh)
        f2 = executor.submit(run_concurrent_refresh)
        res1 = f1.result()
        res2 = f2.result()

    results = [res1, res2]
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(failures) == 1, f"Expected exactly 1 failure, got {len(failures)}: {results}"

    # Verify failed request was rejected due to revocation
    assert "revoked" in failures[0]["error"].lower() or "invalid" in failures[0]["error"].lower()

    # Verify newly issued token
    new_token = successes[0]["data"].refresh_token
    assert new_token != orig_refresh_token

    # Verify subsequent refresh with new token succeeds
    verify_session = TestSession()
    try:
        subsequent_res = authentication_service.refresh_token(
            db=verify_session,
            data=RefreshToken(refresh_token=new_token),
        )
        assert subsequent_res.refresh_token != new_token
    finally:
        verify_session.close()
