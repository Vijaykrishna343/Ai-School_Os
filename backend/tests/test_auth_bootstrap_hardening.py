"""
Phase D: First-User Bootstrap Hardening Security Tests

Verifies that privileged bootstrap creation is a durable, permanently closed,
strictly one-time setup operation that NEVER reopens when users are deactivated,
suspended, or deleted.
"""

import threading
import uuid
import pytest
from datetime import datetime, timezone

from app.models.school.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.bootstrap_state import IdentityBootstrapState
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.schemas.user import UserCreate
from app.identity.services.user_service import identity_user_service
from app.identity.repositories import (
    identity_bootstrap_repository,
    identity_user_repository,
    role_repository,
    user_role_repository,
)


def create_test_school(db, code="BOOTSCH01", name="Bootstrap Test School") -> School:
    school = School(
        id=uuid.uuid4(),
        name=name,
        code=code,
        address_line1="100 Academy Way",
        city="Metropolis",
        district="Metropolis",
        state="New York",
        country="USA",
        postal_code="10001",
    )
    db.add(school)
    db.commit()
    db.refresh(school)
    return school


def reset_to_fresh_installation(db):
    """Resets database state to a clean, unbootstrapped fresh installation."""
    db.query(IdentityUser).delete()
    db.query(IdentityBootstrapState).delete()
    db.commit()
    seed_identity(db)


def test_01_fresh_installation_reports_bootstrap_open(db_session):
    """A clean installation with is_completed=False reports platform bootstrap available."""
    db = db_session
    reset_to_fresh_installation(db)

    is_bootstrapped = identity_bootstrap_repository.is_platform_bootstrapped(db)
    assert is_bootstrapped is False

    state = identity_bootstrap_repository.get_by_scope(db, scope="platform")
    assert state is not None
    assert state.is_completed is False


def test_02_first_valid_bootstrap_succeeds_and_marks_completed(db_session, client):
    """The first unauthenticated POST /api/v1/users succeeds and permanently completes setup."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT02")

    payload = {
        "school_id": str(school.id),
        "email": "firstadmin@boot02.edu",
        "password": "SecurePassword123!",
        "first_name": "First",
        "last_name": "Admin",
    }
    response = client.post("/api/v1/users", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["email"] == "firstadmin@boot02.edu"

    # Verify persistent bootstrap state is now completed
    db.expire_all()
    assert identity_bootstrap_repository.is_platform_bootstrapped(db) is True

    state = identity_bootstrap_repository.get_by_scope(db, scope="platform")
    assert state is not None
    assert state.is_completed is True
    assert state.completed_at is not None
    assert str(state.completed_by_id) == data["id"]


def test_03_first_user_receives_school_admin_role_only(db_session, client):
    """The bootstrap user receives the designated School Admin role, not arbitrary superadmin rights."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT03")

    payload = {
        "school_id": str(school.id),
        "email": "admin@boot03.edu",
        "password": "SecurePassword123!",
        "first_name": "Admin",
        "last_name": "User",
    }
    resp = client.post("/api/v1/users", json=payload)
    assert resp.status_code == 201
    user_id = uuid.UUID(resp.json()["id"])

    user_roles = user_role_repository.get_roles(db, user_id)
    assert len(user_roles) == 1

    admin_role = role_repository.get_by_name(db, school.id, "School Admin") or role_repository.get_by_name(db, None, "School Admin")
    assert user_roles[0].role_id == admin_role.id


