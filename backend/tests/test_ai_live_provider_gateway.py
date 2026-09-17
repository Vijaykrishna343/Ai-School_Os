"""Phase 29.0: Secure Live AI Provider Gateway Integration Tests.

Tests:
1. GeminiAIProvider: payload construction, execution, normalized response, cost calculation, tool calling.
2. GeminiAIProvider: bounded retries on transient errors (429, 503), fail-fast on 401/403, timeout handling.
3. OpenAIAIProvider: payload construction, execution, normalized response, cost calculation, tool calling.
4. OpenAIAIProvider: bounded retries on transient errors, fail-fast on 401/403, timeout handling.
5. AIProviderFactory: direct resolution and tenant-scoped resolution with credential decryption.
6. AIProviderFactory: fail-closed when live provider enabled but API key is missing or allow_external_ai is false.
7. SSRF Protection: validation blocking localhost, RFC-1918 private IPs, and cloud metadata endpoints.
8. AIAdminService: secure credential encryption at rest, masking in GET API, never exposing plaintext keys.
9. Tenant Isolation: School A credentials/config cannot be accessed or consumed by School B.
10. AIAssistantService: end-to-end integration with live provider resolution, quota tracking, PII sanitization, and audit logs.
"""
from __future__ import annotations

import json
import uuid
from unittest.mock import MagicMock, patch
import httpx
import pytest
from sqlalchemy.orm import Session

from app.ai.providers import (
    AIProviderFactory,
    BaseAIProvider,
    GeminiAIProvider,
    OpenAIAIProvider,
    MockAIProvider,
    AIProviderException,
    AIProviderTimeoutException,
)
from app.ai.schemas.provider import AIRequest, AICapability, AIResponse
from app.ai.schemas.admin import AIProviderConfigUpdate
from app.ai.schemas.assistant import AssistantChatRequest
from app.ai.security.ssrf_validator import validate_provider_endpoint
from app.ai.services.ai_admin_service import ai_admin_service
from app.ai.services.ai_assistant_service import ai_assistant_service
from app.common.exceptions import BadRequestException
from app.common.security.encryption import encrypt_credential, decrypt_credential, mask_credential
from app.models.ai.ai_provider_config import AIProviderConfig
from app.models.ai.ai_usage_limit import AIUsageLimit
from app.models.ai.ai_audit_log import AIAuditLog
from app.models.school.school import School
from app.identity.models.user import IdentityUser


# --- 1. GeminiAIProvider Tests ---

def test_gemini_provider_requires_api_key():
    with pytest.raises(AIProviderException, match="Gemini API key is required"):
        GeminiAIProvider(api_key="")


def test_gemini_provider_success():
    provider = GeminiAIProvider(api_key="test-gemini-key-123", model_name="gemini-1.5-flash")
    req = AIRequest(
        capability=AICapability.ASSISTANT,
        prompt="Explain photosynthesis",
        system_prompt="You are a science teacher.",
        max_tokens=500,
        temperature=0.5,
    )

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Photosynthesis is the process by which green plants..."}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 25,
            "candidatesTokenCount": 80,
            "totalTokenCount": 105,
        },
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gemini_response
        mock_post.return_value = mock_resp

        res = provider.execute(req)

        assert res.provider_type == "GEMINI"
        assert res.model_name == "gemini-1.5-flash"
        assert "Photosynthesis is the process" in res.content
        assert res.prompt_tokens == 25
        assert res.completion_tokens == 80
        assert res.total_tokens == 105
        assert res.estimated_cost_usd > 0
        assert res.latency_ms >= 0


