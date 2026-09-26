"""
Tests for Phase C: Password Reset & Account Recovery Workflow
Covers:
- Forgot-password anti-enumeration (generic response for existing, non-existing, inactive, invalid school, ambiguous multi-school)
- Cryptographic token generation & SHA-256 hashed storage
- Delivery service capturing raw token & email
- Password reset validation & single-use invalidation
- Invalidation of all existing active refresh sessions upon successful reset
- Subsequent login verification (new password accepted, old password rejected, old refresh tokens unusable)
- Expiration and malformed/invalid token rejection
- Rate limiting enforcement on forgot-password endpoint
- Concurrency race condition protection on single-use reset token
- Cross-tenant isolation and tampering protection
"""

import hashlib
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.orm import Session

from app.core.config import settings
from app.identity.models.password_reset_token import IdentityPasswordResetToken
from app.identity.models.refresh_token import IdentityRefreshToken
from app.identity.models.user import IdentityUser
from app.identity.repositories import (
    identity_password_reset_token_repository,
    identity_refresh_token_repository,
    identity_user_repository,
)
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password, verify_password
from app.identity.services.password_reset_delivery_service import (
    password_reset_delivery_service,
)
from app.models.school import School


@pytest.fixture(autouse=True)
def clean_delivery_and_rate_limiter():
    """Clear delivery message store and rate limiter state before and after each test."""
    password_reset_delivery_service.clear()
    from app.common.security.rate_limiter import rate_limiter
    rate_limiter.clear_all()
    yield
    password_reset_delivery_service.clear()
    rate_limiter.clear_all()


@pytest.fixture
def reset_fixture_data(db_session: Session):
    """Seed schools and users for testing password reset scenarios."""
    # School A
    sch_a_id = uuid.uuid4()
    school_a = School(
        id=sch_a_id,
        name="Reset Test School A",
        code=f"RST_A_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="123 Reset Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_a_id,
        email="user_a@resettest.com",
        password_hash=hash_password("OldPassword123!"),
        first_name="Alice",
        last_name="Reset",
        is_active=True,
    )
    user_inactive = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_a_id,
        email="inactive@resettest.com",
        password_hash=hash_password("OldPassword123!"),
        first_name="Inactive",
        last_name="User",
        is_active=False,
    )

    # School B (Second tenant)
    sch_b_id = uuid.uuid4()
    school_b = School(
        id=sch_b_id,
        name="Reset Test School B",
        code=f"RST_B_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="456 Reset Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500002",
    )
    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_b_id,
        email="user_b@resettest.com",
        password_hash=hash_password("OldPassword123!"),
        first_name="Bob",
        last_name="Reset",
        is_active=True,
    )

    # Multi-tenant collision user: shared email across School A and School B
    shared_email = f"shared_{uuid.uuid4().hex[:6]}@resettest.com"
    user_shared_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_a_id,
        email=shared_email,
        password_hash=hash_password("OldPassword123!"),
        first_name="Shared",
        last_name="SchoolA",
        is_active=True,
    )
    user_shared_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=sch_b_id,
        email=shared_email,
        password_hash=hash_password("OldPassword123!"),
        first_name="Shared",
        last_name="SchoolB",
        is_active=True,
    )

    db_session.add_all([
        school_a, user_a, user_inactive,
        school_b, user_b,
        user_shared_a, user_shared_b,
    ])
    db_session.commit()

    return {
        "school_a": school_a,
        "user_a": user_a,
        "user_inactive": user_inactive,
        "school_b": school_b,
        "user_b": user_b,
        "shared_email": shared_email,
        "user_shared_a": user_shared_a,
        "user_shared_b": user_shared_b,
    }


