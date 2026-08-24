"""
Phase 3 Workstream 5 — Final Real-School Production Readiness Integration Tests.
Covers:
- Background job recovery after process restart / worker crash
- Database readiness probe failure handling (/readyz HTTP 503)
- Storage write failure (OSError permission/disk error handling)
- Notification delivery failure & retry behavior
- Corrupted/tampered backup restore rejection & missing checksum sidecar handling
- Zero-child parent and empty school state safety
"""

import uuid
import pytest
from unittest.mock import patch
from sqlalchemy.orm import Session

from app.models.school.school import School
from app.models.parent.parent import Parent
from app.common.enums.parent import ParentRelationship
from app.models.background_job import BackgroundJob, JobStatus, JobType
from app.repositories.job_repository import job_repository
from app.services.storage_service import storage_service
from app.services.notification_service import notification_service
from app.identity.models.user import IdentityUser
from app.identity.seeders import seed_identity
from app.common.exceptions import BadRequestException, ForbiddenException
from scripts.restore_db import run_restore


@pytest.fixture
def setup_ws5_data(db_session: Session):
    from app.database.common_model import CommonModel
    CommonModel.metadata.create_all(db_session.get_bind())
    seed_identity(db_session)

    s = uuid.uuid4().hex[:6]
    school = School(
        name=f"WS5 School {s}",
        code=f"WS5_{s}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.flush()

    user = IdentityUser(
        school_id=school.id,
        username=f"admin_{s}",
        email=f"admin_{s}@school.com",
        first_name="Admin",
        last_name="Staff",
        password_hash="hashed_pw",
        is_active=True,
    )
    db_session.add(user)

    parent_user = IdentityUser(
        school_id=school.id,
        username=f"parent_{s}",
        email=f"parent_{s}@school.com",
        first_name="ZeroChild",
        last_name="ParentUser",
        password_hash="hashed_pw",
        is_active=True,
    )
    db_session.add(parent_user)

    parent_record = Parent(
        school_id=school.id,
        father_name="ZeroChild Parent",
        relationship=ParentRelationship.FATHER,
        email=f"parent_{s}@school.com",
        primary_phone="9998887770",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent_record)
    db_session.commit()

    return {
        "school": school,
        "admin_user": user,
        "parent_user": parent_user,
        "parent_record": parent_record,
    }


def test_01_orphaned_job_recovery_on_startup(db_session: Session, setup_ws5_data):
    """Orphaned PROCESSING jobs must be reset to QUEUED or marked FAILED on startup."""
    data = setup_ws5_data
    job = job_repository.create_job(
        db=db_session,
        school_id=data["school"].id,
        user_id=data["admin_user"].id,
        job_type=JobType.BATCH_REPORT_CARD_GEN,
        payload={"section_id": str(uuid.uuid4()), "academic_year_id": str(uuid.uuid4()), "school_class_id": str(uuid.uuid4())},
        max_retries=1,
    )
    job.status = JobStatus.PROCESSING
    db_session.commit()

    # Perform startup recovery (Retry 1)
    recovered_count = job_repository.recover_orphaned_jobs(db_session)
    assert recovered_count >= 1

    db_session.refresh(job)
    assert job.status == JobStatus.QUEUED
    assert job.retry_count == 1
    assert "interrupted by process restart" in job.error_message

    # Recover again (Retry 2 > max_retries 1 -> FAILED)
    job.status = JobStatus.PROCESSING
    db_session.commit()

    recovered_count2 = job_repository.recover_orphaned_jobs(db_session)
    assert recovered_count2 >= 1

    db_session.refresh(job)
    assert job.status == JobStatus.FAILED
    assert job.retry_count == 2
    assert "exceeded max retries" in job.error_message



def test_02_database_readiness_failure(client):
    """/readyz probe must return HTTP 503 if database check fails."""
    with patch("app.main.check_database_connection", return_value=False):
        res = client.get("/readyz")
        assert res.status_code == 503
        data = res.json()
        assert data["status"] == "not_ready"
        assert data["database"] == "disconnected"


def test_03_unwritable_storage_handling(setup_ws5_data):
    """Storage write failure due to OSError must raise BadRequestException."""
    data = setup_ws5_data
    file_bytes = b"%PDF-1.4 Fake PDF Content"
    with patch("builtins.open", side_effect=OSError("Permission denied")):
        with pytest.raises(BadRequestException) as exc_info:
            storage_service.store_file(
                school_id=data["school"].id,
                owner_type="STUDENT",
                owner_id=data["admin_user"].id,
                file_bytes=file_bytes,
                original_filename="test.pdf",
            )
        assert "Storage error" in str(exc_info.value)


def test_04_notification_failure_and_retry(db_session: Session, setup_ws5_data):
    """Notification delivery retry must process previously failed notifications."""
    from app.models.notification import NotificationChannel, NotificationRecipientType, NotificationStatus

    data = setup_ws5_data
    # Create notification with FAILED status
    notif = notification_service.create_and_send(
        db=db_session,
        school_id=data["school"].id,
        recipient_type=NotificationRecipientType.STAFF,
        recipient_name="Test Staff",
        recipient_contact="staff@school.com",
        channel=NotificationChannel.IN_APP,
        template_key="general_announcement",
        template_variables={"title": "Notice", "message": "Test"},
    )
    notif.status = NotificationStatus.FAILED
    notif.error_message = "Network error"
    db_session.commit()

    # Retry notification
    retried = notification_service.retry_failed_notification(
        db=db_session,
        school_id=data["school"].id,
        notification_id=notif.id,
    )
    assert retried.status == NotificationStatus.SENT
    assert retried.error_message is None


def test_05_corrupted_backup_restore_rejection(tmp_path):
    """Restore must reject missing checksum sidecars and corrupted files."""
    backup_file = tmp_path / "corrupted_backup.db"
    backup_file.write_text("Corrupted database payload")

    # Missing sidecar test
    with pytest.raises(ValueError) as exc_info:
        run_restore(str(backup_file), verify_checksum=True)
    assert "Checksum sidecar file missing" in str(exc_info.value)

    # Invalid sidecar hash test
    sidecar_file = tmp_path / "corrupted_backup.db.sha256"
    sidecar_file.write_text("invalid_hash_value_12345")

    with pytest.raises(ValueError) as exc_info2:
        run_restore(str(backup_file), verify_checksum=True)
    assert "Checksum validation failed" in str(exc_info2.value)


def test_06_zero_child_parent_safety(db_session: Session, setup_ws5_data):
    """Parent user with 0 linked children must fail closed cleanly without 500 error."""
    from app.common.authorization import enforce_relationship_access

    data = setup_ws5_data
    with pytest.raises(ForbiddenException) as exc_info:
        enforce_relationship_access(
            db=db_session,
            school_id=data["school"].id,
            current_user=data["parent_user"],
            target_student_id=None,
        )
    assert "Access denied" in str(exc_info.value)
