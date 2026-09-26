"""
Phase G — Production-Grade Distributed Rate Limiting & Redis Enforcement Security Test Suite.

Tests:
1. Production configuration enforcement (missing/insecure REDIS_URL rejected).
2. Development/test clean in-memory fallback when Redis is unconfigured.
3. Multi-instance distributed rate limiting (Instance A & B sharing same Redis backend).
4. Concurrent race condition testing with atomic sliding window transactions.
5. Fail-closed behavior in production on Redis outage (no silent in-memory fallback).
6. Graceful in-memory fallback in development environment on Redis outage.
7. Tenant & IP address isolation across distinct rate limit keys.
8. Anti-spoofing IP extraction when TRUST_PROXY is disabled.
9. End-to-end FastAPI login rate limiting with Redis backend.
10. End-to-end FastAPI password-reset rate limiting with Redis backend.
11. Successful authentication resets Redis rate limit bucket.
12. Redis connection pool reuse and clean lifecycle management.
"""

import concurrent.futures
from unittest.mock import MagicMock, patch
from uuid import uuid4

import fakeredis
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.common.enums.school import SchoolStatus
from app.common.security.rate_limiter import (
    InMemoryRateLimiter,
    RateLimiterService,
    enforce_login_rate_limit,
    enforce_password_reset_rate_limit,
    get_client_ip,
    rate_limiter,
)
from app.core.config import Settings, settings
from app.identity.models.user import IdentityUser
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.main import app
from app.models.school import School


@pytest.fixture
def fake_redis_server():
    """Create a shared in-memory FakeServer simulating a central Redis instance."""
    server = fakeredis.FakeServer()
    yield server


@pytest.fixture
def fake_redis_client(fake_redis_server):
    """Create a fakeredis client connected to the fake server."""
    client = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)
    yield client
    client.flushall()


