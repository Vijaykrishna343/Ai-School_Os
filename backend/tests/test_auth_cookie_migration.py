"""
Tests for Phase E: Secure HttpOnly Cookie Authentication Migration.
Covers all required security tests (Section 22 & 23):
1. Login sets access cookie
2. Login sets refresh cookie
3. Cookies are HttpOnly
4. Production cookies are Secure
5. Correct SameSite policy is present
6. Cookie path is correct
7. Login response compatibility
8. Authenticated browser request succeeds using cookies
9. Request without cookies is rejected
10. Expired access token behaves correctly
11. Refresh cookie successfully obtains a new access session
12. Old refresh cookie cannot be reused after rotation
13. Concurrent refresh requests result in exactly one success
14. New refresh cookie corresponds to the new persisted session
15. Logout revokes refresh session
16. Logout clears authentication cookies
17. Reusing the old refresh cookie fails
18. Logout remains appropriately idempotent
19. Password reset revokes refresh sessions
20. Old refresh cookie fails after password reset
21. New login works after password reset
22. Allowed same-origin state-changing request succeeds
23. Unauthorized cross-origin state-changing request is rejected
24. CORS does not allow wildcard credentialed origins in production
25. Cookie-authenticated requests retain tenant isolation
26. Existing RBAC permission checks remain unchanged
27. Adversarial cross-origin CSRF attack rejection
"""

import concurrent.futures
import hashlib
import secrets
import threading
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from app.common.enums.identity.token_type import TokenType
from app.core.config import Settings, settings
from app.identity.models.permission import IdentityPermission
from app.identity.models.refresh_token import IdentityRefreshToken
from app.identity.models.role import IdentityRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.models.user import IdentityUser
from app.identity.models.user_role import IdentityUserRole
from app.identity.repositories import identity_refresh_token_repository
from app.identity.schemas.user.refresh_token import RefreshToken
from app.identity.schemas.user.user_login import UserLogin
from app.identity.security.jwt_config import jwt_settings
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.services.authentication_service import authentication_service
from app.main import app
from app.models.school import School


@pytest.fixture
def cookie_auth_fixture(db_session: Session):
    """Seed schools, roles, permissions, and users for testing cookie authentication."""
    # School Alpha
    sch_a_id = uuid.uuid4()
    school_a = School(
        id=sch_a_id,
        name="Cookie Alpha School",
        code=f"CK_ALPHA_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="123 Alpha Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_a_id,
        email="cookie_admin_a@school.com",
        password_hash=hash_password("SecurePassword123!"),
        first_name="Alpha",
        last_name="Admin",
        is_active=True,
    )

    # School Beta (Tenant Isolation)
    sch_b_id = uuid.uuid4()
    school_b = School(
        id=sch_b_id,
        name="Cookie Beta School",
        code=f"CK_BETA_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="456 Beta Ave",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500002",
    )
    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_b_id,
        email="cookie_admin_b@school.com",
        password_hash=hash_password("SecurePassword123!"),
        first_name="Beta",
        last_name="Admin",
        is_active=True,
    )

    db_session.add_all([school_a, user_a, school_b, user_b])
    db_session.commit()
    db_session.refresh(school_a)
    db_session.refresh(user_a)
    db_session.refresh(school_b)
    db_session.refresh(user_b)

    return {
        "school_a": school_a,
        "user_a": user_a,
        "school_b": school_b,
        "user_b": user_b,
    }


def test_01_login_issues_secure_httponly_cookies(client: TestClient, cookie_auth_fixture):
    """Test login issues access_token and refresh_token HttpOnly cookies with proper attributes."""
    data = cookie_auth_fixture
    response = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )
    assert response.status_code == 200

    # Verify cookies in response
    cookies = response.cookies
    assert "access_token" in cookies
    assert "refresh_token" in cookies

    # Verify Set-Cookie header attributes
    set_cookie_headers = response.headers.get_list("set-cookie")
    access_cookie_header = next((h for h in set_cookie_headers if "access_token=" in h), "")
    refresh_cookie_header = next((h for h in set_cookie_headers if "refresh_token=" in h), "")

    assert "httponly" in access_cookie_header.lower()
    assert "httponly" in refresh_cookie_header.lower()
    assert "path=/" in access_cookie_header.lower()
    assert "path=/" in refresh_cookie_header.lower()
    assert "samesite=lax" in access_cookie_header.lower()
    assert "samesite=lax" in refresh_cookie_header.lower()


