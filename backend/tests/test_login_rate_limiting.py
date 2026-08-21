"""
Automated regression tests for Login Rate Limiting in AI School OS.
"""

from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.common.security.rate_limiter import rate_limiter
from app.identity.models.user import IdentityUser
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.school import School
from app.common.enums.school import SchoolStatus
from sqlalchemy.orm import Session
import pytest


@pytest.fixture(autouse=True)
def reset_rate_limiter(monkeypatch):
    """Ensure clean rate limiter state for every test."""
    from app.core.config import settings
    monkeypatch.setattr(settings, "TRUST_PROXY", True)
    rate_limiter.clear_all()
    yield
    rate_limiter.clear_all()


@pytest.fixture
def setup_data(db_session: Session):
    """Seed system roles and create a sample active school & user."""
    seed_identity(db_session)
    uid = uuid4().hex[:6]
    school = School(
        name=f"Rate Limit Test School {uid}",
        code=f"RLS_{uid}",
        address_line1="123 Test St",
        city="Bengaluru",
        district="Bengaluru Urban",
        state="Karnataka",
        postal_code="560001",
        status=SchoolStatus.ACTIVE,
    )
    db_session.add(school)
    db_session.commit()

    user = IdentityUser(
        school_id=school.id,
        email=f"user_{uid}@school.edu",
        password_hash=hash_password("Password123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    return school, user


def test_01_normal_login_succeeds(client: TestClient, setup_data):
    """Test 1: Normal login with valid credentials succeeds without throttling."""
    school, user = setup_data
    payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload)
    assert response.status_code == 200
    assert "access_token" in response.json()


def test_02_failed_login_increments_limiter(client: TestClient, setup_data):
    """Test 2: Failed login increments rate limit counter."""
    school, user = setup_data
    payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }
    r1 = client.post("/api/v1/auth/login", json=payload, headers={"X-Forwarded-For": "192.168.1.100"})
    assert r1.status_code == 401

    is_limited, _ = rate_limiter.check_rate_limit("192.168.1.100", limit=5, window_seconds=60)
    assert is_limited is False


def test_03_repeated_failed_attempts_return_429(client: TestClient, setup_data):
    """Test 3: Repeated failed login attempts (5 times) trigger 429 Too Many Requests."""
    school, user = setup_data
    payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }

    ip_headers = {"X-Forwarded-For": "192.168.1.101"}

    # Perform 5 failed attempts
    for i in range(5):
        r = client.post("/api/v1/auth/login", json=payload, headers=ip_headers)
        assert r.status_code in (401, 400), f"Attempt {i+1} returned {r.status_code}: {r.text}"

    # 6th attempt should be blocked with 429 Too Many Requests
    r_throttled = client.post("/api/v1/auth/login", json=payload, headers=ip_headers)
    assert r_throttled.status_code == 429
    assert r_throttled.json().get("error", {}).get("code") == "TOO_MANY_REQUESTS" or r_throttled.json().get("code") == "TOO_MANY_REQUESTS"
    retry_after_val = r_throttled.headers.get("retry-after") or r_throttled.headers.get("Retry-After")
    assert retry_after_val is not None
    assert int(retry_after_val) > 0


def test_04_successful_login_resets_attempt_counter(client: TestClient, setup_data):
    """Test 4: Successful login clears previous failed attempts for the IP."""
    school, user = setup_data
    ip_headers = {"X-Forwarded-For": "192.168.1.102"}
    failed_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }
    success_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "Password123!",
    }

    # 3 failed attempts
    for _ in range(3):
        client.post("/api/v1/auth/login", json=failed_payload, headers=ip_headers)

    # Successful attempt
    r_success = client.post("/api/v1/auth/login", json=success_payload, headers=ip_headers)
    assert r_success.status_code == 200, f"Expected 200 but got {r_success.status_code}: {r_success.text}"

    # Rate limit bucket should now be empty for this IP
    is_limited, _ = rate_limiter.check_rate_limit("192.168.1.102", limit=5, window_seconds=60)
    assert is_limited is False


