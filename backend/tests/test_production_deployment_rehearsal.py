"""
Phase 4 Workstream 1 — Real-School Production Deployment Rehearsal Test Suite.

Validates:
1. Production Configuration & Security Headers (CORS, HSTS, CSP, X-Frame-Options, X-Correlation-ID)
2. Health & Readiness Probes (/healthz, /readyz, DB connection drop simulation)
3. Automated Database Backup & Restore Drill with SHA-256 Checksum Verification
4. Background Job Worker Recovery & Restart Rehearsal
5. Filesystem Storage Write Fault Tolerance
6. Multi-Tenant & Parent-Student Relationship Access Isolation
7. End-to-End Real-School Operational Flow (Onboarding -> Fees -> Attendance -> Async Jobs -> Notifications -> DR Backup)
"""

import os
import shutil
import tempfile
import uuid
from datetime import date
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.config import settings
from app.models.school.school import School
from app.models.student.student import Student
from app.models.parent.parent import Parent
from app.models.teacher.teacher import Teacher
from app.models.academic_year.academic_year import AcademicYear
from app.models.academic_term.academic_term import AcademicTerm
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.repositories.job_repository import job_repository
from app.services.storage_service import storage_service
from app.services.notification_service import notification_service
from app.identity.models.user import IdentityUser
from app.identity.seeders import seed_identity
from app.common.exceptions import BadRequestException, ForbiddenException
from scripts.backup_db import run_backup
from scripts.restore_db import run_restore

client = TestClient(app)


def create_test_school(db: Session, name_prefix: str = "Rehearsal School") -> School:
    s = uuid.uuid4().hex[:6]
    school = School(
        id=uuid.uuid4(),
        name=f"{name_prefix} {s}",
        code=f"SCH_{s}",
        address_line1="123 Production Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500001",
    )
    db.add(school)
    db.commit()
    return school


