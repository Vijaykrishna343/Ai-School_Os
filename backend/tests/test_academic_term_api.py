from datetime import date
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
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School


def create_school_and_user(db, school_name, school_code, permissions_list):
    """
    Seeds identity, creates school, role, permissions, user, user-role mapping, and returns authorization headers.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Term Way",
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
        name=f"ROLE_TERM_{uuid.uuid4().hex[:6]}",
        description="Term Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            db.add(
                IdentityRolePermission(
                    role_id=role.id,
                    permission_id=perm.id,
                )
            )
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        username=f"user_{uuid.uuid4().hex[:6]}",
        email=f"user_{uuid.uuid4().hex[:6]}@example.com",
        password_hash=hash_password("Password@123"),
        first_name="Term",
        last_name="Admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    db.add(IdentityUserRole(user_id=user.id, role_id=role.id))
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)

    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


def test_01_academic_term_crud_api_flow(db_session, client):
    perms = [
        "academic_term.create",
        "academic_term.view",
        "academic_term.update",
        "academic_term.delete",
    ]
    school, user, headers = create_school_and_user(db_session, "Term School", "TSCR", perms)

    ay = AcademicYear(
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db_session.add(ay)
    db_session.commit()

    # 1. Create Academic Term
    create_payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Term 1",
        "code": "TERM1",
        "start_date": "2026-04-01",
        "end_date": "2026-09-30",
        "display_order": 1,
        "is_active": True,
    }

    res = client.post("/api/v1/academic-terms", json=create_payload, headers=headers)
    assert res.status_code == 201, res.text
    data = res.json()
    term_id = data["id"]
    assert data["name"] == "Term 1"
    assert data["code"] == "TERM1"

    # 2. Get Academic Term by ID
    res = client.get(f"/api/v1/academic-terms/{term_id}", headers=headers)
    assert res.status_code == 200
    assert res.json()["id"] == term_id

    # 3. List Academic Terms
    res = client.get(f"/api/v1/academic-terms?academic_year_id={ay.id}", headers=headers)
    assert res.status_code == 200
    list_data = res.json()
    assert list_data["total"] >= 1
    assert any(item["id"] == term_id for item in list_data["items"])

    # 4. Update Academic Term
    res = client.put(
        f"/api/v1/academic-terms/{term_id}",
        json={"name": "Term 1 Revised", "code": "TERM1_REV"},
        headers=headers,
    )
    assert res.status_code == 200
    assert res.json()["name"] == "Term 1 Revised"
    assert res.json()["code"] == "TERM1_REV"

    # 5. Delete Academic Term
    res = client.delete(f"/api/v1/academic-terms/{term_id}", headers=headers)
    assert res.status_code == 204

    # 6. Verify GET 404 after soft delete
    res = client.get(f"/api/v1/academic-terms/{term_id}", headers=headers)
    assert res.status_code == 404


def test_02_academic_term_tenant_isolation_api(db_session, client):
    perms = ["academic_term.create", "academic_term.view"]
    school_1, user_1, headers_1 = create_school_and_user(db_session, "School 1", "SCH1", perms)
    school_2, user_2, headers_2 = create_school_and_user(db_session, "School 2", "SCH2", perms)

    ay_1 = AcademicYear(
        school_id=school_1.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db_session.add(ay_1)
    db_session.commit()

    # User 1 creates term in School 1
    create_payload = {
        "school_id": str(school_1.id),
        "academic_year_id": str(ay_1.id),
        "name": "Term Secret",
        "code": "TSEC",
        "start_date": "2026-04-01",
        "end_date": "2026-09-30",
    }
    res = client.post("/api/v1/academic-terms", json=create_payload, headers=headers_1)
    assert res.status_code == 201
    term_id = res.json()["id"]

    # User 2 from School 2 attempts to get term -> 404 Not Found
    res_cross = client.get(f"/api/v1/academic-terms/{term_id}", headers=headers_2)
    assert res_cross.status_code == 404
