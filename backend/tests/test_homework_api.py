"""
Integration Test Suite for Homework & Assignments Module (Phase 23).
Tests full homework lifecycle, submissions, grading, RBAC, and tenant isolation.
"""
import uuid
from datetime import date, timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import AcademicYearStatus, StudentStatus, Gender, TeacherStatus
from app.main import app
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.subject.subject import Subject
from app.models.teacher.teacher import Teacher
from app.models.parent.parent import Parent
from app.models.student.student import Student
from app.models.homework.homework import Homework, HomeworkStatus
from app.models.homework.homework_submission import HomeworkSubmission, SubmissionStatus
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager


from app.identity.seeders.role_seeder import role_seeder
from app.identity.seeders.permission_seeder import permission_seeder
from app.identity.seeders.role_permission_seeder import role_permission_seeder


@pytest.fixture
def setup_homework_data(db_session: Session):
    role_seeder.seed(db_session)
    permission_seeder.seed(db_session)
    role_permission_seeder.seed(db_session)

    suffix = uuid.uuid4().hex[:6]

    # Create School A & B
    school_a = School(name=f"HW School A {suffix}", code=f"HWSA_{suffix}", address_line1="123 St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    school_b = School(name=f"HW School B {suffix}", code=f"HWSB_{suffix}", address_line1="456 St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001")
    db_session.add_all([school_a, school_b])
    db_session.commit()

    # Academic Years
    ay_a = AcademicYear(school_id=school_a.id, name=f"2026-2027_{suffix}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    ay_b = AcademicYear(school_id=school_b.id, name=f"2026-2027_{suffix}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    # Classes & Sections
    class_a = SchoolClass(school_id=school_a.id, name=f"Class 10_{suffix}", display_order=1)
    class_b = SchoolClass(school_id=school_b.id, name=f"Class 10_{suffix}", display_order=1)
    db_session.add_all([class_a, class_b])
    db_session.commit()

    sec_a = Section(school_class_id=class_a.id, name="A")
    sec_b = Section(school_class_id=class_b.id, name="A")
    db_session.add_all([sec_a, sec_b])
    db_session.commit()

    # Subjects
    sub_a = Subject(school_id=school_a.id, subject_name=f"Math_{suffix}", subject_code=f"MATH_{suffix}")
    sub_b = Subject(school_id=school_b.id, subject_name=f"Math_{suffix}", subject_code=f"MATH_{suffix}")
    db_session.add_all([sub_a, sub_b])
    db_session.commit()

    # Roles
    role_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    role_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    role_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    role_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    role_rec = db_session.query(IdentityRole).filter_by(name="Receptionist").first()

    pwd = hash_password("Password@123")

    # Users for School A
    u_admin_a = IdentityUser(email=f"admin_hw_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Admin", last_name="A")
    u_teacher_a = IdentityUser(email=f"teacher_hw_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Alice", last_name="Teacher")
    u_student_a = IdentityUser(email=f"student_hw_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Charlie", last_name="Student")
    u_parent_a = IdentityUser(email=f"parent_hw_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Papa", last_name="Student")
    u_rec_a = IdentityUser(email=f"rec_hw_a_{suffix}@school.com", password_hash=pwd, school_id=school_a.id, first_name="Rec", last_name="A")

    # Users for School B
    u_admin_b = IdentityUser(email=f"admin_hw_b_{suffix}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Admin", last_name="B")
    u_teacher_b = IdentityUser(email=f"teacher_hw_b_{suffix}@school.com", password_hash=pwd, school_id=school_b.id, first_name="Bob", last_name="Teacher")
    u_student_b = IdentityUser(email=f"student_hw_b_{suffix}@school.com", password_hash=pwd, school_id=school_b.id, first_name="David", last_name="Student")

    db_session.add_all([u_admin_a, u_teacher_a, u_student_a, u_parent_a, u_rec_a, u_admin_b, u_teacher_b, u_student_b])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin_a.id, role_id=role_admin.id),
        IdentityUserRole(user_id=u_teacher_a.id, role_id=role_teacher.id),
        IdentityUserRole(user_id=u_student_a.id, role_id=role_student.id),
        IdentityUserRole(user_id=u_parent_a.id, role_id=role_parent.id),
        IdentityUserRole(user_id=u_rec_a.id, role_id=role_rec.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=role_admin.id),
        IdentityUserRole(user_id=u_teacher_b.id, role_id=role_teacher.id),
        IdentityUserRole(user_id=u_student_b.id, role_id=role_student.id),
    ])
    db_session.commit()

    # Teacher profiles
    t_a = Teacher(
        school_id=school_a.id, employee_id=f"EMP_{suffix}",
        first_name="Alice", last_name="Teacher", email=u_teacher_a.email, phone="9998887771",
        gender=Gender.FEMALE, date_of_birth=date(1990, 1, 1), joining_date=date(2020, 6, 1), status=TeacherStatus.ACTIVE,
        qualification="M.Sc Math", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    t_b = Teacher(
        school_id=school_b.id, employee_id=f"EMP_B_{suffix}",
        first_name="Bob", last_name="Teacher", email=u_teacher_b.email, phone="9998887772",
        gender=Gender.MALE, date_of_birth=date(1990, 1, 1), joining_date=date(2020, 6, 1), status=TeacherStatus.ACTIVE,
        qualification="M.Sc Math", address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    db_session.add_all([t_a, t_b])
    db_session.commit()

    # Parent profile
    p_a = Parent(
        school_id=school_a.id, father_name="Papa", mother_name="Mama",
        email=u_parent_a.email, primary_phone="9876543210", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001",
    )
    db_session.add(p_a)
    db_session.commit()

    # Student profiles
    st_a = Student(
        school_id=school_a.id, user_id=u_student_a.id, academic_year_id=ay_a.id, parent_id=p_a.id,
        school_class_id=class_a.id, section_id=sec_a.id, admission_number=f"ADM_{suffix}",
        roll_number="1", first_name="Charlie", last_name="Student", email=u_student_a.email,
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
    )
    st_b = Student(
        school_id=school_b.id, user_id=u_student_b.id, academic_year_id=ay_b.id,
        school_class_id=class_b.id, section_id=sec_b.id, admission_number=f"ADM_B_{suffix}",
        roll_number="1", first_name="David", last_name="Student", email=u_student_b.email,
        gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE,
    )
    db_session.add_all([st_a, st_b])
    db_session.commit()

    # Generate JWT tokens
    tok_admin_a = jwt_manager.create_access_token(user_id=u_admin_a.id, school_id=school_a.id)
    tok_teacher_a = jwt_manager.create_access_token(user_id=u_teacher_a.id, school_id=school_a.id)
    tok_student_a = jwt_manager.create_access_token(user_id=u_student_a.id, school_id=school_a.id)
    tok_parent_a = jwt_manager.create_access_token(user_id=u_parent_a.id, school_id=school_a.id)
    tok_rec_a = jwt_manager.create_access_token(user_id=u_rec_a.id, school_id=school_a.id)

    tok_teacher_b = jwt_manager.create_access_token(user_id=u_teacher_b.id, school_id=school_b.id)
    tok_student_b = jwt_manager.create_access_token(user_id=u_student_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b,
        "class_a": class_a, "class_b": class_b,
        "sec_a": sec_a, "sec_b": sec_b,
        "sub_a": sub_a, "sub_b": sub_b,
        "teacher_a": t_a, "teacher_b": t_b,
        "student_a": st_a, "student_b": st_b,
        "parent_a": p_a,
        "tok_admin_a": tok_admin_a, "tok_teacher_a": tok_teacher_a,
        "tok_student_a": tok_student_a, "tok_parent_a": tok_parent_a,
        "tok_rec_a": tok_rec_a,
        "tok_teacher_b": tok_teacher_b, "tok_student_b": tok_student_b,
    }


def test_01_homework_creation_and_lifecycle(setup_homework_data):
    client = TestClient(app)
    d = setup_homework_data
    headers_teacher_a = {"Authorization": f"Bearer {d['tok_teacher_a']}"}

    due_date = (date.today() + timedelta(days=5)).isoformat()

    # 1. Teacher creates homework
    create_payload = {
        "teacher_id": str(d["teacher_a"].id),
        "school_class_id": str(d["class_a"].id),
        "section_id": str(d["sec_a"].id),
        "subject_id": str(d["sub_a"].id),
        "title": "Algebra Worksheet 1",
        "description": "Complete all odd-numbered problems on page 42.",
        "due_date": due_date,
    }
    res = client.post("/api/v1/homework", json=create_payload, headers=headers_teacher_a)
    assert res.status_code == 201, res.text
    hw_id = res.json()["data"]["id"]
    assert res.json()["data"]["status"] == "DRAFT"
    assert res.json()["data"]["title"] == "Algebra Worksheet 1"

    # 2. Teacher updates homework
    update_payload = {"title": "Algebra Worksheet 1 (Revised)"}
    res = client.put(f"/api/v1/homework/{hw_id}", json=update_payload, headers=headers_teacher_a)
    assert res.status_code == 200
    assert res.json()["data"]["title"] == "Algebra Worksheet 1 (Revised)"

    # 3. Teacher publishes homework
    res = client.post(f"/api/v1/homework/{hw_id}/publish", headers=headers_teacher_a)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "PUBLISHED"
    assert res.json()["data"]["published_at"] is not None

    # 4. Get homework summary
    res = client.get("/api/v1/homework/summary", headers=headers_teacher_a)
    assert res.status_code == 200
    assert res.json()["data"]["published_count"] >= 1

    # 5. Teacher closes homework
    res = client.post(f"/api/v1/homework/{hw_id}/close", headers=headers_teacher_a)
    assert res.status_code == 200
    assert res.json()["data"]["status"] == "CLOSED"

    # 6. Teacher deletes homework
    res = client.delete(f"/api/v1/homework/{hw_id}", headers=headers_teacher_a)
    assert res.status_code == 204


def test_02_student_submission_and_teacher_grading(setup_homework_data):
    client = TestClient(app)
    d = setup_homework_data
    headers_teacher_a = {"Authorization": f"Bearer {d['tok_teacher_a']}"}
    headers_student_a = {"Authorization": f"Bearer {d['tok_student_a']}"}
    headers_parent_a = {"Authorization": f"Bearer {d['tok_parent_a']}"}

    # Create & publish homework
    create_payload = {
        "school_class_id": str(d["class_a"].id),
        "section_id": str(d["sec_a"].id),
        "subject_id": str(d["sub_a"].id),
        "title": "Geometry Proofs Assignment",
        "description": "Prove triangles ABC and DEF are congruent.",
        "due_date": (date.today() + timedelta(days=3)).isoformat(),
    }
    res_hw = client.post("/api/v1/homework", json=create_payload, headers=headers_teacher_a)
    hw_id = res_hw.json()["data"]["id"]
    client.post(f"/api/v1/homework/{hw_id}/publish", headers=headers_teacher_a)

    # Student views published homework
    res_list = client.get("/api/v1/homework", headers=headers_student_a)
    assert res_list.status_code == 200
    assert any(h["id"] == hw_id for h in res_list.json()["data"]["items"])

    # Parent views published homework
    res_parent_list = client.get("/api/v1/homework", headers=headers_parent_a)
    assert res_parent_list.status_code == 200
    assert any(h["id"] == hw_id for h in res_parent_list.json()["data"]["items"])

    # Student submits work
    submit_payload = {"content_text": "Here is my geometric proof step-by-step: 1. AB=DE, 2. BC=EF..."}
    res_sub = client.post(f"/api/v1/homework/{hw_id}/submit", json=submit_payload, headers=headers_student_a)
    assert res_sub.status_code == 201, res_sub.text
    sub_id = res_sub.json()["data"]["id"]
    assert res_sub.json()["data"]["status"] == "SUBMITTED"

    # Teacher reviews submissions for homework
    res_subs = client.get(f"/api/v1/homework/{hw_id}/submissions", headers=headers_teacher_a)
    assert res_subs.status_code == 200
    assert len(res_subs.json()["data"]["items"]) >= 1

    # Teacher grades submission
    grade_payload = {"grade": "A+", "feedback": "Flawless proof and logical structure!"}
    res_grade = client.post(f"/api/v1/homework/submissions/{sub_id}/grade", json=grade_payload, headers=headers_teacher_a)
    assert res_grade.status_code == 200
    assert res_grade.json()["data"]["grade"] == "A+"
    assert res_grade.json()["data"]["status"] == "GRADED"


def test_03_homework_rbac_permissions(setup_homework_data):
    client = TestClient(app)
    d = setup_homework_data
    headers_teacher_a = {"Authorization": f"Bearer {d['tok_teacher_a']}"}
    headers_rec_a = {"Authorization": f"Bearer {d['tok_rec_a']}"}

    create_payload = {
        "school_class_id": str(d["class_a"].id),
        "subject_id": str(d["sub_a"].id),
        "title": "RBAC Homework Test",
        "description": "Test permission bounds",
        "due_date": (date.today() + timedelta(days=2)).isoformat(),
    }

    # Receptionist attempts to create homework -> FORBIDDEN (403)
    res_rec = client.post("/api/v1/homework", json=create_payload, headers=headers_rec_a)
    assert res_rec.status_code == 403

    # Receptionist attempts to view homework -> FORBIDDEN (403)
    res_rec_list = client.get("/api/v1/homework", headers=headers_rec_a)
    assert res_rec_list.status_code == 403

    # Teacher creates homework -> SUCCESS (201)
    res_t = client.post("/api/v1/homework", json=create_payload, headers=headers_teacher_a)
    assert res_t.status_code == 201


def test_04_homework_tenant_isolation(setup_homework_data):
    client = TestClient(app)
    d = setup_homework_data
    headers_teacher_a = {"Authorization": f"Bearer {d['tok_teacher_a']}"}
    headers_teacher_b = {"Authorization": f"Bearer {d['tok_teacher_b']}"}
    headers_student_b = {"Authorization": f"Bearer {d['tok_student_b']}"}

    # School A Teacher creates & publishes homework
    create_payload = {
        "school_class_id": str(d["class_a"].id),
        "subject_id": str(d["sub_a"].id),
        "title": "Secret School A Assignment",
        "description": "Classified homework for School A students only.",
        "due_date": (date.today() + timedelta(days=2)).isoformat(),
    }
    res_create = client.post("/api/v1/homework", json=create_payload, headers=headers_teacher_a)
    assert res_create.status_code == 201
    hw_id = res_create.json()["data"]["id"]
    client.post(f"/api/v1/homework/{hw_id}/publish", headers=headers_teacher_a)

    # School B Teacher attempts to read School A homework by ID -> NOT FOUND (404)
    res_b_get = client.get(f"/api/v1/homework/{hw_id}", headers=headers_teacher_b)
    assert res_b_get.status_code == 404

    # School B Teacher attempts to edit School A homework -> NOT FOUND (404)
    res_b_put = client.put(f"/api/v1/homework/{hw_id}", json={"title": "Hacked Title"}, headers=headers_teacher_b)
    assert res_b_put.status_code == 404

    # School B Teacher attempts to delete School A homework -> NOT FOUND (404)
    res_b_del = client.delete(f"/api/v1/homework/{hw_id}", headers=headers_teacher_b)
    assert res_b_del.status_code == 404

    # School B Student attempts to submit work to School A homework -> NOT FOUND (404)
    res_b_sub = client.post(
        f"/api/v1/homework/{hw_id}/submit",
        json={"content_text": "Illegal submission"},
        headers=headers_student_b,
    )
    assert res_b_sub.status_code == 404
