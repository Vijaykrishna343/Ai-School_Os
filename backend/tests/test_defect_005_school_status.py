import uuid
from app.models.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.jwt_manager import jwt_manager

def test_school_status_update_e2e(client, db_session):
    # Create test school using UUID object
    sch_id = uuid.uuid4()
    sch = School(
        id=sch_id, name="Status Test School", code=f"STAT_{sch_id.hex[:6]}", status="ACTIVE",
        address_line1="1 St", city="City", district="Dist", state="State", country="India", postal_code="500001"
    )
    db_session.add(sch)
    db_session.commit()

    # Create Super Admin user & role assignment
    sa_role = db_session.query(IdentityRole).filter_by(name="Super Admin").first()
    if not sa_role:
        sa_role = IdentityRole(id=uuid.uuid4(), name="Super Admin")
        db_session.add(sa_role)
        db_session.commit()

    sa_user = IdentityUser(
        id=uuid.uuid4(), school_id=sch_id, email="sa_defect5@schoolos.com",
        password_hash="hash", first_name="Super", last_name="Admin", is_active=True
    )
    db_session.add(sa_user)
    db_session.commit()

    role_assign = IdentityUserRole(user_id=sa_user.id, role_id=sa_role.id)
    db_session.add(role_assign)
    db_session.commit()

    token = jwt_manager.create_access_token(user_id=sa_user.id, school_id=sch_id)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update status ACTIVE -> SUSPENDED
    res_suspend = client.put(f"/api/v1/schools/{str(sch_id)}/status", json={
        "status": "SUSPENDED",
        "suspension_reason": "Policy violation test"
    }, headers=headers)
    assert res_suspend.status_code == 200
    data_suspend = res_suspend.json()["data"]
    assert data_suspend["status"] == "SUSPENDED"
    assert data_suspend["suspension_reason"] == "Policy violation test"

    # 2. Update status SUSPENDED -> ACTIVE
    res_activate = client.put(f"/api/v1/schools/{str(sch_id)}/status", json={
        "status": "ACTIVE"
    }, headers=headers)
    assert res_activate.status_code == 200
    data_activate = res_activate.json()["data"]
    assert data_activate["status"] == "ACTIVE"
    assert data_activate["suspension_reason"] is None