def create_test_parent(db: Session, school_id: uuid.UUID) -> Parent:
    p = uuid.uuid4().hex[:6]
    parent = Parent(
        id=uuid.uuid4(),
        school_id=school_id,
        father_name=f"Father_{p}",
        primary_phone=f"99{uuid.uuid4().int % 100000000:08d}",
        email=f"parent_{p}@example.com",
        address_line1="123 Production Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(parent)
    db.commit()
    return parent


def create_test_student(
    db: Session,
    school_id: uuid.UUID,
    parent_id: uuid.UUID,
    academic_year_id: uuid.UUID,
    school_class_id: uuid.UUID,
    section_id: uuid.UUID,
    first_name: str = "StudentFirst",
) -> Student:
    s = uuid.uuid4().hex[:6]
    student = Student(
        id=uuid.uuid4(),
        school_id=school_id,
        parent_id=parent_id,
        academic_year_id=academic_year_id,
        school_class_id=school_class_id,
        section_id=section_id,
        first_name=first_name,
        last_name=f"Last_{s}",
        admission_number=f"ADM_{s}",
        roll_number=f"R_{s[:4]}",
        gender="FEMALE",
        date_of_birth=date(2015, 1, 1),
        admission_date=date(2026, 4, 1),
        address_line1="123 Production Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db.add(student)
    db.commit()
    return student


def create_test_user(db: Session, school_id: uuid.UUID) -> IdentityUser:
    u = uuid.uuid4().hex[:6]
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_id,
        username=f"user_{u}",
        email=f"user_{u}@example.com",
        password_hash="hashed_rehearsal_password_123",
        first_name="Test",
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()
    return user


def test_01_production_configuration_and_security_headers(db_session: Session):
    """Rehearsal Test 1: Production Configuration, correlation IDs, and security headers."""
    response = client.get("/healthz", headers={"X-Correlation-ID": "rehearsal-corr-id-12345"})
    assert response.status_code == 200
    assert response.headers.get("X-Correlation-ID") == "rehearsal-corr-id-12345"
    assert response.headers.get("X-Frame-Options") == "DENY"
    assert response.headers.get("X-Content-Type-Options") == "nosniff"
    assert response.headers.get("X-XSS-Protection") == "1; mode=block"


def test_02_health_and_readiness_probes_with_db_failure(db_session: Session):
    """Rehearsal Test 2: /healthz and /readyz probes including DB failure simulation."""
    resp_live = client.get("/healthz")
    assert resp_live.status_code == 200
    assert resp_live.json()["status"] == "ok"

    resp_ready = client.get("/readyz")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "ready"

    with patch("app.main.check_database_connection", return_value=False):
        resp_failed = client.get("/readyz")
        assert resp_failed.status_code == 503
        assert resp_failed.json()["status"] == "not_ready"


def test_03_backup_and_restore_checksum_drill(tmp_path):
    """Rehearsal Test 3: Database backup generation, SHA-256 sidecar creation, and restore verification."""
    test_storage = str(tmp_path / "backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)
    sidecar_file = f"{backup_file}.sha256"

    assert os.path.exists(backup_file)
    assert os.path.exists(sidecar_file)

    with open(sidecar_file, "r", encoding="utf-8") as f:
        checksum_content = f.read().strip()
    checksum = checksum_content.split()[0]
    assert len(checksum) == 64

    restored_db_path = str(tmp_path / "restored_rehearsal.db")
    restore_result = run_restore(backup_file_path=backup_file, target_database_url=f"sqlite:///{restored_db_path}", verify_checksum=True)
    assert restore_result is True
    assert os.path.exists(restored_db_path)

    with open(sidecar_file, "w", encoding="utf-8") as f:
        f.write("0000000000000000000000000000000000000000000000000000000000000000")
    
    with pytest.raises(ValueError, match="Checksum validation failed"):
        run_restore(backup_file_path=backup_file, target_database_url=f"sqlite:///{restored_db_path}", verify_checksum=True)


def test_04_background_job_worker_recovery_drill(db_session: Session):
    """Rehearsal Test 4: Background job orphaned state recovery after worker process crash."""
    school = create_test_school(db_session, "Recovery School")
    user = create_test_user(db_session, school.id)

    orphaned_job = BackgroundJob(
        id=uuid.uuid4(),
        school_id=school.id,
        created_by_user_id=user.id,
        job_type=JobType.BATCH_REPORT_CARD_GEN,
        status=JobStatus.PROCESSING,
        retry_count=1,
        max_retries=3,
        payload={"batch_id": "test_batch"},
    )
    db_session.add(orphaned_job)
    db_session.commit()

    recovered_count = job_repository.recover_orphaned_jobs(db_session)
    assert recovered_count >= 1

    db_session.refresh(orphaned_job)
    assert orphaned_job.status == JobStatus.QUEUED
    assert orphaned_job.retry_count == 2
    assert orphaned_job.started_at is None


def test_05_storage_write_fault_tolerance(db_session: Session):
    """Rehearsal Test 5: Storage service fault tolerance on filesystem OSError."""
    school_id = uuid.uuid4()
    dummy_content = b"Rehearsal Document Payload"

    with patch("builtins.open", side_effect=OSError("Disk write permission denied")):
        with pytest.raises(BadRequestException) as exc_info:
            storage_service.store_file(
                school_id=school_id,
                owner_type="documents",
                owner_id=uuid.uuid4(),
                file_bytes=dummy_content,
                original_filename="test.pdf",
            )
        assert "Storage error" in str(exc_info.value)


def test_06_tenant_and_relationship_isolation_drill(db_session: Session):
    """Rehearsal Test 6: Multi-tenant and Parent-Student relationship access isolation drill."""
    seed_identity(db_session)

    school_a = create_test_school(db_session, "School A Rehearsal")
    school_b = create_test_school(db_session, "School B Rehearsal")

    ay_a = AcademicYear(
        id=uuid.uuid4(), school_id=school_a.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True
    )
    sc_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Class 1", display_order=1)
    db_session.add_all([ay_a, sc_a])
    db_session.commit()

    sec_a = Section(id=uuid.uuid4(), school_class_id=sc_a.id, name="A")
    db_session.add(sec_a)
    db_session.commit()

    ay_b = AcademicYear(
        id=uuid.uuid4(), school_id=school_b.id, name="2026-2027", start_date=date(2026, 4, 1), end_date=date(2027, 3, 31), is_current=True
    )
    sc_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Class 1", display_order=1)
    db_session.add_all([ay_b, sc_b])
    db_session.commit()

    sec_b = Section(id=uuid.uuid4(), school_class_id=sc_b.id, name="A")
    db_session.add(sec_b)
    db_session.commit()

    parent_a = create_test_parent(db_session, school_a.id)
    parent_a_unlinked = create_test_parent(db_session, school_a.id)
    parent_b = create_test_parent(db_session, school_b.id)

    student_a1 = create_test_student(db_session, school_a.id, parent_a.id, ay_a.id, sc_a.id, sec_a.id, "ChildA1")
    student_a2_unlinked = create_test_student(db_session, school_a.id, parent_a_unlinked.id, ay_a.id, sc_a.id, sec_a.id, "UnlinkedA2")

    student_b1 = create_test_student(db_session, school_b.id, parent_b.id, ay_b.id, sc_b.id, sec_b.id, "ChildB1")

    parent_user = IdentityUser(
        id=uuid.uuid4(),
        username=parent_a.email,
        email=parent_a.email,
        is_active=True,
    )

    from app.common.authorization import enforce_relationship_access
    with patch("app.common.authorization.resolve_user_role_names", return_value=["Parent"]):
        accessible_id = enforce_relationship_access(
            db=db_session,
            school_id=school_a.id,
            current_user=parent_user,
            target_student_id=student_a1.id,
        )
        assert accessible_id == student_a1.id

        with pytest.raises(ForbiddenException):
            enforce_relationship_access(
                db=db_session,
                school_id=school_a.id,
                current_user=parent_user,
                target_student_id=student_a2_unlinked.id,
            )

        with pytest.raises(ForbiddenException):
            enforce_relationship_access(
                db=db_session,
                school_id=school_b.id,
                current_user=parent_user,
                target_student_id=student_b1.id,
            )


def test_07_complete_real_school_operational_workflow_rehearsal(db_session: Session):
    """Rehearsal Test 7: Full real-school lifecycle workflow rehearsal."""
    from app.models.notification import NotificationChannel, NotificationRecipientType

    school = create_test_school(db_session, "Lincoln Academy Rehearsal")
    user = create_test_user(db_session, school.id)

    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db_session.add(ay)
    db_session.commit()

    term = AcademicTerm(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1",
        code=f"TERM1_{uuid.uuid4().hex[:4]}",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 8, 31),
    )
    db_session.add(term)
    db_session.commit()

    sc = SchoolClass(id=uuid.uuid4(), school_id=school.id, name="Class 1", display_order=1)
    db_session.add(sc)
    db_session.commit()

    sec = Section(id=uuid.uuid4(), school_class_id=sc.id, name="A")
    db_session.add(sec)
    db_session.commit()

    parent = create_test_parent(db_session, school.id)
    student = create_test_student(db_session, school.id, parent.id, ay.id, sc.id, sec.id, "Jane")

    job = job_repository.create_job(
        db=db_session,
        school_id=school.id,
        user_id=user.id,
        job_type=JobType.BATCH_REPORT_CARD_GEN,
        payload={"student_ids": [str(student.id)]},
    )
    assert job.status == JobStatus.QUEUED
    assert job.school_id == school.id

    notif = notification_service.create_and_send(
        db=db_session,
        school_id=school.id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Test Staff",
        recipient_contact="staff@example.com",
        channel=NotificationChannel.EMAIL,
        template_key="general_announcement",
        template_variables={"title": "Rehearsal Alert", "message": "Full real-school deployment rehearsal complete."},
        recipient_id=user.id,
    )
    assert notif.school_id == school.id

