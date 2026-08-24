"""
Security Integration Test Suite for Homework & Submissions Relationship Authorization (SEC-006B).
Tests Parent -> Linked Children and Student -> Self isolation across homework listing,
submissions listing, query tampering, zero-child, multi-child, and staff operational scopes.
"""
from datetime import date, timedelta
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.common.enums import AcademicYearStatus, StudentStatus, Gender, TeacherStatus
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
def hw_rel_fixture(db_session: Session):
    role_seeder.seed(db_session)
    permission_seeder.seed(db_session)
    role_permission_seeder.seed(db_session)

    sfx = uuid.uuid4().hex[:6]

    # Schools
    sch_a = School(name=f"HW Rel School A {sfx}", code=f"HWRA_{sfx}", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    sch_b = School(name=f"HW Rel School B {sfx}", code=f"HWRB_{sfx}", address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    db_session.add_all([sch_a, sch_b])
    db_session.commit()

    # Academic Years
    ay_a = AcademicYear(school_id=sch_a.id, name=f"2026-2027_{sfx}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    ay_b = AcademicYear(school_id=sch_b.id, name=f"2026-2027_{sfx}", start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), status=AcademicYearStatus.ACTIVE)
    db_session.add_all([ay_a, ay_b])
    db_session.commit()

    # Classes
    cls_10a = SchoolClass(school_id=sch_a.id, name=f"Class 10_{sfx}", display_order=1)
    cls_9a = SchoolClass(school_id=sch_a.id, name=f"Class 9_{sfx}", display_order=2)
    cls_10b = SchoolClass(school_id=sch_b.id, name=f"Class 10_{sfx}", display_order=1)
    db_session.add_all([cls_10a, cls_9a, cls_10b])
    db_session.commit()

    # Sections
    sec_10a = Section(school_class_id=cls_10a.id, name="A")
    sec_9a = Section(school_class_id=cls_9a.id, name="A")
    sec_10b = Section(school_class_id=cls_10b.id, name="A")
    db_session.add_all([sec_10a, sec_9a, sec_10b])
    db_session.commit()

    # Subjects
    sub_math_a = Subject(school_id=sch_a.id, subject_name=f"Math_{sfx}", subject_code=f"MATH_{sfx}")
    sub_sci_a = Subject(school_id=sch_a.id, subject_name=f"Science_{sfx}", subject_code=f"SCI_{sfx}")
    sub_math_b = Subject(school_id=sch_b.id, subject_name=f"Math_{sfx}", subject_code=f"MATH_{sfx}")
    db_session.add_all([sub_math_a, sub_sci_a, sub_math_b])
    db_session.commit()

    # Roles
    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_principal = db_session.query(IdentityRole).filter_by(name="Principal").first()
    r_teacher = db_session.query(IdentityRole).filter_by(name="Teacher").first()
    r_cteacher = db_session.query(IdentityRole).filter_by(name="Class Teacher").first()
    r_student = db_session.query(IdentityRole).filter_by(name="Student").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()
    r_rec = db_session.query(IdentityRole).filter_by(name="Receptionist").first()
    r_acc = db_session.query(IdentityRole).filter_by(name="Accountant").first()
    r_super = db_session.query(IdentityRole).filter_by(name="Super Admin").first()

    pwd = hash_password("Password@123")

    # Users
    u_admin_a = IdentityUser(email=f"admin_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Admin", last_name="A", is_active=True, status="ACTIVE")
    u_princ_a = IdentityUser(email=f"princ_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Princ", last_name="A", is_active=True, status="ACTIVE")
    u_teach_a = IdentityUser(email=f"teach_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Alice", last_name="Teacher", is_active=True, status="ACTIVE")
    u_cteach_a = IdentityUser(email=f"cteach_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Carol", last_name="Teacher", is_active=True, status="ACTIVE")
    u_st1_a = IdentityUser(email=f"st1_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Student", last_name="One", is_active=True, status="ACTIVE")
    u_st2_a = IdentityUser(email=f"st2_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Student", last_name="Two", is_active=True, status="ACTIVE")
    u_st3_a = IdentityUser(email=f"st3_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Student", last_name="Three", is_active=True, status="ACTIVE")
    u_p1_a = IdentityUser(email=f"p1_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Parent", last_name="One", is_active=True, status="ACTIVE")
    u_p2_a = IdentityUser(email=f"p2_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Parent", last_name="Two", is_active=True, status="ACTIVE")
    u_pzero_a = IdentityUser(email=f"pzero_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Parent", last_name="Zero", is_active=True, status="ACTIVE")
    u_rec_a = IdentityUser(email=f"rec_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Rec", last_name="A", is_active=True, status="ACTIVE")
    u_acc_a = IdentityUser(email=f"acc_hwrel_a_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Acc", last_name="A", is_active=True, status="ACTIVE")
    u_super = IdentityUser(email=f"super_hwrel_{sfx}@school.com", password_hash=pwd, school_id=sch_a.id, first_name="Super", last_name="Admin", is_active=True, status="ACTIVE")

    # School B Users
    u_teach_b = IdentityUser(email=f"teach_hwrel_b_{sfx}@school.com", password_hash=pwd, school_id=sch_b.id, first_name="Bob", last_name="Teacher", is_active=True, status="ACTIVE")
    u_st1_b = IdentityUser(email=f"st1_hwrel_b_{sfx}@school.com", password_hash=pwd, school_id=sch_b.id, first_name="StudentB", last_name="One", is_active=True, status="ACTIVE")

    db_session.add_all([
        u_admin_a, u_princ_a, u_teach_a, u_cteach_a, u_st1_a, u_st2_a, u_st3_a,
        u_p1_a, u_p2_a, u_pzero_a, u_rec_a, u_acc_a, u_super, u_teach_b, u_st1_b,
    ])
    db_session.commit()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin_a.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_princ_a.id, role_id=r_principal.id),
        IdentityUserRole(user_id=u_teach_a.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_cteach_a.id, role_id=r_cteacher.id),
        IdentityUserRole(user_id=u_st1_a.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_st2_a.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_st3_a.id, role_id=r_student.id),
        IdentityUserRole(user_id=u_p1_a.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_p2_a.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_pzero_a.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_rec_a.id, role_id=r_rec.id),
        IdentityUserRole(user_id=u_acc_a.id, role_id=r_acc.id),
        IdentityUserRole(user_id=u_super.id, role_id=r_super.id),
        IdentityUserRole(user_id=u_teach_b.id, role_id=r_teacher.id),
        IdentityUserRole(user_id=u_st1_b.id, role_id=r_student.id),
    ])
    db_session.commit()

    # Teacher profiles
    t_a = Teacher(school_id=sch_a.id, employee_id=f"EMP1_{sfx}", first_name="Alice", last_name="Teacher", email=u_teach_a.email, phone="9998887711", gender=Gender.FEMALE, date_of_birth=date(1990, 1, 1), joining_date=date(2020, 6, 1), status=TeacherStatus.ACTIVE, qualification="M.Sc", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    t_b = Teacher(school_id=sch_b.id, employee_id=f"EMP2_{sfx}", first_name="Bob", last_name="Teacher", email=u_teach_b.email, phone="9998887722", gender=Gender.MALE, date_of_birth=date(1990, 1, 1), joining_date=date(2020, 6, 1), status=TeacherStatus.ACTIVE, qualification="M.Sc", address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    db_session.add_all([t_a, t_b])
    db_session.commit()

    # Parents
    # Parent 1: Has Student 1 (Class 10A) and Student 2 (Class 9A) [Multi-child parent]
    p1 = Parent(school_id=sch_a.id, father_name="P1", mother_name="M1", email=u_p1_a.email, primary_phone="9876543211", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    # Parent 2: Has Student 3 (Class 10A) only
    p2 = Parent(school_id=sch_a.id, father_name="P2", mother_name="M2", email=u_p2_a.email, primary_phone="9876543212", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    # Parent Zero: Has NO linked students
    pzero = Parent(school_id=sch_a.id, father_name="PZero", mother_name="MZero", email=u_pzero_a.email, primary_phone="9876543213", address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")

    db_session.add_all([p1, p2, pzero])
    db_session.commit()

    # Students
    st1 = Student(school_id=sch_a.id, academic_year_id=ay_a.id, parent_id=p1.id, school_class_id=cls_10a.id, section_id=sec_10a.id, admission_number=f"ADM1_{sfx}", roll_number="1", first_name="Student", last_name="One", email=u_st1_a.email, gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    st2 = Student(school_id=sch_a.id, academic_year_id=ay_a.id, parent_id=p1.id, school_class_id=cls_9a.id, section_id=sec_9a.id, admission_number=f"ADM2_{sfx}", roll_number="2", first_name="Student", last_name="Two", email=u_st2_a.email, gender=Gender.FEMALE, date_of_birth=date(2011, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    st3 = Student(school_id=sch_a.id, academic_year_id=ay_a.id, parent_id=p2.id, school_class_id=cls_10a.id, section_id=sec_10a.id, admission_number=f"ADM3_{sfx}", roll_number="3", first_name="Student", last_name="Three", email=u_st3_a.email, gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE, address_line1="123 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")
    st_b = Student(school_id=sch_b.id, academic_year_id=ay_b.id, parent_id=p1.id, school_class_id=cls_10b.id, section_id=sec_10b.id, admission_number=f"ADMB_{sfx}", roll_number="1", first_name="StudentB", last_name="One", email=u_st1_b.email, gender=Gender.MALE, date_of_birth=date(2010, 1, 1), admission_date=date(2026, 6, 1), status=StudentStatus.ACTIVE, address_line1="456 St", city="Hyd", district="Hyd", state="Telangana", postal_code="500001")

    db_session.add_all([st1, st2, st3, st_b])
    db_session.commit()

    due = date.today() + timedelta(days=5)

    # Homework Assignments for School A
    hw_10a = Homework(
        school_id=sch_a.id, teacher_id=t_a.id, school_class_id=cls_10a.id, section_id=sec_10a.id, subject_id=sub_math_a.id,
        title="Class 10 Math Homework", description="Solve page 50 exercises 1-10.", due_date=due, status=HomeworkStatus.PUBLISHED,
    )
    hw_9a = Homework(
        school_id=sch_a.id, teacher_id=t_a.id, school_class_id=cls_9a.id, section_id=sec_9a.id, subject_id=sub_sci_a.id,
        title="Class 9 Science Homework", description="Draw the cell diagram.", due_date=due, status=HomeworkStatus.PUBLISHED,
    )
    hw_draft_10a = Homework(
        school_id=sch_a.id, teacher_id=t_a.id, school_class_id=cls_10a.id, section_id=sec_10a.id, subject_id=sub_math_a.id,
        title="Draft Homework Class 10", description="Unpublished homework draft.", due_date=due, status=HomeworkStatus.DRAFT,
    )
    hw_10b = Homework(
        school_id=sch_b.id, teacher_id=t_b.id, school_class_id=cls_10b.id, section_id=sec_10b.id, subject_id=sub_math_b.id,
        title="School B Class 10 Homework", description="School B exercises.", due_date=due, status=HomeworkStatus.PUBLISHED,
    )
    db_session.add_all([hw_10a, hw_9a, hw_draft_10a, hw_10b])
    db_session.commit()

    # Submissions
    sub_st1 = HomeworkSubmission(
        school_id=sch_a.id, homework_id=hw_10a.id, student_id=st1.id, content_text="Student 1 math solutions.", grade="A", feedback="Good job!", status=SubmissionStatus.GRADED
    )
    sub_st3 = HomeworkSubmission(
        school_id=sch_a.id, homework_id=hw_10a.id, student_id=st3.id, content_text="Student 3 math solutions.", grade="B+", feedback="Nice work.", status=SubmissionStatus.GRADED
    )
    sub_st2 = HomeworkSubmission(
        school_id=sch_a.id, homework_id=hw_9a.id, student_id=st2.id, content_text="Student 2 science diagram.", grade="A+", feedback="Excellent diagram!", status=SubmissionStatus.GRADED
    )
    db_session.add_all([sub_st1, sub_st3, sub_st2])
    db_session.commit()

    # Tokens
    tok_admin_a = jwt_manager.create_access_token(user_id=u_admin_a.id, school_id=sch_a.id)
    tok_princ_a = jwt_manager.create_access_token(user_id=u_princ_a.id, school_id=sch_a.id)
    tok_teach_a = jwt_manager.create_access_token(user_id=u_teach_a.id, school_id=sch_a.id)
    tok_cteach_a = jwt_manager.create_access_token(user_id=u_cteach_a.id, school_id=sch_a.id)
    tok_st1_a = jwt_manager.create_access_token(user_id=u_st1_a.id, school_id=sch_a.id)
    tok_st2_a = jwt_manager.create_access_token(user_id=u_st2_a.id, school_id=sch_a.id)
    tok_st3_a = jwt_manager.create_access_token(user_id=u_st3_a.id, school_id=sch_a.id)
    tok_p1_a = jwt_manager.create_access_token(user_id=u_p1_a.id, school_id=sch_a.id)
    tok_p2_a = jwt_manager.create_access_token(user_id=u_p2_a.id, school_id=sch_a.id)
    tok_pzero_a = jwt_manager.create_access_token(user_id=u_pzero_a.id, school_id=sch_a.id)
    tok_rec_a = jwt_manager.create_access_token(user_id=u_rec_a.id, school_id=sch_a.id)
    tok_acc_a = jwt_manager.create_access_token(user_id=u_acc_a.id, school_id=sch_a.id)
    tok_super = jwt_manager.create_access_token(user_id=u_super.id, school_id=sch_a.id)
    tok_teach_b = jwt_manager.create_access_token(user_id=u_teach_b.id, school_id=sch_b.id)
    tok_st1_b = jwt_manager.create_access_token(user_id=u_st1_b.id, school_id=sch_b.id)

    return {
        "sch_a": sch_a, "sch_b": sch_b,
        "cls_10a": cls_10a, "cls_9a": cls_9a, "cls_10b": cls_10b,
        "sec_10a": sec_10a, "sec_9a": sec_9a, "sec_10b": sec_10b,
        "st1": st1, "st2": st2, "st3": st3, "st_b": st_b,
        "p1": p1, "p2": p2, "pzero": pzero,
        "hw_10a": hw_10a, "hw_9a": hw_9a, "hw_draft_10a": hw_draft_10a, "hw_10b": hw_10b,
        "sub_st1": sub_st1, "sub_st3": sub_st3, "sub_st2": sub_st2,
        "tok_admin_a": tok_admin_a, "tok_princ_a": tok_princ_a,
        "tok_teach_a": tok_teach_a, "tok_cteach_a": tok_cteach_a,
        "tok_st1_a": tok_st1_a, "tok_st2_a": tok_st2_a, "tok_st3_a": tok_st3_a,
        "tok_p1_a": tok_p1_a, "tok_p2_a": tok_p2_a, "tok_pzero_a": tok_pzero_a,
        "tok_rec_a": tok_rec_a, "tok_acc_a": tok_acc_a, "tok_super": tok_super,
        "tok_teach_b": tok_teach_b, "tok_st1_b": tok_st1_b,
    }


# 1. Parent sees linked-child homework only
def test_parent_list_linked_child_homework(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 2 has only Student 3 (Class 10A)
    headers = {"Authorization": f"Bearer {d['tok_p2_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(d["hw_10a"].id)


# 2. Parent cannot see unrelated student's homework class
def test_parent_cannot_see_unrelated_class_homework(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 2 has child in Class 10A only. Must NOT see Class 9A homework.
    headers = {"Authorization": f"Bearer {d['tok_p2_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert not any(hw["id"] == str(d["hw_9a"].id) for hw in items)


# 3. Student sees own homework only
def test_student_list_own_homework(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Student 2 is in Class 9A. Must see only Class 9A homework.
    headers = {"Authorization": f"Bearer {d['tok_st2_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == str(d["hw_9a"].id)


# 4. Student cannot see peer homework in another class
def test_student_cannot_see_peer_homework_other_class(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Student 2 (Class 9A) must NOT see Class 10A homework.
    headers = {"Authorization": f"Bearer {d['tok_st2_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert not any(hw["id"] == str(d["hw_10a"].id) for hw in items)


# 5. Parent query tampering with student_id is blocked
def test_parent_query_tampering_blocked(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 2 (linked to Student 3) tries to query ?student_id=Student1
    headers = {"Authorization": f"Bearer {d['tok_p2_a']}"}
    res = client.get(f"/api/v1/homework?student_id={d['st1'].id}", headers=headers)
    assert res.status_code == 403


# 6. Student query tampering with student_id is blocked
def test_student_query_tampering_blocked(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Student 1 tries to query ?student_id=Student2
    headers = {"Authorization": f"Bearer {d['tok_st1_a']}"}
    res = client.get(f"/api/v1/homework?student_id={d['st2'].id}", headers=headers)
    assert res.status_code == 403


# 7. Parent class filter tampering cannot expand scope
def test_parent_class_filter_tampering_cannot_expand_scope(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 2 (linked to Class 10A child) queries ?school_class_id=Class9A
    headers = {"Authorization": f"Bearer {d['tok_p2_a']}"}
    res = client.get(f"/api/v1/homework?school_class_id={d['cls_9a'].id}", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    # Scope intersection yields 0 items
    assert len(items) == 0


# 8. Student class filter tampering cannot expand scope
def test_student_class_filter_tampering_cannot_expand_scope(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Student 2 (Class 9A) queries ?school_class_id=Class10A
    headers = {"Authorization": f"Bearer {d['tok_st2_a']}"}
    res = client.get(f"/api/v1/homework?school_class_id={d['cls_10a'].id}", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 0


# 9. Parent sees linked-child submissions only
def test_parent_sees_linked_child_submissions_only(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 1 is linked to Student 1 and Student 2.
    # For Homework 10A, both Student 1 and Student 3 submitted work.
    # Parent 1 must see Student 1 submission, but NOT Student 3 submission!
    headers = {"Authorization": f"Bearer {d['tok_p1_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == str(d["st1"].id)


# 10. Parent cannot see another student's submission
def test_parent_cannot_see_other_student_submission(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 2 is linked ONLY to Student 3.
    # For Homework 9A, only Student 2 submitted work.
    # Parent 2 listing submissions for Homework 9A must get 0 items.
    headers = {"Authorization": f"Bearer {d['tok_p2_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_9a'].id}/submissions", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 0


# 11. Student sees own submission only
def test_student_sees_own_submission_only(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Student 1 listing submissions for Homework 10A must see ONLY Student 1's submission.
    headers = {"Authorization": f"Bearer {d['tok_st1_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == str(d["st1"].id)


# 12. Student cannot see peer submission
def test_student_cannot_see_peer_submission(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Student 3 listing submissions for Homework 10A must see ONLY Student 3's submission, NOT Student 1's.
    headers = {"Authorization": f"Bearer {d['tok_st3_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 1
    assert items[0]["student_id"] == str(d["st3"].id)


# 13. Multi-child parent sees all linked children homework
def test_multi_child_parent_sees_all_linked_children_homework(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    # Parent 1 has Student 1 (Class 10A) and Student 2 (Class 9A). Must see both homeworks.
    headers = {"Authorization": f"Bearer {d['tok_p1_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    assert len(items) == 2
    hw_ids = {hw["id"] for hw in items}
    assert str(d["hw_10a"].id) in hw_ids
    assert str(d["hw_9a"].id) in hw_ids


# 14. Zero-child Parent receives empty homework list
def test_zero_child_parent_receives_empty_homework_list(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_pzero_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


# 15. Zero-child Parent receives empty submission list
def test_zero_child_parent_receives_empty_submission_list(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_pzero_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 0
    assert data["items"] == []


# 16. Cross-tenant homework access denied
def test_cross_tenant_homework_access_denied(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_teach_b']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}", headers=headers)
    assert res.status_code == 404


# 17. Cross-tenant submission access denied
def test_cross_tenant_submission_access_denied(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_teach_b']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 404


# 18. Teacher operational homework listing functional
def test_teacher_homework_listing_remains_functional(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_teach_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    # Teacher sees all homeworks in school (published & draft)
    assert len(items) >= 2


# 19. Teacher operational submission listing functional
def test_teacher_submission_listing_remains_functional(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_teach_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 200
    items = res.json()["items"]
    # Teacher sees both Student 1 and Student 3 submissions
    assert len(items) == 2


# 20. Class Teacher access remains functional
def test_class_teacher_homework_access(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_cteach_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200


# 21. Principal access remains functional
def test_principal_homework_access(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_princ_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200


# 22. Admin access remains functional
def test_admin_homework_access(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_admin_a']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200


# 23. Super Admin access remains functional
def test_super_admin_homework_access(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_super']}"}
    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 200


# 24. Student submit endpoint remains self-bound
def test_student_submit_remains_self_bound(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_st1_a']}"}
    res = client.post(
        f"/api/v1/homework/{d['hw_10a'].id}/submit",
        json={"content_text": "Self bound submission text"},
        headers=headers,
    )
    assert res.status_code in (200, 201)
    data = res.json()
    sub_data = data.get("data") or data
    assert sub_data["student_id"] == str(d["st1"].id)


# 25. Parent cannot submit homework
def test_parent_cannot_submit_homework(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_p1_a']}"}
    res = client.post(
        f"/api/v1/homework/{d['hw_10a'].id}/submit",
        json={"content_text": "Parent attempting submit"},
        headers=headers,
    )
    assert res.status_code == 403


# 26. Receptionist cannot access submissions
def test_receptionist_cannot_access_submissions(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_rec_a']}"}
    res = client.get(f"/api/v1/homework/{d['hw_10a'].id}/submissions", headers=headers)
    assert res.status_code == 403


# 27. Accountant cannot grade homework
def test_accountant_cannot_grade_homework(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers = {"Authorization": f"Bearer {d['tok_acc_a']}"}
    res = client.post(
        f"/api/v1/homework/submissions/{d['sub_st1'].id}/grade",
        json={"grade": "F", "feedback": "Illegal grade attempt"},
        headers=headers,
    )
    assert res.status_code == 403


# 28. Homework summary restricted from Parent and Student
def test_homework_summary_restricted_from_parent_and_student(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    res_p = client.get("/api/v1/homework/summary", headers={"Authorization": f"Bearer {d['tok_p1_a']}"})
    assert res_p.status_code == 403

    res_st = client.get("/api/v1/homework/summary", headers={"Authorization": f"Bearer {d['tok_st1_a']}"})
    assert res_st.status_code == 403

    res_t = client.get("/api/v1/homework/summary", headers={"Authorization": f"Bearer {d['tok_teach_a']}"})
    assert res_t.status_code == 200


# 29. Draft homework hidden from Parents and Students
def test_draft_homework_hidden_from_parents_and_students(client: TestClient, hw_rel_fixture):
    d = hw_rel_fixture
    headers_p = {"Authorization": f"Bearer {d['tok_p1_a']}"}
    res_p = client.get("/api/v1/homework", headers=headers_p)
    assert res_p.status_code == 200
    items_p = res_p.json()["items"]
    assert not any(hw["id"] == str(d["hw_draft_10a"].id) for hw in items_p)

    headers_st = {"Authorization": f"Bearer {d['tok_st1_a']}"}
    res_st = client.get("/api/v1/homework", headers=headers_st)
    assert res_st.status_code == 200
    items_st = res_st.json()["items"]
    assert not any(hw["id"] == str(d["hw_draft_10a"].id) for hw in items_st)


# 30. Unknown role fails closed
def test_unknown_role_fails_closed(client: TestClient, hw_rel_fixture, db_session: Session):
    d = hw_rel_fixture
    pwd = hash_password("Password@123")
    custom_role = IdentityRole(name="CustomUnrecognizedRole", description="Custom role")
    db_session.add(custom_role)
    db_session.commit()

    u_custom = IdentityUser(
        email=f"custom_role_{uuid.uuid4().hex[:6]}@school.com",
        password_hash=pwd,
        school_id=d["sch_a"].id,
        first_name="Custom",
        last_name="User",
        is_active=True,
        status="ACTIVE",
    )
    db_session.add(u_custom)
    db_session.commit()

    db_session.add(IdentityUserRole(user_id=u_custom.id, role_id=custom_role.id))
    db_session.commit()

    tok_custom = jwt_manager.create_access_token(user_id=u_custom.id, school_id=d["sch_a"].id)
    headers = {"Authorization": f"Bearer {tok_custom}"}

    res = client.get("/api/v1/homework", headers=headers)
    assert res.status_code == 403
