import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.identity.models import (
    IdentityPermission,
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.repositories import permission_repository
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.models.school.school import School


def create_school_and_user(db, school_name, school_code, permissions_list):
    """
    Helper function to seed permissions, create a school, user, role with
    specified permissions, and generate a valid authorization header.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=school_code,
        address_line1="100 Academic Way",
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
        description="Test Role",
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
        email=f"user_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Pass123!"),
        first_name="Test",
        last_name="User",
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
    return school, user, headers


def test_01_authenticated_user_can_create_academic_year_for_own_school(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 1", "APIS1", ["academic_year.create"]
    )
    payload = {
        "school_id": str(school.id),
        "name": "2026-2027",
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
        "is_current": True,
    }
    response = client.post("/api/v1/academic-years/", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()["data"]
    assert data["name"] == "2026-2027"
    assert data["school_id"] == str(school.id)


def test_02_anonymous_request_is_rejected(client):
    payload = {
        "school_id": str(uuid.uuid4()),
        "name": "2026-2027",
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
        "is_current": True,
    }
    response = client.post("/api/v1/academic-years/", json=payload)
    assert response.status_code == 401


def test_03_user_without_permission_is_rejected(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 3", "APIS3", []
    )
    payload = {
        "school_id": str(school.id),
        "name": "2026-2027",
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
    }
    response = client.post("/api/v1/academic-years/", json=payload, headers=headers)
    assert response.status_code == 403


def test_04_user_with_create_permission_can_create(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 4", "APIS4", ["academic_year.create"]
    )
    payload = {
        "school_id": str(school.id),
        "name": "2026-2027",
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
    }
    response = client.post("/api/v1/academic-years/", json=payload, headers=headers)
    assert response.status_code == 201


def test_05_user_cannot_create_academic_year_for_another_school(client, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "API School 5A", "APIS5A", ["academic_year.create"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "API School 5B", "APIS5B", ["academic_year.create"]
    )

    payload = {
        "school_id": str(school_b.id),
        "name": "2026-2027",
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
    }
    response = client.post("/api/v1/academic-years/", json=payload, headers=headers_a)
    assert response.status_code == 403


def test_06_list_returns_only_current_user_school_academic_years(client, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "API School 6A", "APIS6A", ["academic_year.create", "academic_year.view"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "API School 6B", "APIS6B", ["academic_year.create", "academic_year.view"]
    )

    client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_a.id),
            "name": "2026-2027-A",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_a,
    )

    client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_b.id),
            "name": "2026-2027-B",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_b,
    )

    response_a = client.get("/api/v1/academic-years/", headers=headers_a)
    assert response_a.status_code == 200
    items_a = response_a.json()["data"]["items"]
    assert len(items_a) == 1
    assert items_a[0]["name"] == "2026-2027-A"


def test_07_user_cannot_retrieve_another_school_academic_year(client, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "API School 7A", "APIS7A", ["academic_year.create", "academic_year.view"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "API School 7B", "APIS7B", ["academic_year.create", "academic_year.view"]
    )

    res_b = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_b.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_b,
    )
    ay_b_id = res_b.json()["data"]["id"]

    response = client.get(f"/api/v1/academic-years/{ay_b_id}", headers=headers_a)
    assert response.status_code == 404


def test_08_user_can_retrieve_own_school_academic_year(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 8", "APIS8", ["academic_year.create", "academic_year.view"]
    )
    res = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers,
    )
    ay_id = res.json()["data"]["id"]

    response = client.get(f"/api/v1/academic-years/{ay_id}", headers=headers)
    assert response.status_code == 200
    assert response.json()["data"]["id"] == ay_id


def test_09_user_can_update_own_school_academic_year(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 9", "APIS9", ["academic_year.create", "academic_year.update"]
    )
    res = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers,
    )
    ay_id = res.json()["data"]["id"]

    response = client.put(
        f"/api/v1/academic-years/{ay_id}",
        json={"name": "2026-2027 Updated"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["data"]["name"] == "2026-2027 Updated"


def test_10_user_cannot_update_another_school_academic_year(client, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "API School 10A", "APIS10A", ["academic_year.create", "academic_year.update"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "API School 10B", "APIS10B", ["academic_year.create", "academic_year.update"]
    )

    res_b = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_b.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_b,
    )
    ay_b_id = res_b.json()["data"]["id"]

    response = client.put(
        f"/api/v1/academic-years/{ay_b_id}",
        json={"name": "Hacked Name"},
        headers=headers_a,
    )
    assert response.status_code == 404


def test_11_user_can_soft_delete_own_school_academic_year(client, db_session):
    school, user, headers = create_school_and_user(
        db_session,
        "API School 11",
        "APIS11",
        ["academic_year.create", "academic_year.delete", "academic_year.view"],
    )
    res = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers,
    )
    ay_id = res.json()["data"]["id"]

    del_res = client.delete(f"/api/v1/academic-years/{ay_id}", headers=headers)
    assert del_res.status_code == 200

    get_res = client.get(f"/api/v1/academic-years/{ay_id}", headers=headers)
    assert get_res.status_code == 404


def test_12_user_cannot_delete_another_school_academic_year(client, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "API School 12A", "APIS12A", ["academic_year.create", "academic_year.delete"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "API School 12B", "APIS12B", ["academic_year.create", "academic_year.delete"]
    )

    res_b = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_b.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_b,
    )
    ay_b_id = res_b.json()["data"]["id"]

    response = client.delete(f"/api/v1/academic-years/{ay_b_id}", headers=headers_a)
    assert response.status_code == 404


def test_13_current_academic_year_switching_works(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 13", "APIS13", ["academic_year.create", "academic_year.view"]
    )
    res1 = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school.id),
            "name": "2025-2026",
            "start_date": "2025-04-01",
            "end_date": "2026-03-31",
            "is_current": True,
        },
        headers=headers,
    )
    ay1_id = res1.json()["data"]["id"]
    assert res1.json()["data"]["is_current"] is True

    res2 = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
            "is_current": True,
        },
        headers=headers,
    )
    ay2_id = res2.json()["data"]["id"]
    assert res2.json()["data"]["is_current"] is True

    get1 = client.get(f"/api/v1/academic-years/{ay1_id}", headers=headers)
    assert get1.json()["data"]["is_current"] is False


def test_14_invalid_start_end_dates_are_rejected(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 14", "APIS14", ["academic_year.create"]
    )
    payload = {
        "school_id": str(school.id),
        "name": "2026-2027",
        "start_date": "2026-12-31",
        "end_date": "2026-01-01",
    }
    response = client.post("/api/v1/academic-years/", json=payload, headers=headers)
    assert response.status_code == 422


def test_15_duplicate_name_within_same_school_is_rejected(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "API School 15", "APIS15", ["academic_year.create"]
    )
    payload = {
        "school_id": str(school.id),
        "name": "2026-2027",
        "start_date": "2026-04-01",
        "end_date": "2027-03-31",
    }
    res1 = client.post("/api/v1/academic-years/", json=payload, headers=headers)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/academic-years/", json=payload, headers=headers)
    assert res2.status_code == 409


def test_16_same_academic_year_name_allowed_in_different_school(client, db_session):
    school_a, user_a, headers_a = create_school_and_user(
        db_session, "API School 16A", "APIS16A", ["academic_year.create"]
    )
    school_b, user_b, headers_b = create_school_and_user(
        db_session, "API School 16B", "APIS16B", ["academic_year.create"]
    )

    res_a = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_a.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_a,
    )
    assert res_a.status_code == 201

    res_b = client.post(
        "/api/v1/academic-years/",
        json={
            "school_id": str(school_b.id),
            "name": "2026-2027",
            "start_date": "2026-04-01",
            "end_date": "2027-03-31",
        },
        headers=headers_b,
    )
    assert res_b.status_code == 201
