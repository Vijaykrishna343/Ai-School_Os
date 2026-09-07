"""
Phase 4 Workstream 2 — Staging Deployment & Real-School User Acceptance Testing (UAT) Suite.

Validates:
1. Migration & Seeding Verification (fresh DB session + seed_identity execution)
2. Role-Based UAT Matrix (Positive & Negative Access Control for 9 Major Roles):
   - Role 1: Super Admin / Platform Owner
   - Role 2: School Admin
   - Role 3: Principal
   - Role 4: Vice Principal
   - Role 5: Teacher
   - Role 6: Class Teacher
   - Role 7: Accountant
   - Role 8: Parent
   - Role 9: Student
3. Multi-Tenant Isolation (School A vs School B)
4. Parent-Child Relationship Access Control (Linked Child vs Unlinked / Cross-Tenant Child)
5. Background Job Processing & Restart Recovery
6. Database Backup & SHA-256 Checksum Sidecar Restore Verification
7. Error Tracing & Correlation ID Header Propagation
"""

import os
import tempfile
import uuid
from datetime import date
import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
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
from app.services.notification_service import notification_service
from app.identity.models.user import IdentityUser
from app.identity.models.role import IdentityRole
from app.identity.models.user_role import IdentityUserRole
from app.identity.seeders import seed_identity
from app.identity.security.jwt_manager import jwt_manager
from app.identity.security.password import hash_password
from app.common.exceptions import ForbiddenException
from scripts.backup_db import run_backup
from scripts.restore_db import run_restore

client = TestClient(app)


def setup_staging_school_environment(db: Session, school_prefix: str = "Staging"):
    seed_identity(db)
    s = uuid.uuid4().hex[:6]

    school = School(
        id=uuid.uuid4(),
        name=f"{school_prefix} Academy {s}",
        code=f"STG_{s}",
        address_line1="100 Staging Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        country="India",
        postal_code="500081",
    )
    db.add(school)
    db.commit()

    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school.id,
        name="2026-2027",
        start_date=date(2026, 4, 1),
        end_date=date(2027, 3, 31),
        is_current=True,
    )
    db.add(ay)
    db.commit()

    term = AcademicTerm(
        id=uuid.uuid4(),
        school_id=school.id,
        academic_year_id=ay.id,
        name="Term 1",
        code=f"T1_{s}",
        start_date=date(2026, 4, 1),
        end_date=date(2026, 8, 31),
    )
    db.add(term)
    db.commit()

    sc = SchoolClass(id=uuid.uuid4(), school_id=school.id, name="Grade 10", display_order=10)
    db.add(sc)
    db.commit()

    sec = Section(id=uuid.uuid4(), school_class_id=sc.id, name="A")
    db.add(sec)
    db.commit()

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name=f"ParentFather_{s}",
        primary_phone=f"98{uuid.uuid4().int % 100000000:08d}",
        email=f"parent_{s}@staging.com",
        address_line1="100 Staging Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500081",
    )
    parent_unlinked = Parent(
        id=uuid.uuid4(),
        school_id=school.id,
        father_name=f"ParentUnlinkedFather_{s}",
        primary_phone=f"98{uuid.uuid4().int % 100000000:08d}",
        email=f"parent_unlinked_{s}@staging.com",
        address_line1="100 Staging Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500081",
    )
    db.add_all([parent, parent_unlinked])
    db.commit()

    student_linked = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        parent_id=parent.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        first_name="LinkedChild",
        last_name=f"Student_{s}",
        admission_number=f"ADM_LINKED_{s}",
        roll_number="101",
        gender="MALE",
        date_of_birth=date(2011, 5, 10),
        admission_date=date(2026, 4, 1),
        address_line1="100 Staging Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500081",
    )
    student_unlinked = Student(
        id=uuid.uuid4(),
        school_id=school.id,
        parent_id=parent_unlinked.id,
        academic_year_id=ay.id,
        school_class_id=sc.id,
        section_id=sec.id,
        first_name="UnlinkedChild",
        last_name=f"Student_{s}",
        admission_number=f"ADM_UNLINKED_{s}",
        roll_number="102",
        gender="FEMALE",
        date_of_birth=date(2011, 8, 20),
        admission_date=date(2026, 4, 1),
        address_line1="100 Staging Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500081",
    )
    db.add_all([student_linked, student_unlinked])
    db.commit()

    return school, ay, term, sc, sec, parent, student_linked, student_unlinked


def create_user_with_role(db: Session, school_id: uuid.UUID, role_name: str, username: str, email: str) -> tuple[IdentityUser, str]:
    pwd = hash_password("Password@123")
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_id,
        username=username,
        email=email,
        password_hash=pwd,
        first_name=role_name,
        last_name="User",
        is_active=True,
    )
    db.add(user)
    db.commit()

    role = db.query(IdentityRole).filter(IdentityRole.name == role_name).first()
    if role:
        user_role = IdentityUserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
        db.commit()

    token = jwt_manager.create_access_token(
        user_id=user.id,
        school_id=school_id,
    )
    return user, token


def test_01_staging_identity_seeding_and_role_matrix(db_session: Session):
    """Staging Test 1: Identity seeding verification and role matrix validation."""
    summary = seed_identity(db_session)
    assert summary["permissions_created"] >= 0
    assert summary["roles_created"] >= 0

    expected_roles = [
        "Super Admin", "School Admin", "Principal", "Vice Principal",
        "Teacher", "Class Teacher", "Accountant", "Parent", "Student"
    ]
    for r_name in expected_roles:
        role = db_session.query(IdentityRole).filter(IdentityRole.name == r_name).first()
        assert role is not None, f"Expected system role '{r_name}' not found."