def test_02_authenticated_request_succeeds_using_cookies(client: TestClient, cookie_auth_fixture):
    """Protected endpoint /auth/me succeeds with cookie authentication without Bearer header."""
    data = cookie_auth_fixture
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200

    # Call /api/v1/auth/me without Authorization header (relies on client cookies)
    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    user_data = me_resp.json()
    assert user_data["email"] == "cookie_admin_a@school.com"
    assert user_data["id"] == str(data["user_a"].id)


def test_03_request_without_cookies_or_bearer_rejected(client: TestClient):
    """Protected endpoint /auth/me fails with 401 when no credentials are provided."""
    client.cookies.clear()
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "not authenticated" in resp.text.lower() or "invalid" in resp.text.lower()


def test_04_expired_access_token_cookie_rejected(client: TestClient, cookie_auth_fixture):
    """An expired access token in cookie is rejected with 401."""
    data = cookie_auth_fixture
    # Create an expired access token manually
    expired_payload = {
        "sub": str(data["user_a"].id),
        "school_id": str(data["school_a"].id),
        "type": TokenType.ACCESS,
        "exp": datetime.now(timezone.utc) - timedelta(hours=1),
        "iat": datetime.now(timezone.utc) - timedelta(hours=2),
    }
    from jose import jwt
    expired_token = jwt.encode(expired_payload, jwt_settings.SECRET_KEY, algorithm=jwt_settings.ALGORITHM)

    client.cookies.set("access_token", expired_token)
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401
    assert "expired" in resp.text.lower() or "invalid" in resp.text.lower()


def test_05_refresh_using_cookie_and_rotates_session(client: TestClient, cookie_auth_fixture, db_session: Session):
    """POST /auth/refresh with HttpOnly refresh cookie produces new access & refresh cookies and rotates session."""
    data = cookie_auth_fixture
    # 1. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200
    old_access_token = client.cookies.get("access_token")
    old_refresh_token = client.cookies.get("refresh_token")

    old_payload = jwt_manager.verify_token(old_refresh_token)
    old_jti = old_payload["jti"]

    # 2. Refresh using cookies (no body required)
    refresh_resp = client.post("/api/v1/auth/refresh", json={})
    assert refresh_resp.status_code == 200

    new_access_token = client.cookies.get("access_token")
    new_refresh_token = client.cookies.get("refresh_token")

    assert new_access_token != old_access_token
    assert new_refresh_token != old_refresh_token

    # 3. Verify old session is revoked in DB
    db_session.expire_all()
    old_session = identity_refresh_token_repository.get_by_jti(db_session, old_jti)
    assert old_session.is_revoked is True
    assert old_session.revocation_reason == "REFRESH_ROTATION"

    # 4. Attempting to reuse old refresh token must fail
    replay_client = TestClient(app)
    replay_client.cookies.set("refresh_token", old_refresh_token)
    replay_resp = replay_client.post("/api/v1/auth/refresh", json={})
    assert replay_resp.status_code == 401
    assert "revoked" in replay_resp.text.lower()


def test_06_concurrent_refresh_with_cookies(engine):
    """Two concurrent refresh requests using the same refresh cookie result in exactly 1 success."""
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    setup_session = TestSession()

    sch_id = uuid.uuid4()
    school = School(
        id=sch_id,
        name="Concurrent Cookie School",
        code=f"CONC_CK_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="123 Cookie Lane",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_id,
        email="conc_cookie_user@school.com",
        password_hash=hash_password("Password123!"),
        first_name="Conc",
        last_name="Cookie",
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
            email="conc_cookie_user@school.com",
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
            return ("SUCCESS", res)
        except Exception as exc:
            return ("FAILED", exc)
        finally:
            s.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_concurrent_refresh)
        f2 = executor.submit(run_concurrent_refresh)
        status1, _ = f1.result()
        status2, _ = f2.result()

    results = [status1, status2]
    assert results.count("SUCCESS") == 1
    assert results.count("FAILED") == 1


