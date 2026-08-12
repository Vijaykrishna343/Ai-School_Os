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
        name=f"ROLE_ROOM_{uuid.uuid4().hex[:6]}",
        description="Room Role",
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
        first_name="Room",
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


def test_classroom_api_flow(client, db_session):
    school, user, headers = create_school_and_user(
        db_session,
        "Classroom API School",
        "CAS1",
        ["timetable.create", "timetable.view", "timetable.update", "timetable.delete"],
    )

    # 1. Create Classroom
    create_payload = {
        "school_id": str(school.id),
        "room_number": "101",
        "building_name": "Block A",
        "capacity": 40,
        "room_type": "CLASSROOM",
    }
    response = client.post("/api/v1/classrooms", json=create_payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED, response.text
    data = response.json()
    classroom_id = data["id"]
    assert data["room_number"] == "101"

    # 2. Get Classroom by ID
    get_res = client.get(f"/api/v1/classrooms/{classroom_id}", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    assert get_res.json()["room_number"] == "101"

    # 3. List Classrooms
    list_res = client.get("/api/v1/classrooms", headers=headers)
    assert list_res.status_code == status.HTTP_200_OK
    assert list_res.json()["total"] == 1

    # 4. Update Classroom
    update_payload = {"room_number": "101-A", "room_type": "LABORATORY", "capacity": 30}
    update_res = client.put(f"/api/v1/classrooms/{classroom_id}", json=update_payload, headers=headers)
    assert update_res.status_code == status.HTTP_200_OK
    assert update_res.json()["room_number"] == "101-A"
    assert update_res.json()["room_type"] == "LABORATORY"

    # 5. Delete Classroom
    del_res = client.delete(f"/api/v1/classrooms/{classroom_id}", headers=headers)
    assert del_res.status_code == status.HTTP_204_NO_CONTENT

    # 6. Verify GET 404 after soft delete
    get_del_res = client.get(f"/api/v1/classrooms/{classroom_id}", headers=headers)
    assert get_del_res.status_code == status.HTTP_404_NOT_FOUND