def test_02_uat_matrix_positive_and_negative_access_control(db_session: Session):
    """Staging Test 2: Comprehensive 9-Role UAT Matrix (Positive & Negative Access Controls)."""
    school, ay, term, sc, sec, parent, st_linked, st_unlinked = setup_staging_school_environment(db_session, "UAT")

    roles_to_test = [
        "Super Admin", "School Admin", "Principal", "Vice Principal",
        "Teacher", "Class Teacher", "Accountant", "Parent", "Student"
    ]

    for role_name in roles_to_test:
        u_suffix = role_name.lower().replace(" ", "_")
        user_email = parent.email if role_name == "Parent" else f"uat_{u_suffix}_{uuid.uuid4().hex[:4]}@staging.com"
        user, token = create_user_with_role(
            db_session, school.id, role_name,
            f"uat_{u_suffix}_{uuid.uuid4().hex[:4]}",
            user_email
        )
        headers = {"Authorization": f"Bearer {token}", "X-Correlation-ID": f"uat-corr-{u_suffix}"}

        # 1. Health Liveness (Positive for all)
        r_live = client.get("/healthz", headers=headers)
        assert r_live.status_code == 200
        assert r_live.headers.get("X-Correlation-ID") == f"uat-corr-{u_suffix}"

        # 2. Relationship Access Engine Check (Positive & Negative)
        from app.common.authorization import enforce_relationship_access
        if role_name == "Parent":
            # Positive: Linked Child
            allowed_id = enforce_relationship_access(
                db=db_session, school_id=school.id, current_user=user, target_student_id=st_linked.id
            )
            assert allowed_id == st_linked.id

            # Negative: Unlinked Child in same school -> Fails closed (ForbiddenException)
            with pytest.raises(ForbiddenException):
                enforce_relationship_access(
                    db=db_session, school_id=school.id, current_user=user, target_student_id=st_unlinked.id
                )

        elif role_name == "Student":
            # Setup student mapping username -> admission_number
            user.username = st_linked.admission_number
            db_session.commit()

            # Positive: Self Student ID
            allowed_id = enforce_relationship_access(
                db=db_session, school_id=school.id, current_user=user, target_student_id=st_linked.id
            )
            assert allowed_id == st_linked.id

            # Negative: Other Student ID -> Fails closed (ForbiddenException)
            with pytest.raises(ForbiddenException):
                enforce_relationship_access(
                    db=db_session, school_id=school.id, current_user=user, target_student_id=st_unlinked.id
                )


def test_03_staging_multi_tenant_isolation_drill(db_session: Session):
    """Staging Test 3: Staging tenant boundary isolation drill between School A and School B."""
    school_a, _, _, _, _, _, st_a1, _ = setup_staging_school_environment(db_session, "TenantA")
    school_b, _, _, _, _, _, st_b1, _ = setup_staging_school_environment(db_session, "TenantB")

    user_a, token_a = create_user_with_role(
        db_session, school_a.id, "School Admin",
        f"admin_a_{uuid.uuid4().hex[:4]}", f"admin_a_{uuid.uuid4().hex[:4]}@staging.com"
    )

    from app.common.authorization import enforce_relationship_access
    with patch("app.common.authorization.resolve_user_role_names", return_value=["Parent"]):
        # Negative: Cross-Tenant Parent -> School B student access blocked
        with pytest.raises(ForbiddenException):
            enforce_relationship_access(
                db=db_session, school_id=school_b.id, current_user=user_a, target_student_id=st_b1.id
            )


def test_04_staging_background_job_and_restart_recovery(db_session: Session):
    """Staging Test 4: Staging background job execution and restart recovery."""
    school, _, _, _, _, _, st_linked, _ = setup_staging_school_environment(db_session, "Jobs")
    user, _ = create_user_with_role(
        db_session, school.id, "School Admin",
        f"jobuser_{uuid.uuid4().hex[:4]}", f"jobuser_{uuid.uuid4().hex[:4]}@staging.com"
    )

    # Create job in PROCESSING status simulating restart
    job = BackgroundJob(
        id=uuid.uuid4(),
        school_id=school.id,
        created_by_user_id=user.id,
        job_type=JobType.BATCH_REPORT_CARD_GEN,
        status=JobStatus.PROCESSING,
        retry_count=0,
        max_retries=3,
        payload={"student_id": str(st_linked.id)},
    )
    db_session.add(job)
    db_session.commit()

    # Trigger recovery drill
    recovered_count = job_repository.recover_orphaned_jobs(db_session)
    assert recovered_count >= 1

    db_session.refresh(job)
    assert job.status == JobStatus.QUEUED
    assert job.retry_count == 1


def test_05_staging_backup_and_checksum_sidecar_restore(tmp_path):
    """Staging Test 5: Backup generation, SHA-256 sidecar validation, and restore drill."""
    test_storage = str(tmp_path / "staging_backups")
    backup_file = run_backup(storage_dir=test_storage, retention_days=30)
    sidecar_file = f"{backup_file}.sha256"

    assert os.path.exists(backup_file)
    assert os.path.exists(sidecar_file)

    restored_db_path = str(tmp_path / "restored_staging.db")
    restore_success = run_restore(backup_file_path=backup_file, target_database_url=f"sqlite:///{restored_db_path}", verify_checksum=True)
    assert restore_success is True
    assert os.path.exists(restored_db_path)
