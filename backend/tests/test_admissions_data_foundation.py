from __future__ import annotations

from datetime import date, datetime, timezone
import uuid
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.common.enums import (
    AcademicYearStatus,
    SchoolClassStatus,
    SectionStatus,
)
from app.common.enums.admissions import (
    AdmissionApplicationStatus,
    AdmissionCycleStatus,
    AdmissionDecisionType,
    ApplicantStatus,
)
from app.database.common_model import CommonModel
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.models.user import IdentityUser
from app.identity.repositories import (
    permission_repository,
    role_permission_repository,
    role_repository,
)
from app.identity.seeders.permission_seeder import DEFAULT_PERMISSIONS, permission_seeder
from app.identity.seeders.role_permission_seeder import ROLE_PERMISSIONS_MATRIX, role_permission_seeder
from app.models.academic_year.academic_year import AcademicYear
from app.models.admissions import (
    AdmissionApplication,
    AdmissionCycle,
    AdmissionDecision,
    Applicant,
    ApplicationStatusHistory,
)
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section


@pytest.fixture(autouse=True)
def setup_admissions_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    yield


@pytest.fixture
def admissions_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Oakridge International School A",
        code=f"ADM-SCH-A-{uuid.uuid4().hex[:4]}",
        address_line1="100 Admissions Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B (for multi-tenant isolation tests)
    school_b = School(
        id=uuid.uuid4(),
        name="Oakridge International School B",
        code=f"ADM-SCH-B-{uuid.uuid4().hex[:4]}",
        address_line1="200 Admissions Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    # Academic Years
    ay_a = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    ay_b = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add_all([ay_a, ay_b])
    db_session.flush()

    # Classes & Sections
    class_a = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Grade 1",
        display_order=1,
    )
    class_b = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="Grade 1",
        display_order=1,
    )
    db_session.add_all([class_a, class_b])
    db_session.flush()

    sec_a = Section(
        id=uuid.uuid4(),
        school_class_id=class_a.id,
        name="Section A",
    )
    db_session.add(sec_a)
    db_session.flush()

    # Reviewer / Staff User
    reviewer = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"admissions_officer_{uuid.uuid4().hex[:4]}@school.com",
        username=f"officer_{uuid.uuid4().hex[:4]}",
        password_hash="hashed_pw",
        first_name="Jane",
        last_name="Doe",
        is_active=True,
    )
    db_session.add(reviewer)
    db_session.flush()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "class_a": class_a,
        "class_b": class_b,
        "sec_a": sec_a,
        "reviewer": reviewer,
    }


# ==============================================================================
# 1. ADMISSION CYCLE TESTS
# ==============================================================================

def test_admission_cycle_creation_and_defaults(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="AY 2026-2027 Admissions",
        code="CYCLE-2026-01",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
        description="General Admissions for 2026-2027",
    )
    db_session.add(cycle)
    db_session.flush()

    saved = db_session.get(AdmissionCycle, cycle.id)
    assert saved is not None
    assert saved.status == AdmissionCycleStatus.DRAFT
    assert saved.is_active is True
    assert saved.is_deleted is False
    assert saved.school.id == f["school_a"].id
    assert saved.academic_year.id == f["ay_a"].id


def test_admission_cycle_code_uniqueness_per_school(db_session, admissions_fixture):
    f = admissions_fixture
    c1 = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle 1",
        code="CYCLE-UNIQUE",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    db_session.add(c1)
    db_session.flush()

    # Same school duplicate code should fail
    c2 = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle 2",
        code="CYCLE-UNIQUE",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(c2)
            db_session.flush()

    # Different school same code should succeed
    c3 = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_b"].id,
        academic_year_id=f["ay_b"].id,
        name="Cycle School B",
        code="CYCLE-UNIQUE",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    db_session.add(c3)
    db_session.flush()
    assert db_session.get(AdmissionCycle, c3.id) is not None