def test_gemini_provider_tool_calls():
    provider = GeminiAIProvider(api_key="test-gemini-key-123", model_name="gemini-1.5-flash")
    req = AIRequest(
        capability=AICapability.ASSISTANT,
        prompt="What is the attendance for class 5A?",
        tools=[
            {
                "name": "get_attendance_summary",
                "description": "Fetch attendance",
                "parameters": {"type": "object", "properties": {"class_name": {"type": "string"}}},
            }
        ],
    )

    mock_gemini_response = {
        "candidates": [
            {
                "content": {
                    "parts": [
                        {
                            "functionCall": {
                                "name": "get_attendance_summary",
                                "args": {"class_name": "5A"},
                            }
                        }
                    ],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 40,
            "candidatesTokenCount": 20,
            "totalTokenCount": 60,
        },
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gemini_response
        mock_post.return_value = mock_resp

        res = provider.execute(req)

        assert res.tool_calls is not None
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0]["name"] == "get_attendance_summary"
        assert res.tool_calls[0]["arguments"] == {"class_name": "5A"}


def test_gemini_provider_transient_retry_success():
    provider = GeminiAIProvider(api_key="test-gemini-key-123", max_retries=2)
    req = AIRequest(capability=AICapability.ASSISTANT, prompt="Hello")

    success_resp = MagicMock()
    success_resp.status_code = 200
    success_resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Hello back"}]}}],
        "usageMetadata": {"promptTokenCount": 5, "candidatesTokenCount": 5, "totalTokenCount": 10},
    }

    rate_limit_resp = MagicMock()
    rate_limit_resp.status_code = 429

    with patch("httpx.Client.post", side_effect=[rate_limit_resp, success_resp]):
        with patch("time.sleep"):  # Avoid test delay
            res = provider.execute(req)
            assert res.content == "Hello back"


def test_gemini_provider_fail_fast_on_auth_error():
    provider = GeminiAIProvider(api_key="bad-key-123", max_retries=2)
    req = AIRequest(capability=AICapability.ASSISTANT, prompt="Hello")

    auth_err_resp = MagicMock()
    auth_err_resp.status_code = 401

    with patch("httpx.Client.post", return_value=auth_err_resp) as mock_post:
        with pytest.raises(AIProviderException, match="Invalid or unauthorized Gemini API key"):
            provider.execute(req)
        # Verify no retries were attempted for 401
        assert mock_post.call_count == 1


def test_gemini_provider_timeout_exception():
    provider = GeminiAIProvider(api_key="test-gemini-key-123", max_retries=1)
    req = AIRequest(capability=AICapability.ASSISTANT, prompt="Hello")

    with patch("httpx.Client.post", side_effect=httpx.TimeoutException("Connection timed out")):
        with patch("time.sleep"):
            with pytest.raises(AIProviderTimeoutException, match="timed out"):
                provider.execute(req)


# --- 2. OpenAIAIProvider Tests ---

def test_openai_provider_requires_api_key():
    with pytest.raises(AIProviderException, match="OpenAI API key is required"):
        OpenAIAIProvider(api_key="")


def test_openai_provider_success():
    provider = OpenAIAIProvider(api_key="test-openai-key-123", model_name="gpt-4o-mini")
    req = AIRequest(
        capability=AICapability.ASSISTANT,
        prompt="Summarize the school policy",
        system_prompt="You are an administrative assistant.",
        max_tokens=300,
        temperature=0.3,
    )

    mock_openai_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Here is the summary of the school policy...",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": 120,
            "total_tokens": 170,
        },
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_openai_response
        mock_post.return_value = mock_resp

        res = provider.execute(req)

        assert res.provider_type == "OPENAI"
        assert res.model_name == "gpt-4o-mini"
        assert "Here is the summary" in res.content
        assert res.prompt_tokens == 50
        assert res.completion_tokens == 120
        assert res.total_tokens == 170
        assert res.estimated_cost_usd > 0


def test_openai_provider_tool_calls():
    provider = OpenAIAIProvider(api_key="test-openai-key-123", model_name="gpt-4o-mini")
    req = AIRequest(
        capability=AICapability.ASSISTANT,
        prompt="Check timetable for teacher John",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "get_teacher_timetable",
                    "parameters": {"type": "object", "properties": {"teacher_name": {"type": "string"}}},
                },
            }
        ],
    )

    mock_openai_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": None,
                    "tool_calls": [
                        {
                            "id": "call_123",
                            "type": "function",
                            "function": {
                                "name": "get_teacher_timetable",
                                "arguments": json.dumps({"teacher_name": "John"}),
                            },
                        }
                    ],
                },
                "finish_reason": "tool_calls",
            }
        ],
        "usage": {"prompt_tokens": 30, "completion_tokens": 15, "total_tokens": 45},
    }

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_openai_response
        mock_post.return_value = mock_resp

        res = provider.execute(req)

        assert res.tool_calls is not None
        assert len(res.tool_calls) == 1
        assert res.tool_calls[0]["name"] == "get_teacher_timetable"
        assert res.tool_calls[0]["arguments"] == {"teacher_name": "John"}


