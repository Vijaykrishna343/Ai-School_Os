import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.permission import IdentityPermission
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

    user_a = IdentityUser(school_id=school_a.id, email=f"admin_a_hst_{uuid.uuid4().hex[:4]}@school.com", password_hash="hash", first_name="User", last_name="A", is_active=True, status="ACTIVE")
    user_b = IdentityUser(school_id=school_b.id, email=f"admin_b_hst_{uuid.uuid4().hex[:4]}@school.com", password_hash="hash", first_name="User", last_name="B", is_active=True, status="ACTIVE")
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


def test_hostel_unauthenticated_and_inactive_rejected(client: TestClient, db_session: Session):
    seed_identity(db_session)

    school = School(
        name="Hostel Auth School",
        code=f"HAS-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()

    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin", school_id=None).first()

    inactive_user = IdentityUser(
        school_id=school.id,
        email=f"inactive_{uuid.uuid4().hex[:4]}@school.com",
        password_hash="hash",
        first_name="Inactive",
        last_name="User",
        is_active=False,
        status="INACTIVE",
    )
    db_session.add(inactive_user)
    db_session.commit()

    db_session.add(IdentityUserRole(user_id=inactive_user.id, role_id=admin_role.id))
    db_session.commit()

    # 1. Unauthenticated request without token -> 401
    res_no_auth = client.get("/api/v1/hostel/buildings")
    assert res_no_auth.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)

    # 2. Inactive user request -> 401/403
    inactive_token = jwt_manager.create_access_token(inactive_user.id, school.id)
    res_inactive = client.get("/api/v1/hostel/buildings", headers={"Authorization": f"Bearer {inactive_token}"})
    assert res_inactive.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_hostel_rbac_permission_boundaries(client: TestClient, db_session: Session):
    seed_identity(db_session)

    school = School(
        name="Hostel RBAC School",
        code=f"HRB-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()

    perm_view = db_session.query(IdentityPermission).filter_by(name="hostel.view").first()
    assert perm_view is not None

    # Role with only hostel.view permission (no hostel.create or hostel.fees.manage)
    view_only_role = IdentityRole(
        school_id=school.id,
        name=f"Hostel Viewer {uuid.uuid4().hex[:4]}",
        description="Hostel View Only",
        permissions=[perm_view],
    )
    db_session.add(view_only_role)
    db_session.commit()

    viewer_user = IdentityUser(
        school_id=school.id,
        email=f"viewer_{uuid.uuid4().hex[:4]}@school.com",
        password_hash="hash",
        first_name="Hostel",
        last_name="Viewer",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(viewer_user)
    db_session.commit()

    db_session.add(IdentityUserRole(user_id=viewer_user.id, role_id=view_only_role.id))
    db_session.commit()

    headers = {"Authorization": f"Bearer {jwt_manager.create_access_token(viewer_user.id, school.id)}"}

    # Viewer can view buildings
    res_view = client.get("/api/v1/hostel/buildings", headers=headers)
    assert res_view.status_code == 200

    # Viewer CANNOT create building (requires hostel.create)
    res_create = client.post(
        "/api/v1/hostel/buildings",
        headers=headers,
        json={"name": "New Block", "code": "NB-01", "gender_designation": "BOYS", "capacity": 30},
    )
    assert res_create.status_code == status.HTTP_403_FORBIDDEN
