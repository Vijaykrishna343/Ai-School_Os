from __future__ import annotations

from datetime import date, datetime, timezone
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

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
from app.dependencies.database import get_db
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
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
def setup_admissions_api_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def admissions_api_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Oakridge Public School A",
        code=f"ADM-SCH-A-{uuid.uuid4().hex[:4]}",
        address_line1="100 Admissions Blvd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B (for tenant isolation)
    school_b = School(
        id=uuid.uuid4(),
        name="Oakridge Public School B",
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
    cls_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Grade 1", display_order=1)
    cls_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Grade 1", display_order=1)
    db_session.add_all([cls_a, cls_b])
    db_session.flush()

    sec_a = Section(id=uuid.uuid4(), school_class_id=cls_a.id, name="Section A")
    sec_b = Section(id=uuid.uuid4(), school_class_id=cls_b.id, name="Section B")
    db_session.add_all([sec_a, sec_b])
    db_session.flush()

    # Helper for Permissions
    def get_or_create_perm(name, action, module="admissions"):
        p = db_session.query(IdentityPermission).filter_by(name=name).first()
        if not p:
            p = IdentityPermission(
                id=uuid.uuid4(),
                name=name,
                action=action,
                module=module,
                description=f"{action} {module}",
            )
            db_session.add(p)
            db_session.flush()
        return p

    perm_view = get_or_create_perm("admissions.view", "view")
    perm_create = get_or_create_perm("admissions.create", "create")
    perm_update = get_or_create_perm("admissions.update", "update")
    perm_delete = get_or_create_perm("admissions.delete", "delete")
    perm_review = get_or_create_perm("admissions.review", "review")
    perm_manage = get_or_create_perm("admissions.manage", "manage")

    # Roles
    admin_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Admissions Admin A {uuid.uuid4().hex[:4]}",
        description="Full Admissions Admin",
        permissions=[perm_view, perm_create, perm_update, perm_delete, perm_review, perm_manage],
    )
    officer_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Admissions Officer A {uuid.uuid4().hex[:4]}",
        description="Officer with review capabilities",
        permissions=[perm_view, perm_create, perm_update, perm_review],
    )
    viewer_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Admissions Viewer A {uuid.uuid4().hex[:4]}",
        description="View only",
        permissions=[perm_view],
    )
    admin_role_b = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name=f"Admissions Admin B {uuid.uuid4().hex[:4]}",
        description="Full Admissions Admin B",
        permissions=[perm_view, perm_create, perm_update, perm_delete, perm_review, perm_manage],
    )
    db_session.add_all([admin_role_a, officer_role_a, viewer_role_a, admin_role_b])
    db_session.flush()

    # Users
    user_admin_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"admin.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Alice",
        last_name="Admin",
        is_active=True,
        roles=[admin_role_a],
    )
    user_officer_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"officer.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Olivia",
        last_name="Officer",
        is_active=True,
        roles=[officer_role_a],
    )
    user_viewer_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"viewer.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Victor",
        last_name="Viewer",
        is_active=True,
        roles=[viewer_role_a],
    )
    user_admin_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"admin.b.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Bob",
        last_name="Admin",
        is_active=True,
        roles=[admin_role_b],
    )
    user_inactive_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"inactive.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Ian",
        last_name="Inactive",
        is_active=False,
        roles=[admin_role_a],
    )
    db_session.add_all([user_admin_a, user_officer_a, user_viewer_a, user_admin_b, user_inactive_a])
    db_session.flush()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "cls_a": cls_a,
        "cls_b": cls_b,
        "sec_a": sec_a,
        "sec_b": sec_b,
        "user_admin_a": user_admin_a,
        "user_officer_a": user_officer_a,
        "user_viewer_a": user_viewer_a,
        "user_admin_b": user_admin_b,
        "user_inactive_a": user_inactive_a,
    }


def auth_client(user: IdentityUser) -> TestClient:
    fastapi_app.dependency_overrides[get_current_user] = lambda: user
    return TestClient(fastapi_app)


# =============================================================================
# 1. AUTHENTICATION & RBAC TESTS
# =============================================================================

def test_unauthenticated_request_rejected():
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(fastapi_app)
    response = client.get("/api/v1/admissions/cycles")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_inactive_user_rejected(admissions_api_fixture):
    from app.identity.security.jwt_manager import jwt_manager
    user_inactive = admissions_api_fixture["user_inactive_a"]
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(fastapi_app)

    token = jwt_manager.create_access_token(
        user_id=user_inactive.id, school_id=user_inactive.school_id
    )
    response = client.get("/api/v1/admissions/cycles", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_viewer_permission_enforcement(admissions_api_fixture):
    user_viewer = admissions_api_fixture["user_viewer_a"]
    client = auth_client(user_viewer)

    # Allowed: GET list
    resp = client.get("/api/v1/admissions/cycles")
    assert resp.status_code == status.HTTP_200_OK

    # Denied: POST cycle -> 403
    resp_create = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(admissions_api_fixture["ay_a"].id),
            "name": "New Cycle",
            "code": "CYC-VIEWER-DENIED",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
        },
    )
    assert resp_create.status_code == status.HTTP_403_FORBIDDEN


