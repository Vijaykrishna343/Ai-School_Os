"""
Phase 12.3 — AI Timetable Generator & CP-SAT Constraint Solver Test Suite.
Covers CP-SAT solver constraints, independent validator, tenant boundary protection, RBAC, workflow stages, and API endpoints.
"""

import uuid
import pytest
from datetime import date, time
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.ai.timetable.solver import (
    TimetableCPSATSolver,
    TimetableSolverInput,
    TimetableAssignmentOutput,
    PeriodSlotInput,
    ClassroomInput,
    CurriculumRequirementInput,
    TeacherUnavailabilityInput,
    SectionUnavailabilityInput,
)
from app.ai.timetable.validator import TimetableValidator, timetable_validator
from app.models.school import School
from app.models.academic_year import AcademicYear
from app.models.school_class import SchoolClass
from app.models.section import Section
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.models.timetable import PeriodSlot, Classroom, Timetable, TimetableEntry
from app.models.ai import AITimetableDraft, AITimetableDraftEntry
from app.identity.models import IdentityUser, IdentityRole
from app.identity.security.password import hash_password
from app.identity.security.jwt_manager import jwt_manager
from app.identity.seeders import seed_identity
from app.common.enums import Gender
from app.common.exceptions import ForbiddenException, BadRequestException


