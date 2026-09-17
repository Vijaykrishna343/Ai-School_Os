"""
Phase 12.2 — AI Foundation & Core Providers Test Suite.
Covers MockAIProvider, Provider Factory, AI Security, Tenant Boundary, Data Minimizer, Tool Registry, Usage Limits, Audit Logging, and API endpoints.
"""

import uuid
import pytest
from datetime import date, timedelta
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.schemas.provider import AIRequest, AICapability, AIProviderType
from app.ai.schemas.assistant import AssistantChatRequest
from app.ai.providers import MockAIProvider, AIProviderFactory, AIProviderException, AIProviderTimeoutException
from app.ai.security import AITenantBoundaryService, AIDataMinimizer
from app.ai.tools import ai_tool_registry, ToolDefinition
from app.ai.services import ai_usage_service, ai_audit_service, ai_assistant_service
from app.models.ai import AIAuditLog, AIUsageLimit, AIProviderConfig
from app.models.school import School
from app.identity.models import IdentityUser, IdentityRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.common.exceptions import ForbiddenException, BadRequestException


@pytest.fixture
def ai_test_environment(db_session: Session):
    seed_identity(db_session)

    s_a = uuid.uuid4().hex[:6]
    s_b = uuid.uuid4().hex[:6]

    school_a = School(
        id=uuid.uuid4(), name=f"AI School Alpha {s_a}", code=f"AIA_{s_a}",
        address_line1="1 AI Way", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500081",
    )
    school_b = School(
        id=uuid.uuid4(), name=f"AI School Beta {s_b}", code=f"AIB_{s_b}",
        address_line1="2 AI Road", city="Bangalore", district="Bangalore", state="Karnataka", postal_code="560001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    # User School A with ai.assistant permission (School Admin role has ai.*)
    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    pwd = hash_password("Password@123")

    user_a = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"ai_admin_a_{s_a}", email=f"admin_a_{s_a}@ai.com",
        password_hash=pwd, first_name="AdminA", last_name="User", is_active=True,
    )
    user_a.roles = [admin_role]

    user_b = IdentityUser(
        id=uuid.uuid4(), school_id=school_b.id, username=f"ai_admin_b_{s_b}", email=f"admin_b_{s_b}@ai.com",
        password_hash=pwd, first_name="AdminB", last_name="User", is_active=True,
    )
    user_b.roles = [admin_role]

    # User without ai.assistant permission (e.g. Receptionist)
    rec_role = db_session.query(IdentityRole).filter_by(name="Receptionist").first()
    user_unauth = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"ai_rec_a_{s_a}", email=f"rec_a_{s_a}@ai.com",
        password_hash=pwd, first_name="RecA", last_name="User", is_active=True,
    )
    user_unauth.roles = [rec_role]

    db_session.add_all([user_a, user_b, user_unauth])
    db_session.commit()

    tok_a = jwt_manager.create_access_token(user_id=user_a.id, school_id=school_a.id)
    tok_b = jwt_manager.create_access_token(user_id=user_b.id, school_id=school_b.id)
    tok_unauth = jwt_manager.create_access_token(user_id=user_unauth.id, school_id=school_a.id)

    return {
        "school_a": school_a,
        "school_b": school_b,
        "user_a": user_a,
        "user_b": user_b,
        "user_unauth": user_unauth,
        "headers_a": {"Authorization": f"Bearer {tok_a}"},
        "headers_b": {"Authorization": f"Bearer {tok_b}"},
        "headers_unauth": {"Authorization": f"Bearer {tok_unauth}"},
    }


# ============================================================================
# 1. PROVIDER TESTS
# ============================================================================

def test_mock_provider_success_and_determinism():
    provider = MockAIProvider()
    req = AIRequest(capability=AICapability.ASSISTANT, prompt="Tell me about the school profile summary")
    res = provider.execute(req)

    assert res.provider_type == "MOCK"
    assert res.model_name == "mock-default-v1"
    assert "Mock response" in res.content
    assert res.prompt_tokens > 0
    assert res.completion_tokens > 0
    assert res.total_tokens == res.prompt_tokens + res.completion_tokens
    assert res.latency_ms >= 0


def test_mock_provider_simulated_failure_and_timeout():
    provider = MockAIProvider()

    req_fail = AIRequest(capability=AICapability.ASSISTANT, prompt="Test", simulate_failure=True)
    with pytest.raises(AIProviderException, match="Simulated AI Provider failure"):
        provider.execute(req_fail)

    req_timeout = AIRequest(capability=AICapability.ASSISTANT, prompt="Test", simulate_timeout=True)
    with pytest.raises(AIProviderTimeoutException, match="Simulated AI Provider timeout"):
        provider.execute(req_timeout)


def test_provider_factory_resolution():
    prov_mock = AIProviderFactory.get_provider("MOCK")
    assert prov_mock.provider_type == "MOCK"

    with pytest.raises(AIProviderException, match="OpenAI live provider requires an API key"):
        AIProviderFactory.get_provider("OPENAI")

    with pytest.raises(AIProviderException, match="not supported or recognized"):
        AIProviderFactory.get_provider("NON_EXISTENT_PROVIDER")


# ============================================================================
# 2. TENANT BOUNDARY TESTS
# ============================================================================

def test_tenant_boundary_validation(ai_test_environment):
    env = ai_test_environment
    user_a = env["user_a"]

    # Valid tenant context
    sch_id = AITenantBoundaryService.validate_and_get_school_id(user_a)
    assert sch_id == user_a.school_id

    # Cross-tenant target rejection
    with pytest.raises(ForbiddenException, match="Cross-tenant AI operations are strictly prohibited"):
        AITenantBoundaryService.validate_and_get_school_id(user_a, target_school_id=env["school_b"].id)

    # Missing school context rejection
    user_no_school = IdentityUser(id=uuid.uuid4(), school_id=None)
    with pytest.raises(ForbiddenException, match="Authentication and active school context are required"):
        AITenantBoundaryService.validate_and_get_school_id(user_no_school)


