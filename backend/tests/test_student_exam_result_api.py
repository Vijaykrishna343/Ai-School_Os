import uuid
from datetime import date, time
from decimal import Decimal
import pytest

from app.common.enums import Gender, StudentStatus
from app.common.enums.exam import AssessmentType, AttemptType, ExamStatus
from app.common.enums.parent import ParentRelationship
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
from app.models.academic_year.academic_year import AcademicYear
from app.models.exam.exam import Exam
from app.models.exam.exam_schedule import ExamSchedule
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.subject.subject import Subject


def create_school_and_user(db, school_name, school_code, permissions_list):
    """
    Seeds identity, creates school, role, permissions, user, user-role mapping, and returns authorization headers.
    """
    seed_identity(db)

    school = School(
        id=uuid.uuid4(),
        name=school_name,
        code=f"{school_code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Result Way",
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
        description="Test Result Role",
        is_system=False,
    )
    db.add(role)
    db.commit()

    for perm_name in permissions_list:
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


def setup_result_fixture_data(
    db, school, student_status=StudentStatus.ACTIVE, max_marks="100.00"
):
    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"AY-{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay)

    sc = SchoolClass(
        id=uuid.uuid4(),
        school_id=school.id,
        name=f"Class-{uuid.uuid4().hex[:4]}",
        display_order=1,
    )
    db.add(sc)
    db.commit()

    sec = Section(
        id=uuid.uuid4(),
        school_class_id=sc.id,
        name="Section A",
    )
    db.add(sec)

    subj = Subject(
        id=uuid.uuid4(),
        school_id=school.id,
        subject_code=f"SUBJ-{uuid.uuid4().hex[:4]}",
        subject_name="Mathematics",
    )
    db.add(subj)
    db.commit()

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name="Parent Ramesh",
        primary_phone=f"9{uuid.uuid4().int % 1000000009:09d}",
        relationship=ParentRelationship.FATHER,
        address_line1="12 Park St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    db.add(parent)
    db.commit()

    student = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        parent_id=parent.id,
        admission_number=f"ADM_{uuid.uuid4().hex[:6]}",
        roll_number=f"R_{uuid.uuid4().hex[:4]}",
        first_name="Rohan",
        last_name="Sharma",
        gender=Gender.MALE,
        date_of_birth=date(2012, 1, 1),
        admission_date=date(2026, 4, 1),
        address_line1="12 Park St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
        status=student_status,
    )
    db.add(student)
    db.commit()

    exam = Exam(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        name=f"Exam_{uuid.uuid4().hex[:6]}",
        assessment_type=AssessmentType.TERM,
        attempt_type=AttemptType.REGULAR,
        start_date=date(2026, 10, 1),
        end_date=date(2026, 10, 20),
        status=ExamStatus.DRAFT,
    )
    db.add(exam)
    db.commit()

    schedule = ExamSchedule(
        id=uuid.uuid4(),
        exam_id=exam.id,
        school_id=school.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        subject_id=subj.id,
        exam_date=date(2026, 10, 5),
        start_time=time(9, 0),
        end_time=time(11, 0),
        maximum_marks=Decimal(max_marks),
        passing_marks=Decimal("35.00"),
    )
    db.add(schedule)
    db.commit()

    return ay, sc, sec, subj, student, exam, schedule


# ----------------------------------------------------------------------
# API TESTS
# ----------------------------------------------------------------------