def test_01_forgot_password_existing_user_returns_generic_success(client, reset_fixture_data):
    """POST /auth/forgot-password with valid existing email must return generic success message and dispatch token."""
    data = reset_fixture_data
    payload = {
        "email": "user_a@resettest.com",
        "school_code": data["school_a"].code,
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["success"] is True
    assert "If an account with that email exists" in res_json["message"]

    # Verify a token was dispatched
    dispatched = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")
    assert dispatched is not None
    assert len(dispatched) > 20


def test_02_forgot_password_nonexistent_user_returns_identical_generic_response(client, reset_fixture_data):
    """POST /auth/forgot-password with non-existent email returns identical generic message without dispatching token."""
    data = reset_fixture_data
    payload = {
        "email": "nonexistent_random_email@resettest.com",
        "school_code": data["school_a"].code,
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["success"] is True
    assert "If an account with that email exists" in res_json["message"]

    # Verify NO token was dispatched
    dispatched = password_reset_delivery_service.get_last_token_for_email("nonexistent_random_email@resettest.com")
    assert dispatched is None


def test_03_forgot_password_invalid_school_code_returns_identical_generic_response(client):
    """POST /auth/forgot-password with invalid school code returns identical generic message without dispatching token."""
    payload = {
        "email": "user_a@resettest.com",
        "school_code": "INVALID_NON_EXISTENT_SCHOOL_CODE",
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["success"] is True
    assert "If an account with that email exists" in res_json["message"]

    dispatched = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")
    assert dispatched is None


def test_04_forgot_password_inactive_user_returns_identical_generic_response(client, reset_fixture_data):
    """POST /auth/forgot-password with inactive user returns identical generic message without dispatching token."""
    data = reset_fixture_data
    payload = {
        "email": "inactive@resettest.com",
        "school_code": data["school_a"].code,
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["success"] is True
    assert "If an account with that email exists" in res_json["message"]

    dispatched = password_reset_delivery_service.get_last_token_for_email("inactive@resettest.com")
    assert dispatched is None


def test_05_forgot_password_ambiguous_email_across_schools_returns_generic_response_without_token(
    client, reset_fixture_data
):
    """When an email exists in multiple schools and school_code is omitted, return generic success without generating a token."""
    data = reset_fixture_data
    payload = {
        "email": data["shared_email"],
        # school_code omitted -> ambiguous
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["success"] is True
    assert "If an account with that email exists" in res_json["message"]

    dispatched = password_reset_delivery_service.get_last_token_for_email(data["shared_email"])
    assert dispatched is None


def test_06_forgot_password_with_school_code_disambiguates_multi_school_user(client, reset_fixture_data):
    """When an email exists in multiple schools and school_code IS provided, correctly issue reset token for that school."""
    data = reset_fixture_data
    payload = {
        "email": data["shared_email"],
        "school_code": data["school_b"].code,
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200
    res_json = resp.json()
    assert res_json["success"] is True

    dispatched = password_reset_delivery_service.get_last_token_for_email(data["shared_email"])
    assert dispatched is not None


def test_07_forgot_password_stores_hashed_token_not_plaintext(client, db_session: Session, reset_fixture_data):
    """Verify that only the SHA-256 hash of the generated token is stored in the database."""
    data = reset_fixture_data
    payload = {
        "email": "user_a@resettest.com",
        "school_code": data["school_a"].code,
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200

    raw_token = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")
    assert raw_token is not None

    expected_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Query DB directly
    token_record = identity_password_reset_token_repository.get_by_token_hash(db_session, expected_hash)
    assert token_record is not None
    assert token_record.user_id == data["user_a"].id
    assert token_record.school_id == data["school_a"].id
    assert token_record.token_hash == expected_hash
    assert token_record.used_at is None
    # Ensure plaintext is never stored
    assert raw_token not in repr(token_record.__dict__)


def test_08_forgot_password_delivery_captures_correct_token_and_email(client, reset_fixture_data):
    """Verify the delivery service receives the accurate recipient email, raw token, and school code."""
    data = reset_fixture_data
    payload = {
        "email": "user_a@resettest.com",
        "school_code": data["school_a"].code,
    }
    resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert resp.status_code == 200

    sent = password_reset_delivery_service.get_sent_messages()
    assert len(sent) == 1
    assert sent[0]["email"] == "user_a@resettest.com"
    assert sent[0]["school_code"] == data["school_a"].code
    assert len(sent[0]["token"]) > 20


def test_09_reset_password_success_with_valid_token(client, db_session: Session, reset_fixture_data):
    """POST /auth/reset-password with a valid token successfully updates password and marks token as used."""
    data = reset_fixture_data
    # 1. Request reset
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user_a@resettest.com", "school_code": data["school_a"].code},
    )
    raw_token = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")

    # 2. Reset password
    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "BrandNewPassword123!"},
    )
    assert reset_resp.status_code == 200
    res_json = reset_resp.json()
    assert res_json["success"] is True
    assert "successfully reset" in res_json["message"]

    # 3. Verify DB state: token used_at timestamped
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
    token_record = identity_password_reset_token_repository.get_by_token_hash(db_session, token_hash)
    assert token_record.used_at is not None

    # 4. Verify password hash updated
    user = identity_user_repository.get_by_id(db_session, data["user_a"].id)
    assert verify_password("BrandNewPassword123!", user.password_hash)
    assert not verify_password("OldPassword123!", user.password_hash)


def test_10_reset_password_single_use_subsequent_attempt_rejected(client, reset_fixture_data):
    """Once a reset token is consumed, a subsequent reset attempt with the same token must fail (single-use)."""
    data = reset_fixture_data
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user_a@resettest.com", "school_code": data["school_a"].code},
    )
    raw_token = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")

    # First reset succeeds
    r1 = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPasswordOne123!"},
    )
    assert r1.status_code == 200

    # Second reset with the same token fails
    r2 = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPasswordTwo123!"},
    )
    assert r2.status_code == 400
    assert "already been used" in r2.text


def test_11_reset_password_expired_token_rejected(client, db_session: Session, reset_fixture_data):
    """An expired reset token must be rejected upon reset attempt."""
    data = reset_fixture_data
    raw_token = "custom_expired_token_xyz"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Manually insert expired token into DB
    expired_at = datetime.now(timezone.utc) - timedelta(hours=2)
    identity_password_reset_token_repository.create_token_record(
        db=db_session,
        school_id=data["school_a"].id,
        user_id=data["user_a"].id,
        token_hash=token_hash,
        expires_at=expired_at,
        commit=True,
    )

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPassword123!"},
    )
    assert resp.status_code == 400
    assert "expired" in resp.text.lower()