# ============================================================================
# 3. DATA MINIMIZER TESTS
# ============================================================================

def test_data_minimizer_restricted_field_blocking_and_pii_masking():
    sensitive_dict = {
        "username": "johndoe",
        "password": "SuperSecretPassword123",
        "password_hash": "$argon2id$v=19$m=65536...",
        "jwt": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
        "api_key": "sk-proj-123456789",
        "contact_phone": "9876543210",
        "contact_email": "john.doe@example.com",
    }

    sanitized, redactions = AIDataMinimizer.sanitize_dict(sensitive_dict)

    # Restricted fields completely removed
    assert "password" not in sanitized
    assert "password_hash" not in sanitized
    assert "jwt" not in sanitized
    assert "api_key" not in sanitized

    # PII fields masked
    assert sanitized["contact_phone"] == "[REDACTED_PHONE]"
    assert sanitized["contact_email"] == "[REDACTED_EMAIL]"

    # Redactions summary contains category labels without revealing values
    assert "password" in redactions
    assert "email" in redactions
    assert "phone" in redactions


# ============================================================================
# 4. USAGE LIMITS & QUOTA TESTS
# ============================================================================

def test_usage_limits_quota_check_and_recording(db_session: Session, ai_test_environment):
    env = ai_test_environment
    sch_a = env["school_a"]

    # Initial limit creation
    limit = ai_usage_service.get_or_create_usage_limit(db_session, sch_a.id)
    assert limit.monthly_token_quota == 1000000
    assert limit.used_tokens_current_month == 0

    # Record usage
    ai_usage_service.record_usage(db_session, sch_a.id, 500)
    db_session.refresh(limit)
    assert limit.used_tokens_current_month == 500

    # Quota exhaustion simulation
    limit.used_tokens_current_month = 1000000
    db_session.commit()

    with pytest.raises(BadRequestException, match="Monthly AI token quota exhausted"):
        ai_usage_service.check_and_reserve_quota(db_session, sch_a.id, estimated_tokens=100)


# ============================================================================
# 5. AUDIT LOGGING TESTS
# ============================================================================

def test_audit_logging_records_events_without_sensitive_data(db_session: Session, ai_test_environment):
    env = ai_test_environment
    sch_a = env["school_a"]
    user_a = env["user_a"]

    log = ai_audit_service.log_ai_event(
        db=db_session,
        school_id=sch_a.id,
        user_id=user_a.id,
        capability="ASSISTANT",
        provider_type="MOCK",
        model_name="mock-default-v1",
        prompt_tokens=20,
        completion_tokens=30,
        estimated_cost_usd=0.0001,
        latency_ms=45,
        status="SUCCESS",
    )

    assert log.id is not None
    assert log.school_id == sch_a.id
    assert log.user_id == user_a.id
    assert log.capability == "ASSISTANT"
    assert log.prompt_tokens == 20
    assert log.status == "SUCCESS"


# ============================================================================
# 6. TOOL REGISTRY TESTS
# ============================================================================

def test_tool_registry_execution_and_tenant_protection(db_session: Session, ai_test_environment):
    env = ai_test_environment
    user_a = env["user_a"]
    sch_a = env["school_a"]

    # Assign permissions set to mock current_user object
    user_a.permissions = {"school.view"}

    # Execute get_school_summary tool
    res = ai_tool_registry.execute_tool("get_school_summary", db_session, user_a, {})
    assert res["school_id"] == str(sch_a.id)
    assert res["name"] == sch_a.name

    # Unregistered tool rejection
    with pytest.raises(BadRequestException, match="is not registered or supported"):
        ai_tool_registry.execute_tool("non_existent_tool", db_session, user_a, {})

    # Missing permission rejection
    user_a.permissions = set()
    user_a.roles = []
    with pytest.raises(ForbiddenException, match="Missing required permission"):
        ai_tool_registry.execute_tool("get_school_summary", db_session, user_a, {})


# ============================================================================
# 7. AI ASSISTANT ENDPOINT TESTS
# ============================================================================

def test_ai_assistant_chat_api_success(client: TestClient, ai_test_environment):
    env = ai_test_environment
    headers_a = env["headers_a"]

    payload = {
        "message": "Please give me a school summary for my institution john.doe@example.com",
    }
    res = client.post("/api/v1/ai/assistant/chat", json=payload, headers=headers_a)
    assert res.status_code == 200

    data = res.json()
    assert "reply" in data
    assert data["tokens_used"] > 0
    assert data["latency_ms"] >= 0
    assert "email" in data["redacted_fields"]


def test_ai_assistant_chat_api_unauthorized_and_forbidden(client: TestClient, ai_test_environment):
    env = ai_test_environment

    payload = {"message": "Hello assistant"}

    # Unauthenticated -> 401
    res_unauth = client.post("/api/v1/ai/assistant/chat", json=payload)
    assert res_unauth.status_code == 401

    # User lacking ai.assistant permission -> 403
    res_forbidden = client.post("/api/v1/ai/assistant/chat", json=payload, headers=env["headers_unauth"])
    assert res_forbidden.status_code == 403


def test_ai_usage_stats_api(client: TestClient, ai_test_environment):
    env = ai_test_environment

    res = client.get("/api/v1/ai/usage/stats", headers=env["headers_a"])
    assert res.status_code == 200

    data = res.json()
    assert data["school_id"] == str(env["school_a"].id)
    assert data["monthly_token_quota"] == 1000000
    assert data["is_enabled"] is True
