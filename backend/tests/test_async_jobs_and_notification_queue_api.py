import uuid
from datetime import date
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

import app.database.models  # noqa: F401
from app.models.school.school import School
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.parent.parent import Parent
from app.models.grading.evaluation_config import EvaluationConfig
from app.models.grading.grade_scale import GradeScale
from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.services.async_job_runner import async_job_runner


@pytest.fixture
def setup_job_test_data(db_session: Session):
    from app.database.common_model import CommonModel
    CommonModel.metadata.create_all(db_session.get_bind())
    seed_identity(db_session)
    s = uuid.uuid4().hex[:6]

    # School A & B
    school_a = School(
        name=f"Job School A {s}", code=f"JSA_{s}",
        address_line1="123 Main St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    school_b = School(
        name=f"Job School B {s}", code=f"JSB_{s}",
        address_line1="456 Other St", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay = AcademicYear(school_id=school_a.id, name=f"2025-2026 {s}", start_date=date(2025, 6, 1), end_date=date(2026, 4, 30), is_current=True)
    db_session.add(ay)
    db_session.commit()

    term = AcademicTerm(school_id=school_a.id, academic_year_id=ay.id, name="Term 1", code=f"T1_{s}", start_date=date(2025, 6, 1), end_date=date(2025, 10, 31))
    db_session.add(term)
    db_session.commit()

    sc = SchoolClass(school_id=school_a.id, name="Grade 8", display_order=8)
    db_session.add(sc)
    db_session.commit()

    sec = Section(school_class_id=sc.id, name="A")
    db_session.add(sec)
    db_session.commit()

    eval_config = EvaluationConfig(
        school_id=school_a.id, academic_year_id=ay.id, name=f"Eval Config {s}"
    )
    gs = GradeScale(school_id=school_a.id, name=f"CBSE Scale {s}", is_default=True)
    db_session.add_all([eval_config, gs])
    db_session.commit()

    parent = Parent(
        school_id=school_a.id, father_name="Job Parent", primary_phone=f"9777{s[:6]}", email=f"jobparent_{s}@school.com",
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(parent)
    db_session.commit()

    st1 = Student(
        school_id=school_a.id, academic_year_id=ay.id, school_class_id=sc.id, section_id=sec.id, parent_id=parent.id,
        first_name="JobChild", last_name="One", admission_number=f"ADM_J1_{s}", roll_number="1",
        gender="MALE", date_of_birth=date(2012, 1, 1), admission_date=date(2020, 6, 1),
        address_line1="123 Street", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500001"
    )
    db_session.add(st1)
    db_session.commit()

    pwd = hash_password("Password@123")
    u_admin_a = IdentityUser(email=f"admin_a_{s}@school.com", password_hash=pwd, school_id=school_a.id, first_name="AdminA")
    u_parent_a = IdentityUser(email=parent.email, password_hash=pwd, school_id=school_a.id, first_name="ParentA")
    u_admin_b = IdentityUser(email=f"admin_b_{s}@school.com", password_hash=pwd, school_id=school_b.id, first_name="AdminB")

    db_session.add_all([u_admin_a, u_parent_a, u_admin_b])
    db_session.commit()

    r_admin = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    r_parent = db_session.query(IdentityRole).filter_by(name="Parent").first()

    db_session.add_all([
        IdentityUserRole(user_id=u_admin_a.id, role_id=r_admin.id),
        IdentityUserRole(user_id=u_parent_a.id, role_id=r_parent.id),
        IdentityUserRole(user_id=u_admin_b.id, role_id=r_admin.id),
    ])
    db_session.commit()

    tok_admin_a = jwt_manager.create_access_token(user_id=u_admin_a.id, school_id=school_a.id)
    tok_parent_a = jwt_manager.create_access_token(user_id=u_parent_a.id, school_id=school_a.id)
    tok_admin_b = jwt_manager.create_access_token(user_id=u_admin_b.id, school_id=school_b.id)

    return {
        "school_a": school_a, "school_b": school_b, "ay": ay, "term": term, "sc": sc, "sec": sec,
        "eval_config": eval_config, "st1": st1,
        "tok_admin_a": tok_admin_a, "tok_parent_a": tok_parent_a, "tok_admin_b": tok_admin_b,
    }


def test_01_async_job_creation_and_polling(client: TestClient, setup_job_test_data, db_session: Session):
    d = setup_job_test_data
    # Trigger batch notification async
    payload = {
        "template_key": "general_announcement",
        "template_variables": {"title": "Async Test", "message": "Test Message"},
        "recipients": [
            {"recipient_name": "Teacher A", "recipient_contact": "teacher_a@school.com", "recipient_type": "TEACHER"},
            {"recipient_name": "Teacher B", "recipient_contact": "teacher_b@school.com", "recipient_type": "TEACHER"},
        ],
        "channel": "IN_APP",
    }
    res = client.post("/api/v1/notifications/batch-send-async", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res.status_code == 202
    job_id = res.json()["data"]["job_id"]

    # Poll initial status
    poll_res = client.get(f"/api/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert poll_res.status_code == 200
    assert poll_res.json()["data"]["status"] in ("QUEUED", "PROCESSING", "COMPLETED")

    # Manually trigger process_job to simulate background runner execution
    async_job_runner.process_job(d["school_a"].id, uuid.UUID(job_id), db=db_session)

    # Verify status completed
    poll_res2 = client.get(f"/api/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert poll_res2.status_code == 200
    assert poll_res2.json()["data"]["status"] == "COMPLETED"
    assert poll_res2.json()["data"]["progress_percentage"] == 100
    assert poll_res2.json()["data"]["result"]["dispatched_count"] == 2


def test_02_async_section_report_card_batch_generation(client: TestClient, setup_job_test_data, db_session: Session):
    d = setup_job_test_data
    payload = {
        "school_id": str(d["school_a"].id),
        "academic_year_id": str(d["ay"].id),
        "academic_term_id": str(d["term"].id),
        "school_class_id": str(d["sc"].id),
        "section_id": str(d["sec"].id),
        "evaluation_config_id": str(d["eval_config"].id),
    }
    res = client.post("/api/v1/report-cards/batch-generate-async", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res.status_code == 202
    job_id = res.json()["data"]["job_id"]

    # Run worker execution
    async_job_runner.process_job(d["school_a"].id, uuid.UUID(job_id), db=db_session)

    poll_res = client.get(f"/api/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert poll_res.status_code == 200
    data = poll_res.json()["data"]
    print("JOB DATA:", data)
    assert data["status"] == "COMPLETED"
    assert data["result"]["generated_count"] >= 1


def test_03_idempotency_protection(client: TestClient, setup_job_test_data):
    d = setup_job_test_data
    key = f"IDEM_{uuid.uuid4().hex}"
    payload = {
        "template_key": "general_announcement",
        "template_variables": {"title": "Idem Test", "message": "Idem Message"},
        "recipients": [{"recipient_name": "Staff 1", "recipient_contact": "staff1@school.com", "recipient_type": "STAFF"}],
        "idempotency_key": key,
    }
    res1 = client.post("/api/v1/notifications/batch-send-async", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res1.status_code == 202
    job_id1 = res1.json()["data"]["job_id"]

    # Re-send exact same request with idempotency_key
    res2 = client.post("/api/v1/notifications/batch-send-async", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert res2.status_code == 202
    job_id2 = res2.json()["data"]["job_id"]

    assert job_id1 == job_id2


def test_04_multi_tenant_job_isolation(client: TestClient, setup_job_test_data):
    d = setup_job_test_data
    payload = {
        "template_key": "general_announcement",
        "template_variables": {"title": "Tenant Test", "message": "Message"},
        "recipients": [{"recipient_name": "Staff A", "recipient_contact": "staffa@school.com", "recipient_type": "STAFF"}],
    }
    res = client.post("/api/v1/notifications/batch-send-async", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    job_id = res.json()["data"]["job_id"]

    # Tenant B attempts to inspect Tenant A job
    res_b = client.get(f"/api/v1/jobs/{job_id}", headers={"Authorization": f"Bearer {d['tok_admin_b']}"})
    assert res_b.status_code == 404


def test_05_job_retry_and_cancellation(client: TestClient, setup_job_test_data, db_session: Session):
    d = setup_job_test_data
    payload = {
        "template_key": "general_announcement",
        "template_variables": {"title": "Cancel Test", "message": "Message"},
        "recipients": [{"recipient_name": "Staff C", "recipient_contact": "staffc@school.com", "recipient_type": "STAFF"}],
    }
    res = client.post("/api/v1/notifications/batch-send-async", json=payload, headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    job_id = res.json()["data"]["job_id"]

    # Cancel job
    cancel_res = client.post(f"/api/v1/jobs/{job_id}/cancel", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert cancel_res.status_code == 200
    assert cancel_res.json()["data"]["status"] == "CANCELLED"

    # Retry job
    retry_res = client.post(f"/api/v1/jobs/{job_id}/retry", headers={"Authorization": f"Bearer {d['tok_admin_a']}"})
    assert retry_res.status_code == 200
    assert retry_res.json()["data"]["status"] == "QUEUED"

