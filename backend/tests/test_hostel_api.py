import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


def test_create_and_list_hostel_buildings(client: TestClient, db_session: Session):
    seed_identity(db_session)

    school = School(
        name="Hostel Test School",
        code=f"HTS-{uuid.uuid4().hex[:4]}",
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
        email="hostel_admin@school.com",
        password_hash="hash",
        first_name="Admin",
        last_name="Hostel",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(admin_user)
    db_session.commit()

    db_session.add(IdentityUserRole(user_id=admin_user.id, role_id=admin_role.id))
    db_session.commit()

    headers = {"Authorization": f"Bearer {jwt_manager.create_access_token(admin_user.id, school.id)}"}

    # 1. Create Building
    res_bldg = client.post(
        "/api/v1/hostel/buildings",
        json={
            "name": "Senior Boys Block",
            "code": f"SBB-{uuid.uuid4().hex[:4]}",
            "gender_designation": "BOYS",
            "capacity": 100,
            "description": "Main senior hostel block",
        },
        headers=headers,
    )
    assert res_bldg.status_code == 201
    bldg_id = res_bldg.json()["data"]["id"]

    # 2. List Buildings
    res_list = client.get("/api/v1/hostel/buildings", headers=headers)
    assert res_list.status_code == 200
    assert len(res_list.json()["data"]) >= 1

    # 3. Create Room in Building
    res_room = client.post(
        f"/api/v1/hostel/buildings/{bldg_id}/rooms",
        json={
            "room_number": "101",
            "floor": 1,
            "room_type": "STANDARD",
            "capacity": 2,
        },
        headers=headers,
    )
    assert res_room.status_code == 201
    room_id = res_room.json()["data"]["id"]

    # 4. Create Bed in Room
    res_bed = client.post(
        f"/api/v1/hostel/rooms/{room_id}/beds",
        json={
            "bed_number": "101-A",
        },
        headers=headers,
    )
    assert res_bed.status_code == 201
    assert "id" in res_bed.json()["data"]
