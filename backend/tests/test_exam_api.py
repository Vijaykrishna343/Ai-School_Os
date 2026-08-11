import uuid
from datetime import date
import pytest

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
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
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
        address_line1="100 Exam Way",
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
        description="Test Exam Role",
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


def setup_exam_fixture_data(db, school):
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
    return ay, sc, sec, subj


# ----------------------------------------------------------------------
# EXAM TESTS
# ----------------------------------------------------------------------

def test_01_authenticated_create(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Auth School 1", "AUTH1", ["exam.create"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Mid Term 2026",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
        "status": "DRAFT",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 201
    assert response.json()["name"] == "Mid Term 2026"


def test_02_anonymous_rejection(client):
    response = client.post("/api/v1/exams", json={})
    assert response.status_code == 401


def test_03_missing_exam_create_permission(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "No Perm School", "NOPERM", ["student.view"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Mid Term 2026",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 403


def test_04_cross_school_exam_creation(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School 1", "SCH1", ["exam.create"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School 2", "SCH2", ["exam.create"]
    )
    ay1, _, _, _ = setup_exam_fixture_data(db_session, school1)

    payload = {
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Cross School Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    # User 2 (school 2) trying to create exam for School 1
    response = client.post("/api/v1/exams", json=payload, headers=headers2)
    assert response.status_code == 403


def test_05_cross_school_academic_year(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "School AY 1", "SAY1", ["exam.create"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "School AY 2", "SAY2", ["exam.create"]
    )
    ay2, _, _, _ = setup_exam_fixture_data(db_session, school2)

    payload = {
        "school_id": str(school1.id),
        "academic_year_id": str(ay2.id),
        "name": "Cross AY Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers1)
    assert response.status_code == 422


def test_06_duplicate_active_exam_name(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "School Dup", "SDUP", ["exam.create"]
    )
    ay, _, _, _ = setup_exam_fixture_data(db_session, school)

    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Duplicate Exam Name",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    resp1 = client.post("/api/v1/exams", json=payload, headers=headers)
    assert resp1.status_code == 201

    resp2 = client.post("/api/v1/exams", json=payload, headers=headers)
    assert resp2.status_code == 409


def test_07_invalid_start_end_dates(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "School Dates", "SDATES", ["exam.create"]
    )
    ay, _, _, _ = setup_exam_fixture_data(db_session, school)

    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Invalid Dates Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-20",
        "end_date": "2026-10-10",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 422


def test_08_exam_crud(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "CRUD School", "SCRUD", ["exam.create", "exam.view", "exam.update", "exam.delete"]
    )
    ay, _, _, _ = setup_exam_fixture_data(db_session, school)

    # Create
    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "CRUD Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    create_resp = client.post("/api/v1/exams", json=payload, headers=headers)
    assert create_resp.status_code == 201
    exam_id = create_resp.json()["id"]

    # Read
    get_resp = client.get(f"/api/v1/exams/{exam_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == exam_id

    # Update
    update_payload = {"name": "CRUD Exam Updated"}
    put_resp = client.put(f"/api/v1/exams/{exam_id}", json=update_payload, headers=headers)
    assert put_resp.status_code == 200
    assert put_resp.json()["name"] == "CRUD Exam Updated"

    # Delete
    del_resp = client.delete(f"/api/v1/exams/{exam_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify soft deleted
    get_del = client.get(f"/api/v1/exams/{exam_id}", headers=headers)
    assert get_del.status_code == 404


def test_09_exam_pagination_and_listing(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "List School", "SLIST", ["exam.create", "exam.view"]
    )
    ay, _, _, _ = setup_exam_fixture_data(db_session, school)

    for i in range(5):
        payload = {
            "school_id": str(school.id),
            "academic_year_id": str(ay.id),
            "name": f"List Exam {i}",
            "exam_type": "REGULAR",
            "start_date": "2026-10-10",
            "end_date": "2026-10-20",
        }
        client.post("/api/v1/exams", json=payload, headers=headers)

    list_resp = client.get(f"/api/v1/exams?school_id={school.id}&page=1&page_size=3", headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert data["total"] == 5
    assert len(data["items"]) == 3


def test_10_cross_school_exam_retrieval(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "Ret School 1", "SRET1", ["exam.create", "exam.view"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "Ret School 2", "SRET2", ["exam.view"]
    )
    ay1, _, _, _ = setup_exam_fixture_data(db_session, school1)

    payload = {
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Secret Exam School 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    create_resp = client.post("/api/v1/exams", json=payload, headers=headers1)
    exam_id = create_resp.json()["id"]

    # User 2 tries to view School 1's exam by ID
    resp = client.get(f"/api/v1/exams/{exam_id}", headers=headers2)
    assert resp.status_code == 404


def test_11_cross_school_exam_update(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "Upd School 1", "SUPD1", ["exam.create", "exam.update"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "Upd School 2", "SUPD2", ["exam.update"]
    )
    ay1, _, _, _ = setup_exam_fixture_data(db_session, school1)

    payload = {
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Exam School 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    create_resp = client.post("/api/v1/exams", json=payload, headers=headers1)
    exam_id = create_resp.json()["id"]

    # User 2 tries to update School 1's exam
    resp = client.put(f"/api/v1/exams/{exam_id}", json={"name": "Hacked"}, headers=headers2)
    assert resp.status_code == 404


def test_12_cross_school_exam_delete(client, db_session):
    school1, user1, headers1 = create_school_and_user(
        db_session, "Del School 1", "SDEL1", ["exam.create", "exam.delete"]
    )
    school2, user2, headers2 = create_school_and_user(
        db_session, "Del School 2", "SDEL2", ["exam.delete"]
    )
    ay1, _, _, _ = setup_exam_fixture_data(db_session, school1)

    payload = {
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Exam to Delete",
        "exam_type": "REGULAR",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    create_resp = client.post("/api/v1/exams", json=payload, headers=headers1)
    exam_id = create_resp.json()["id"]

    # User 2 tries to delete School 1's exam
    resp = client.delete(f"/api/v1/exams/{exam_id}", headers=headers2)
    assert resp.status_code == 404


# ----------------------------------------------------------------------
# EXAM SCHEDULE TESTS
# ----------------------------------------------------------------------

def test_13_authenticated_exam_schedule_creation(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "Sched Auth School", "SASH1", ["exam.create"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Exam Sched 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code == 201


def test_14_exam_schedule_missing_permission(client, db_session):
    school, user, headers = create_school_and_user(
        db_session, "No Sched Perm", "NOSP", ["student.view"]
    )
    resp = client.post("/api/v1/exam-schedules", json={}, headers=headers)
    assert resp.status_code == 403


def test_15_cross_school_exam_schedule_exam(client, db_session):
    school1, user1, headers1 = create_school_and_user(db_session, "Sch1", "S1", ["exam.create"])
    school2, user2, headers2 = create_school_and_user(db_session, "Sch2", "S2", ["exam.create"])

    ay1, sc1, sec1, subj1 = setup_exam_fixture_data(db_session, school1)
    ay2, _, _, _ = setup_exam_fixture_data(db_session, school2)

    exam2_resp = client.post("/api/v1/exams", json={
        "school_id": str(school2.id),
        "academic_year_id": str(ay2.id),
        "name": "Exam Sch 2",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers2)
    exam2_id = exam2_resp.json()["id"]

    # User 1 tries to create schedule for Exam 2 (belongs to School 2)
    sched_payload = {
        "exam_id": exam2_id,
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "school_class_id": str(sc1.id),
        "section_id": str(sec1.id),
        "subject_id": str(subj1.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers1)
    assert resp.status_code in [404, 422]


def test_16_cross_school_exam_schedule_class(client, db_session):
    school1, user1, headers1 = create_school_and_user(db_session, "CS School 1", "CS1", ["exam.create"])
    school2, user2, headers2 = create_school_and_user(db_session, "CS School 2", "CS2", ["exam.create"])

    ay1, sc1, sec1, subj1 = setup_exam_fixture_data(db_session, school1)
    ay2, sc2, sec2, subj2 = setup_exam_fixture_data(db_session, school2)

    exam1_resp = client.post("/api/v1/exams", json={
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Exam Sch 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers1)
    exam1_id = exam1_resp.json()["id"]

    # Reference Class 2 (belongs to School 2)
    sched_payload = {
        "exam_id": exam1_id,
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "school_class_id": str(sc2.id),
        "section_id": str(sec1.id),
        "subject_id": str(subj1.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers1)
    assert resp.status_code == 422


def test_17_cross_school_exam_schedule_section(client, db_session):
    school1, user1, headers1 = create_school_and_user(db_session, "Sec Sch 1", "SS1", ["exam.create"])
    school2, user2, headers2 = create_school_and_user(db_session, "Sec Sch 2", "SS2", ["exam.create"])

    ay1, sc1, sec1, subj1 = setup_exam_fixture_data(db_session, school1)
    ay2, sc2, sec2, subj2 = setup_exam_fixture_data(db_session, school2)

    exam1_resp = client.post("/api/v1/exams", json={
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Exam Sch Sec 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers1)
    exam1_id = exam1_resp.json()["id"]

    sched_payload = {
        "exam_id": exam1_id,
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "school_class_id": str(sc1.id),
        "section_id": str(sec2.id),
        "subject_id": str(subj1.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers1)
    assert resp.status_code == 422


def test_18_cross_school_exam_schedule_subject(client, db_session):
    school1, user1, headers1 = create_school_and_user(db_session, "Subj Sch 1", "SUB1", ["exam.create"])
    school2, user2, headers2 = create_school_and_user(db_session, "Subj Sch 2", "SUB2", ["exam.create"])

    ay1, sc1, sec1, subj1 = setup_exam_fixture_data(db_session, school1)
    ay2, sc2, sec2, subj2 = setup_exam_fixture_data(db_session, school2)

    exam1_resp = client.post("/api/v1/exams", json={
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Exam Sch Subj 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers1)
    exam1_id = exam1_resp.json()["id"]

    sched_payload = {
        "exam_id": exam1_id,
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "school_class_id": str(sc1.id),
        "section_id": str(sec1.id),
        "subject_id": str(subj2.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers1)
    assert resp.status_code == 422


def test_19_section_class_mismatch(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Mismatch Sch", "MM1", ["exam.create"])
    ay, sc1, sec1, subj = setup_exam_fixture_data(db_session, school)
    sc2 = SchoolClass(id=uuid.uuid4(), school_id=school.id, name="Class 11", display_order=2)
    db_session.add(sc2)
    db_session.commit()

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Mismatch Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    # sec1 belongs to sc1, but payload specifies sc2
    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc2.id),
        "section_id": str(sec1.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code == 422


def test_20_invalid_exam_date_outside_range(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Date Range Sch", "DRS1", ["exam.create"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Date Range Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-05",
        "end_date": "2026-10-10",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    # Date before start_date
    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-01",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code == 422


def test_21_start_time_ge_end_time(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Time Check Sch", "TCS1", ["exam.create"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Time Check Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "11:00:00",
        "end_time": "09:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code in [400, 422]


def test_22_maximum_marks_le_zero(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Max Marks Sch", "MMS1", ["exam.create"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Max Marks Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 0.0,
        "passing_marks": 0.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code in [400, 422]


def test_23_passing_marks_lt_zero(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Pass Marks Sch", "PMS1", ["exam.create"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Pass Marks Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": -5.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code in [400, 422]


def test_24_passing_marks_gt_maximum_marks(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Marks Exceed Sch", "MES1", ["exam.create"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Marks Exceed Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 50.0,
        "passing_marks": 60.0,
    }
    resp = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert resp.status_code in [400, 422]


def test_25_duplicate_active_schedule(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Dup Sched Sch", "DSS1", ["exam.create"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Dup Sched Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    r1 = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert r1.status_code == 201

    r2 = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert r2.status_code == 409


def test_26_soft_delete_then_recreate(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Recreate Sch", "REC1", ["exam.create", "exam.delete"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Recreate Sched Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    r1 = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert r1.status_code == 201
    sched_id = r1.json()["id"]

    # Delete
    del_resp = client.delete(f"/api/v1/exam-schedules/{sched_id}", headers=headers)
    assert del_resp.status_code == 204

    # Recreate same schedule
    r2 = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert r2.status_code == 201
    assert r2.json()["id"] != sched_id


def test_27_exam_schedule_crud(client, db_session):
    school, user, headers = create_school_and_user(db_session, "CRUD Sched Sch", "CSCS1", ["exam.create", "exam.view", "exam.update", "exam.delete"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "CRUD Sched Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    sched_payload = {
        "exam_id": exam_id,
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "school_class_id": str(sc.id),
        "section_id": str(sec.id),
        "subject_id": str(subj.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }
    r1 = client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)
    assert r1.status_code == 201
    sched_id = r1.json()["id"]

    # Read
    r_get = client.get(f"/api/v1/exam-schedules/{sched_id}", headers=headers)
    assert r_get.status_code == 200

    # Update
    r_put = client.put(f"/api/v1/exam-schedules/{sched_id}", json={"passing_marks": 40.0}, headers=headers)
    assert r_put.status_code == 200
    assert float(r_put.json()["passing_marks"]) == 40.0

    # Delete
    r_del = client.delete(f"/api/v1/exam-schedules/{sched_id}", headers=headers)
    assert r_del.status_code == 204


def test_28_exam_schedule_pagination(client, db_session):
    school, user, headers = create_school_and_user(db_session, "Page Sched Sch", "PSS1", ["exam.create", "exam.view"])
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    exam_resp = client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Page Sched Exam",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers)
    exam_id = exam_resp.json()["id"]

    # Create 3 schedules on different dates
    for day in range(1, 4):
        sched_payload = {
            "exam_id": exam_id,
            "school_id": str(school.id),
            "academic_year_id": str(ay.id),
            "school_class_id": str(sc.id),
            "section_id": str(sec.id),
            "subject_id": str(subj.id),
            "exam_date": f"2026-10-0{day}",
            "start_time": "09:00:00",
            "end_time": "11:00:00",
            "maximum_marks": 100.0,
            "passing_marks": 35.0,
        }
        client.post("/api/v1/exam-schedules", json=sched_payload, headers=headers)

    r_list = client.get(f"/api/v1/exam-schedules?exam_id={exam_id}&page=1&page_size=2", headers=headers)
    assert r_list.status_code == 200
    data = r_list.json()
    assert data["total"] == 3
    assert len(data["items"]) == 2


def test_29_cross_school_schedule_retrieval_update_delete(client, db_session):
    school1, user1, headers1 = create_school_and_user(db_session, "CS Sched Sch 1", "CSS1", ["exam.create", "exam.view", "exam.update", "exam.delete"])
    school2, user2, headers2 = create_school_and_user(db_session, "CS Sched Sch 2", "CSS2", ["exam.view", "exam.update", "exam.delete"])

    ay1, sc1, sec1, subj1 = setup_exam_fixture_data(db_session, school1)

    exam1_resp = client.post("/api/v1/exams", json={
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "name": "Exam 1",
        "exam_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    }, headers=headers1)
    exam1_id = exam1_resp.json()["id"]

    sched1_resp = client.post("/api/v1/exam-schedules", json={
        "exam_id": exam1_id,
        "school_id": str(school1.id),
        "academic_year_id": str(ay1.id),
        "school_class_id": str(sc1.id),
        "section_id": str(sec1.id),
        "subject_id": str(subj1.id),
        "exam_date": "2026-10-05",
        "start_time": "09:00:00",
        "end_time": "11:00:00",
        "maximum_marks": 100.0,
        "passing_marks": 35.0,
    }, headers=headers1)
    sched1_id = sched1_resp.json()["id"]

    # User 2 attempts GET, PUT, DELETE for School 1's schedule
    r_get = client.get(f"/api/v1/exam-schedules/{sched1_id}", headers=headers2)
    assert r_get.status_code == 404

    r_put = client.put(f"/api/v1/exam-schedules/{sched1_id}", json={"passing_marks": 50.0}, headers=headers2)
    assert r_put.status_code == 404

    r_del = client.delete(f"/api/v1/exam-schedules/{sched1_id}", headers=headers2)
    assert r_del.status_code == 404


def test_assessment_and_attempt_type_api(db_session, client):
    school, user, headers = create_school_and_user(
        db_session, "Assessment API School", "AASCH", ["exam.create", "exam.view"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Unit Test 1 Math",
        "assessment_type": "UNIT_TEST",
        "attempt_type": "MAKEUP",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
        "status": "DRAFT",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["assessment_type"] == "UNIT_TEST"
    assert data["attempt_type"] == "MAKEUP"


def test_legacy_exam_type_api_compatibility(db_session, client):
    school, user, headers = create_school_and_user(
        db_session, "Legacy API School", "LASCH", ["exam.create", "exam.view", "exam.update"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    # Legacy POST
    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Legacy Exam 1",
        "exam_type": "RETEST",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 201
    data = response.json()
    assert data["assessment_type"] == "OTHER"
    assert data["attempt_type"] == "RETEST"
    exam_id = data["id"]

    # Update assessment_type to TERM
    up_res = client.put(f"/api/v1/exams/{exam_id}", json={"assessment_type": "TERM"}, headers=headers)
    assert up_res.status_code == 200
    assert up_res.json()["assessment_type"] == "TERM"

    # Legacy PUT with exam_type="REGULAR" -> must update attempt_type to REGULAR while PRESERVING assessment_type=TERM
    up_legacy = client.put(f"/api/v1/exams/{exam_id}", json={"exam_type": "REGULAR"}, headers=headers)
    assert up_legacy.status_code == 200
    assert up_legacy.json()["assessment_type"] == "TERM"
    assert up_legacy.json()["attempt_type"] == "REGULAR"


def test_invalid_legacy_exam_type_rejection(db_session, client):
    school, user, headers = create_school_and_user(
        db_session, "Invalid Legacy School", "ILSCH", ["exam.create"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    payload = {
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Invalid Legacy Exam",
        "exam_type": "UNSUPPORTED_TYPE",
        "start_date": "2026-10-10",
        "end_date": "2026-10-20",
    }
    response = client.post("/api/v1/exams", json=payload, headers=headers)
    assert response.status_code == 422


def test_filtering_by_assessment_and_attempt_types(db_session, client):
    school, user, headers = create_school_and_user(
        db_session, "Filter School", "FLSCH", ["exam.create", "exam.view"]
    )
    ay, sc, sec, subj = setup_exam_fixture_data(db_session, school)

    client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Formative 1",
        "assessment_type": "FORMATIVE_ASSESSMENT",
        "attempt_type": "REGULAR",
        "start_date": "2026-10-01",
        "end_date": "2026-10-05",
    }, headers=headers)

    client.post("/api/v1/exams", json={
        "school_id": str(school.id),
        "academic_year_id": str(ay.id),
        "name": "Summative 1",
        "assessment_type": "SUMMATIVE_ASSESSMENT",
        "attempt_type": "RETEST",
        "start_date": "2026-10-10",
        "end_date": "2026-10-15",
    }, headers=headers)

    res_fa = client.get("/api/v1/exams?assessment_type=FORMATIVE_ASSESSMENT", headers=headers)
    assert res_fa.status_code == 200
    assert res_fa.json()["total"] == 1
    assert res_fa.json()["items"][0]["name"] == "Formative 1"

    res_retest = client.get("/api/v1/exams?attempt_type=RETEST", headers=headers)
    assert res_retest.status_code == 200
    assert res_retest.json()["total"] == 1
    assert res_retest.json()["items"][0]["name"] == "Summative 1"
