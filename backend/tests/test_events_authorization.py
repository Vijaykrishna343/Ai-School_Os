import uuid
from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.services.event_service import event_service


def test_events_tenant_isolation_and_visibility(client: TestClient, db_session: Session):
    seed_identity(db_session)

    # School A
    school_a = School(
        name="School A Events",
        code=f"SAE-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B
    school_b = School(
        name="School B Events",
        code=f"SBE-{uuid.uuid4().hex[:4]}",
        address_line1="456 Other St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500002",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()

    user_a = IdentityUser(school_id=school_a.id, email="admin_a_evt@school.com", password_hash="hash", first_name="User", last_name="A", is_active=True, status="ACTIVE")
    user_b = IdentityUser(school_id=school_b.id, email="admin_b_evt@school.com", password_hash="hash", first_name="User", last_name="B", is_active=True, status="ACTIVE")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=user_a.id, role_id=admin_role.id),
        IdentityUserRole(user_id=user_b.id, role_id=admin_role.id),
    ])
    db_session.commit()

    headers_a = {"Authorization": f"Bearer {jwt_manager.create_access_token(user_a.id, school_a.id)}"}

    now = datetime.now(timezone.utc)

    # Event in School B
    event_b = event_service.create_event(
        db=db_session,
        school_id=school_b.id,
        user_id=user_b.id,
        user_email=user_b.email,
        title="School B Flag Hoisting",
        event_type="FLAG_HOISTING",
        start_datetime=now + timedelta(days=2),
        end_datetime=now + timedelta(days=2, hours=2),
        status="PUBLISHED",
    )

    # School A user trying to access School B event -> 404 / denied
    res_get_b = client.get(f"/api/v1/events/{event_b.id}", headers=headers_a)
    assert res_get_b.status_code == 404

    # List events for School A -> must not contain School B event
    res_list_a = client.get("/api/v1/events", headers=headers_a)
    assert res_list_a.status_code == 200
    events_a = res_list_a.json()["data"]
    assert not any(e["id"] == str(event_b.id) for e in events_a)