def test_12_reset_password_invalid_or_unknown_token_rejected(client):
    """An unknown/random reset token must be rejected with 400."""
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "completely_random_unknown_token", "new_password": "NewPassword123!"},
    )
    assert resp.status_code == 400
    assert "Invalid or expired" in resp.text


def test_13_reset_password_inactive_user_rejected(client, db_session: Session, reset_fixture_data):
    """If a user becomes inactive after token generation, reset password attempt must be rejected."""
    data = reset_fixture_data
    raw_token = "valid_token_for_now_inactive_user"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    identity_password_reset_token_repository.create_token_record(
        db=db_session,
        school_id=data["school_a"].id,
        user_id=data["user_inactive"].id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        commit=True,
    )

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPassword123!"},
    )
    assert resp.status_code == 400
    assert "inactive" in resp.text.lower()


def test_14_reset_password_deleted_user_rejected(client, db_session: Session, reset_fixture_data):
    """If a user is soft-deleted, reset password attempt must be rejected."""
    data = reset_fixture_data
    # Generate token
    raw_token = "valid_token_for_deleted_user"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    identity_password_reset_token_repository.create_token_record(
        db=db_session,
        school_id=data["school_a"].id,
        user_id=data["user_a"].id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        commit=True,
    )

    # Soft delete user
    data["user_a"].is_deleted = True
    db_session.add(data["user_a"])
    db_session.commit()

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPassword123!"},
    )
    assert resp.status_code == 400
    assert "invalid" in resp.text.lower()


