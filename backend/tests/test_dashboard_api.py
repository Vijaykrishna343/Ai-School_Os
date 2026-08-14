import uuid
from datetime import date
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.common.enums import AcademicYearStatus
from app.common.enums.student import Gender
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
from app.models.academic_term.academic_term import AcademicTerm
from app.models.academic_year import AcademicYear
from app.models.parent import Parent
from app.models.school.school import School
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.student import Student
from app.models.teacher import Teacher


def create_test_school_user(db: Session, school_name: str, school_code: str, permissions: list[str]):
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=school_code,
        address_line1="100 Test St",
        city="Test City",
        district="Test Dist",
        state="Test State",
        country="India",
        postal_code="110001",
    )
    db.add(school)
    db.commit()

    role = IdentityRole(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Role_{uuid.uuid4().hex[:6]}",
        description="Test Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions:
        perm = permission_repository.get_by_name(db, perm_name)
        if perm:
            rp = IdentityRolePermission(
                role_id=role.id,
                permission_id=perm.id,
            )
            db.add(rp)
    db.commit()

    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school.id,
        email=f"admin_{uuid.uuid4().hex[:6]}@test.com",
        username=f"admin_{uuid.uuid4().hex[:6]}",
        password_hash=hash_password("Password123!"),
        first_name="Test",
        last_name="Admin",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(user_id=user.id, role_id=role.id)
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    return school, user, {"Authorization": f"Bearer {token}"}


def test_dashboard_admin_summary_authorized(client: TestClient, db_session: Session):
    school, user, headers = create_test_school_user(
        db_session, "Dashboard School 1", "DS1", ["school.view"]
    )

    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.ACTIVE,
        is_current=True,
    )
    db_session.add(ay)
    db_session.commit()

    term = AcademicTerm(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1",
        code="TERM1",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 9, 30),
        display_order=1,
        is_active=True,
    )
    db_session.add(term)
    db_session.commit()

    sc = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 10",
        display_order=10,
    )
    db_session.add(sc)
    db_session.commit()

    sec = Section(
        id=uuid.uuid4(),
        school_class_id=sc.id,
        name="A",
        capacity=40,
    )
    db_session.add(sec)
    db_session.commit()

    p = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Robert Doe",
        primary_phone=f"98765{uuid.uuid4().hex[:5]}",
        address_line1="123 Street",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
    )
    db_session.add(p)
    db_session.commit()

    st = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        parent_id=p.id,
        first_name="John",
        last_name="Doe",
        admission_number="ADM001",
        roll_number="1",
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2026, 4, 1),
        gender=Gender.MALE,
        address_line1="123 Main St",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
    )
    db_session.add(st)

    t = Teacher(
        id=uuid.uuid4(),
        school_id=school.id,
        first_name="Jane",
        last_name="Smith",
        employee_id=f"EMP_{uuid.uuid4().hex[:6]}",
        gender=Gender.FEMALE,
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2020, 1, 1),
        qualification="M.Ed",
        phone=f"98764{uuid.uuid4().hex[:5]}",
        email=f"teacher_{uuid.uuid4().hex[:6]}@test.com",
        address_line1="123 Main St",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
    )
    db_session.add(t)
    db_session.commit()

    response = client.get("/api/v1/dashboard/admin/summary", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    summary = data["data"]
    assert summary["active_students"] == 1
    assert summary["active_teachers"] == 1
    assert summary["active_parents"] == 1
    assert summary["active_classes"] == 1
    assert summary["active_sections"] == 1
    assert summary["current_academic_year"]["name"] == "2026-2027"
    assert summary["current_academic_term"]["name"] == "Term 1"


def test_dashboard_admin_summary_unauthorized_role(client: TestClient, db_session: Session):
    _, _, headers = create_test_school_user(
        db_session, "Dashboard School 2", "DS2", []  # No permissions
    )

    response = client.get("/api/v1/dashboard/admin/summary", headers=headers)
    assert response.status_code == 403


def test_dashboard_admin_summary_tenant_isolation(client: TestClient, db_session: Session):
    school1, _, headers1 = create_test_school_user(
        db_session, "Tenant School A", "TSA", ["school.view"]
    )
    school2, _, headers2 = create_test_school_user(
        db_session, "Tenant School B", "TSB", ["school.view"]
    )

    ay1 = AcademicYear(
        id=uuid.uuid4(),
        school_id=school1.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.ACTIVE,
        is_current=True,
    )
    sc1 = SchoolClass(
        id=uuid.uuid4(),
        school_id=school1.id,
        name="Class 1",
        display_order=1,
    )
    sec1 = Section(
        id=uuid.uuid4(),
        school_class_id=sc1.id,
        name="A",
        capacity=30,
    )
    p1 = Parent(
        id=uuid.uuid4(),
        school_id=school1.id,
        father_name="Parent A",
        primary_phone=f"98763{uuid.uuid4().hex[:5]}",
        address_line1="123 Street",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
    )
    db_session.add_all([ay1, sc1, sec1, p1])
    db_session.commit()

    st1 = Student(
        id=uuid.uuid4(),
        school_id=school1.id,
        academic_year_id=ay1.id,
        school_class_id=sc1.id,
        section_id=sec1.id,
        parent_id=p1.id,
        first_name="Alice",
        last_name="Wonderland",
        admission_number="ADM_A1",
        roll_number="1",
        date_of_birth=date(2011, 2, 2),
        admission_date=date(2026, 4, 1),
        gender=Gender.FEMALE,
        address_line1="123 Main St",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
    )
    db_session.add(st1)
    db_session.commit()

    # Query using headers 1 (School 1)
    res1 = client.get("/api/v1/dashboard/admin/summary", headers=headers1)
    assert res1.status_code == 200
    assert res1.json()["data"]["active_students"] == 1

    # Query using headers 2 (School 2)
    res2 = client.get("/api/v1/dashboard/admin/summary", headers=headers2)
    assert res2.status_code == 200
    assert res2.json()["data"]["active_students"] == 0


def test_dashboard_admin_summary_soft_deleted_excluded(client: TestClient, db_session: Session):
    school, _, headers = create_test_school_user(
        db_session, "Soft Delete School", "SDS", ["school.view"]
    )

    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        status=AcademicYearStatus.ACTIVE,
        is_current=True,
    )
    sc = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name="Class 1",
        display_order=1,
    )
    sec = Section(
        id=uuid.uuid4(),
        school_class_id=sc.id,
        name="A",
        capacity=30,
    )
    p = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Parent Ghost",
        primary_phone=f"98762{uuid.uuid4().hex[:5]}",
        address_line1="123 Street",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
    )
    db_session.add_all([ay, sc, sec, p])
    db_session.commit()

    st_deleted = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        parent_id=p.id,
        first_name="Ghost",
        last_name="Student",
        admission_number="ADM_DEL",
        roll_number="1",
        date_of_birth=date(2012, 3, 3),
        admission_date=date(2026, 4, 1),
        gender=Gender.MALE,
        address_line1="123 Main St",
        city="Test City",
        district="Test Dist",
        state="Test State",
        postal_code="110001",
        is_deleted=True,
    )
    db_session.add(st_deleted)
    db_session.commit()

    res = client.get("/api/v1/dashboard/admin/summary", headers=headers)
    assert res.status_code == 200
    assert res.json()["data"]["active_students"] == 0