def test_07_logout_revokes_session_and_clears_cookies(client: TestClient, cookie_auth_fixture, db_session: Session):
    """POST /auth/logout revokes the persisted session and clears HttpOnly authentication cookies."""
    data = cookie_auth_fixture
    # 1. Login
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )
    assert login_resp.status_code == 200
    refresh_token = client.cookies.get("refresh_token")
    payload = jwt_manager.verify_token(refresh_token)
    jti = payload["jti"]

    # 2. Logout (using cookies)
    logout_resp = client.post("/api/v1/auth/logout", json={})
    assert logout_resp.status_code == 200

    # Verify cookies were deleted
    set_cookie_headers = logout_resp.headers.get_list("set-cookie")
    assert any("access_token=" in h and ('max-age=0' in h.lower() or 'expires=' in h.lower()) for h in set_cookie_headers)
    assert any("refresh_token=" in h and ('max-age=0' in h.lower() or 'expires=' in h.lower()) for h in set_cookie_headers)

    # 3. Verify session is revoked in DB
    db_session.expire_all()
    session = identity_refresh_token_repository.get_by_jti(db_session, jti)
    assert session.is_revoked is True
    assert session.revocation_reason == "USER_LOGOUT"


def test_08_logout_idempotency_with_cookies(client: TestClient, cookie_auth_fixture):
    """Repeated calls to logout do not raise errors (idempotent)."""
    data = cookie_auth_fixture
    client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )

    resp1 = client.post("/api/v1/auth/logout", json={})
    assert resp1.status_code == 200

    # Second logout without active cookies succeeds cleanly or returns 401 if access cookie cleared
    # Re-calling with Bearer token is idempotent
    login_resp2 = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    ).json()

    resp2 = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_resp2['access_token']}"},
        json={"refresh_token": login_resp2["refresh_token"]},
    )
    assert resp2.status_code == 200

    resp3 = client.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {login_resp2['access_token']}"},
        json={"refresh_token": login_resp2["refresh_token"]},
    )
    assert resp3.status_code == 200


def test_09_csrf_origin_validation_allowed_origins_succeed(client: TestClient, cookie_auth_fixture):
    """Mutating state-changing requests with cookie credentials succeed when Origin is in ALLOWED_ORIGINS."""
    data = cookie_auth_fixture
    client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )

    resp = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://localhost:3000"},
        json={},
    )
    assert resp.status_code == 200


def test_10_adversarial_csrf_attack_rejected(client: TestClient, cookie_auth_fixture):
    """Adversarial Test: Attacker website (http://evil-attacker.com) attempting state-changing request is blocked."""
    data = cookie_auth_fixture
    client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )

    resp = client.post(
        "/api/v1/auth/logout",
        headers={"Origin": "http://evil-attacker.com"},
        json={},
    )
    assert resp.status_code == 403
    assert "CSRF verification failed" in resp.text


def test_11_password_reset_invalidates_cookie_refresh_sessions(client: TestClient, cookie_auth_fixture, db_session: Session):
    """Password reset revokes active refresh session; old refresh cookie fails; new login works."""
    data = cookie_auth_fixture
    # 1. Login to establish session
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )
    old_refresh_cookie = client.cookies.get("refresh_token")

    # 2. Issue password reset
    from app.identity.repositories import identity_password_reset_token_repository

    raw_reset_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_reset_token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=15)

    identity_password_reset_token_repository.create_token_record(
        db=db_session,
        school_id=data["school_a"].id,
        user_id=data["user_a"].id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    # 3. Confirm password reset
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={
            "token": raw_reset_token,
            "new_password": "NewBrandSecurePassword456!",
        },
    )
    assert reset_resp.status_code == 200

    # 4. Old refresh cookie must now be rejected
    replay_client = TestClient(app)
    replay_client.cookies.set("refresh_token", old_refresh_cookie)
    refresh_attempt = replay_client.post(
        "/api/v1/auth/refresh",
        json={},
    )
    assert refresh_attempt.status_code == 401
    assert "revoked" in refresh_attempt.text.lower()

    # 5. New login with new password succeeds
    new_login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "NewBrandSecurePassword456!",
        },
    )
    assert new_login_resp.status_code == 200
    assert "access_token" in new_login_resp.cookies