# =============================================================================
# 2. ADMISSION CYCLE CRUD & MULTI-TENANT TESTS
# =============================================================================

def test_admission_cycle_crud_and_validation(admissions_api_fixture):
    f = admissions_api_fixture
    client = auth_client(f["user_admin_a"])

    # 1. Create Cycle
    res = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(f["ay_a"].id),
            "name": "AY 2026-27 Intake",
            "code": "CYC-2026-INTAKE",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
            "description": "General admissions for nursery to grade 12",
            "status": "ACTIVE",
        },
    )
    assert res.status_code == status.HTTP_201_CREATED, res.text
    cycle_data = res.json()
    cycle_id = cycle_data["id"]
    assert cycle_data["code"] == "CYC-2026-INTAKE"
    assert cycle_data["status"] == "ACTIVE"

    # 2. Cross-tenant Academic Year reference -> 404
    res_cross = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(f["ay_b"].id),
            "name": "Cross School Cycle",
            "code": "CYC-CROSS-AY",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
        },
    )
    assert res_cross.status_code == status.HTTP_404_NOT_FOUND

    # 3. Invalid dates -> 400
    res_invalid_dates = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(f["ay_a"].id),
            "name": "Bad Dates",
            "code": "CYC-BAD-DATES",
            "start_date": "2026-05-31",
            "end_date": "2026-01-01",
        },
    )
    assert res_invalid_dates.status_code == status.HTTP_400_BAD_REQUEST

    # 4. Duplicate code in same school -> 409
    res_dup = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(f["ay_a"].id),
            "name": "Duplicate Code",
            "code": "CYC-2026-INTAKE",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
        },
    )
    assert res_dup.status_code == status.HTTP_409_CONFLICT

    # 5. List cycles
    res_list = client.get("/api/v1/admissions/cycles?search=Intake")
    assert res_list.status_code == status.HTTP_200_OK
    assert res_list.json()["total"] >= 1

    # 6. Retrieve cycle
    res_get = client.get(f"/api/v1/admissions/cycles/{cycle_id}")
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["id"] == cycle_id

    # 7. Cross-tenant retrieval by School B user -> 404
    client_b = auth_client(f["user_admin_b"])
    res_get_b = client_b.get(f"/api/v1/admissions/cycles/{cycle_id}")
    assert res_get_b.status_code == status.HTTP_404_NOT_FOUND

    # 8. Update cycle (switch back to School A admin)
    client_a = auth_client(f["user_admin_a"])
    res_upd = client_a.put(
        f"/api/v1/admissions/cycles/{cycle_id}",
        json={"description": "Updated description", "status": "CLOSED"},
    )
    assert res_upd.status_code == status.HTTP_200_OK
    assert res_upd.json()["description"] == "Updated description"
    assert res_upd.json()["status"] == "CLOSED"

    # 9. Delete cycle
    res_del = client_a.delete(f"/api/v1/admissions/cycles/{cycle_id}")
    assert res_del.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 3. APPLICANT / PROSPECT CRUD & MULTI-TENANT TESTS
# =============================================================================

