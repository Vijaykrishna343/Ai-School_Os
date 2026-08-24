import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.logger.logger import sanitize_log_data
from app.models.school.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_obs_test_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    school_a = School(
        name=f"Obs School A {s}", code=f"OSA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(school_a)
    db_session.commit()

    pwd = hash_password("Password@123")
    u_admin = IdentityUser(email=f"admin_obs_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="AdminObs")
    db_session.add(u_admin)
    db_session.commit()

    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    db_session.add(IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id))
    db_session.commit()

    tok_admin = jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id)

    return {
        "school_a": school_a,
        "tok_admin": tok_admin,
    }


def test_01_correlation_id_generated_and_propagated(client: TestClient):
    # 1. No correlation ID in request header -> generated automatically
    res1 = client.get("/healthz")
    assert res1.status_code == 200
    cid1 = res1.headers.get("X-Correlation-ID")
    assert cid1 is not None
    assert len(cid1) > 10

    # 2. Correlation ID passed in request header -> preserved in response
    custom_cid = f"test-cid-{uuid.uuid4()}"
    res2 = client.get("/healthz", headers={"X-Correlation-ID": custom_cid})
    assert res2.status_code == 200
    assert res2.headers.get("X-Correlation-ID") == custom_cid
    assert res2.headers.get("X-Request-ID") == custom_cid


def test_02_sensitive_data_redaction():
    raw_log = {
        "user_id": "usr-123",
        "password": "SuperSecretPassword123!",
        "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "details": {
            "credit_card": "4111222233334444",
            "salary": 150000,
        },
        "auth_header": "Bearer eyJhbGciOiJIUzI1Ni...",
    }

    sanitized = sanitize_log_data(raw_log)

    assert sanitized["user_id"] == "usr-123"
    assert sanitized["password"] == "[REDACTED]"
    assert sanitized["access_token"] == "[REDACTED]"
    assert sanitized["details"]["credit_card"] == "[REDACTED]"
    assert sanitized["details"]["salary"] == "[REDACTED]"
    assert "[REDACTED]" in sanitized["auth_header"]


def test_03_standardized_error_response_contains_correlation_id(client: TestClient):
    custom_cid = f"test-err-cid-{uuid.uuid4()}"
    # Trigger 422 validation error
    res = client.post(
        "/api/v1/auth/login",
        json={"school_code": "INVALID"},
        headers={"X-Correlation-ID": custom_cid},
    )
    assert res.status_code == 422
    assert res.headers.get("X-Correlation-ID") == custom_cid
    body = res.json()
    assert body["success"] is False
    assert body["error"]["code"] == "VALIDATION_ERROR"
    assert body["error"]["correlation_id"] == custom_cid


def test_04_notification_delivery_metrics(client: TestClient, setup_obs_test_data):
    tok = setup_obs_test_data["tok_admin"]
    headers = {"Authorization": f"Bearer {tok}"}
    res = client.get("/api/v1/notifications/delivery-metrics", headers=headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert "total_notifications" in data
    assert "sent_count" in data
    assert "failed_count" in data
    assert "pending_count" in data
    assert "failure_rate_percent" in data
