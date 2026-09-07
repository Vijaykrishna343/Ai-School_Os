import uuid
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient

from app.identity.models import IdentityUser, IdentityRole, IdentityPermission
from app.identity.security.password import hash_password
from app.models.school import School
from app.models.ai import AIProviderConfig, AIUsageLimit, AIAuditLog


@pytest.fixture
def admin_user_and_school(db_session):
    school_a = School(
        id=uuid.uuid4(),
        name="Admin Test School A",
        code=f"TSA_{uuid.uuid4().hex[:6]}",
        address_line1="123 St",
        city="City A",
        district="District A",
        state="State A",
        postal_code="500001",
    )
    db_session.add(school_a)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="Super Admin").first()
    if not admin_role:
        admin_role = db_session.query(IdentityRole).filter_by(name="School Admin").first()

    perm = db_session.query(IdentityPermission).filter_by(name="system.settings").first()
    if perm and admin_role:
        from app.identity.models import IdentityRolePermission
        existing_rp = db_session.query(IdentityRolePermission).filter_by(role_id=admin_role.id, permission_id=perm.id).first()
        if not existing_rp:
            db_session.add(IdentityRolePermission(role_id=admin_role.id, permission_id=perm.id))
            db_session.commit()

    user_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        username=f"admin_a_{uuid.uuid4().hex[:6]}",
        email=f"admin_a_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Password@123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
    )
    if admin_role:
        user_a.roles = [admin_role]

    db_session.add(user_a)
    db_session.commit()
    return user_a, school_a


@pytest.fixture
def teacher_user(db_session, admin_user_and_school):
    _, school_a = admin_user_and_school
    teacher_role = db_session.query(IdentityRole).filter_by(name="Teacher").first()

    teacher = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        username=f"teacher_{uuid.uuid4().hex[:6]}",
        email=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Password@123"),
        first_name="Teacher",
        last_name="User",
        is_active=True,
    )
    if teacher_role:
        teacher.roles = [teacher_role]

    db_session.add(teacher)
    db_session.commit()
    return teacher


from app.identity.security.jwt_manager import jwt_manager


def get_auth_headers(client: TestClient, user: IdentityUser) -> dict[str, str]:
    token = jwt_manager.create_access_token(user_id=user.id, school_id=user.school_id)
    return {"Authorization": f"Bearer {token}"}


def test_get_and_update_provider_config_success(client: TestClient, admin_user_and_school):
    user, school = admin_user_and_school
    headers = get_auth_headers(client, user)

    # 1. Get initial provider config
    res_get = client.get("/api/v1/ai/admin/provider-config", headers=headers)
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert data_get["provider_type"] == "MOCK"
    assert data_get["is_enabled"] is True

    # 2. Update provider config
    update_payload = {
        "provider_type": "GEMINI",
        "model_name": "gemini-1.5-flash",
        "is_enabled": True,
        "allow_external_ai": True,
        "notes": "Enabled Gemini Flash for school",
    }
    res_put = client.put("/api/v1/ai/admin/provider-config", json=update_payload, headers=headers)
    assert res_put.status_code == 200
    data_put = res_put.json()
    assert data_put["provider_type"] == "GEMINI"
    assert data_put["model_name"] == "gemini-1.5-flash"
    assert data_put["allow_external_ai"] is True


def test_update_usage_limit_success(client: TestClient, admin_user_and_school):
    user, school = admin_user_and_school
    headers = get_auth_headers(client, user)

    payload = {
        "monthly_token_quota": 5000000,
        "is_enabled": True,
    }
    res = client.put("/api/v1/ai/admin/usage-limit", json=payload, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["monthly_token_quota"] == 5000000
    assert data["quota_remaining"] == 5000000


def test_query_audit_logs_with_filters(client: TestClient, db_session, admin_user_and_school):
    user, school = admin_user_and_school
    headers = get_auth_headers(client, user)

    # Seed mock audit log records
    log1 = AIAuditLog(
        id=uuid.uuid4(),
        school_id=school.id,
        user_id=user.id,
        capability="ASSISTANT",
        provider_type="MOCK",
        model_name="mock-default-v1",
        prompt_tokens=10,
        completion_tokens=20,
        estimated_cost_usd=0.0001,
        latency_ms=50,
        status="SUCCESS",
    )
    log2 = AIAuditLog(
        id=uuid.uuid4(),
        school_id=school.id,
        user_id=user.id,
        capability="TIMETABLE",
        provider_type="LOCAL_ORTOOLS",
        model_name="ortools-sat-v1",
        prompt_tokens=0,
        completion_tokens=0,
        estimated_cost_usd=0.0,
        latency_ms=120,
        status="SUCCESS",
    )
    db_session.add_all([log1, log2])
    db_session.commit()

    # Query all audit logs
    res = client.get("/api/v1/ai/admin/audit-logs", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total_count"] >= 2
    assert len(data["items"]) >= 2

    # Query filtered by capability
    res_cap = client.get("/api/v1/ai/admin/audit-logs?capability=TIMETABLE", headers=headers)
    assert res_cap.status_code == 200
    data_cap = res_cap.json()
    assert data_cap["total_count"] == 1
    assert data_cap["items"][0]["capability"] == "TIMETABLE"


def test_admin_endpoints_rbac_denial(client: TestClient, teacher_user):
    headers = get_auth_headers(client, teacher_user)

    res_config = client.get("/api/v1/ai/admin/provider-config", headers=headers)
    assert res_config.status_code == 403

    res_logs = client.get("/api/v1/ai/admin/audit-logs", headers=headers)
    assert res_logs.status_code == 403


def test_admin_endpoints_cross_tenant_isolation(client: TestClient, db_session, admin_user_and_school):
    user_a, school_a = admin_user_and_school

    # Create School B and Audit Log in School B
    school_b = School(
        id=uuid.uuid4(),
        name="Admin Test School B",
        code=f"TSB_{uuid.uuid4().hex[:6]}",
        address_line1="456 St",
        city="City B",
        district="District B",
        state="State B",
        postal_code="500002",
    )
    user_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        username=f"user_b_{uuid.uuid4().hex[:6]}",
        email=f"user_b_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Password@123"),
        first_name="User",
        last_name="B",
        is_active=True,
    )
    log_b = AIAuditLog(
        id=uuid.uuid4(),
        school_id=school_b.id,
        user_id=user_b.id,
        capability="RISK",
        provider_type="MOCK",
        model_name="mock-default-v1",
        prompt_tokens=50,
        completion_tokens=50,
        estimated_cost_usd=0.0005,
        latency_ms=80,
        status="SUCCESS",
    )
    db_session.add_all([school_b, user_b, log_b])
    db_session.commit()

    # Admin of School A queries audit logs
    headers_a = get_auth_headers(client, user_a)
    res_a = client.get("/api/v1/ai/admin/audit-logs?capability=RISK", headers=headers_a)
    assert res_a.status_code == 200
    data_a = res_a.json()
    # Should NOT return School B audit log
    for item in data_a["items"]:
        assert item["school_id"] == str(school_a.id)


def test_invalid_provider_type_validation(client: TestClient, admin_user_and_school):
    user, _ = admin_user_and_school
    headers = get_auth_headers(client, user)

    payload = {
        "provider_type": "INVALID_PROVIDER_NAME",
        "model_name": "unknown",
        "is_enabled": True,
        "allow_external_ai": False,
    }
    res = client.put("/api/v1/ai/admin/provider-config", json=payload, headers=headers)
    assert res.status_code == 400
    assert "Invalid provider_type" in str(res.json())
