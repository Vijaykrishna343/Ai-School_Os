import uuid
from decimal import Decimal
import pytest

from app.identity.models import (
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity
from app.models.school.school import School


def create_school_and_user(db, school_name, school_code, permissions_list):
    """
    Helper to seed identity, create school, role, user, and return auth headers & user/school objects.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Grading Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Test Grading Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(
                role_id=role.id,
                permission_id=perm.id,
            )
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"user_{uuid.uuid4().hex[:6]}@test.com",
        password_hash=hash_password("Password123!"),
        first_name="Grading",
        last_name="Tester",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return headers, school, user


def test_01_authenticated_access(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Auth School", "ASCH", ["grading.view"]
    )
    res = client.get("/api/v1/grading-scales", headers=headers)
    assert res.status_code == 200


def test_02_unauthenticated_rejection(db_session, client):
    res = client.get("/api/v1/grading-scales")
    assert res.status_code == 401


def test_03_rbac_view_permission(db_session, client):
    # User with only grading.view should be able to GET but not POST
    headers, school, user = create_school_and_user(
        db_session, "View School", "VSCH", ["grading.view"]
    )
    res_get = client.get("/api/v1/grading-scales", headers=headers)
    assert res_get.status_code == 200

    payload = {"name": "Unauthorized Scale", "is_default": False, "entries": []}
    res_post = client.post(
        "/api/v1/grading-scales", json=payload, headers=headers
    )
    assert res_post.status_code == 403


def test_04_rbac_manage_permission(db_session, client):
    # User with grading.manage can create and update
    headers, school, user = create_school_and_user(
        db_session, "Manage School", "MSCH", ["grading.manage", "grading.view"]
    )
    payload = {"name": "Managed Scale", "is_default": False, "entries": []}
    res = client.post("/api/v1/grading-scales", json=payload, headers=headers)
    assert res.status_code == 201


def test_05_create_scale(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Create School", "CSCH", ["grading.manage", "grading.view"]
    )
    payload = {
        "name": "CBSE Standard",
        "description": "10-point scale",
        "is_default": True,
        "entries": [
            {
                "grade_code": "A1",
                "min_percentage": 91.0,
                "max_percentage": 100.0,
                "grade_point": 10.0,
                "description": "Top Grade",
                "is_pass": True,
            }
        ],
    }
    res = client.post("/api/v1/grading-scales", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "CBSE Standard"
    assert data["is_default"] is True
    assert len(data["entries"]) == 1


def test_06_list_scales(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "List School", "LSCH", ["grading.manage", "grading.view"]
    )
    client.post(
        "/api/v1/grading-scales",
        json={"name": "Scale Alpha", "is_default": False, "entries": []},
        headers=headers,
    )
    client.post(
        "/api/v1/grading-scales",
        json={"name": "Scale Beta", "is_default": True, "entries": []},
        headers=headers,
    )

    res = client.get("/api/v1/grading-scales", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 2


def test_07_get_scale(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Get School", "GSCH", ["grading.manage", "grading.view"]
    )
    res_create = client.post(
        "/api/v1/grading-scales",
        json={"name": "Target Scale", "is_default": False, "entries": []},
        headers=headers,
    )
    scale_id = res_create.json()["id"]

    res_get = client.get(f"/api/v1/grading-scales/{scale_id}", headers=headers)
    assert res_get.status_code == 200
    assert res_get.json()["name"] == "Target Scale"


def test_08_update_scale(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Update School", "USCH", ["grading.manage", "grading.view"]
    )
    res_create = client.post(
        "/api/v1/grading-scales",
        json={"name": "Original Name", "is_default": False, "entries": []},
        headers=headers,
    )
    scale_id = res_create.json()["id"]

    update_payload = {"name": "Updated Name", "is_default": True}
    res_update = client.put(
        f"/api/v1/grading-scales/{scale_id}",
        json=update_payload,
        headers=headers,
    )
    assert res_update.status_code == 200
    assert res_update.json()["name"] == "Updated Name"
    assert res_update.json()["is_default"] is True


def test_09_delete_scale(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Delete School", "DSCH", ["grading.manage", "grading.view"]
    )
    res_create = client.post(
        "/api/v1/grading-scales",
        json={"name": "Scale To Delete", "is_default": False, "entries": []},
        headers=headers,
    )
    scale_id = res_create.json()["id"]

    res_del = client.delete(
        f"/api/v1/grading-scales/{scale_id}", headers=headers
    )
    assert res_del.status_code == 204

    res_get = client.get(f"/api/v1/grading-scales/{scale_id}", headers=headers)
    assert res_get.status_code == 404


def test_10_entry_management(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Entry School", "ESCH", ["grading.manage", "grading.view"]
    )
    payload = {
        "name": "Multi Entry Scale",
        "entries": [
            {
                "grade_code": "A",
                "min_percentage": 80.0,
                "max_percentage": 100.0,
                "grade_point": 4.0,
            },
            {
                "grade_code": "B",
                "min_percentage": 60.0,
                "max_percentage": 79.99,
                "grade_point": 3.0,
            },
        ],
    }
    res = client.post("/api/v1/grading-scales", json=payload, headers=headers)
    assert res.status_code == 201
    assert len(res.json()["entries"]) == 2


def test_11_validation_errors(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Val School", "VALSCH", ["grading.manage", "grading.view"]
    )
    # Min pct > max pct
    payload = {
        "name": "Bad Min Max Scale",
        "entries": [
            {
                "grade_code": "A",
                "min_percentage": 90.0,
                "max_percentage": 80.0,
            }
        ],
    }
    res = client.post("/api/v1/grading-scales", json=payload, headers=headers)
    assert res.status_code in (400, 422)


def test_12_overlapping_grade_rejection(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Overlap School", "OVSCH", ["grading.manage", "grading.view"]
    )
    payload = {
        "name": "Overlapping Scale",
        "entries": [
            {
                "grade_code": "A",
                "min_percentage": 80.0,
                "max_percentage": 100.0,
            },
            {
                "grade_code": "B",
                "min_percentage": 75.0,
                "max_percentage": 85.0,
            },
        ],
    }
    res = client.post("/api/v1/grading-scales", json=payload, headers=headers)
    assert res.status_code in (400, 422)


def test_13_cross_school_isolation(db_session, client):
    headers1, school1, user1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["grading.manage", "grading.view"]
    )
    headers2, school2, user2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["grading.manage", "grading.view"]
    )

    res_create = client.post(
        "/api/v1/grading-scales",
        json={"name": "School 1 Scale"},
        headers=headers1,
    )
    scale_id = res_create.json()["id"]

    # User from School 2 trying to GET scale of School 1
    res_cross_get = client.get(
        f"/api/v1/grading-scales/{scale_id}", headers=headers2
    )
    assert res_cross_get.status_code == 404

    # User from School 2 trying to UPDATE scale of School 1
    res_cross_put = client.put(
        f"/api/v1/grading-scales/{scale_id}",
        json={"name": "Hacked"},
        headers=headers2,
    )
    assert res_cross_put.status_code == 404


def test_14_default_scale_behavior(db_session, client):
    headers, school, user = create_school_and_user(
        db_session, "Default API School", "DEFAPISCH", ["grading.manage", "grading.view"]
    )
    # Create scale 1 as default
    res1 = client.post(
        "/api/v1/grading-scales",
        json={"name": "Scale 1", "is_default": True},
        headers=headers,
    )
    assert res1.status_code == 201

    # Get default API endpoint
    res_def1 = client.get("/api/v1/grading-scales/default", headers=headers)
    assert res_def1.status_code == 200
    assert res_def1.json()["name"] == "Scale 1"

    # Create scale 2 as default
    res2 = client.post(
        "/api/v1/grading-scales",
        json={"name": "Scale 2", "is_default": True},
        headers=headers,
    )
    assert res2.status_code == 201

    # Get default API endpoint should now return scale 2
    res_def2 = client.get("/api/v1/grading-scales/default", headers=headers)
    assert res_def2.status_code == 200
    assert res_def2.json()["name"] == "Scale 2"