@pytest.fixture
def setup_auth_data(db_session: Session):
    """Seed test school and test user for end-to-end auth rate limit tests."""
    seed_identity(db_session)
    uid = uuid4().hex[:6]
    school = School(
        name=f"Distributed Rate Limit School {uid}",
        code=f"DRL_{uid}",
        address_line1="100 Tech Blvd",
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
        email=f"dist_user_{uid}@school.edu",
        password_hash=hash_password("Password123!"),
        first_name="Distributed",
        last_name="Tester",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(user)
    db_session.commit()
    return school, user


# ----------------------------------------------------------------------
# 1. Configuration Hardening Tests
# ----------------------------------------------------------------------

def test_01_production_config_requires_redis_url():
    """Settings must raise ValidationError in production if REDIS_URL is missing or empty."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
            REDIS_URL=None,
        )
    assert "REDIS_URL must be configured" in str(exc_info.value)


def test_02_production_config_rejects_insecure_redis_url():
    """Settings must raise ValidationError in production if REDIS_URL has invalid scheme or placeholder."""
    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
            REDIS_URL="redis://user:change_me@redis:6379/0",
        )
    assert "REDIS_URL contains default/placeholder credentials" in str(exc_info.value)

    with pytest.raises(ValidationError) as exc_info:
        Settings(
            APP_NAME="AI School OS",
            ENVIRONMENT="production",
            DEBUG=False,
            DATABASE_URL="postgresql://produser:ProdPass987%21@dbserver:5432/school_prod",
            SECRET_KEY="a_very_secure_and_random_production_secret_key_1234567890",
            ALLOWED_ORIGINS=["https://app.schoolos.com"],
            COOKIE_SECURE=True,
            METRICS_AUTH_TOKEN="a_very_secure_and_random_metrics_token_1234567890",
            REDIS_URL="http://redis:6379/0",
        )
    assert "REDIS_URL must be a valid redis://" in str(exc_info.value)


def test_03_development_fallback_to_in_memory_when_redis_unconfigured(monkeypatch):
    """In development/test, limiter falls back cleanly to InMemoryRateLimiter when REDIS_URL is None."""
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")
    monkeypatch.setattr(settings, "REDIS_URL", None)

    service = RateLimiterService()
    assert service._get_redis_client() is None

    # Operations work via in-memory store
    is_limited, retry = service.check_rate_limit("dev_client_1", limit=3, window_seconds=60)
    assert not is_limited
    assert retry == 0

    service.record_failure("dev_client_1", window_seconds=60)
    service.record_failure("dev_client_1", window_seconds=60)
    service.record_failure("dev_client_1", window_seconds=60)

    is_limited_now, retry_now = service.check_rate_limit("dev_client_1", limit=3, window_seconds=60)
    assert is_limited_now is True
    assert retry_now > 0


# ----------------------------------------------------------------------
# 2. Multi-Instance & Distributed Rate Limiting Tests
# ----------------------------------------------------------------------

def test_04_multi_instance_shared_redis_rate_limiting(fake_redis_server):
    """
    Simulate two separate application instances (Instance A and Instance B)
    connected to the same Redis cluster. Verify that attempts on Instance A
    immediately enforce rate limiting on Instance B.
    """
    client_a = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)
    client_b = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)

    instance_a = RateLimiterService(redis_client=client_a)
    instance_b = RateLimiterService(redis_client=client_b)

    ip = "198.51.100.42"
    limit = 3
    window = 60

    # 1. Initially both instances see 0 attempts
    is_lim_a, _ = instance_a.check_rate_limit(ip, limit=limit, window_seconds=window)
    is_lim_b, _ = instance_b.check_rate_limit(ip, limit=limit, window_seconds=window)
    assert not is_lim_a
    assert not is_lim_b

    # 2. Instance A records 2 failed attempts
    instance_a.record_failure(ip, window_seconds=window)
    instance_a.record_failure(ip, window_seconds=window)

    # 3. Instance B records the 3rd failed attempt
    instance_b.record_failure(ip, window_seconds=window)

    # 4. Now both Instance A and Instance B see the client as rate limited
    is_lim_a2, retry_a = instance_a.check_rate_limit(ip, limit=limit, window_seconds=window)
    is_lim_b2, retry_b = instance_b.check_rate_limit(ip, limit=limit, window_seconds=window)
    assert is_lim_a2 is True
    assert is_lim_b2 is True
    assert retry_a > 0
    assert retry_b > 0

    # 5. Instance A resets attempts (e.g. following successful authentication)
    instance_a.reset_attempts(ip)

    # 6. Instance B immediately sees the rate limit cleared
    is_lim_b3, _ = instance_b.check_rate_limit(ip, limit=limit, window_seconds=window)
    assert is_lim_b3 is False


# ----------------------------------------------------------------------
# 3. Concurrency & Atomic Security Decision Verification
# ----------------------------------------------------------------------

def test_05_concurrent_rate_limiting_atomic_security_decision(fake_redis_server):
    """
    Race Condition / Security Decision Atomicity Test:
    Configured limit = 5.
    Launch 25 concurrent requests simultaneously hitting the atomic acquire() method.
    Verify that EXACTLY 5 requests are permitted and the remaining 20 are REJECTED.
    """
    client = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)
    service = RateLimiterService(redis_client=client)

    test_ip = "203.0.113.88"
    limit = 5
    window = 60
    total_threads = 25

    results = []

    def acquire_worker():
        is_limited, retry_after = service.acquire(test_ip, limit=limit, window_seconds=window)
        results.append((is_limited, retry_after))

    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(acquire_worker) for _ in range(total_threads)]
        concurrent.futures.wait(futures)

    allowed_count = sum(1 for is_lim, _ in results if not is_lim)
    blocked_count = sum(1 for is_lim, _ in results if is_lim)

    assert allowed_count == limit, f"Expected exactly {limit} allowed requests, but got {allowed_count}"
    assert blocked_count == total_threads - limit, f"Expected {total_threads - limit} blocked requests, but got {blocked_count}"
    assert client.zcard(f"rate_limit:{test_ip}") == limit


def test_05b_multi_instance_concurrent_race_prevention(fake_redis_server):
    """
    Multi-Instance Concurrency Test:
    Instance A and Instance B both connect to the same Redis backend.
    20 concurrent threads randomly distribute calls across Instance A and Instance B.
    Verify that across both instances, EXACTLY 5 requests pass the security decision.
    """
    client_a = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)
    client_b = fakeredis.FakeRedis(server=fake_redis_server, decode_responses=True)

    instance_a = RateLimiterService(redis_client=client_a)
    instance_b = RateLimiterService(redis_client=client_b)

    test_ip = "198.51.100.77"
    limit = 5
    window = 60
    total_threads = 20

    results = []

    def multi_worker(idx: int):
        target_instance = instance_a if idx % 2 == 0 else instance_b
        is_limited, retry_after = target_instance.acquire(test_ip, limit=limit, window_seconds=window)
        results.append((is_limited, retry_after))

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(multi_worker, i) for i in range(total_threads)]
        concurrent.futures.wait(futures)

    allowed_count = sum(1 for is_lim, _ in results if not is_lim)
    blocked_count = sum(1 for is_lim, _ in results if is_lim)

    assert allowed_count == limit
    assert blocked_count == total_threads - limit
    assert client_a.zcard(f"rate_limit:{test_ip}") == limit


# ----------------------------------------------------------------------
# 4. Production Fail-Closed Behavior on Redis Outage
# ----------------------------------------------------------------------

def test_06_redis_outage_in_production_fails_closed(monkeypatch):
    """
    In production (ENVIRONMENT=production), if Redis is unreachable or encounters an error,
    check_rate_limit MUST fail closed (return is_limited=True) and NEVER silently switch to in-memory.
    """
    monkeypatch.setattr(settings, "ENVIRONMENT", "production")
    monkeypatch.setattr(settings, "REDIS_URL", "redis://fake.redis.server:6379/0")

    # Mock redis client that raises ConnectionError on eval/pipeline
    broken_client = MagicMock()
    broken_client.eval.side_effect = Exception("Redis connection timed out")
    broken_pipe = MagicMock()
    broken_pipe.execute.side_effect = Exception("Redis connection timed out")
    broken_client.pipeline.return_value = broken_pipe

    service = RateLimiterService(redis_client=broken_client)
    assert service.is_production() is True

    # check_rate_limit must fail closed (is_limited=True)
    is_limited, retry_after = service.check_rate_limit("attacker_ip", limit=5, window_seconds=60)
    assert is_limited is True
    assert retry_after == 60

    # In-memory limiter must NOT have been used or populated
    assert "rate_limit:attacker_ip" not in service.memory_limiter._attempts


def test_07_redis_outage_in_development_falls_back_cleanly(monkeypatch):
    """
    In development (ENVIRONMENT=development), Redis error falls back cleanly to in-memory store.
    """
    monkeypatch.setattr(settings, "ENVIRONMENT", "development")

    broken_client = MagicMock()
    broken_pipe = MagicMock()
    broken_pipe.execute.side_effect = Exception("Local dev Redis offline")
    broken_client.pipeline.return_value = broken_pipe

    service = RateLimiterService(redis_client=broken_client)
    assert service.is_production() is False

    is_limited, _ = service.check_rate_limit("dev_ip", limit=5, window_seconds=60)
    assert is_limited is False


# ----------------------------------------------------------------------
# 5. Tenant & IP Address Isolation Tests
# ----------------------------------------------------------------------

def test_08_tenant_and_ip_isolation(fake_redis_client):
    """Ensure different IP addresses and endpoints do not share rate limit buckets."""
    service = RateLimiterService(redis_client=fake_redis_client)

    ip_1 = "10.0.0.1"
    ip_2 = "10.0.0.2"

    # Exhaust limit for ip_1
    for _ in range(5):
        service.record_failure(ip_1, window_seconds=60)

    # ip_1 is limited
    is_lim_1, _ = service.check_rate_limit(ip_1, limit=5, window_seconds=60)
    assert is_lim_1 is True

    # ip_2 is NOT limited
    is_lim_2, _ = service.check_rate_limit(ip_2, limit=5, window_seconds=60)
    assert is_lim_2 is False

    # Password reset bucket for ip_1 is distinct from login bucket for ip_1
    pwd_reset_key = f"pwd_reset:{ip_1}"
    is_pwd_lim, _ = service.check_rate_limit(pwd_reset_key, limit=5, window_seconds=300)
    assert is_pwd_lim is False


def test_09_anti_spoofing_ip_extraction(monkeypatch):
    """When TRUST_PROXY is False, X-Forwarded-For is ignored and client.host is used."""
    monkeypatch.setattr(settings, "TRUST_PROXY", False)

    request = MagicMock(spec=Request)
    request.headers = {"X-Forwarded-For": "203.0.113.195, 10.0.0.1"}
    request.client.host = "192.168.1.50"

    extracted_ip = get_client_ip(request)
    assert extracted_ip == "192.168.1.50"


# ----------------------------------------------------------------------
# 6. End-to-End Route Integration Tests with Redis
# ----------------------------------------------------------------------

def test_10_e2e_login_rate_limiting_with_redis(client: TestClient, setup_auth_data, fake_redis_client, monkeypatch):
    """End-to-end test: POST /api/v1/auth/login triggers HTTP 429 when Redis counter hits limit."""
    monkeypatch.setattr(settings, "TRUST_PROXY", True)
    # Inject fake_redis_client into global rate_limiter singleton
    monkeypatch.setattr(rate_limiter, "_redis_client", fake_redis_client)
    rate_limiter.clear_all()

    school, user = setup_auth_data
    target_ip = "198.51.100.99"
    headers = {"X-Forwarded-For": target_ip}

    payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword123!",
    }

    # Perform 5 failed login attempts
    for i in range(5):
        resp = client.post("/api/v1/auth/login", json=payload, headers=headers)
        assert resp.status_code in (400, 401)

    # 6th attempt should be blocked with 429 Too Many Requests
    blocked_resp = client.post("/api/v1/auth/login", json=payload, headers=headers)
    assert blocked_resp.status_code == 429
    assert "Retry-After" in blocked_resp.headers or "retry-after" in blocked_resp.headers
    assert "TOO_MANY_REQUESTS" in blocked_resp.text or "Too many failed login attempts" in blocked_resp.text


def test_11_e2e_password_reset_rate_limiting_with_redis(client: TestClient, fake_redis_client, monkeypatch):
    """End-to-end test: POST /api/v1/auth/forgot-password triggers HTTP 429 with Redis backend."""
    monkeypatch.setattr(settings, "TRUST_PROXY", True)
    monkeypatch.setattr(rate_limiter, "_redis_client", fake_redis_client)
    rate_limiter.clear_all()

    target_ip = "198.51.100.100"
    headers = {"X-Forwarded-For": target_ip}
    payload = {"email": "someone@example.com"}

    limit = settings.PASSWORD_RESET_RATE_LIMIT

    for _ in range(limit):
        resp = client.post("/api/v1/auth/forgot-password", json=payload, headers=headers)
        assert resp.status_code == 200

    # Next attempt triggers 429
    blocked_resp = client.post("/api/v1/auth/forgot-password", json=payload, headers=headers)
    assert blocked_resp.status_code == 429
    assert "Retry-After" in blocked_resp.headers or "retry-after" in blocked_resp.headers
    assert "TOO_MANY_REQUESTS" in blocked_resp.text or "Too many password reset requests" in blocked_resp.text


def test_12_successful_login_resets_redis_attempts(client: TestClient, setup_auth_data, fake_redis_client, monkeypatch):
    """Successful login resets the failure counter in Redis."""
    monkeypatch.setattr(settings, "TRUST_PROXY", True)
    monkeypatch.setattr(rate_limiter, "_redis_client", fake_redis_client)
    rate_limiter.clear_all()

    school, user = setup_auth_data
    target_ip = "198.51.100.101"
    headers = {"X-Forwarded-For": target_ip}

    # 3 failed attempts
    bad_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "WrongPassword!",
    }
    for _ in range(3):
        client.post("/api/v1/auth/login", json=bad_payload, headers=headers)

    assert fake_redis_client.zcard(f"rate_limit:{target_ip}") == 3

    # 1 successful login
    good_payload = {
        "school_code": school.code,
        "email": user.email,
        "password": "Password123!",
    }
    success_resp = client.post("/api/v1/auth/login", json=good_payload, headers=headers)
    assert success_resp.status_code == 200

    # Redis key deleted
    assert fake_redis_client.exists(f"rate_limit:{target_ip}") == 0


def test_13_redis_connection_pool_lifecycle():
    """Verify rate limiter ping and clean connection pool closure."""
    service = RateLimiterService()
    assert service.ping() is False  # When unconfigured, returns False without raising

    # Test with a mock pool
    service._redis_pool = MagicMock()
    service._redis_client = MagicMock()
    service.close()
    assert service._redis_pool is None
    assert service._redis_client is None