def test_admission_cycle_invalid_dates_constraint(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Invalid Date Cycle",
        code="CYCLE-INVALID-DATES",
        start_date=date(2026, 5, 31),
        end_date=date(2026, 1, 1),  # end_date before start_date
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(cycle)
            db_session.flush()


# ==============================================================================
# 2. APPLICANT TESTS
# ==============================================================================

def test_applicant_creation_and_defaults(db_session, admissions_fixture):
    f = admissions_fixture
    applicant = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-2026-0001",
        first_name="Rohan",
        last_name="Sharma",
        date_of_birth=date(2020, 3, 15),
        gender="MALE",
        email="parent.rohan@example.com",
        phone="+91-9876543210",
        parent_name="Rajesh Sharma",
        source="ONLINE",
    )
    db_session.add(applicant)
    db_session.flush()

    saved = db_session.get(Applicant, applicant.id)
    assert saved is not None
    assert saved.status == ApplicantStatus.PROSPECT
    assert saved.first_name == "Rohan"
    assert saved.parent_name == "Rajesh Sharma"
    assert saved.is_deleted is False


def test_applicant_number_uniqueness_per_school(db_session, admissions_fixture):
    f = admissions_fixture
    a1 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-NUM-001",
        first_name="Alice",
        last_name="Smith",
        date_of_birth=date(2020, 5, 10),
        gender="FEMALE",
    )
    db_session.add(a1)
    db_session.flush()

    # Same school duplicate applicant_number should fail
    a2 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-NUM-001",
        first_name="Bob",
        last_name="Jones",
        date_of_birth=date(2020, 8, 20),
        gender="MALE",
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(a2)
            db_session.flush()

    # Different school same applicant_number should succeed
    a3 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_b"].id,
        applicant_number="APP-NUM-001",
        first_name="Charlie",
        last_name="Brown",
        date_of_birth=date(2020, 9, 15),
        gender="MALE",
    )
    db_session.add(a3)
    db_session.flush()
    assert db_session.get(Applicant, a3.id) is not None


def test_applicant_soft_delete_uniqueness(db_session, admissions_fixture):
    f = admissions_fixture
    a1 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-NUM-REUSE",
        first_name="Daisy",
        last_name="Miller",
        date_of_birth=date(2020, 1, 1),
        gender="FEMALE",
    )
    db_session.add(a1)
    db_session.flush()

    # Soft delete a1
    a1.is_deleted = True
    a1.deleted_at = datetime.now(timezone.utc)
    db_session.flush()

    # Now creating a new active applicant with same applicant_number should succeed
    a2 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-NUM-REUSE",
        first_name="Danielle",
        last_name="Miller",
        date_of_birth=date(2020, 1, 1),
        gender="FEMALE",
    )
    db_session.add(a2)
    db_session.flush()
    assert db_session.get(Applicant, a2.id) is not None


# ==============================================================================
# 3. ADMISSION APPLICATION TESTS
# ==============================================================================

def test_admission_application_creation_and_relationships(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="AY 2026-27 Cycle",
        code="CYCLE-APP-TEST",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    applicant = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-0099",
        first_name="Priya",
        last_name="Nair",
        date_of_birth=date(2020, 4, 12),
        gender="FEMALE",
    )
    db_session.add_all([cycle, applicant])
    db_session.flush()

    app = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        target_section_id=f["sec_a"].id,
        application_number="ADM-APP-2026-001",
        application_date=date(2026, 2, 1),
        status=AdmissionApplicationStatus.SUBMITTED,
        submitted_at=datetime.now(timezone.utc),
        remarks="Submitted online with all forms",
    )
    db_session.add(app)
    db_session.flush()

    saved = db_session.get(AdmissionApplication, app.id)
    assert saved is not None
    assert saved.status == AdmissionApplicationStatus.SUBMITTED
    assert saved.applicant.first_name == "Priya"
    assert saved.admission_cycle.code == "CYCLE-APP-TEST"
    assert saved.target_class.name == "Grade 1"
    assert saved.target_section.name == "Section A"