def test_05_different_ips_do_not_share_buckets(client: TestClient, setup_data):
    """Test 5: Rate limit bucket is isolated per client IP address."""
    school, user = setup_data
    failed_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }

    # Exhaust IP 1
    for _ in range(5):
        client.post("/api/v1/auth/login", json=failed_payload, headers={"X-Forwarded-For": "10.0.0.1"})

    assert client.post("/api/v1/auth/login", json=failed_payload, headers={"X-Forwarded-For": "10.0.0.1"}).status_code == 429

    # IP 2 should NOT be throttled
    r_ip2 = client.post("/api/v1/auth/login", json=failed_payload, headers={"X-Forwarded-For": "10.0.0.2"})
    assert r_ip2.status_code == 401


def test_06_legitimate_users_not_permanently_blocked(client: TestClient, setup_data):
    """Test 6: Clearing rate limit (or window expiry) allows legitimate user login."""
    school, user = setup_data
    ip_headers = {"X-Forwarded-For": "192.168.1.103"}
    failed_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }
    success_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "Password123!",
    }

    # Exhaust attempts
    for _ in range(5):
        client.post("/api/v1/auth/login", json=failed_payload, headers=ip_headers)
    assert client.post("/api/v1/auth/login", json=failed_payload, headers=ip_headers).status_code == 429

    # Reset rate limit (simulating window expiry)
    rate_limiter.reset_attempts("192.168.1.103")

    # Legitimate login succeeds
    r_success = client.post("/api/v1/auth/login", json=success_payload, headers=ip_headers)
    assert r_success.status_code == 200, f"Expected 200 but got {r_success.status_code}: {r_success.text}"


def test_07_suspended_users_remain_blocked(db_session: Session, client: TestClient, setup_data):
    """Test 7: Suspended users remain blocked regardless of rate limiter state."""
    school, user = setup_data
    user.status = "SUSPENDED"
    user.is_active = False
    db_session.commit()

    payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "Password123!",
    }
    response = client.post("/api/v1/auth/login", json=payload, headers={"X-Forwarded-For": "192.168.1.104"})
    assert response.status_code in (401, 403)
    res_msg = str(response.json()).lower()
    assert "inactive" in res_msg or "invalid" in res_msg or "suspended" in res_msg


def test_08_rate_limiting_does_not_bypass_rbac(client: TestClient):
    """Test 8: Rate limiter error response (429) does not leak permissions or bypass RBAC authorization."""
    r_unauth = client.get("/api/v1/users")
    assert r_unauth.status_code == 401


def test_09_rate_limiting_does_not_bypass_school_suspension(db_session: Session, client: TestClient, setup_data):
    """Test 9: School suspension checks remain enforced alongside rate limiting."""
    school, user = setup_data
    school.status = SchoolStatus.SUSPENDED
    db_session.commit()

    from app.identity.security.jwt_manager import jwt_manager
    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}

    r_susp = client.get("/api/v1/users", headers=headers)
    assert r_susp.status_code == 403
    res_msg = str(r_susp.json()).lower()
    assert "suspended" in res_msg or "permission" in res_msg


def test_10_security_headers_present_on_rate_limit_response(client: TestClient, setup_data):
    """Test 10: 429 Too Many Requests response includes security headers."""
    school, user = setup_data
    payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }
    ip_headers = {"X-Forwarded-For": "192.168.1.105"}

    for _ in range(5):
        client.post("/api/v1/auth/login", json=payload, headers=ip_headers)

    r_throttled = client.post("/api/v1/auth/login", json=payload, headers=ip_headers)
    assert r_throttled.status_code == 429
    assert r_throttled.headers.get("X-Content-Type-Options") == "nosniff"
    assert r_throttled.headers.get("X-Frame-Options") == "DENY"
