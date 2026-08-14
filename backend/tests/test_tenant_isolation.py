import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient

from app.identity.models import (
    IdentityPermission,
    IdentityRole,
    IdentityRolePermission,
    IdentityUser,
    IdentityUserRole,
)
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.models.school.school import School
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.parent.parent import Parent
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.academic_year.academic_year import AcademicYear
from app.models.subject.subject import Subject


def create_school_user_and_headers(db, school_name, school_code, permissions_list):
    """
    Seeder helper to create a school, user, role with specific permissions,
    and return authorization headers.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=school_code,
        address_line1="100 Academic Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
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

    for perm_name in permissions_list:
        from app.identity.repositories import permission_repository
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
        email=f"user_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=hash_password("Pass123!"),
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    ur = IdentityUserRole(
        user_id=user.id,
        role_id=role.id,
    )
    db.add(ur)
    db.commit()

    token = jwt_manager.create_access_token(user.id, school.id)
    headers = {"Authorization": f"Bearer {token}"}
    return school, user, headers


@pytest.fixture
def tenant_setup(db_session):
    db = db_session
    all_perms = [
        "student.create", "student.view", "student.update", "student.delete",
        "teacher.create", "teacher.view", "teacher.update", "teacher.delete",
        "parent.create", "parent.view", "parent.update", "parent.delete",
        "class.create", "class.view", "class.update", "class.delete",
        "section.create", "section.view", "section.update", "section.delete",
        "subject.create", "subject.view", "subject.update", "subject.delete",
    ]

    # School A Setup
    school_a, user_a, headers_a = create_school_user_and_headers(
        db, "Apex School A", "APEXA", all_perms
    )
    ay_a = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="2026-2027 A",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay_a)
    class_a = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Class A",
        display_order=1,
    )
    db.add(class_a)
    db.commit()
    section_a = Section(
        id=uuid.uuid4(),
        school_class_id=class_a.id,
        name="Section A",
    )
    db.add(section_a)
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father A",
        primary_phone="1111111111",
        address_line1="100 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    db.add(parent_a)
    db.commit()
    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent_a.id,
        academic_year_id=ay_a.id,
        school_class_id=class_a.id,
        section_id=section_a.id,
        first_name="Student A",
        last_name="Test",
        gender="MALE",
        date_of_birth=date(2018, 5, 15),
        admission_date=date(2026, 4, 1),
        admission_number="ADM-A-001",
        roll_number="1",
        address_line1="100 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    db.add(student_a)
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id="EMP-A-01",
        first_name="Teacher A",
        last_name="Test",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2026, 4, 1),
        qualification="B.Ed",
        phone="9000000001",
        email="teacher_a@apex.com",
        address_line1="100 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    db.add(teacher_a)
    db.commit()

    # School B Setup
    school_b, user_b, headers_b = create_school_user_and_headers(
        db, "Apex School B", "APEXB", all_perms
    )
    ay_b = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="2026-2027 B",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay_b)
    class_b = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="Class B",
        display_order=1,
    )
    db.add(class_b)
    db.commit()
    section_b = Section(
        id=uuid.uuid4(),
        school_class_id=class_b.id,
        name="Section B",
    )
    db.add(section_b)
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Father B",
        primary_phone="2222222222",
        address_line1="200 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    db.add(parent_b)
    db.commit()
    student_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        parent_id=parent_b.id,
        academic_year_id=ay_b.id,
        school_class_id=class_b.id,
        section_id=section_b.id,
        first_name="Student B",
        last_name="Test",
        gender="MALE",
        date_of_birth=date(2018, 5, 15),
        admission_date=date(2026, 4, 1),
        admission_number="ADM-B-001",
        roll_number="1",
        address_line1="200 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    db.add(student_b)
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        employee_id="EMP-B-01",
        first_name="Teacher B",
        last_name="Test",
        gender="FEMALE",
        date_of_birth=date(1990, 1, 1),
        joining_date=date(2026, 4, 1),
        qualification="B.Ed",
        phone="9000000002",
        email="teacher_b@apex.com",
        address_line1="200 Main St",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        postal_code="411001",
    )
    subject_a = Subject(
        id=uuid.uuid4(),
        school_id=school_a.id,
        subject_code="SUB-A",
        subject_name="Subject A",
        status="ACTIVE",
        is_optional=False,
    )
    db.add(subject_a)
    subject_b = Subject(
        id=uuid.uuid4(),
        school_id=school_b.id,
        subject_code="SUB-B",
        subject_name="Subject B",
        status="ACTIVE",
        is_optional=False,
    )
    db.add(subject_b)
    db.commit()

    return {
        "school_a": school_a, "user_a": user_a, "headers_a": headers_a,
        "ay_a": ay_a, "class_a": class_a, "section_a": section_a, "parent_a": parent_a, "student_a": student_a, "teacher_a": teacher_a, "subject_a": subject_a,
        "school_b": school_b, "user_b": user_b, "headers_b": headers_b,
        "ay_b": ay_b, "class_b": class_b, "section_b": section_b, "parent_b": parent_b, "student_b": student_b, "teacher_b": teacher_b, "subject_b": subject_b,
    }


# ======================================================================
# STUDENT ISOLATION TESTS
# ======================================================================

def test_student_isolation(client, tenant_setup):
    data = tenant_setup
    student_b_id = str(data["student_b"].id)
    student_a_id = str(data["student_a"].id)

    # 1. School A cannot GET School B student (404)
    res = client.get(f"/api/v1/students/{student_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 2. School A cannot UPDATE School B student (404)
    res = client.put(f"/api/v1/students/{student_b_id}", json={"middle_name": "Tamper"}, headers=data["headers_a"])
    assert res.status_code == 404

    # 3. School A cannot DELETE School B student (404)
    res = client.delete(f"/api/v1/students/{student_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 4. School A cannot create a student under School B (it gets forced to School A)
    payload = {
        "school_id": str(data["school_b"].id),
        "parent_id": str(data["parent_a"].id),
        "academic_year_id": str(data["ay_a"].id),
        "school_class_id": str(data["class_a"].id),
        "section_id": str(data["section_a"].id),
        "first_name": "New Student",
        "last_name": "A",
        "gender": "MALE",
        "date_of_birth": "2019-01-01",
        "admission_date": "2026-04-01",
        "address_line1": "100 St",
        "city": "Pune",
        "district": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "postal_code": "411001",
    }
    res = client.post("/api/v1/students", json=payload, headers=data["headers_a"])
    assert res.status_code == 200
    assert res.json()["data"]["school_id"] == str(data["school_a"].id)

    # 5. Student list only returns School A students
    res = client.get("/api/v1/students", headers=data["headers_a"])
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for s in items:
        assert s["school_id"] == str(data["school_a"].id)


# ======================================================================
# TEACHER ISOLATION TESTS
# ======================================================================

def test_teacher_isolation(client, tenant_setup):
    data = tenant_setup
    teacher_b_id = str(data["teacher_b"].id)

    # 6. School A cannot GET School B teacher (404)
    res = client.get(f"/api/v1/teachers/{teacher_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 7. School A cannot UPDATE School B teacher (404)
    res = client.put(f"/api/v1/teachers/{teacher_b_id}", json={"middle_name": "Tamper"}, headers=data["headers_a"])
    assert res.status_code == 404

    # 8. School A cannot DELETE School B teacher (404)
    res = client.delete(f"/api/v1/teachers/{teacher_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 9. School A cannot create teacher under School B
    payload = {
        "school_id": str(data["school_b"].id),
        "first_name": "New Teacher",
        "last_name": "A",
        "gender": "FEMALE",
        "date_of_birth": "1990-01-01",
        "joining_date": "2026-04-01",
        "qualification": "B.Ed",
        "phone": "9999999999",
        "email": "new_teacher@apex.com",
        "address_line1": "100 St",
        "city": "Pune",
        "district": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
    }
    res = client.post("/api/v1/teachers", json=payload, headers=data["headers_a"])
    assert res.status_code == 200
    assert res.json()["data"]["school_id"] == str(data["school_a"].id)

    # 10. Teacher list only returns School A teachers
    res = client.get("/api/v1/teachers", headers=data["headers_a"])
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for t in items:
        assert t["school_id"] == str(data["school_a"].id)


# ======================================================================
# PARENT ISOLATION TESTS
# ======================================================================

def test_parent_isolation(client, tenant_setup):
    data = tenant_setup
    parent_b_id = str(data["parent_b"].id)

    # 11. School A cannot GET School B parent (404)
    res = client.get(f"/api/v1/parents/{parent_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 12. School A cannot UPDATE School B parent (404)
    res = client.put(f"/api/v1/parents/{parent_b_id}", json={"father_name": "Tamper"}, headers=data["headers_a"])
    assert res.status_code == 404

    # 13. School A cannot DELETE School B parent (404)
    res = client.delete(f"/api/v1/parents/{parent_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 14. School A cannot create parent under School B (forces School A)
    payload = {
        "school_id": str(data["school_b"].id),
        "father_name": "New Father",
        "primary_phone": "9999999991",
        "address_line1": "100 St",
        "city": "Pune",
        "district": "Pune",
        "state": "Maharashtra",
        "postal_code": "411001",
    }
    res = client.post("/api/v1/parents/", json=payload, headers=data["headers_a"])
    assert res.status_code == 201
    assert res.json()["data"]["school_id"] == str(data["school_a"].id)

    # 15. Parent list only returns School A parents
    res = client.get("/api/v1/parents/", headers=data["headers_a"])
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for p in items:
        assert p["school_id"] == str(data["school_a"].id)


# ======================================================================
# SCHOOL CLASS ISOLATION TESTS
# ======================================================================

def test_class_isolation(client, tenant_setup):
    data = tenant_setup
    class_b_id = str(data["class_b"].id)

    # 16. School A cannot GET School B class
    res = client.get(f"/api/v1/school-classes/{class_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 17. School A cannot UPDATE School B class
    res = client.put(f"/api/v1/school-classes/{class_b_id}", json={"name": "Tamper"}, headers=data["headers_a"])
    assert res.status_code == 404

    # 18. School A cannot DELETE School B class
    res = client.delete(f"/api/v1/school-classes/{class_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 19. School A cannot create class under School B (forces School A)
    payload = {
        "school_id": str(data["school_b"].id),
        "name": "Class B-Fake",
        "display_order": 2,
    }
    res = client.post("/api/v1/school-classes/", json=payload, headers=data["headers_a"])
    assert res.status_code == 201
    assert res.json()["data"]["school_id"] == str(data["school_a"].id)

    # 20. Class list only returns School A classes
    res = client.get("/api/v1/school-classes/", headers=data["headers_a"])
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    for c in items:
        assert c["school_id"] == str(data["school_a"].id)


# ======================================================================
# SECTION ISOLATION TESTS
# ======================================================================

def test_section_isolation(client, tenant_setup):
    data = tenant_setup
    section_b_id = str(data["section_b"].id)
    class_b_id = str(data["class_b"].id)

    # 21. School A cannot GET School B section
    res = client.get(f"/api/v1/sections/{section_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 22. School A cannot UPDATE School B section
    res = client.put(f"/api/v1/sections/{section_b_id}", json={"name": "X"}, headers=data["headers_a"])
    assert res.status_code == 404

    # 23. School A cannot DELETE School B section
    res = client.delete(f"/api/v1/sections/{section_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 24. School A cannot create section under School B class
    payload = {
        "school_class_id": class_b_id,
        "name": "Tamper",
    }
    res = client.post("/api/v1/sections", json=payload, headers=data["headers_a"])
    assert res.status_code == 404

    # 25. Section list under Class B is not viewable by School A
    res = client.get(f"/api/v1/sections/class/{class_b_id}", headers=data["headers_a"])
    assert res.status_code == 404


# ======================================================================
# RELATIONSHIP SECURITY TESTS
# ======================================================================

def test_relationship_security(client, tenant_setup):
    data = tenant_setup

    # 26. School A cannot assign School B student to School A parent
    payload = {
        "school_id": str(data["school_a"].id),
        "parent_id": str(data["parent_a"].id),
        "academic_year_id": str(data["ay_a"].id),
        "school_class_id": str(data["class_a"].id),
        "section_id": str(data["section_a"].id),
        "first_name": "Student Bad",
        "last_name": "A",
        "gender": "MALE",
        "date_of_birth": "2019-01-01",
        "admission_date": "2026-04-01",
        "address_line1": "100 St",
        "city": "Pune",
        "district": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "postal_code": "411001",
    }
    # Assign mismatching School B parent to School A student
    payload["parent_id"] = str(data["parent_b"].id)
    res = client.post("/api/v1/students", json=payload, headers=data["headers_a"])
    assert res.status_code == 404  # Since Parent B is not found in school A context

    # 27. School A cannot assign School B section to School A student
    payload["parent_id"] = str(data["parent_a"].id)
    payload["section_id"] = str(data["section_b"].id)
    res = client.post("/api/v1/students", json=payload, headers=data["headers_a"])
    assert res.status_code == 404  # Section B is not found in school A context

    # 28. School A cannot use School B class for student placement
    payload["section_id"] = str(data["section_a"].id)
    payload["school_class_id"] = str(data["class_b"].id)
    res = client.post("/api/v1/students", json=payload, headers=data["headers_a"])
    assert res.status_code == 404  # Class B is not found in school A context


# ======================================================================
# SUBJECT ISOLATION TESTS
# ======================================================================

def test_subject_isolation(client, tenant_setup):
    data = tenant_setup
    subject_b_id = str(data["subject_b"].id)

    # 29. School A cannot GET School B subject (404)
    res = client.get(f"/api/v1/subjects/{subject_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 30. School A cannot UPDATE School B subject (404)
    res = client.put(f"/api/v1/subjects/{subject_b_id}", json={"subject_name": "Tamper"}, headers=data["headers_a"])
    assert res.status_code == 404

    # 31. School A cannot DELETE School B subject (404)
    res = client.delete(f"/api/v1/subjects/{subject_b_id}", headers=data["headers_a"])
    assert res.status_code == 404

    # 32. School A cannot create subject under School B (forces School A)
    payload = {
        "school_id": str(data["school_b"].id),
        "subject_code": "SUB-NEW-A",
        "subject_name": "New Subject A",
        "status": "ACTIVE",
        "is_optional": False,
    }
    res = client.post("/api/v1/subjects", json=payload, headers=data["headers_a"])
    assert res.status_code == 201 or res.status_code == 200
    assert res.json()["school_id"] == str(data["school_a"].id)

    # 33. Subject list only returns School A subjects
    res = client.get("/api/v1/subjects", headers=data["headers_a"])
    assert res.status_code == 200
    items = res.json()["items"]
    for s in items:
        assert s["school_id"] == str(data["school_a"].id)