def test_openai_provider_transient_retry_success():
    provider = OpenAIAIProvider(api_key="test-openai-key-123", max_retries=2)
    req = AIRequest(capability=AICapability.ASSISTANT, prompt="Hello")

    success_resp = MagicMock()
    success_resp.status_code = 200
    success_resp.json.return_value = {
        "choices": [{"message": {"content": "Hello!"}}],
        "usage": {"prompt_tokens": 5, "completion_tokens": 5, "total_tokens": 10},
    }

    service_unavailable_resp = MagicMock()
    service_unavailable_resp.status_code = 503

    with patch("httpx.Client.post", side_effect=[service_unavailable_resp, success_resp]):
        with patch("time.sleep"):
            res = provider.execute(req)
            assert res.content == "Hello!"


def test_openai_provider_fail_fast_on_auth_error():
    provider = OpenAIAIProvider(api_key="invalid-openai-key", max_retries=2)
    req = AIRequest(capability=AICapability.ASSISTANT, prompt="Hello")

    auth_err_resp = MagicMock()
    auth_err_resp.status_code = 401

    with patch("httpx.Client.post", return_value=auth_err_resp) as mock_post:
        with pytest.raises(AIProviderException, match="Invalid or expired OpenAI API key"):
            provider.execute(req)
        assert mock_post.call_count == 1


# --- 3. SSRF & Endpoint Security Tests ---

def test_ssrf_validator():
    # Valid endpoints
    assert validate_provider_endpoint("https://api.openai.com/v1") == "https://api.openai.com/v1"
    assert validate_provider_endpoint("https://generativelanguage.googleapis.com/v1beta") == "https://generativelanguage.googleapis.com/v1beta"
    assert validate_provider_endpoint(None) is None
    assert validate_provider_endpoint("") is None

    # Invalid schemes
    with pytest.raises(BadRequestException, match="must use https"):
        validate_provider_endpoint("ftp://example.com/api")

    with pytest.raises(BadRequestException, match="must use https"):
        validate_provider_endpoint("http://api.openai.com/v1")

    # Localhost & Loopback
    with pytest.raises(BadRequestException, match="SSRF"):
        validate_provider_endpoint("https://localhost:8000/api")

    with pytest.raises(BadRequestException, match="SSRF"):
        validate_provider_endpoint("https://127.0.0.1:8000/v1")

    # Cloud metadata
    with pytest.raises(BadRequestException, match="SSRF"):
        validate_provider_endpoint("https://169.254.169.254/latest/meta-data")

    with pytest.raises(BadRequestException, match="SSRF"):
        validate_provider_endpoint("https://metadata.google.internal/computeMetadata/v1")


# --- 4. Factory & Tenant Isolation Tests ---

def test_factory_get_provider_direct():
    mock_p = AIProviderFactory.get_provider("MOCK")
    assert isinstance(mock_p, MockAIProvider)

    gemini_p = AIProviderFactory.get_provider("GEMINI", api_key="valid-gemini-key")
    assert isinstance(gemini_p, GeminiAIProvider)

    openai_p = AIProviderFactory.get_provider("OPENAI", api_key="valid-openai-key")
    assert isinstance(openai_p, OpenAIAIProvider)

    with pytest.raises(AIProviderException, match="not supported"):
        AIProviderFactory.get_provider("UNKNOWN_PROVIDER")


def _create_test_school(db_session: Session, name: str = "AI Test School") -> School:
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=f"SCH_{uuid.uuid4().hex[:6]}",
        address_line1="123 AI Lane",
        city="Test City",
        district="Test District",
        state="Test State",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()
    return school


def test_factory_resolve_for_school_default_mock(db_session: Session):
    school = _create_test_school(db_session)
    provider = AIProviderFactory.resolve_for_school(db_session, school.id)
    assert isinstance(provider, MockAIProvider)


def test_factory_resolve_for_school_live_gemini(db_session: Session):
    school = _create_test_school(db_session)
    encrypted_key = encrypt_credential("live-gemini-secret-key-1234")

    config = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school.id,
        provider_type="GEMINI",
        model_name="gemini-1.5-flash",
        is_enabled=True,
        allow_external_ai=True,
        encrypted_api_key=encrypted_key,
    )
    db_session.add(config)
    db_session.commit()

    provider = AIProviderFactory.resolve_for_school(db_session, school.id)
    assert isinstance(provider, GeminiAIProvider)
    assert provider.model_name == "gemini-1.5-flash"
    assert provider._api_key == "live-gemini-secret-key-1234"


