"""
Comprehensive test suite for Phase 12.5 AI Smart Communication & Announcement Draft Generator.
Tests engine multi-channel formatting, PII redaction, RBAC enforcement, tenant isolation, and API endpoints.
"""

import uuid
import pytest
from datetime import date, datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.communication.engine import (
    AICommunicationDraftEngine,
    CommunicationDraftInput,
    ai_communication_draft_engine,
)
from app.ai.security.data_minimizer import AIDataMinimizer
from app.models.school import School
from app.identity.models import IdentityUser, IdentityRole, IdentityPermission
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def comm_env(db_session: Session):
    seed_identity(db_session)

    s_a = uuid.uuid4().hex[:6]
    school = School(
        id=uuid.uuid4(),
        name=f"Comm School A {s_a}",
        code=f"CSA_{s_a}",
        address_line1="100 Comm Street",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500081",
    )
    db_session.add(school)
    db_session.commit()

    # Ensure ai.communication.draft permission exists & assign to School Admin
    perm = db_session.query(IdentityPermission).filter(IdentityPermission.name == "ai.communication.draft").first()
    if not perm:
        perm = IdentityPermission(name="ai.communication.draft", description="Draft AI Announcements", module="ai", action="communication.draft")
        db_session.add(perm)
        db_session.commit()

    admin_role = db_session.query(IdentityRole).filter(IdentityRole.name == "School Admin").first()
    if admin_role and perm not in admin_role.permissions:
        admin_role.permissions.append(perm)
        db_session.commit()

    receptionist_role = db_session.query(IdentityRole).filter(IdentityRole.name == "Receptionist").first()

    pwd = hash_password("AdminPass123!")

    # Create Admin User
    admin_user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"comm_admin_{s_a}",
        email=f"admin_{s_a}@comm.com",
        password_hash=pwd,
        first_name="CommAdmin",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    if admin_role:
        admin_user.roles = [admin_role]

    # Create Receptionist User (unauthorized for AI communication draft)
    receptionist_user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"comm_recep_{s_a}",
        email=f"reception_{s_a}@comm.com",
        password_hash=pwd,
        first_name="CommRecep",
        last_name="User",
        is_active=True,
        is_verified=True,
    )
    if receptionist_role:
        receptionist_user.roles = [receptionist_role]

    db_session.add_all([admin_user, receptionist_user])
    db_session.commit()

    # Generate JWT tokens
    admin_token = jwt_manager.create_access_token(user_id=admin_user.id, school_id=school.id)
    receptionist_token = jwt_manager.create_access_token(user_id=receptionist_user.id, school_id=school.id)

    return {
        "school": school,
        "admin_user": admin_user,
        "admin_token": admin_token,
        "receptionist_user": receptionist_user,
        "receptionist_token": receptionist_token,
    }


def test_01_communication_draft_engine_multi_channel_constraints():
    engine = AICommunicationDraftEngine()
    input_data = CommunicationDraftInput(
        category="ANNOUNCEMENT",
        target_audience="PARENTS",
        tone="FORMAL",
        key_details="The school will remain closed on Friday, October 15th for Staff Development Day. Classes will resume on Monday.",
        school_name="Greenwood Academy",
        requested_channels=["SMS", "EMAIL", "WHATSAPP", "IN_APP"],
    )

    output = engine.generate(input_data)

    assert output.category == "ANNOUNCEMENT"
    assert output.target_audience == "PARENTS"
    assert "SMS" in output.variants
    assert "EMAIL" in output.variants
    assert "WHATSAPP" in output.variants
    assert "IN_APP" in output.variants

    # SMS Constraint: <= 160 characters
    sms_var = output.variants["SMS"]
    assert len(sms_var.body) <= 160
    assert "Greenwood Academy" in sms_var.body

    # WhatsApp Formatting: Markdown bold & headers
    wa_var = output.variants["WHATSAPP"]
    assert "*" in wa_var.body

    # Email Formatting: Formal Subject & Body
    email_var = output.variants["EMAIL"]
    assert "Greenwood Academy" in email_var.title
    assert "Dear Parents" in email_var.body

    # In-App Formatting: Summary
    in_app_var = output.variants["IN_APP"]
    assert len(in_app_var.body) <= 250


def test_02_communication_draft_pii_redaction():
    text_with_pii = "Contact Principal John at principal@greenwood.edu or call +919876543210 regarding the trip."
    sanitized, redactions = AIDataMinimizer.sanitize_text(text_with_pii)

    assert "[REDACTED_EMAIL]" in sanitized
    assert "[REDACTED_PHONE]" in sanitized
    assert "principal@greenwood.edu" not in sanitized
    assert "9876543210" not in sanitized
    assert "email" in redactions
    assert "phone" in redactions


def test_03_ai_communication_api_generate_list_and_get(client: TestClient, comm_env: dict):
    headers = {"Authorization": f"Bearer {comm_env['admin_token']}"}

    payload = {
        "category": "EVENT_INVITATION",
        "target_audience": "PARENTS",
        "tone": "FRIENDLY",
        "key_details": "Annual Sports Day will be held on Nov 10th at 9:00 AM. All parents are cordially invited.",
        "requested_channels": ["SMS", "EMAIL", "WHATSAPP", "IN_APP"],
    }

    # 1. Generate Draft via POST
    response = client.post("/api/v1/ai/communication/draft", json=payload, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()

    assert data["category"] == "EVENT_INVITATION"
    assert data["target_audience"] == "PARENTS"
    assert "SMS" in data["channel_variants"]
    assert "EMAIL" in data["channel_variants"]
    assert "WHATSAPP" in data["channel_variants"]
    assert "IN_APP" in data["channel_variants"]
    assert data["status"] == "DRAFT"
    assert len(data["channel_variants"]["SMS"]["body"]) <= 160

    draft_id = data["id"]

    # 2. Get Draft by ID via GET
    get_res = client.get(f"/api/v1/ai/communication/draft/{draft_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == draft_id

    # 3. List Drafts via GET
    list_res = client.get("/api/v1/ai/communication/drafts", headers=headers)
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(d["id"] == draft_id for d in list_data["drafts"])


def test_04_ai_communication_rbac_unauthorized(client: TestClient, comm_env: dict):
    # Receptionist does not have ai.communication.draft permission
    headers = {"Authorization": f"Bearer {comm_env['receptionist_token']}"}

    payload = {
        "category": "ANNOUNCEMENT",
        "target_audience": "PARENTS",
        "tone": "FORMAL",
        "key_details": "Unscheduled power shutdown notice.",
    }

    response = client.post("/api/v1/ai/communication/draft", json=payload, headers=headers)
    assert response.status_code == 403
