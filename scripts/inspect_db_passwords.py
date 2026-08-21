"""
Seed / Reset standard test credentials for all 6 roles in dev database so browser login audit can test every role.
Roles:
1. Super Admin: superadmin@schoolos.com / SuperAdmin123!
2. Principal: principal@vaagdevi.com / Principal123!
3. Teacher: teacher@vaagdevi.com / Teacher123!
4. Class Teacher: classteacher@vaagdevi.com / ClassTeacher123!
5. Parent: parent@vaagdevi.com / Parent123!
6. Student: student@vaagdevi.com / Student123!
"""

import os
import sys
import uuid

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "backend"))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

DB_USER = os.getenv("POSTGRES_USER", "postgres")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "Eicher2789")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "school_erp")

db_url = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

import app.database.models  # noqa: F401
from app.models.school import School
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.seeders import seed_identity

def seed_test_users():
    print("=== SEEDING STANDARD TEST CREDENTIALS FOR BROWSER AUDIT ===")
    engine = create_engine(db_url)
    
    with Session(engine) as db:
        # First ensure system roles are seeded
        seed_identity(db)

        # Get or create School VGS001
        school = db.execute(select(School).where(School.code == "VGS001")).scalar_one_or_none()
        if not school:
            school = School(
                id=str(uuid.uuid4()),
                name="Vaagdevi High School",
                code="VGS001",
                status="ACTIVE",
                address_line1="10 Main St",
                city="Springfield",
                district="Dist 1",
                state="State A",
                country="India",
                postal_code="500001"
            )
            db.add(school)
            db.flush()
        print(f"School: {school.name} (Code: {school.code}, ID: {school.id})")

        # Get System Roles
        roles = db.execute(select(IdentityRole)).scalars().all()
        role_map = {r.name: r.id for r in roles}

        test_accounts = [
            ("superadmin@schoolos.com", "SuperAdmin123!", "Super Admin", school.id),
            ("principal@vaagdevi.com", "Principal123!", "Principal", school.id),
            ("teacher@vaagdevi.com", "Teacher123!", "Teacher", school.id),
            ("classteacher@vaagdevi.com", "ClassTeacher123!", "Class Teacher", school.id),
            ("parent@vaagdevi.com", "Parent123!", "Parent", school.id),
            ("student@vaagdevi.com", "Student123!", "Student", school.id),
        ]

        for email, pwd, role_name, sch_id in test_accounts:
            user = db.execute(select(IdentityUser).where(IdentityUser.email == email)).scalar_one_or_none()
            hashed = hash_password(pwd)
            if not user:
                user = IdentityUser(
                    id=str(uuid.uuid4()),
                    school_id=sch_id,
                    email=email,
                    password_hash=hashed,
                    first_name=role_name.split()[0],
                    last_name="User",
                    is_active=True
                )
                db.add(user)
                db.flush()
                print(f"Created user: {email}")
            else:
                user.password_hash = hashed
                user.is_active = True
                print(f"Updated user password: {email}")

            role_id = role_map.get(role_name)
            if role_id:
                assignment = db.execute(
                    select(IdentityUserRole).where(
                        IdentityUserRole.user_id == user.id,
                        IdentityUserRole.role_id == role_id
                    )
                ).scalar_one_or_none()
                if not assignment:
                    assignment = IdentityUserRole(
                        user_id=user.id,
                        role_id=role_id
                    )
                    db.add(assignment)
                    print(f"Assigned role '{role_name}' to {email}")

        db.commit()
    print("=== SEEDING COMPLETE ===")

if __name__ == "__main__":
    seed_test_users()