@pytest.fixture
def ai_timetable_env(db_session: Session):
    seed_identity(db_session)

    s_a = uuid.uuid4().hex[:6]
    s_b = uuid.uuid4().hex[:6]

    school_a = School(
        id=uuid.uuid4(), name=f"Timetable School A {s_a}", code=f"TTA_{s_a}",
        address_line1="1 Timetable Lane", city="Hyderabad", district="Hyderabad", state="Telangana", postal_code="500081",
    )
    school_b = School(
        id=uuid.uuid4(), name=f"Timetable School B {s_b}", code=f"TTB_{s_b}",
        address_line1="2 Timetable Road", city="Bangalore", district="Bangalore", state="Karnataka", postal_code="560001",
    )
    db_session.add_all([school_a, school_b])
    db_session.commit()

    ay_a = AcademicYear(
        id=uuid.uuid4(), school_id=school_a.id, name="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), is_current=True,
    )
    ay_b = AcademicYear(
        id=uuid.uuid4(), school_id=school_b.id, name="2026-2027",
        start_date=date(2026, 6, 1), end_date=date(2027, 4, 30), is_current=True,
    )
    db_session.add_all([ay_a, ay_b])

    # Class and Section
    cls_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Class 10", display_order=1)
    sec_a = Section(id=uuid.uuid4(), school_class_id=cls_a.id, name="Section A")
    db_session.add_all([cls_a, sec_a])

    # Period Slots
    p1 = PeriodSlot(id=uuid.uuid4(), school_id=school_a.id, name="Period 1", start_time=time(8, 30), end_time=time(9, 15), display_order=1)
    p2 = PeriodSlot(id=uuid.uuid4(), school_id=school_a.id, name="Period 2", start_time=time(9, 30), end_time=time(10, 15), display_order=2)
    db_session.add_all([p1, p2])

    # Subjects & Teachers
    sub1 = Subject(id=uuid.uuid4(), school_id=school_a.id, subject_code="MATH101", subject_name="Mathematics")
    sub2 = Subject(id=uuid.uuid4(), school_id=school_a.id, subject_code="SCI101", subject_name="Science")
    db_session.add_all([sub1, sub2])

    t1 = Teacher(
        id=uuid.uuid4(), school_id=school_a.id, employee_id=f"EMP_T1_{s_a}", gender=Gender.FEMALE,
        first_name="Alice", last_name="Teacher", phone=f"90000{s_a[:5]}", email=f"alice_{s_a}@school.com",
        date_of_birth=date(1990, 1, 1), joining_date=date(2020, 1, 1), qualification="M.Sc Math",
        address_line1="Street 1", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    t2 = Teacher(
        id=uuid.uuid4(), school_id=school_a.id, employee_id=f"EMP_T2_{s_a}", gender=Gender.MALE,
        first_name="Bob", last_name="Teacher", phone=f"91000{s_a[:5]}", email=f"bob_{s_a}@school.com",
        date_of_birth=date(1991, 1, 1), joining_date=date(2021, 1, 1), qualification="M.Sc Physics",
        address_line1="Street 2", city="Hyd", district="Hyd", state="TS", postal_code="500081",
    )
    db_session.add_all([t1, t2])

    # Classrooms
    r1 = Classroom(id=uuid.uuid4(), school_id=school_a.id, room_number="101", capacity=40)
    r2 = Classroom(id=uuid.uuid4(), school_id=school_a.id, room_number="102", capacity=40)
    db_session.add_all([r1, r2])

    # Users
    admin_role = db_session.query(IdentityRole).filter_by(name="School Admin").first()
    rec_role = db_session.query(IdentityRole).filter_by(name="Receptionist").first()
    pwd = hash_password("Password@123")

    user_a = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"tt_admin_a_{s_a}", email=f"tt_admin_a_{s_a}@school.com",
        password_hash=pwd, first_name="Admin", last_name="A", is_active=True,
    )
    user_a.roles = [admin_role]

    user_b = IdentityUser(
        id=uuid.uuid4(), school_id=school_b.id, username=f"tt_admin_b_{s_b}", email=f"tt_admin_b_{s_b}@school.com",
        password_hash=pwd, first_name="Admin", last_name="B", is_active=True,
    )
    user_b.roles = [admin_role]

    user_unauth = IdentityUser(
        id=uuid.uuid4(), school_id=school_a.id, username=f"tt_rec_a_{s_a}", email=f"tt_rec_a_{s_a}@school.com",
        password_hash=pwd, first_name="Rec", last_name="A", is_active=True,
    )
    user_unauth.roles = [rec_role]

    db_session.add_all([user_a, user_b, user_unauth])
    db_session.commit()

    tok_a = jwt_manager.create_access_token(user_id=user_a.id, school_id=school_a.id)
    tok_b = jwt_manager.create_access_token(user_id=user_b.id, school_id=school_b.id)
    tok_unauth = jwt_manager.create_access_token(user_id=user_unauth.id, school_id=school_a.id)

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "sec_a": sec_a,
        "user_a": user_a,
        "user_b": user_b,
        "headers_a": {"Authorization": f"Bearer {tok_a}"},
        "headers_b": {"Authorization": f"Bearer {tok_b}"},
        "headers_unauth": {"Authorization": f"Bearer {tok_unauth}"},
    }


# ============================================================================
# 1. CP-SAT SOLVER UNIT TESTS
# ============================================================================

def test_solver_simple_schedule_success():
    solver_input = TimetableSolverInput(
        school_id="sch_1",
        academic_year_id="ay_1",
        days=["MONDAY", "TUESDAY"],
        period_slots=[
            PeriodSlotInput(id="p1", name="P1", display_order=1),
            PeriodSlotInput(id="p2", name="P2", display_order=2),
        ],
        classrooms=[ClassroomInput(id="r1", name="101")],
        curriculum_requirements=[
            CurriculumRequirementInput(
                section_id="sec_1", school_class_id="cls_1", subject_id="sub_1", teacher_id="t1", required_weekly_periods=2
            ),
        ],
    )

    solver = TimetableCPSATSolver()
    res = solver.solve(solver_input)

    assert res.status in ("OPTIMAL", "FEASIBLE")
    assert len(res.assignments) == 2
    assert res.solver_duration_ms >= 0


