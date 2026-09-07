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


def test_events_crud_and_lifecycle(client: TestClient, db_session: Session):
    seed_identity(db_session)

    # Setup school
    school = School(
        name="Events Test School",
        code=f"ETS-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()
    admin_user = IdentityUser(
        school_id=school.id,
        email="events_admin@school.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Events",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_user)
    db_session.commit()

    db_session.add(IdentityUserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.commit()

    token = jwt_manager.create_access_token(user_id=admin_user.id, school_id=school.id)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(timezone.utc)
    start_dt = now + timedelta(days=1)
    end_dt = start_dt + timedelta(hours=4)

    # 1. Create Event (Draft)
    res_create = client.post(
        "/api/v1/events",
        json={
            "title": "Annual Sports Day 2026",
            "event_type": "SPORTS",
            "start_datetime": start_dt.isoformat(),
            "end_datetime": end_dt.isoformat(),
            "description": "Inter-house athletic meet",
            "venue": "Main School Sports Complex",
            "audience_scope": "SCHOOL",
            "status": "DRAFT",
        },
        headers=headers,
    )
    assert res_create.status_code == 201
    event_id = res_create.json()["data"]["id"]
    assert res_create.json()["data"]["status"] == "DRAFT"

    # 2. List Events
    res_list = client.get("/api/v1/events", headers=headers)
    assert res_list.status_code == 200
    events = res_list.json()["data"]
    assert any(e["id"] == event_id for e in events)

    # 3. Get Event Details
    res_get = client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["data"]["title"] == "Annual Sports Day 2026"

    # 4. Update Event
    res_update = client.put(
        f"/api/v1/events/{event_id}",
        json={"venue": "Renovated Sports Ground"},
        headers=headers,
    )
    assert res_update.status_code == 200

    # 5. Publish Event
    res_pub = client.put(f"/api/v1/events/{event_id}/publish", headers=headers)
    assert res_pub.status_code == 200
    assert res_pub.json()["data"]["status"] == "PUBLISHED"

    # 6. Cancel Event
    res_cancel = client.put(f"/api/v1/events/{event_id}/cancel", headers=headers)
    assert res_cancel.status_code == 200
    assert res_cancel.json()["data"]["status"] == "CANCELLED"

    # 7. Delete Event
    res_del = client.delete(f"/api/v1/events/{event_id}", headers=headers)
    assert res_del.status_code == 200

    # Verify soft delete
    res_get_deleted = client.get(f"/api/v1/events/{event_id}", headers=headers)
    assert res_get_deleted.status_code == 404