def test_15_reset_password_revokes_all_active_refresh_sessions(client, db_session: Session, reset_fixture_data):
    """Password reset must revoke ALL active refresh sessions for the user."""
    data = reset_fixture_data

    # Login user_a on Device 1
    dev1_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@resettest.com",
            "password": "OldPassword123!",
        },
    ).json()
    dev1_refresh = dev1_resp["refresh_token"]
    dev1_jti = jwt_manager.decode_token(dev1_refresh)["jti"]

    # Login user_a on Device 2
    dev2_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@resettest.com",
            "password": "OldPassword123!",
        },
    ).json()
    dev2_refresh = dev2_resp["refresh_token"]
    dev2_jti = jwt_manager.decode_token(dev2_refresh)["jti"]

    # Verify both sessions are active before reset
    s1 = identity_refresh_token_repository.get_by_jti(db_session, dev1_jti)
    s2 = identity_refresh_token_repository.get_by_jti(db_session, dev2_jti)
    assert s1.is_revoked is False
    assert s2.is_revoked is False

    # Request forgot password & perform reset
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user_a@resettest.com", "school_code": data["school_a"].code},
    )
    raw_token = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")

    reset_resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "BrandNewSecretPassword123!"},
    )
    assert reset_resp.status_code == 200

    # Verify both sessions are now revoked with reason PASSWORD_RESET
    db_session.expire_all()
    s1_after = identity_refresh_token_repository.get_by_jti(db_session, dev1_jti)
    s2_after = identity_refresh_token_repository.get_by_jti(db_session, dev2_jti)
    assert s1_after.is_revoked is True
    assert s1_after.revocation_reason == "PASSWORD_RESET"
    assert s2_after.is_revoked is True
    assert s2_after.revocation_reason == "PASSWORD_RESET"

    # Verify attempting to refresh using pre-reset tokens fails
    r1 = client.post("/api/v1/auth/refresh", json={"refresh_token": dev1_refresh})
    assert r1.status_code == 401
    assert "revoked" in r1.text.lower()

    r2 = client.post("/api/v1/auth/refresh", json={"refresh_token": dev2_refresh})
    assert r2.status_code == 401
    assert "revoked" in r2.text.lower()


def test_16_reset_password_allows_login_with_new_password_and_rejects_old(client, reset_fixture_data):
    """After reset, login succeeds with new password and fails with old password."""
    data = reset_fixture_data
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user_a@resettest.com", "school_code": data["school_a"].code},
    )
    raw_token = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")

    client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewSecretPassword123!"},
    )

    # Old password fails
    fail_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@resettest.com",
            "password": "OldPassword123!",
        },
    )
    assert fail_resp.status_code == 401

    # New password succeeds
    success_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@resettest.com",
            "password": "NewSecretPassword123!",
        },
    )
    assert success_resp.status_code == 200
    assert "access_token" in success_resp.json()


def test_17_reset_password_short_password_fails_validation(client, reset_fixture_data):
    """New password shorter than 8 characters must fail schema validation (422)."""
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "some_token", "new_password": "short"},
    )
    assert resp.status_code == 422


def test_18_reset_password_empty_token_fails_validation(client):
    """Empty token must fail schema validation (422)."""
    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": "", "new_password": "ValidPassword123!"},
    )
    assert resp.status_code == 422


def test_19_forgot_password_rate_limit_enforced_by_ip(client, reset_fixture_data):
    """Exceeding rate limit on forgot-password endpoint returns 429 Too Many Requests."""
    data = reset_fixture_data
    payload = {
        "email": "user_a@resettest.com",
        "school_code": data["school_a"].code,
    }

    # Send requests up to limit (5)
    for _ in range(settings.PASSWORD_RESET_RATE_LIMIT):
        resp = client.post("/api/v1/auth/forgot-password", json=payload)
        assert resp.status_code == 200

    # 6th request must trigger 429 Too Many Requests
    excess_resp = client.post("/api/v1/auth/forgot-password", json=payload)
    assert excess_resp.status_code == 429
    assert "Too many password reset requests" in excess_resp.text
    assert "Retry-After" in excess_resp.headers