def test_solver_teacher_and_section_overlap_prevention():
    solver_input = TimetableSolverInput(
        school_id="sch_1",
        academic_year_id="ay_1",
        days=["MONDAY"],
        period_slots=[PeriodSlotInput(id="p1", name="P1", display_order=1)],
        classrooms=[ClassroomInput(id="r1", name="101"), ClassroomInput(id="r2", name="102")],
        curriculum_requirements=[
            # Teacher t1 assigned to two different sections for 1 period on MONDAY (only 1 slot exists)
            CurriculumRequirementInput(section_id="sec_1", school_class_id="c1", subject_id="sub_1", teacher_id="t1", required_weekly_periods=1),
            CurriculumRequirementInput(section_id="sec_2", school_class_id="c2", subject_id="sub_2", teacher_id="t1", required_weekly_periods=1),
        ],
    )

    solver = TimetableCPSATSolver()
    res = solver.solve(solver_input)

    # Impossible schedule -> INFEASIBLE
    assert res.status == "INFEASIBLE"
    assert len(res.assignments) == 0


def test_solver_impossible_schedule_returns_infeasible():
    solver_input = TimetableSolverInput(
        school_id="sch_1",
        academic_year_id="ay_1",
        days=["MONDAY"],
        period_slots=[PeriodSlotInput(id="p1", name="P1", display_order=1)],
        classrooms=[ClassroomInput(id="r1", name="101")],
        curriculum_requirements=[
            # Section sec_1 needs 5 weekly periods, but total available slots = 1
            CurriculumRequirementInput(section_id="sec_1", school_class_id="c1", subject_id="sub_1", teacher_id="t1", required_weekly_periods=5),
        ],
    )

    solver = TimetableCPSATSolver()
    res = solver.solve(solver_input)

    assert res.status == "INFEASIBLE"


def test_solver_unavailability_respect():
    solver_input = TimetableSolverInput(
        school_id="sch_1",
        academic_year_id="ay_1",
        days=["MONDAY"],
        period_slots=[PeriodSlotInput(id="p1", name="P1", display_order=1), PeriodSlotInput(id="p2", name="P2", display_order=2)],
        classrooms=[ClassroomInput(id="r1", name="101")],
        curriculum_requirements=[
            CurriculumRequirementInput(section_id="sec_1", school_class_id="c1", subject_id="sub_1", teacher_id="t1", required_weekly_periods=1),
        ],
        teacher_unavailabilities=[
            TeacherUnavailabilityInput(teacher_id="t1", day_of_week="MONDAY", period_slot_id="p1"),
        ],
    )

    solver = TimetableCPSATSolver()
    res = solver.solve(solver_input)

    assert res.status in ("OPTIMAL", "FEASIBLE")
    assert len(res.assignments) == 1
    # Must be scheduled in p2, not p1
    assert res.assignments[0].period_slot_id == "p2"


# ============================================================================
# 2. INDEPENDENT VALIDATOR TESTS
# ============================================================================

def test_validator_detects_mutated_teacher_overlap():
    solver_input = TimetableSolverInput(
        school_id="sch_1",
        academic_year_id="ay_1",
        days=["MONDAY"],
        period_slots=[PeriodSlotInput(id="p1", name="P1", display_order=1)],
        classrooms=[ClassroomInput(id="r1", name="101"), ClassroomInput(id="r2", name="102")],
        curriculum_requirements=[
            CurriculumRequirementInput(section_id="sec_1", school_class_id="c1", subject_id="sub_1", teacher_id="t1", required_weekly_periods=1),
            CurriculumRequirementInput(section_id="sec_2", school_class_id="c2", subject_id="sub_2", teacher_id="t1", required_weekly_periods=1),
        ],
    )

    # Intentionally mutated assignment with teacher double-booked
    bad_assignments = [
        TimetableAssignmentOutput(section_id="sec_1", school_class_id="c1", subject_id="sub_1", teacher_id="t1", classroom_id="r1", period_slot_id="p1", day_of_week="MONDAY"),
        TimetableAssignmentOutput(section_id="sec_2", school_class_id="c2", subject_id="sub_2", teacher_id="t1", classroom_id="r2", period_slot_id="p1", day_of_week="MONDAY"),
    ]

    report = timetable_validator.validate(solver_input, bad_assignments)

    assert report.is_valid is False
    assert len(report.hard_violations) > 0
    assert any("Teacher 't1' double-booked" in v for v in report.hard_violations)


