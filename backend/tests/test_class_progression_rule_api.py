import uuid
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
from app.models.school import School
from app.models.school_class import SchoolClass


def create_test_env_with_permissions(db, permissions_list):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=f"School-{uuid.uuid4().hex[:6]}",
        code=f"SCH-{uuid.uuid4().hex[:6]}",
        address_line1="100 Academic Way",
        city="TestCity",
        district="Central",
        state="TestState",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Test Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(role_id=role.id, permission_id=perm.id)
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"user_{uuid.uuid4().hex[:6]}",
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Secret123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user_id=user.id, school_id=school.id)
    headers = {"Authorization": f"Bearer {token}"}

    c1 = SchoolClass(id=uuid.uuid4(), school_id=school.id, name="Class 1", display_order=1)
    c2 = SchoolClass(id=uuid.uuid4(), school_id=school.id, name="Class 2", display_order=2)
    db.add_all([c1, c2])
    db.commit()

    return {
        "school": school,
        "user": user,
        "token": token,
        "headers": headers,
        "c1": c1,
        "c2": c2,
    }


def test_api_class_progression_rule_crud_flow(client, db_session):
    env = create_test_env_with_permissions(
        db_session,
        ["progression_matrix.view", "progression_matrix.manage"],
    )

    # 1. Create Progression Rule
    payload = {
        "source_class_id": str(env["c1"].id),
        "target_class_id": str(env["c2"].id),
        "is_terminal": False,
        "description": "Standard Class 1 -> 2",
    }
    res_create = client.post("/api/v1/progression-matrix/", json=payload, headers=env["headers"])
    assert res_create.status_code == 201
    rule_data = res_create.json()["data"]
    rule_id = rule_data["id"]
    assert rule_data["source_class_id"] == str(env["c1"].id)
    assert rule_data["target_class_id"] == str(env["c2"].id)

    # 2. Get All Progression Rules
    res_list = client.get("/api/v1/progression-matrix/", headers=env["headers"])
    assert res_list.status_code == 200
    assert res_list.json()["data"]["total"] == 1

    # 3. Get Progression Rule By ID
    res_get = client.get(f"/api/v1/progression-matrix/{rule_id}", headers=env["headers"])
    assert res_get.status_code == 200
    assert res_get.json()["data"]["id"] == rule_id

    # 4. Update Progression Rule
    res_update = client.put(
        f"/api/v1/progression-matrix/{rule_id}",
        json={"description": "Updated rule description"},
        headers=env["headers"],
    )
    assert res_update.status_code == 200
    assert res_update.json()["data"]["description"] == "Updated rule description"

    # 5. Delete Progression Rule
    res_del = client.delete(f"/api/v1/progression-matrix/{rule_id}", headers=env["headers"])
    assert res_del.status_code == 200

    # 6. Verify Deleted
    res_after = client.get("/api/v1/progression-matrix/", headers=env["headers"])
    assert res_after.json()["data"]["total"] == 0


def test_api_rbac_permissions(client, db_session):
    # User with NO permissions
    env_no_perm = create_test_env_with_permissions(db_session, [])
    res_create = client.post(
        "/api/v1/progression-matrix/",
        json={"source_class_id": str(env_no_perm["c1"].id), "target_class_id": str(env_no_perm["c2"].id), "is_terminal": False},
        headers=env_no_perm["headers"],
    )
    assert res_create.status_code == 403

    res_view = client.get("/api/v1/progression-matrix/", headers=env_no_perm["headers"])
    assert res_view.status_code == 403

    # User with view permission only
    env_view_only = create_test_env_with_permissions(db_session, ["progression_matrix.view"])
    res_view_ok = client.get("/api/v1/progression-matrix/", headers=env_view_only["headers"])
    assert res_view_ok.status_code == 200

    res_create_fail = client.post(
        "/api/v1/progression-matrix/",
        json={"source_class_id": str(env_view_only["c1"].id), "target_class_id": str(env_view_only["c2"].id), "is_terminal": False},
        headers=env_view_only["headers"],
    )
    assert res_create_fail.status_code == 403


def test_api_tenant_isolation(client, db_session):
    env1 = create_test_env_with_permissions(db_session, ["progression_matrix.view", "progression_matrix.manage"])
    env2 = create_test_env_with_permissions(db_session, ["progression_matrix.view", "progression_matrix.manage"])

    # Env1 creates a rule
    res_create = client.post(
        "/api/v1/progression-matrix/",
        json={"source_class_id": str(env1["c1"].id), "target_class_id": str(env1["c2"].id), "is_terminal": False},
        headers=env1["headers"],
    )
    assert res_create.status_code == 201
    rule_id = res_create.json()["data"]["id"]

    # Env2 tries to access Env1's rule -> 404
    res_env2_get = client.get(f"/api/v1/progression-matrix/{rule_id}", headers=env2["headers"])
    assert res_env2_get.status_code == 404

    # Env2 tries to update Env1's rule -> 404
    res_env2_put = client.put(f"/api/v1/progression-matrix/{rule_id}", json={"description": "Hacked"}, headers=env2["headers"])
    assert res_env2_put.status_code == 404

    # Env2 tries to delete Env1's rule -> 404
    res_env2_del = client.delete(f"/api/v1/progression-matrix/{rule_id}", headers=env2["headers"])
    assert res_env2_del.status_code == 404
