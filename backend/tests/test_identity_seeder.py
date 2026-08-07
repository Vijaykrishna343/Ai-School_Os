import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
import app.identity.models  # Ensure all identity models are registered with Base
import app.models.school  # Ensure school model is registered with Base
from app.identity.seeders import (
    seed_identity,
    permission_seeder,
    role_seeder,
    role_permission_seeder,
)
from app.identity.repositories import (
    permission_repository,
    role_repository,
    role_permission_repository,
)


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_seed_identity_first_run(db_session):
    summary = seed_identity(db_session)

    assert summary["permissions_created"] == 74
    assert summary["permissions_skipped"] == 0

    assert summary["roles_created"] == 10
    assert summary["roles_skipped"] == 0

    assert summary["assignments_created"] > 0
    assert summary["assignments_skipped"] == 0

    # Verify Database Counts
    all_perms = permission_repository.get_all(db_session)
    assert len(all_perms) == 74

    all_roles = role_repository.get_system_roles(db_session)
    assert len(all_roles) == 10

    # Verify Super Admin has all permissions
    super_admin = role_repository.get_by_name(db_session, None, "Super Admin")
    assert super_admin is not None
    super_admin_perms = role_permission_repository.get_permissions(db_session, super_admin.id)
    assert len(super_admin_perms) == 74


def test_seed_identity_idempotency(db_session):
    # First execution
    summary_1 = seed_identity(db_session)
    assert summary_1["permissions_created"] == 74
    assert summary_1["roles_created"] == 10
    assert summary_1["assignments_created"] > 0

    # Second execution (must skip all existing)
    summary_2 = seed_identity(db_session)
    assert summary_2["permissions_created"] == 0
    assert summary_2["permissions_skipped"] == 74

    assert summary_2["roles_created"] == 0
    assert summary_2["roles_skipped"] == 10

    assert summary_2["assignments_created"] == 0
    assert summary_2["assignments_skipped"] == summary_1["assignments_created"]


def test_role_permissions_matrix_coverage(db_session):
    seed_identity(db_session)

    expected_roles = [
        "Super Admin",
        "School Admin",
        "Principal",
        "Vice Principal",
        "Teacher",
        "Class Teacher",
        "Receptionist",
        "Accountant",
        "Parent",
        "Student",
    ]

    for role_name in expected_roles:
        role = role_repository.get_by_name(db_session, None, role_name)
        assert role is not None, f"Role '{role_name}' was not seeded"
        assert role.is_system is True
        assignments = role_permission_repository.get_permissions(db_session, role.id)
        assert len(assignments) > 0, f"Role '{role_name}' has no permissions assigned"