def test_applicant_crud_and_isolation(admissions_api_fixture):
    f = admissions_api_fixture
    client = auth_client(f["user_officer_a"])

    # 1. Create Applicant
    res = client.post(
        "/api/v1/admissions/applicants",
        json={
            "first_name": "Rohan",
            "last_name": "Sharma",
            "date_of_birth": "2020-03-15",
            "gender": "MALE",
            "email": "rohan.sharma@example.com",
            "phone": "+91-9876543210",
            "parent_name": "Rajesh Sharma",
            "source": "WALK_IN",
            "notes": "Interested in Grade 1",
        },
    )
    assert res.status_code == status.HTTP_201_CREATED, res.text
    app_data = res.json()
    applicant_id = app_data["id"]
    assert app_data["first_name"] == "Rohan"
    assert app_data["applicant_number"].startswith("APP-")
    assert app_data["status"] == "PROSPECT"

    # 2. Retrieve Applicant
    res_get = client.get(f"/api/v1/admissions/applicants/{applicant_id}")
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["id"] == applicant_id

    # 3. Cross-tenant access from School B -> 404
    client_b = auth_client(f["user_admin_b"])
    res_get_b = client_b.get(f"/api/v1/admissions/applicants/{applicant_id}")
    assert res_get_b.status_code == status.HTTP_404_NOT_FOUND

    # 4. Update Applicant (switch back to School A officer)
    client_officer = auth_client(f["user_officer_a"])
    res_upd = client_officer.put(
        f"/api/v1/admissions/applicants/{applicant_id}",
        json={"notes": "Completed initial consultation", "status": "APPLIED"},
    )
    assert res_upd.status_code == status.HTTP_200_OK
    assert res_upd.json()["status"] == "APPLIED"

    # 5. List applicants
    res_list = client_officer.get("/api/v1/admissions/applicants?search=Rohan")
    assert res_list.status_code == status.HTTP_200_OK
    assert res_list.json()["total"] >= 1

    # 6. Delete applicant (requires delete permission)
    res_del_denied = client_officer.delete(f"/api/v1/admissions/applicants/{applicant_id}")
    assert res_del_denied.status_code == status.HTTP_403_FORBIDDEN

    client_admin = auth_client(f["user_admin_a"])
    res_del = client_admin.delete(f"/api/v1/admissions/applicants/{applicant_id}")
    assert res_del.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 4. ADMISSION APPLICATION LIFECYCLE & WORKFLOW TESTS
# =============================================================================

def test_admission_application_full_lifecycle_and_decision(admissions_api_fixture):
    f = admissions_api_fixture
    client = auth_client(f["user_officer_a"])

    # 1. Setup Cycle and Applicant
    res_cycle = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(f["ay_a"].id),
            "name": "AY 2026-2027 Cycle",
            "code": f"CYC-FLOW-{uuid.uuid4().hex[:4]}",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
            "status": "ACTIVE",
        },
    )
    assert res_cycle.status_code == status.HTTP_201_CREATED
    cycle_id = res_cycle.json()["id"]

    res_applicant = client.post(
        "/api/v1/admissions/applicants",
        json={
            "admission_cycle_id": cycle_id,
            "first_name": "Aarav",
            "last_name": "Patel",
            "date_of_birth": "2020-04-10",
            "gender": "MALE",
            "parent_name": "Vikram Patel",
        },
    )
    assert res_applicant.status_code == status.HTTP_201_CREATED
    applicant_id = res_applicant.json()["id"]

    # 2. Create Application in DRAFT
    res_app = client.post(
        "/api/v1/admissions/applications",
        json={
            "applicant_id": applicant_id,
            "admission_cycle_id": cycle_id,
            "academic_year_id": str(f["ay_a"].id),
            "target_class_id": str(f["cls_a"].id),
            "target_section_id": str(f["sec_a"].id),
            "remarks": "Draft online application",
        },
    )
    assert res_app.status_code == status.HTTP_201_CREATED, res_app.text
    app_data = res_app.json()
    application_id = app_data["id"]
    assert app_data["status"] == "DRAFT"

    # 3. Duplicate active application in same cycle -> 409
    res_dup = client.post(
        "/api/v1/admissions/applications",
        json={
            "applicant_id": applicant_id,
            "admission_cycle_id": cycle_id,
            "academic_year_id": str(f["ay_a"].id),
            "target_class_id": str(f["cls_a"].id),
        },
    )
    assert res_dup.status_code == status.HTTP_409_CONFLICT

    # 4. Cross-tenant foreign class reference -> 404
    res_foreign_cls = client.post(
        "/api/v1/admissions/applications",
        json={
            "applicant_id": applicant_id,
            "admission_cycle_id": cycle_id,
            "academic_year_id": str(f["ay_a"].id),
            "target_class_id": str(f["cls_b"].id),  # School B Class
        },
    )
    assert res_foreign_cls.status_code == status.HTTP_404_NOT_FOUND

    # 5. Review before submit should fail -> 400
    res_early_review = client.post(f"/api/v1/admissions/applications/{application_id}/review")
    assert res_early_review.status_code == status.HTTP_400_BAD_REQUEST

    # 6. Submit Application
    res_submit = client.post(
        f"/api/v1/admissions/applications/{application_id}/submit",
        json={"remarks": "All documents attached"},
    )
    assert res_submit.status_code == status.HTTP_200_OK
    assert res_submit.json()["status"] == "SUBMITTED"
    assert res_submit.json()["submitted_at"] is not None

    # Repeated submit is idempotent
    res_submit_repeat = client.post(f"/api/v1/admissions/applications/{application_id}/submit")
    assert res_submit_repeat.status_code == status.HTTP_200_OK
    assert res_submit_repeat.json()["status"] == "SUBMITTED"

    # 7. Start Review
    res_review = client.post(
        f"/api/v1/admissions/applications/{application_id}/review",
        json={"remarks": "Documents verified by admissions officer"},
    )
    assert res_review.status_code == status.HTTP_200_OK
    assert res_review.json()["status"] == "UNDER_REVIEW"
    assert res_review.json()["reviewed_at"] is not None

    # Repeated review is idempotent
    res_review_repeat = client.post(f"/api/v1/admissions/applications/{application_id}/review")
    assert res_review_repeat.status_code == status.HTTP_200_OK
    assert res_review_repeat.json()["status"] == "UNDER_REVIEW"

    # 8. Record Admission Decision (ACCEPTED)
    res_decision = client.post(
        f"/api/v1/admissions/applications/{application_id}/decision",
        json={
            "decision_type": "ACCEPTED",
            "comments": "Eligible for Grade 1. Offer letter issued.",
            "conditions": "Enrollment fee payment within 14 days",
        },
    )
    assert res_decision.status_code == status.HTTP_200_OK
    dec_data = res_decision.json()
    assert dec_data["decision_type"] == "ACCEPTED"
    assert dec_data["decided_by_user_id"] == str(f["user_officer_a"].id)

    # 9. Verify Application status is now ACCEPTED
    res_app_final = client.get(f"/api/v1/admissions/applications/{application_id}")
    assert res_app_final.status_code == status.HTTP_200_OK
    assert res_app_final.json()["status"] == "ACCEPTED"
    assert res_app_final.json()["decision_at"] is not None

    # 10. Audit Status History
    res_hist = client.get(f"/api/v1/admissions/applications/{application_id}/history")
    assert res_hist.status_code == status.HTTP_200_OK
    hist_items = res_hist.json()["items"]
    # Should have DRAFT (init) -> SUBMITTED -> UNDER_REVIEW -> ACCEPTED
    assert len(hist_items) >= 4
    statuses = [h["new_status"] for h in hist_items]
    assert "DRAFT" in statuses
    assert "SUBMITTED" in statuses
    assert "UNDER_REVIEW" in statuses
    assert "ACCEPTED" in statuses

    # 11. Audit Decisions List
    res_decs = client.get(f"/api/v1/admissions/applications/{application_id}/decisions")
    assert res_decs.status_code == status.HTTP_200_OK
    assert res_decs.json()["total"] == 1
    assert res_decs.json()["items"][0]["decision_type"] == "ACCEPTED"