def test_20_concurrent_reset_password_single_use_race_closed(engine):
    """
    Concurrency Security Verification:
    When two concurrent requests on distinct DB sessions attempt to reset password using the SAME token:
    - Exactly ONE request must succeed (200).
    - The other request MUST fail with BadRequestException (400: already used).
    """
    import concurrent.futures
    import threading
    from sqlalchemy.orm import sessionmaker
    from app.common.exceptions import BadRequestException
    from app.identity.schemas.user.forgot_password import ForgotPassword
    from app.identity.schemas.user.reset_password import ResetPassword
    from app.identity.services.authentication_service import authentication_service

    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    # Setup test data
    setup_session = TestSession()
    sch_id = uuid.uuid4()
    school = School(
        id=sch_id,
        name="Concurrent Reset School",
        code=f"CONC_RST_{uuid.uuid4().hex[:6]}",
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
        email="concurrent_reset_user@resettest.com",
        password_hash=hash_password("InitialPassword123!"),
        first_name="Conc",
        last_name="ResetUser",
        is_active=True,
    )
    setup_session.add(school)
    setup_session.add(user)
    setup_session.commit()

    # Generate reset token
    authentication_service.forgot_password(
        db=setup_session,
        data=ForgotPassword(email=user.email, school_code=school.code),
    )
    raw_token = password_reset_delivery_service.get_last_token_for_email(user.email)
    setup_session.close()

    barrier = threading.Barrier(2)

    def run_concurrent_reset(new_pwd: str):
        s = TestSession()
        try:
            barrier.wait()
            res = authentication_service.reset_password(
                db=s,
                data=ResetPassword(token=raw_token, new_password=new_pwd),
            )
            return {"success": True, "data": res}
        except BadRequestException as exc:
            return {"success": False, "error": str(exc.detail)}
        finally:
            s.close()

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_concurrent_reset, "ConcurrentPasswordAlpha123!")
        f2 = executor.submit(run_concurrent_reset, "ConcurrentPasswordBeta123!")
        res1 = f1.result()
        res2 = f2.result()

    results = [res1, res2]
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]

    assert len(successes) == 1, f"Expected exactly 1 success, got {len(successes)}: {results}"
    assert len(failures) == 1, f"Expected exactly 1 failure, got {len(failures)}: {results}"
    assert "already been used" in failures[0]["error"].lower() or "invalid" in failures[0]["error"].lower()


def test_21_cross_tenant_token_tamper_rejected(client, db_session: Session, reset_fixture_data):
    """If a token record's school_id does not match the user's school_id, reject reset."""
    data = reset_fixture_data
    raw_token = "cross_tenant_tampered_token"
    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    # Associate School B's school_id with School A's user
    identity_password_reset_token_repository.create_token_record(
        db=db_session,
        school_id=data["school_b"].id,  # Mismatch!
        user_id=data["user_a"].id,
        token_hash=token_hash,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
        commit=True,
    )

    resp = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "NewPassword123!"},
    )
    assert resp.status_code == 400
    assert "tenant mismatch" in resp.text.lower() or "invalid" in resp.text.lower()


def test_22_replay_attack_post_password_reset_rejected(client, reset_fixture_data):
    """Full lifecycle replay test: token created -> consumed -> replayed -> must fail."""
    data = reset_fixture_data
    client.post(
        "/api/v1/auth/forgot-password",
        json={"email": "user_a@resettest.com", "school_code": data["school_a"].code},
    )
    raw_token = password_reset_delivery_service.get_last_token_for_email("user_a@resettest.com")

    # Step 1: Legitimate reset
    r1 = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "ValidNewPassword123!"},
    )
    assert r1.status_code == 200

    # Step 2: Attacker intercepts and replays token
    r2 = client.post(
        "/api/v1/auth/reset-password",
        json={"token": raw_token, "new_password": "AttackerHijackPassword123!"},
    )
    assert r2.status_code == 400
    assert "already been used" in r2.text

    # Step 3: Legitimate user can still log in with their password
    login_resp = client.post(
        "/api/v1/auth/login",
        json={
            "school_code": data["school_a"].code,
            "email": "user_a@resettest.com",
            "password": "ValidNewPassword123!",
        },
    )
    assert login_resp.status_code == 200