def test_04_second_unauthenticated_bootstrap_attempt_rejected(db_session, client):
    """After setup is completed, subsequent unauthenticated POST /api/v1/users must be rejected (401/403)."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT04")

    # 1. First user bootstraps
    payload_1 = {
        "school_id": str(school.id),
        "email": "first@boot04.edu",
        "password": "SecurePassword123!",
        "first_name": "First",
    }
    r1 = client.post("/api/v1/users", json=payload_1)
    assert r1.status_code == 201

    # 2. Second user attempts anonymous creation
    payload_2 = {
        "school_id": str(school.id),
        "email": "second@boot04.edu",
        "password": "SecurePassword123!",
        "first_name": "Second",
    }
    r2 = client.post("/api/v1/users", json=payload_2)
    assert r2.status_code in (401, 403)


def test_05_adversarial_reopening_all_users_deactivated_fails(db_session, client):
    """
    CRITICAL ADVERSARIAL TEST:
    Even when ALL users are deactivated (active_user_count == 0),
    unauthenticated bootstrap MUST REMAIN PERMANENTLY CLOSED.
    """
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT05")

    # 1. Bootstrap first user
    payload_1 = {
        "school_id": str(school.id),
        "email": "admin@boot05.edu",
        "password": "SecurePassword123!",
        "first_name": "Admin",
    }
    r1 = client.post("/api/v1/users", json=payload_1)
    assert r1.status_code == 201

    # 2. Deactivate ALL users in identity_users
    users = db.query(IdentityUser).all()
    for u in users:
        u.is_active = False
    db.commit()

    # 3. Confirm active_user_count is 0
    active_count = db.query(IdentityUser).filter(IdentityUser.is_active.is_(True), IdentityUser.is_deleted.is_(False)).count()
    assert active_count == 0

    # 4. Attacker attempts unauthenticated bootstrap creation
    payload_attack = {
        "school_id": str(school.id),
        "email": "attacker@boot05.edu",
        "password": "AttackerPass123!",
        "first_name": "Attacker",
    }
    r_attack = client.post("/api/v1/users", json=payload_attack)

    # MUST BE REJECTED!
    assert r_attack.status_code in (401, 403)

    # Confirm attacker user was NOT created
    attacker_user = identity_user_repository.get_by_email(db, school.id, "attacker@boot05.edu")
    assert attacker_user is None


def test_06_adversarial_reopening_all_users_soft_deleted_fails(db_session, client):
    """
    ADVERSARIAL TEST:
    Soft-deleting all users does NOT reopen unauthenticated bootstrap.
    """
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT06")

    # 1. Bootstrap first user
    r1 = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "admin@boot06.edu",
            "password": "SecurePassword123!",
            "first_name": "Admin",
        },
    )
    assert r1.status_code == 201

    # 2. Soft-delete all users
    users = db.query(IdentityUser).all()
    for u in users:
        u.is_deleted = True
        u.deleted_at = datetime.now(timezone.utc)
    db.commit()

    # 3. Attempt anonymous bootstrap
    r_attack = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "attacker@boot06.edu",
            "password": "AttackerPass123!",
            "first_name": "Attacker",
        },
    )
    assert r_attack.status_code in (401, 403)


def test_07_bootstrap_state_persists_across_transactions(db_session):
    """Persistent setup completion survives session commits, rollbacks, and re-queries."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT07")

    # Create a real user to satisfy FK constraint
    user = identity_user_service.create_user(
        db,
        UserCreate(
            school_id=school.id,
            email="admin@boot07.edu",
            password="SecurePassword123!",
            first_name="Admin",
        ),
    )

    # Mark completed with real user ID
    identity_bootstrap_repository.mark_completed(db, completed_by_id=user.id, scope="platform")
    db.commit()

    # Re-query
    db.expire_all()
    assert identity_bootstrap_repository.is_platform_bootstrapped(db) is True
    state = identity_bootstrap_repository.get_by_scope(db, scope="platform")
    assert state.is_completed is True
    assert state.completed_by_id == user.id


def test_08_transaction_rollback_preserves_bootstrap_availability(db_session, client):
    """If user creation fails and rolls back, bootstrap state remains uncompleted, allowing valid retry."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT08")

    # 1. Send invalid request (e.g. invalid password or school) -> fails
    invalid_payload = {
        "school_id": str(uuid.uuid4()),  # Nonexistent school
        "email": "admin@boot08.edu",
        "password": "SecurePassword123!",
        "first_name": "Admin",
    }
    res_fail = client.post("/api/v1/users", json=invalid_payload)
    assert res_fail.status_code == 404

    # Confirm bootstrap remains available
    db.expire_all()
    assert identity_bootstrap_repository.is_platform_bootstrapped(db) is False

    # 2. Subsequent valid bootstrap attempt succeeds
    valid_payload = {
        "school_id": str(school.id),
        "email": "admin@boot08.edu",
        "password": "SecurePassword123!",
        "first_name": "Admin",
    }
    res_ok = client.post("/api/v1/users", json=valid_payload)
    assert res_ok.status_code == 201

    db.expire_all()
    assert identity_bootstrap_repository.is_platform_bootstrapped(db) is True


def test_09_authenticated_admin_can_create_users_after_bootstrap(db_session, client):
    """Once bootstrap is completed, authenticated admin with user.create permission can create users."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT09")

    # 1. Bootstrap admin
    r1 = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "admin@boot09.edu",
            "password": "SecurePassword123!",
            "first_name": "Admin",
        },
    )
    assert r1.status_code == 201
    admin_id = uuid.UUID(r1.json()["id"])

    # 2. Generate token for admin
    token = jwt_manager.create_access_token(admin_id, school.id)

    # 3. Admin creates regular user
    r2 = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "staff@boot09.edu",
            "password": "SecurePassword123!",
            "first_name": "Staff",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 201
    assert r2.json()["email"] == "staff@boot09.edu"


