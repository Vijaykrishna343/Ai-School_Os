import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity


@pytest.fixture
def setup_bulk_onboarding_data(db_session: Session):
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    school_a = School(
        name=f"Onboarding School A {s}", code=f"OSA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(school_a)
    db_session.commit()

    ay = AcademicYear(school_id=school_a.id, name=f"2025-2026 {s}", start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True)
    sc = SchoolClass(school_id=school_a.id, name="Class 5", display_order=5)
    db_session.add_all([ay, sc])
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="A")
    db_session.add(sec)
    db_session.commit()

    pwd = hash_password("Password@123")
    u_admin = IdentityUser(email=f"admin_onboard_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin")
    u_parent = IdentityUser(email=f"parent_onboard_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Parent")

    db_session.add_all([u_admin, u_parent])
    db_session.commit()

    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_parent.id, role_id=r_parent.id),
    ])
    db_session.commit()

    tok_admin = jwt_manager.create_access_token(user_id=u_admin.id, school_id=school_a.id)
    tok_parent = jwt_manager.create_access_token(user_id=u_parent.id, school_id=school_a.id)

    return {
        "school_a": school_a, "ay": ay, "sc": sc, "sec": sec,
        "tok_admin": tok_admin, "tok_parent": tok_parent,
    }


def test_01_bulk_onboarding_validation_preview(client: TestClient, setup_bulk_onboarding_data):
    d = setup_bulk_onboarding_data
    csv_content = (
        "first_name,last_name,gender,admission_number,class_name,section_name,parent_phone\n"
        "John,Doe,MALE,ADM_101,Class 5,A,9998887771\n"
        "Jane,Smith,FEMALE,ADM_102,Class 5,A,9998887772\n"
    )
    files = {"file": ("students.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post("/api/v1/import/students/preview", files=files, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["total_rows"] == 2
    assert data["valid_rows_count"] == 2
    assert data["can_commit"] is True


def test_02_bulk_onboarding_atomic_commit_success(client: TestClient, setup_bulk_onboarding_data):
    d = setup_bulk_onboarding_data
    csv_content = (
        "first_name,last_name,gender,admission_number,class_name,section_name,parent_phone\n"
        "John,Doe,MALE,ADM_201,Class 5,A,9998887771\n"
        "Jane,Smith,FEMALE,ADM_202,Class 5,A,9998887772\n"
    )
    files = {"file": ("students.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post("/api/v1/import/students/commit?atomic_mode=true", files=files, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["committed_rows"] == 2


def test_03_bulk_onboarding_atomic_rollback_on_invalid_row(client: TestClient, setup_bulk_onboarding_data):
    d = setup_bulk_onboarding_data
    csv_content = (
        "first_name,last_name,gender,admission_number,class_name,section_name,parent_phone\n"
        "John,Doe,MALE,ADM_301,Class 5,A,9998887771\n"
        "BadRow,,INVALID_GENDER,ADM_302,Class 5,A,9998887772\n"  # Invalid gender & missing last_name
    )
    files = {"file": ("students.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post("/api/v1/import/students/commit?atomic_mode=true", files=files, headers={"Authorization": f"Bearer {d['tok_admin']}"})
    assert res.status_code == 422
    data = res.json()
    assert data["success"] is False
    assert data["committed_rows"] == 0  # 100% rolled back


def test_04_parent_unauthorized_onboarding_denied(client: TestClient, setup_bulk_onboarding_data):
    d = setup_bulk_onboarding_data
    csv_content = "first_name,last_name,gender,admission_number\nJohn,Doe,MALE,ADM_401\n"
    files = {"file": ("students.csv", csv_content.encode("utf-8"), "text/csv")}
    res = client.post("/api/v1/import/students/preview", files=files, headers={"Authorization": f"Bearer {d['tok_parent']}"})
    assert res.status_code == 403
