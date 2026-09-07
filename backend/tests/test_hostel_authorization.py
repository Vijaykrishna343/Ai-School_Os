import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.services.hostel_service import hostel_service


def test_hostel_tenant_isolation(client: TestClient, db_session: Session):
    seed_identity(db_session)

    # School A
    school_a = School(
        name="Hostel School A",
        code=f"HSA-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B
    school_b = School(
        name="Hostel School B",
        code=f"HSB-{uuid.uuid4().hex[:4]}",
        address_line1="456 Secondary St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500002",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()

    user_a = IdentityUser(school_id=school_a.id, email="admin_a_hst@school.com", password_hash="hash", first_name="User", last_name="A", is_active=True, status="ACTIVE")
    user_b = IdentityUser(school_id=school_b.id, email="admin_b_hst@school.com", password_hash="hash", first_name="User", last_name="B", is_active=True, status="ACTIVE")
    db_session.add_all([user_a, user_b])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=user_a.id, role_id=admin_role.id),
        IdentityUserRole(user_id=user_b.id, role_id=admin_role.id),
    ])
    db_session.commit()

    # Create building in School B
    bldg_b = hostel_service.create_building(
        db=db_session,
        school_id=school_b.id,
        data={
            "name": "School B Block",
            "code": f"SBB-{uuid.uuid4().hex[:4]}",
            "gender_designation": "GIRLS",
            "capacity": 50,
        },
    )

    headers_a = {"Authorization": f"Bearer {jwt_manager.create_access_token(user_a.id, school_a.id)}"}

    # List buildings for School A -> must not return School B building
    res_list = client.get("/api/v1/hostel/buildings", headers=headers_a)
    assert res_list.status_code == 200
    bldgs = res_list.json()["data"]
    assert not any(b["id"] == str(bldg_b.id) for b in bldgs)