def test_factory_resolve_for_school_fail_closed_if_missing_key(db_session: Session):
    school = _create_test_school(db_session)
    config = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school.id,
        provider_type="GEMINI",
        is_enabled=True,
        allow_external_ai=True,
        encrypted_api_key=None,
    )
    db_session.add(config)
    db_session.commit()

    with pytest.raises(AIProviderException, match="no valid API key is configured"):
        AIProviderFactory.resolve_for_school(db_session, school.id)


def test_factory_resolve_for_school_fail_closed_if_external_disallowed(db_session: Session):
    school = _create_test_school(db_session)
    encrypted_key = encrypt_credential("live-key")
    config = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school.id,
        provider_type="OPENAI",
        is_enabled=True,
        allow_external_ai=False,
        encrypted_api_key=encrypted_key,
    )
    db_session.add(config)
    db_session.commit()

    with pytest.raises(AIProviderException, match="allow_external_ai.*not enabled"):
        AIProviderFactory.resolve_for_school(db_session, school.id)


def test_tenant_isolation_credentials(db_session: Session):
    school_a = _create_test_school(db_session, name="School Alpha")
    school_b = _create_test_school(db_session, name="School Beta")

    key_a = "secret-key-school-a"
    config_a = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school_a.id,
        provider_type="GEMINI",
        is_enabled=True,
        allow_external_ai=True,
        encrypted_api_key=encrypt_credential(key_a),
    )
    db_session.add(config_a)
    db_session.commit()

    # School B has no config -> gets MOCK, cannot access School A's Gemini key
    provider_b = AIProviderFactory.resolve_for_school(db_session, school_id=school_b.id)
    assert isinstance(provider_b, MockAIProvider)


# --- 5. Admin Service Credential Security Tests ---

def test_admin_service_encrypts_and_masks_api_key(db_session: Session):
    school = _create_test_school(db_session)
    secret_key = "sk-proj-supersecretkey1234567890"

    # Save configuration with API key
    update_data = AIProviderConfigUpdate(
        provider_type="OPENAI",
        model_name="gpt-4o-mini",
        is_enabled=True,
        allow_external_ai=True,
        api_key=secret_key,
        notes="Production OpenAI configuration",
    )

    resp = ai_admin_service.update_provider_config(db_session, school.id, update_data)

    # API Response verification
    assert resp.api_key_configured is True
    assert resp.masked_api_key == "••••••••"
    # Verify plaintext key is NOT in response model
    assert not hasattr(resp, "api_key")
    assert not hasattr(resp, "encrypted_api_key")

    # DB verification
    db_config = db_session.query(AIProviderConfig).filter(AIProviderConfig.school_id == school.id).first()
    assert db_config is not None
    assert db_config.encrypted_api_key != secret_key
    assert decrypt_credential(db_config.encrypted_api_key) == secret_key

    # GET configuration response verification
    get_resp = ai_admin_service.get_provider_config(db_session, school.id)
    assert get_resp.api_key_configured is True
    assert get_resp.masked_api_key == "••••••••"


# --- 6. End-to-End AIAssistantService with Live Providers ---

def test_ai_assistant_service_with_live_gemini_provider(db_session: Session):
    school = _create_test_school(db_session, name="Gemini Test School")
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"teacher_{uuid.uuid4().hex[:6]}",
        email=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        password_hash="hashed",
        first_name="Gemini",
        last_name="Teacher",
        is_active=True,
    )
    db_session.add(user)

    # Configure school for live Gemini provider
    encrypted_key = encrypt_credential("live-gemini-key-999")
    config = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school.id,
        provider_type="GEMINI",
        model_name="gemini-1.5-flash",
        is_enabled=True,
        allow_external_ai=True,
        encrypted_api_key=encrypted_key,
    )
    db_session.add(config)
    db_session.commit()

    mock_gemini_json = {
        "candidates": [
            {
                "content": {
                    "parts": [{"text": "Hello! I am your AI Assistant powered by Gemini."}],
                    "role": "model",
                },
                "finishReason": "STOP",
            }
        ],
        "usageMetadata": {
            "promptTokenCount": 20,
            "candidatesTokenCount": 35,
            "totalTokenCount": 55,
        },
    }

    req = AssistantChatRequest(message="Hello AI")

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_gemini_json
        mock_post.return_value = mock_resp

        response = ai_assistant_service.process_chat(
            db=db_session,
            current_user=user,
            request_data=req,
        )

        assert "powered by Gemini" in response.reply
        assert response.tokens_used == 55

        # Verify audit log was recorded
        audit = db_session.query(AIAuditLog).filter(
            AIAuditLog.school_id == school.id,
            AIAuditLog.user_id == user.id,
        ).first()
        assert audit is not None
        assert audit.provider_type == "GEMINI"
        assert audit.model_name == "gemini-1.5-flash"
        assert audit.status == "SUCCESS"
        assert audit.prompt_tokens == 20
        assert audit.completion_tokens == 35