def test_admission_application_number_uniqueness(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle 1",
        code="CYC-UNIQ-01",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    a1 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-U1",
        first_name="A1",
        last_name="L1",
        date_of_birth=date(2020, 1, 1),
        gender="MALE",
    )
    a2 = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-U2",
        first_name="A2",
        last_name="L2",
        date_of_birth=date(2020, 1, 1),
        gender="FEMALE",
    )
    db_session.add_all([cycle, a1, a2])
    db_session.flush()

    app1 = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=a1.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-NUM-DUP",
        application_date=date(2026, 2, 1),
    )
    db_session.add(app1)
    db_session.flush()

    # Same school duplicate application_number should fail
    app2 = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=a2.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-NUM-DUP",
        application_date=date(2026, 2, 1),
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(app2)
            db_session.flush()


def test_admission_application_prevent_duplicate_active_in_same_cycle(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle 1",
        code="CYC-DUP-CHECK",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    applicant = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-DUP-01",
        first_name="Kiran",
        last_name="Reddy",
        date_of_birth=date(2020, 1, 1),
        gender="MALE",
    )
    db_session.add_all([cycle, applicant])
    db_session.flush()

    app1 = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-NUM-001",
        application_date=date(2026, 2, 1),
        status=AdmissionApplicationStatus.SUBMITTED,
    )
    db_session.add(app1)
    db_session.flush()

    # Same applicant applying again in the same cycle while active should fail
    app2 = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-NUM-002",
        application_date=date(2026, 2, 5),
        status=AdmissionApplicationStatus.DRAFT,
    )
    with pytest.raises(IntegrityError):
        with db_session.begin_nested():
            db_session.add(app2)
            db_session.flush()

    # But if app1 was rejected or withdrawn, re-application is allowed by the partial unique index
    app1.status = AdmissionApplicationStatus.REJECTED
    db_session.flush()

    app3 = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-NUM-003",
        application_date=date(2026, 2, 10),
        status=AdmissionApplicationStatus.SUBMITTED,
    )
    db_session.add(app3)
    db_session.flush()
    assert db_session.get(AdmissionApplication, app3.id) is not None


# ==============================================================================
# 4. APPLICATION STATUS HISTORY TESTS
# ==============================================================================

def test_application_status_history_creation(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle 1",
        code="CYC-HIST-01",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    applicant = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-HIST-01",
        first_name="Ananya",
        last_name="Rao",
        date_of_birth=date(2020, 2, 2),
        gender="FEMALE",
    )
    db_session.add_all([cycle, applicant])
    db_session.flush()

    app = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-HIST-001",
        application_date=date(2026, 2, 1),
        status=AdmissionApplicationStatus.UNDER_REVIEW,
    )
    db_session.add(app)
    db_session.flush()

    history = ApplicationStatusHistory(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        application_id=app.id,
        old_status=AdmissionApplicationStatus.DRAFT.value,
        new_status=AdmissionApplicationStatus.UNDER_REVIEW.value,
        changed_by_user_id=f["reviewer"].id,
        changed_at=datetime.now(timezone.utc),
        reason="Initial document verification complete",
        remarks="Passed phase 1 review",
    )
    db_session.add(history)
    db_session.flush()

    saved_hist = db_session.get(ApplicationStatusHistory, history.id)
    assert saved_hist is not None
    assert saved_hist.old_status == "DRAFT"
    assert saved_hist.new_status == "UNDER_REVIEW"
    assert saved_hist.changed_by_user.id == f["reviewer"].id
    assert saved_hist.application.id == app.id


# ==============================================================================
# 5. ADMISSION DECISION TESTS
# ==============================================================================