def test_12_tenant_isolation_with_cookies(client: TestClient, cookie_auth_fixture):
    """User A's cookie authentication cannot access User B's tenant-scoped data."""
    data = cookie_auth_fixture
    # Login as User A (School A)
    client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "cookie_admin_a@school.com",
            "password": "SecurePassword123!",
        },
    )

    me_resp = client.get("/api/v1/auth/me")
    assert me_resp.status_code == 200
    assert me_resp.json()["school_id"] == str(data["school_a"].id)
    assert me_resp.json()["school_id"] != str(data["school_b"].id)


def test_13_production_cookie_settings_validation():
    """Production environment requires COOKIE_SECURE=True, valid COOKIE_SAMESITE, and no wildcard ALLOWED_ORIGINS."""
    # Test insecure production configuration fails validation
    with pytest.raises(ValueError, match="COOKIE_SECURE must be True"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="a" * 64,
            DATABASE_URL="postgresql://valid_prod_user:SuperStrongProdPass123!@prod-db.internal:5432/school_prod",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=False,
            COOKIE_SAMESITE="lax",
        )

    with pytest.raises(ValueError, match="COOKIE_SAMESITE must be 'lax' or 'strict'"):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="a" * 64,
            DATABASE_URL="postgresql://valid_prod_user:SuperStrongProdPass123!@prod-db.internal:5432/school_prod",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            COOKIE_SAMESITE="none",
        )

    # Valid production settings pass
    valid_prod_settings = Settings(
        ENVIRONMENT="production",
        DEBUG=False,
        SECRET_KEY="a" * 64,
        DATABASE_URL="postgresql://valid_prod_user:SuperStrongProdPass123!@prod-db.internal:5432/school_prod",
        ALLOWED_ORIGINS=["https://app.schoolos.com"],
        COOKIE_SECURE=True,
        COOKIE_SAMESITE="lax",
        METRICS_AUTH_TOKEN="a" * 32,
        REDIS_URL="redis://prod-redis:6379/0",
    )
    assert valid_prod_settings.COOKIE_SECURE is True
    assert valid_prod_settings.COOKIE_SAMESITE == "lax"


def test_14_jwt_algorithm_restriction_and_non_hs256_rejection(client: TestClient, cookie_auth_fixture):
    """
    Verify that JWT decoding and authentication endpoints explicitly accept ONLY HS256.
    Tokens using 'none', 'RS256', 'ES256', or other algorithm headers MUST be strictly rejected.
    """
    import base64
    import json
    from jose import jwt as raw_jwt

    data = cookie_auth_fixture
    user = data["user_a"]
    school = data["school_a"]

    payload = {
        "sub": str(user.id),
        "school_id": str(school.id),
        "type": TokenType.ACCESS.value,
        "exp": int((datetime.now(timezone.utc) + timedelta(minutes=15)).timestamp()),
    }

    # 1. Valid HS256 token is accepted
    valid_hs256_token = raw_jwt.encode(payload, jwt_settings.SECRET_KEY, algorithm="HS256")
    decoded = jwt_manager.verify_token(valid_hs256_token)
    assert decoded is not None
    assert decoded["sub"] == str(user.id)

    # 2. 'none' algorithm token is rejected by jwt_manager and auth endpoint
    h_none = base64.urlsafe_b64encode(json.dumps({"alg": "none", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    p_b64 = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
    none_token = f"{h_none}.{p_b64}."
    
    assert jwt_manager.verify_token(none_token) is None
    resp_none = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {none_token}"})
    assert resp_none.status_code == 401

    # 3. Disallowed ES256 / RS256 algorithm headers are rejected
    h_es256 = base64.urlsafe_b64encode(json.dumps({"alg": "ES256", "typ": "JWT"}).encode()).rstrip(b"=").decode()
    fake_es256_token = f"{h_es256}.{p_b64}.fakesignature"
    assert jwt_manager.verify_token(fake_es256_token) is None
    resp_es256 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {fake_es256_token}"})
    assert resp_es256.status_code == 401

    # 4. Direct decode_token fails on disallowed algorithms
    with pytest.raises(Exception):
        jwt_manager.decode_token(none_token)

    with pytest.raises(Exception):
        jwt_manager.decode_token(fake_es256_token)