# ============================================================================
# 3. TENANT ISOLATION TESTS
# ============================================================================

def test_ai_timetable_tenant_isolation(client: TestClient, ai_timetable_env):
    env = ai_timetable_env
    headers_a = env["headers_a"]
    headers_b = env["headers_b"]

    # 1. School A generates draft
    gen_res = client.post(
        "/api/v1/ai/timetable/generate",
        json={"academic_year_id": str(env["ay_a"].id), "name": "School A Draft"},
        headers=headers_a,
    )
    assert gen_res.status_code == 201
    draft_a_id = gen_res.json()["id"]

    # 2. School B cannot read School A draft -> 404
    get_res_b = client.get(f"/api/v1/ai/timetable/drafts/{draft_a_id}", headers=headers_b)
    assert get_res_b.status_code == 404

    # 3. School B cannot approve School A draft -> 404
    app_res_b = client.post(f"/api/v1/ai/timetable/drafts/{draft_a_id}/approve", headers=headers_b)
    assert app_res_b.status_code == 404

    # 4. School B cannot publish School A draft -> 404
    pub_res_b = client.post(f"/api/v1/ai/timetable/drafts/{draft_a_id}/publish", headers=headers_b)
    assert pub_res_b.status_code == 404


# ============================================================================
# 4. AUTHORIZATION TESTS
# ============================================================================

def test_ai_timetable_authorization_enforcement(client: TestClient, ai_timetable_env):
    env = ai_timetable_env
    headers_unauth = env["headers_unauth"]

    payload = {"academic_year_id": str(env["ay_a"].id), "name": "Unauth Draft"}

    # Unauthorized user (Receptionist) gets 403
    res_gen = client.post("/api/v1/ai/timetable/generate", json=payload, headers=headers_unauth)
    assert res_gen.status_code == 403


# ============================================================================
# 5. DRAFT LIFECYCLE & WORKFLOW TESTS
# ============================================================================

def test_ai_timetable_complete_workflow(client: TestClient, ai_timetable_env):
    env = ai_timetable_env
    headers_a = env["headers_a"]
    ay_a_id = str(env["ay_a"].id)

    # 1. Generate Draft
    res_gen = client.post(
        "/api/v1/ai/timetable/generate",
        json={"academic_year_id": ay_a_id, "name": "Production Timetable 2026"},
        headers=headers_a,
    )
    assert res_gen.status_code == 201
    draft_data = res_gen.json()
    draft_id = draft_data["id"]

    assert draft_data["status"] in ("SOLVED", "FAILED")
    assert draft_data["solver_status"] in ("OPTIMAL", "FEASIBLE", "INFEASIBLE")

    if draft_data["status"] == "SOLVED":
        # 2. Reject Direct Publish without Approval
        res_pub_bad = client.post(f"/api/v1/ai/timetable/drafts/{draft_id}/publish", headers=headers_a)
        assert res_pub_bad.status_code == 400
        assert "Only drafts in 'APPROVED' status can be published" in str(res_pub_bad.json())

        # 3. Human Approve Step
        res_app = client.post(f"/api/v1/ai/timetable/drafts/{draft_id}/approve", headers=headers_a)
        assert res_app.status_code == 200
        assert res_app.json()["status"] == "APPROVED"

        # 4. Publish Step
        res_pub = client.post(f"/api/v1/ai/timetable/drafts/{draft_id}/publish", headers=headers_a)
        assert res_pub.status_code == 200
        assert res_pub.json()["status"] == "PUBLISHED"
