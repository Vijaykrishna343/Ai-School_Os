import uuid

from fastapi import status

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
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Timetable Way",
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
        name=f"ROLE_SLOT_{uuid.uuid4().hex[:6]}",
        description="Slot Role",
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
        first_name="Slot",
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


def test_period_slot_api_flow(client, db_session):
    school, user, headers = create_school_and_user(
        db_session,
        "API School",
        "AS1",
        ["timetable.create", "timetable.view", "timetable.update", "timetable.delete"],
    )

    # 1. Create PeriodSlot
    create_payload = {
        "school_id": str(school.id),
        "name": "Period 1",
        "period_type": "REGULAR",
        "start_time": "08:30:00",
        "end_time": "09:15:00",
        "display_order": 1,
    }
    response = client.post("/api/v1/period-slots", json=create_payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    slot_id = data["id"]
    assert data["name"] == "Period 1"

    # 2. Get PeriodSlot by ID
    get_res = client.get(f"/api/v1/period-slots/{slot_id}", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["name"] == "Period 1"

    # 3. List PeriodSlots
    list_res = client.get("/api/v1/period-slots", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 1

    # 4. Update PeriodSlot
    update_payload = {"name": "Updated Period 1", "period_type": "ASSEMBLY"}
    update_res = client.put(f"/api/v1/period-slots/{slot_id}", json=update_payload, headers=headers)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["name"] == "Updated Period 1"
    assert update_res.json()["period_type"] == "ASSEMBLY"

    # 5. Delete PeriodSlot
    del_res = client.delete(f"/api/v1/period-slots/{slot_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 6. Verify GET 404 after soft delete
    get_del_res = client.get(f"/api/v1/period-slots/{slot_id}", headers=headers)
    assert get_del_res.status_code == status.HTTP_404_NOT_FOUND
