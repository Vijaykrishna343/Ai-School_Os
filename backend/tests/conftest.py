import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import app.database.models  # noqa: F401 - Register all SQLAlchemy models with Base.metadata
from app.database.base import Base
from app.dependencies.database import get_db
from app.main import app as fastapi_app
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.security.current_user import get_current_user
from app.database.session import engine as db_engine
from app.models.school.school import School

Base.metadata.create_all(bind=db_engine)


@pytest.fixture
def engine():
    return db_engine


@pytest.fixture
def db_session(engine):
    connection = engine.connect()
    transaction = connection.begin()
    Session = sessionmaker(bind=connection, autoflush=False, expire_on_commit=False)
    session = Session()

    yield session

    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()


@pytest.fixture
def client(engine, db_session):
    def override_get_db():
        yield db_session

    fastapi_app.dependency_overrides[get_db] = override_get_db
    with TestClient(fastapi_app) as c:
        yield c
    fastapi_app.dependency_overrides.clear()


@pytest.fixture
def super_admin_user(db_session):
    school = School(
        id=uuid.uuid4(),
        name="Fixture School",
        code=f"FXS-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.commit()

    super_admin_role = IdentityRole(
        name="Super Admin",
        description="Super Admin Role",
        is_system=True,
    )
    db_session.add(super_admin_role)
    db_session.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email="superadmin@school.com",
        password_hash="hash",
        first_name="Super",
        last_name="Admin",
        is_active=True,
        status="ACTIVE",
    )
    user.roles = [super_admin_role]
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def authenticated_client(client, super_admin_user):
    def override_get_current_user():
        return super_admin_user

    fastapi_app.dependency_overrides[get_current_user] = override_get_current_user
    yield client
    if get_current_user in fastapi_app.dependency_overrides:
        del fastapi_app.dependency_overrides[get_current_user]
