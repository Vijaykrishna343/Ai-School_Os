import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database.base import Base
import app.identity.models
import app.models.school.school
from app.models.school.school import School
from app.identity.seeders import seed_identity
from app.identity.schemas.user import UserCreate
from app.identity.services.user_service import identity_user_service
from app.identity.repositories import user_role_repository, identity_user_repository, role_repository


def create_in_memory_db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    return TestingSessionLocal()


def create_sample_school(db, code="SPRING1", name="Springfield Elementary"):
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


def test_first_user_receives_school_admin_automatically():
    db = create_in_memory_db()
    try:
        # Seed system roles including School Admin
        seed_identity(db)

        # Get system School Admin role
        admin_role = role_repository.get_by_name(db, None, "School Admin")
        assert admin_role is not None

        # Create a school
        school = create_sample_school(db, code="SPRING1", name="Springfield Elementary")

        # Create first user
        first_user_in = UserCreate(
            school_id=school.id,
            email="admin@springfield.edu",
            password="SecurePassword123!",
            first_name="Seymour",
            last_name="Skinner",
        )
        first_user = identity_user_service.create_user(db, first_user_in)

        # Verify active user count is 1
        assert identity_user_repository.count_by_school(db, school.id) == 1

        # Verify first user received School Admin role
        user_roles = user_role_repository.get_roles(db, first_user.id)
        assert len(user_roles) == 1
        assert user_roles[0].role_id == admin_role.id
    finally:
        db.close()


def test_second_user_receives_no_automatic_role():
    db = create_in_memory_db()
    try:
        seed_identity(db)

        school = create_sample_school(db, code="SPRING2", name="Springfield High")

        # Create first user (receives School Admin)
        u1_in = UserCreate(
            school_id=school.id,
            email="principal@springfield.edu",
            password="SecurePassword123!",
            first_name="Seymour",
        )
        u1 = identity_user_service.create_user(db, u1_in)
        assert len(user_role_repository.get_roles(db, u1.id)) == 1

        # Create second user for the same school
        u2_in = UserCreate(
            school_id=school.id,
            email="teacher@springfield.edu",
            password="SecurePassword123!",
            first_name="Edna",
            last_name="Krabappel",
        )
        u2 = identity_user_service.create_user(db, u2_in)

        # Verify active user count is 2
        assert identity_user_repository.count_by_school(db, school.id) == 2

        # Verify second user receives NO automatic role
        u2_roles = user_role_repository.get_roles(db, u2.id)
        assert len(u2_roles) == 0
    finally:
        db.close()


def test_first_user_in_new_school_receives_school_admin():
    db = create_in_memory_db()
    try:
        seed_identity(db)

        school1 = create_sample_school(db, code="SCH1", name="School One")
        school2 = create_sample_school(db, code="SCH2", name="School Two")

        # First user in School 1
        u1 = identity_user_service.create_user(
            db,
            UserCreate(
                school_id=school1.id,
                email="admin1@sch1.edu",
                password="SecurePassword123!",
                first_name="Admin1",
            ),
        )
        # Second user in School 1
        u2 = identity_user_service.create_user(
            db,
            UserCreate(
                school_id=school1.id,
                email="user2@sch1.edu",
                password="SecurePassword123!",
                first_name="User2",
            ),
        )

        # First user in School 2
        u3 = identity_user_service.create_user(
            db,
            UserCreate(
                school_id=school2.id,
                email="admin1@sch2.edu",
                password="SecurePassword123!",
                first_name="Admin2",
            ),
        )

        assert len(user_role_repository.get_roles(db, u1.id)) == 1
        assert len(user_role_repository.get_roles(db, u2.id)) == 0
        assert len(user_role_repository.get_roles(db, u3.id)) == 1
    finally:
        db.close()