def test_01_authenticated_create(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Result School 1", "RES1", ["exam.create"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "88.50",
        "remarks": "Good performance",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["exam_schedule_id"] == str(schedule.id)
    assert data["student_id"] == str(student.id)
    assert float(data["marks_obtained"]) == 88.50
    assert data["remarks"] == "Good performance"


def test_02_anonymous_rejection(client):
    response = client.post("/api/v1/student-exam-results", json={})
    assert response.status_code == 401


def test_03_missing_permission_rejection(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "No Perm School", "NOPERM", ["exam.view"]
    )
    payload = {
        "exam_schedule_id": str(uuid.uuid4()),
        "student_id": str(uuid.uuid4()),
        "marks_obtained": "50.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert response.status_code == 403


def test_04_cross_school_schedule_rejection(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["exam.create"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["exam.create"]
    )

    ay1, sc1, sec1, subj1, student1, exam1, schedule1 = setup_result_fixture_data(
        db_session, school1
    )
    ay2, sc2, sec2, subj2, student2, exam2, schedule2 = setup_result_fixture_data(
        db_session, school2
    )

    # user1 tries using schedule2 from school2
    payload = {
        "exam_schedule_id": str(schedule2.id),
        "student_id": str(student1.id),
        "marks_obtained": "50.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers1
    )
    assert response.status_code == 422


def test_05_cross_school_student_rejection(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["exam.create"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["exam.create"]
    )

    ay1, sc1, sec1, subj1, student1, exam1, schedule1 = setup_result_fixture_data(
        db_session, school1
    )
    ay2, sc2, sec2, subj2, student2, exam2, schedule2 = setup_result_fixture_data(
        db_session, school2
    )

    # user1 tries using student2 from school2
    payload = {
        "exam_schedule_id": str(schedule1.id),
        "student_id": str(student2.id),
        "marks_obtained": "50.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers1
    )
    assert response.status_code == 422


def test_06_inactive_student_rejection(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Inactive Student School", "INACT", ["exam.create"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school, student_status=StudentStatus.INACTIVE
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "50.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert response.status_code == 422


def test_07_student_class_section_academic_year_mismatches(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Mismatch School", "MIS", ["exam.create"]
    )
    ay1, sc1, sec1, subj1, student1, exam1, schedule1 = setup_result_fixture_data(
        db_session, school
    )
    ay2, sc2, sec2, subj2, student2, exam2, schedule2 = setup_result_fixture_data(
        db_session, school
    )

    # Student 2 belongs to Class2/Section2/AY2, schedule1 is Class1/Section1/AY1
    payload = {
        "exam_schedule_id": str(schedule1.id),
        "student_id": str(student2.id),
        "marks_obtained": "50.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert response.status_code == 422


def test_08_marks_validations(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Marks School", "MRK", ["exam.create"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school, max_marks="100.00"
    )

    # Marks > maximum marks
    payload_exceed = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "120.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload_exceed, headers=headers
    )
    assert response.status_code == 422

    # Negative marks (Pydantic schema ge=0 validation)
    payload_neg = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "-10.00",
    }
    response = client.post(
        "/api/v1/student-exam-results", json=payload_neg, headers=headers
    )
    assert response.status_code == 422


def test_09_duplicate_active_result(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Dup Result School", "DUP", ["exam.create"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "75.00",
    }
    res1 = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert res1.status_code == 201

    res2 = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert res2.status_code == 409


def test_10_successful_retrieval_and_tenant_isolation(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["exam.create", "exam.view"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["exam.create", "exam.view"]
    )

    ay1, sc1, sec1, subj1, student1, exam1, schedule1 = setup_result_fixture_data(
        db_session, school1
    )

    payload = {
        "exam_schedule_id": str(schedule1.id),
        "student_id": str(student1.id),
        "marks_obtained": "92.00",
    }
    res = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers1
    )
    assert res.status_code == 201
    result_id = res.json()["id"]

    # Retrieval by user1
    get_res = client.get(
        f"/api/v1/student-exam-results/{result_id}", headers=headers1
    )
    assert get_res.status_code == 200
    assert get_res.json()["id"] == result_id

    # Tenant-isolated retrieval by user2 (returns 404)
    iso_res = client.get(
        f"/api/v1/student-exam-results/{result_id}", headers=headers2
    )
    assert iso_res.status_code == 404


def test_11_update(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Update School", "UPD", ["exam.create", "exam.update"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school, max_marks="100.00"
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "60.00",
    }
    res = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    result_id = res.json()["id"]

    # Valid update
    update_payload = {
        "marks_obtained": "95.00",
        "remarks": "Updated remark",
    }
    upd_res = client.put(
        f"/api/v1/student-exam-results/{result_id}",
        json=update_payload,
        headers=headers,
    )
    assert upd_res.status_code == 200
    assert float(upd_res.json()["marks_obtained"]) == 95.00
    assert upd_res.json()["remarks"] == "Updated remark"


def test_12_delete_and_cross_school_rejection(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["exam.create", "exam.delete"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["exam.create", "exam.delete"]
    )

    ay1, sc1, sec1, subj1, student1, exam1, schedule1 = setup_result_fixture_data(
        db_session, school1
    )

    payload = {
        "exam_schedule_id": str(schedule1.id),
        "student_id": str(student1.id),
        "marks_obtained": "80.00",
    }
    res = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers1
    )
    result_id = res.json()["id"]

    # User2 attempts cross-school update/delete -> 404
    cross_del = client.delete(
        f"/api/v1/student-exam-results/{result_id}", headers=headers2
    )
    assert cross_del.status_code == 404

    # User1 soft-deletes -> 204
    del_res = client.delete(
        f"/api/v1/student-exam-results/{result_id}", headers=headers1
    )
    assert del_res.status_code == 204


def test_13_pagination_and_filtering(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "List School", "LST", ["exam.create", "exam.view"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "70.00",
    }
    client.post("/api/v1/student-exam-results", json=payload, headers=headers)

    list_res = client.get(
        f"/api/v1/student-exam-results?exam_schedule_id={schedule.id}",
        headers=headers,
    )
    assert list_res.status_code == 200
    data = list_res.json()
    assert data["total"] == 1
    assert len(data["items"]) == 1


def test_14_soft_delete_then_recreate(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Recreate School", "REC", ["exam.create", "exam.delete"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "65.00",
    }
    res1 = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert res1.status_code == 201
    res1_id = res1.json()["id"]

    # Delete result
    del_res = client.delete(
        f"/api/v1/student-exam-results/{res1_id}", headers=headers
    )
    assert del_res.status_code == 204

    # Recreate same schedule and student result
    res2 = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert res2.status_code == 201
    assert res2.json()["id"] != res1_id


def test_15_get_list_query_school_id_restricted(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["exam.create", "exam.view"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["exam.create", "exam.view"]
    )

    ay1, sc1, sec1, subj1, student1, exam1, schedule1 = setup_result_fixture_data(
        db_session, school1
    )
    ay2, sc2, sec2, subj2, student2, exam2, schedule2 = setup_result_fixture_data(
        db_session, school2
    )

    payload1 = {
        "exam_schedule_id": str(schedule1.id),
        "student_id": str(student1.id),
        "marks_obtained": "80.00",
    }
    res1 = client.post(
        "/api/v1/student-exam-results", json=payload1, headers=headers1
    )
    assert res1.status_code == 201

    payload2 = {
        "exam_schedule_id": str(schedule2.id),
        "student_id": str(student2.id),
        "marks_obtained": "90.00",
    }
    res2 = client.post(
        "/api/v1/student-exam-results", json=payload2, headers=headers2
    )
    assert res2.status_code == 201

    # User 1 queries GET list passing school_id=school2.id query parameter
    list_res = client.get(
        f"/api/v1/student-exam-results?school_id={school2.id}",
        headers=headers1,
    )
    assert list_res.status_code == 200
    data = list_res.json()
    # Response must only contain results from user1's school (school1), ignoring requested school2.id
    assert data["total"] == 1
    assert data["items"][0]["id"] == res1.json()["id"]


def test_16_get_by_id_with_soft_deleted_exam_schedule(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Del Sched School", "DELS", ["exam.create", "exam.view"]
    )
    ay, sc, sec, subj, student, exam, schedule = setup_result_fixture_data(
        db_session, school
    )

    payload = {
        "exam_schedule_id": str(schedule.id),
        "student_id": str(student.id),
        "marks_obtained": "75.00",
    }
    res = client.post(
        "/api/v1/student-exam-results", json=payload, headers=headers
    )
    assert res.status_code == 201
    result_id = res.json()["id"]

    # Soft delete the ExamSchedule
    schedule.is_deleted = True
    db_session.commit()

    # Retrieving result via GET API returns 404 Not Found
    get_res = client.get(
        f"/api/v1/student-exam-results/{result_id}", headers=headers
    )
    assert get_res.status_code == 404