def test_admission_application_withdrawal_workflow(admissions_api_fixture):
    f = admissions_api_fixture
    client = auth_client(f["user_officer_a"])

    # 1. Setup Cycle and Applicant
    res_cycle = client.post(
        "/api/v1/admissions/cycles",
        json={
            "academic_year_id": str(f["ay_a"].id),
            "name": "Withdrawal Test Cycle",
            "code": f"CYC-WITH-{uuid.uuid4().hex[:4]}",
            "start_date": "2026-01-01",
            "end_date": "2026-05-31",
            "status": "ACTIVE",
        },
    )
    cycle_id = res_cycle.json()["id"]

    res_applicant = client.post(
        "/api/v1/admissions/applicants",
        json={
            "admission_cycle_id": cycle_id,
            "first_name": "Kavya",
            "last_name": "Rao",
            "date_of_birth": "2020-07-20",
            "gender": "FEMALE",
        },
    )
    applicant_id = res_applicant.json()["id"]

    res_app = client.post(
        "/api/v1/admissions/applications",
        json={
            "applicant_id": applicant_id,
            "admission_cycle_id": cycle_id,
            "academic_year_id": str(f["ay_a"].id),
            "target_class_id": str(f["cls_a"].id),
        },
    )
    application_id = res_app.json()["id"]

    # 2. Withdraw application
    res_withdraw = client.post(
        f"/api/v1/admissions/applications/{application_id}/withdraw",
        json={"reason": "Parent relocated to another city", "remarks": "Requested full withdrawal"},
    )
    assert res_withdraw.status_code == status.HTTP_200_OK
    assert res_withdraw.json()["status"] == "WITHDRAWN"

    # Repeated withdrawal is idempotent
    res_withdraw_repeat = client.post(
        f"/api/v1/admissions/applications/{application_id}/withdraw",
        json={"reason": "Parent relocated", "remarks": "Duplicate request"},
    )
    assert res_withdraw_repeat.status_code == status.HTTP_200_OK
    assert res_withdraw_repeat.json()["status"] == "WITHDRAWN"

    # 3. Verify history reflects withdrawal
    res_hist = client.get(f"/api/v1/admissions/applications/{application_id}/history")
    assert res_hist.status_code == status.HTTP_200_OK
    hist_items = res_hist.json()["items"]
    assert hist_items[-1]["new_status"] == "WITHDRAWN"
    assert "Parent relocated" in hist_items[-1]["reason"]