def test_10_unprivileged_authenticated_user_cannot_create_users(db_session, client):
    """Authenticated user without user.create permission is rejected (403)."""
    db = db_session
    reset_to_fresh_installation(db)
    school = create_test_school(db, code="BOOT10")

    # 1. Bootstrap admin
    r1 = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "admin@boot10.edu",
            "password": "SecurePassword123!",
            "first_name": "Admin",
        },
    )
    assert r1.status_code == 201
    admin_id = uuid.UUID(r1.json()["id"])
    token_admin = jwt_manager.create_access_token(admin_id, school.id)

    # 2. Admin creates unprivileged user
    r2 = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "regular@boot10.edu",
            "password": "SecurePassword123!",
            "first_name": "Regular",
        },
        headers={"Authorization": f"Bearer {token_admin}"},
    )
    assert r2.status_code == 201
    regular_id = uuid.UUID(r2.json()["id"])

    # 3. Unprivileged user attempts to create another user
    token_regular = jwt_manager.create_access_token(regular_id, school.id)
    r3 = client.post(
        "/api/v1/users",
        json={
            "school_id": str(school.id),
            "email": "other@boot10.edu",
            "password": "SecurePassword123!",
            "first_name": "Other",
        },
        headers={"Authorization": f"Bearer {token_regular}"},
    )
    assert r3.status_code == 403


def test_11_concurrent_bootstrap_requests_race_condition(engine):
    """
    Simultaneous unauthenticated bootstrap requests result in exactly ONE success.
    The competing request is blocked by row locking and rejected.
    """
    from sqlalchemy.orm import sessionmaker
    TestSession = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)

    setup_session = TestSession()
    setup_session.query(IdentityUser).delete()
    setup_session.query(IdentityBootstrapState).delete()
    setup_session.commit()
    seed_identity(setup_session)

    school = School(
        id=uuid.uuid4(),
        name="Concurrent Bootstrap School",
        code=f"CONC_BOOT_{uuid.uuid4().hex[:6]}",
        status="ACTIVE",
        address_line1="123 Concurrency Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    setup_session.add(school)
    setup_session.commit()
    setup_session.close()

    barrier = threading.Barrier(2)
    results = []
    errors = []

    def attempt_bootstrap(email_suffix):
        session = TestSession()
        barrier.wait()
        try:
            user_in = UserCreate(
                school_id=school.id,
                email=f"admin_{email_suffix}@boot11.edu",
                password="SecurePassword123!",
                first_name=f"Admin{email_suffix}",
            )
            created = identity_user_service.create_user(
                session,
                user_in,
                current_user=None,
                is_bootstrap_request=True,
            )
            results.append(created.email)
        except Exception as ex:
            errors.append(type(ex).__name__)
        finally:
            session.close()

    t1 = threading.Thread(target=attempt_bootstrap, args=("A",))
    t2 = threading.Thread(target=attempt_bootstrap, args=("B",))

    t1.start()
    t2.start()

    t1.join()
    t2.join()

    # Exactly one thread succeeds, one thread fails
    assert len(results) == 1, f"Expected exactly 1 success, got {results}"
    assert len(errors) == 1, f"Expected exactly 1 failure, got {errors}"
    assert errors[0] in ("ForbiddenException", "IntegrityError")