def test_admission_decision_creation(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle 1",
        code="CYC-DEC-01",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    applicant = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-DEC-01",
        first_name="Vikram",
        last_name="Singh",
        date_of_birth=date(2020, 7, 7),
        gender="MALE",
    )
    db_session.add_all([cycle, applicant])
    db_session.flush()

    app = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-DEC-001",
        application_date=date(2026, 2, 1),
        status=AdmissionApplicationStatus.ACCEPTED,
        decision_at=datetime.now(timezone.utc),
    )
    db_session.add(app)
    db_session.flush()

    decision = AdmissionDecision(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        application_id=app.id,
        decision_type=AdmissionDecisionType.ACCEPTED,
        decided_by_user_id=f["reviewer"].id,
        decided_at=datetime.now(timezone.utc),
        comments="Accepted for Grade 1 academic session 2026-2027",
        conditions="Fee payment before March 31, 2026",
    )
    db_session.add(decision)
    db_session.flush()

    saved_decision = db_session.get(AdmissionDecision, decision.id)
    assert saved_decision is not None
    assert saved_decision.decision_type == AdmissionDecisionType.ACCEPTED
    assert saved_decision.decided_by_user.id == f["reviewer"].id
    assert saved_decision.application.id == app.id
    assert "March 31" in saved_decision.conditions


# ==============================================================================
# 6. RBAC PERMISSIONS SEEDING & ROLE MATRIX TESTS
# ==============================================================================

def test_admissions_rbac_permissions_seeder(db_session):
    expected_perms = [
        "admissions.view",
        "admissions.create",
        "admissions.update",
        "admissions.delete",
        "admissions.review",
        "admissions.manage",
    ]

    # Verify all permissions are in DEFAULT_PERMISSIONS definition
    registered_names = {p["name"] for p in DEFAULT_PERMISSIONS}
    for perm_name in expected_perms:
        assert perm_name in registered_names, f"{perm_name} must be in DEFAULT_PERMISSIONS"

    # Verify role permissions matrix definitions
    school_admin_perms = ROLE_PERMISSIONS_MATRIX.get("School Admin", [])
    assert "admissions.*" in school_admin_perms

    principal_perms = ROLE_PERMISSIONS_MATRIX.get("Principal", [])
    assert "admissions.*" in principal_perms

    vice_principal_perms = ROLE_PERMISSIONS_MATRIX.get("Vice Principal", [])
    assert "admissions.*" in vice_principal_perms

    receptionist_perms = ROLE_PERMISSIONS_MATRIX.get("Receptionist", [])
    assert "admissions.view" in receptionist_perms
    assert "admissions.create" in receptionist_perms
    assert "admissions.update" in receptionist_perms
    assert "admissions.delete" not in receptionist_perms
    assert "admissions.manage" not in receptionist_perms

# ==============================================================================
# 7. CROSS-TENANT STRICT ISOLATION AUDIT
# ==============================================================================

def test_cross_tenant_admissions_isolation(db_session, admissions_fixture):
    f = admissions_fixture
    school_a = f["school_a"]
    school_b = f["school_b"]

    cycle_a = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=f["ay_a"].id,
        name="Cycle A",
        code="CYC-ISO-A",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    cycle_b = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=school_b.id,
        academic_year_id=f["ay_b"].id,
        name="Cycle B",
        code="CYC-ISO-B",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    app_a = Applicant(
        id=uuid.uuid4(),
        school_id=school_a.id,
        applicant_number="APP-ISO-A",
        first_name="Alice",
        last_name="A",
        date_of_birth=date(2020, 1, 1),
        gender="FEMALE",
    )
    app_b = Applicant(
        id=uuid.uuid4(),
        school_id=school_b.id,
        applicant_number="APP-ISO-B",
        first_name="Bob",
        last_name="B",
        date_of_birth=date(2020, 1, 1),
        gender="MALE",
    )
    db_session.add_all([cycle_a, cycle_b, app_a, app_b])
    db_session.flush()

    # Query School A records
    a_cycles = db_session.scalars(select(AdmissionCycle).where(AdmissionCycle.school_id == school_a.id)).all()
    b_cycles = db_session.scalars(select(AdmissionCycle).where(AdmissionCycle.school_id == school_b.id)).all()
    a_apps = db_session.scalars(select(Applicant).where(Applicant.school_id == school_a.id)).all()
    b_apps = db_session.scalars(select(Applicant).where(Applicant.school_id == school_b.id)).all()

    assert len(a_cycles) == 1
    assert a_cycles[0].id == cycle_a.id
    assert len(b_cycles) == 1
    assert b_cycles[0].id == cycle_b.id
    assert len(a_apps) == 1
    assert a_apps[0].id == app_a.id
    assert len(b_apps) == 1
    assert b_apps[0].id == app_b.id