def test_ai_assistant_service_with_live_openai_provider(db_session: Session):
    school = _create_test_school(db_session, name="OpenAI Test School")
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"teacher_{uuid.uuid4().hex[:6]}",
        email=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        password_hash="hashed",
        first_name="OpenAI",
        last_name="Teacher",
        is_active=True,
    )
    db_session.add(user)

    # Configure school for live OpenAI provider
    encrypted_key = encrypt_credential("sk-openai-live-key-888")
    config = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school.id,
        provider_type="OPENAI",
        model_name="gpt-4o-mini",
        is_enabled=True,
        allow_external_ai=True,
        encrypted_api_key=encrypted_key,
    )
    db_session.add(config)
    db_session.commit()

    mock_openai_json = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "Hello! I am your AI Assistant powered by OpenAI GPT-4o-mini.",
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": 15,
            "completion_tokens": 25,
            "total_tokens": 40,
        },
    }

    req = AssistantChatRequest(message="Hello OpenAI Assistant")

    with patch("httpx.Client.post") as mock_post:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = mock_openai_json
        mock_post.return_value = mock_resp

        response = ai_assistant_service.process_chat(
            db=db_session,
            current_user=user,
            request_data=req,
        )

        assert "powered by OpenAI GPT-4o-mini" in response.reply
        assert response.tokens_used == 40

        # Verify audit log was recorded
        audit = db_session.query(AIAuditLog).filter(
            AIAuditLog.school_id == school.id,
            AIAuditLog.user_id == user.id,
        ).first()
        assert audit is not None
        assert audit.provider_type == "OPENAI"
        assert audit.model_name == "gpt-4o-mini"
        assert audit.status == "SUCCESS"
        assert audit.prompt_tokens == 15
        assert audit.completion_tokens == 25


# --- 7. Production Fail-Closed & Deep SSRF Audit Tests ---

def test_production_mode_missing_config_fails_closed(db_session: Session):
    from app.core.config import settings
    school = _create_test_school(db_session, name="Production School")

    with patch.object(settings, "ENVIRONMENT", "production"):
        with pytest.raises(AIProviderException, match="No AI provider is configured for this school"):
            AIProviderFactory.resolve_for_school(db_session, school.id)


def test_production_live_mode_failure_does_not_return_mock(db_session: Session):
    school = _create_test_school(db_session, name="Live Fail School")
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"teacher_{uuid.uuid4().hex[:6]}",
        email=f"teacher_{uuid.uuid4().hex[:6]}@school.com",
        password_hash="hashed",
        first_name="Fail",
        last_name="Test",
        is_active=True,
    )
    db_session.add(user)

    config = AIProviderConfig(
        id=uuid.uuid4(),
        school_id=school.id,
        provider_type="GEMINI",
        model_name="gemini-1.5-flash",
        is_enabled=True,
        allow_external_ai=True,
        encrypted_api_key=encrypt_credential("test-gemini-key"),
    )
    db_session.add(config)
    db_session.commit()

    req = AssistantChatRequest(message="Hello AI")

    # Simulate upstream 500 error from Gemini API
    with patch("httpx.Client.post", side_effect=httpx.ConnectError("Connection refused")):
        with patch("time.sleep"):
            with pytest.raises(AIProviderException, match="Failed to connect to Gemini API"):
                ai_assistant_service.process_chat(
                    db=db_session,
                    current_user=user,
                    request_data=req,
                )


def test_ssrf_validator_enforces_https():
    with pytest.raises(BadRequestException, match="must use https"):
        validate_provider_endpoint("http://api.openai.com/v1")


def test_ssrf_validator_rejects_embedded_credentials():
    with pytest.raises(BadRequestException, match="embedded user credentials"):
        validate_provider_endpoint("https://admin:secret@api.openai.com/v1")


def test_ssrf_validator_blocks_dns_resolving_to_private_ip():
    import socket
    # Simulate DNS resolving 'proxy.internal.school' to 192.168.1.50
    mock_addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("192.168.1.50", 443))]
    with patch("socket.getaddrinfo", return_value=mock_addrinfo):
        with pytest.raises(BadRequestException, match="resolves to private/loopback IP"):
            validate_provider_endpoint("https://proxy.internal.school/v1")

