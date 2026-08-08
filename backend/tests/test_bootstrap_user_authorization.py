import uuid
from app.models.school.school import School
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.schemas.user import UserCreate
from app.identity.services.user_service import identity_user_service
from app.identity.repositories import identity_user_repository


def create_sample_school(db, code="SCH001", name="Test School"):
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=code,
        address_line1="123 Main St",
        city="Springfield",
        district="Springfield",
        state="Illinois",
        country="USA",
        postal_code="62701",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def test_first_user_can_be_created_anonymously_on_fresh_installation(db_session, client):
    db = db_session
    seed_identity(db)
    school = create_sample_school(db)

    # Verify active users count is 0
    assert identity_user_repository.count_by_school(db, school.id) == 0

    # POST /api/v1/users anonymously (no Authorization header)
    payload = {
        "school_id": str(school.id),
        "email": "admin@testschool.edu",
        "password": "SecurePassword123!",
        "first_name": "Admin",
        "last_name": "User",
    }
    response = client.post("/api/v1/users", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "admin@testschool.edu"
    assert data["first_name"] == "Admin"

    # Verify active user count is now 1
    assert identity_user_repository.count_by_school(db, school.id) == 1


def test_second_user_requires_authentication_and_permission(db_session, client):
    db = db_session
    seed_identity(db)
    school = create_sample_school(db)

    # 1. Create first user (active user count becomes 1, receives School Admin automatically)
    first_user = identity_user_service.create_user(
        db,
        UserCreate(
            school_id=school.id,
            email="first@testschool.edu",
            password="SecurePassword123!",
            first_name="First",
        ),
    )

    # 2. Attempt to create second user anonymously -> must fail
    payload_2 = {
        "school_id": str(school.id),
        "email": "second@testschool.edu",
        "password": "SecurePassword123!",
        "first_name": "Second",
    }
    res_anon = client.post("/api/v1/users", json=payload_2)
    assert res_anon.status_code in (401, 403)

    # 3. Create a user without 'user.create' permission (second user)
    second_user = identity_user_service.create_user(
        db,
        UserCreate(
            school_id=school.id,
            email="unprivileged@testschool.edu",
            password="SecurePassword123!",
            first_name="Unprivileged",
        ),
    )
    token_unprivileged = jwt_manager.create_access_token(
        second_user.id,
        school.id,
    )

    # Attempt to create user using unprivileged user token -> must fail with 403
    payload_3 = {
        "school_id": str(school.id),
        "email": "third@testschool.edu",
        "password": "SecurePassword123!",
        "first_name": "Third",
    }
    res_unprivileged = client.post(
        "/api/v1/users",
        json=payload_3,
        headers={"Authorization": f"Bearer {token_unprivileged}"},
    )
    assert res_unprivileged.status_code == 403

    # 4. Attempt to create user using first user's token (First user has School Admin / user.create perm)
    token_admin = jwt_manager.create_access_token(
        first_user.id,
        school.id,
    )
    res_admin = client.post(
        "/api/v1/users",
        json=payload_3,
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert res_admin.status_code == 201
    assert res_admin.json()["email"] == "third@testschool.edu"


def test_existing_authorization_behavior_unchanged_for_other_endpoints(db_session, client):
    db = db_session
    seed_identity(db)
    school = create_sample_school(db)

    # Fresh installation with 0 users.
    # Other endpoints (GET /users, PUT /users/{id}, DELETE /users/{id}) MUST still enforce auth.
    dummy_id = str(uuid.uuid4())

    # Anonymous GET /users
    res_get_users = client.get("/api/v1/users")
    assert res_get_users.status_code in (401, 403)

    # Anonymous GET /users/{id}
    res_get_user = client.get(f"/api/v1/users/{dummy_id}")
    assert res_get_user.status_code in (401, 403)

    # Anonymous PUT /users/{id}
    res_put_user = client.put(f"/api/v1/users/{dummy_id}", json={"first_name": "New"})
    assert res_put_user.status_code in (401, 403)

    # Anonymous DELETE /users/{id}
    res_del_user = client.delete(f"/api/v1/users/{dummy_id}")
    assert res_del_user.status_code in (401, 403)