# ==============================================================================
# 8. CASCADE DELETION & ENUM TESTS
# ==============================================================================

def test_admission_application_cascade_deletion(db_session, admissions_fixture):
    f = admissions_fixture
    cycle = AdmissionCycle(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        academic_year_id=f["ay_a"].id,
        name="Cycle Cascade",
        code="CYC-CASC",
        start_date=date(2026, 1, 1),
        end_date=date(2026, 5, 31),
    )
    applicant = Applicant(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_number="APP-CASC-01",
        first_name="Cascade",
        last_name="Test",
        date_of_birth=date(2020, 1, 1),
        gender="FEMALE",
    )
    db_session.add_all([cycle, applicant])
    db_session.flush()

    app = AdmissionApplication(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        applicant_id=applicant.id,
        admission_cycle_id=cycle.id,
        academic_year_id=f["ay_a"].id,
        target_class_id=f["class_a"].id,
        application_number="APP-CASC-001",
        application_date=date(2026, 2, 1),
    )
    db_session.add(app)
    db_session.flush()

    hist = ApplicationStatusHistory(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        application_id=app.id,
        old_status=None,
        new_status="DRAFT",
        changed_at=datetime.now(timezone.utc),
    )
    decision = AdmissionDecision(
        id=uuid.uuid4(),
        school_id=f["school_a"].id,
        application_id=app.id,
        decision_type=AdmissionDecisionType.ACCEPTED,
        decided_at=datetime.now(timezone.utc),
    )
    db_session.add_all([hist, decision])
    db_session.flush()

    # Delete application and verify cascade deletion of history & decisions
    db_session.delete(app)
    db_session.flush()

    assert db_session.get(ApplicationStatusHistory, hist.id) is None
    assert db_session.get(AdmissionDecision, decision.id) is None


def test_admission_enums_completeness():
    assert set(AdmissionCycleStatus) == {
        AdmissionCycleStatus.DRAFT,
        AdmissionCycleStatus.ACTIVE,
        AdmissionCycleStatus.CLOSED,
        AdmissionCycleStatus.ARCHIVED,
    }
    assert set(ApplicantStatus) == {
        ApplicantStatus.PROSPECT,
        ApplicantStatus.APPLIED,
        ApplicantStatus.UNDER_REVIEW,
        ApplicantStatus.SHORTLISTED,
        ApplicantStatus.ACCEPTED,
        ApplicantStatus.REJECTED,
        ApplicantStatus.WITHDRAWN,
        ApplicantStatus.ENROLLED,
    }
    assert set(AdmissionApplicationStatus) == {
        AdmissionApplicationStatus.DRAFT,
        AdmissionApplicationStatus.SUBMITTED,
        AdmissionApplicationStatus.UNDER_REVIEW,
        AdmissionApplicationStatus.WAITLISTED,
        AdmissionApplicationStatus.ACCEPTED,
        AdmissionApplicationStatus.REJECTED,
        AdmissionApplicationStatus.WITHDRAWN,
        AdmissionApplicationStatus.ENROLLED,
    }
    assert set(AdmissionDecisionType) == {
        AdmissionDecisionType.ACCEPTED,
        AdmissionDecisionType.REJECTED,
        AdmissionDecisionType.WAITLISTED,
        AdmissionDecisionType.WITHDRAWN,
        AdmissionDecisionType.CONDITIONAL_ACCEPT,
    }

