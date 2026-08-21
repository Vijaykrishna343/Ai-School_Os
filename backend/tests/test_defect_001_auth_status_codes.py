"""
Regression test for DEFECT-001:
Ensures authentication endpoints return HTTP 401 Unauthorized for invalid credentials / email / password,
HTTP 422 Unprocessable Entity for malformed/missing JSON payloads, and HTTP 200 for valid login.
"""

import uuid
from app.models.school import School
from app.identity.models.user import IdentityUser
from app.identity.security.password import hash_password

def test_login_status_codes(client, db_session):
    # Seed test school and user using UUID objects
    sch_id = uuid.uuid4()
    sch = School(
        id=sch_id, name="Test School", code="DEFECT1_SCH", status="ACTIVE",
        address_line1="1 St", city="City", district="Dist", state="State", country="India", postal_code="500001"
    )
    user = IdentityUser(
        id=uuid.uuid4(), school_id=sch_id, email="test_defect1@school.com",
        password_hash=hash_password("CorrectPassword123!"), first_name="Test", last_name="User", is_active=True
    )
    db_session.add_all([sch, user])
    db_session.commit()

    # 1. Malformed payload -> 422
    res_malformed = client.post("/api/v1/auth/login", json={})
    assert res_malformed.status_code == 422

    # 2. Unknown email with existing school -> 401
    res_unknown_user = client.post("/api/v1/auth/login", json={
        "school_code": "DEFECT1_SCH",
        "email": "nonexistent_user_abc123@school.com",
        "password": "AnyPassword123!"
    })
    assert res_unknown_user.status_code == 401

    # 3. Wrong password with existing user -> 401
    res_wrong_pass = client.post("/api/v1/auth/login", json={
        "school_code": "DEFECT1_SCH",
        "email": "test_defect1@school.com",
        "password": "WrongPassword123!"
    })
    assert res_wrong_pass.status_code == 401

    # 4. Valid login -> 200
    res_valid = client.post("/api/v1/auth/login", json={
        "school_code": "DEFECT1_SCH",
        "email": "test_defect1@school.com",
        "password": "CorrectPassword123!"
    })
    assert res_valid.status_code == 200
