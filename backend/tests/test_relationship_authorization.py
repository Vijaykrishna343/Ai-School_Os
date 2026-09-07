"""
Tests for Central Relationship Authorization Primitives (SEC-001A).
"""
import uuid
from datetime import date
import pytest
from app.common.enums import Gender, StudentStatus
from app.common.exceptions import ForbiddenException
from app.common.authorization import (
    resolve_parent_linked_student_ids,
    resolve_student_id_for_user,
    enforce_relationship_access,
)
from app.identity.models import IdentityRole, IdentityUser, IdentityUserRole
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.student.student import Student
from app.models.academic_year.academic_year import AcademicYear
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section


@pytest.fixture
def auth_fixture(db_session):
    """
    Creates two schools (School A & School B), parents, students, staff, and identity users
    to test all relationship authorization primitive scenarios.
    """
    db = db_session

    # 1. School A & School B
    school_a = School(
        id=uuid.uuid4(),
        name="School Alpha",
        code=f"SCHA_{uuid.uuid4().hex[:4]}",
        address_line1="100 Alpha St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )
    school_b = School(
        id=uuid.uuid4(),
        name="School Beta",
        code=f"SCHB_{uuid.uuid4().hex[:4]}",
        address_line1="200 Beta St",
        city="Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110002",
    )
    db.add_all([school_a, school_b])
    db.commit()

    # 2. Roles in School A
    parent_role = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Parent", is_system=True)
    student_role = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Student", is_system=True)
    teacher_role = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Teacher", is_system=True)
    superadmin_role = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Super Admin", is_system=True)
    unknown_role = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name="Guest", is_system=False)
    db.add_all([parent_role, student_role, teacher_role, superadmin_role, unknown_role])
    db.commit()

    # 3. Parents in School A
    parent1 = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father One",
        mother_name="Mother One",
        primary_phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        email=f"parent1_{uuid.uuid4().hex[:6]}@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    parent2 = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father Two",
        mother_name="Mother Two",
        primary_phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        email=f"parent2_{uuid.uuid4().hex[:6]}@schoola.com",
        address_line1="456 Park Ave",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
    )
    # Parent in School B
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Father Beta",
        mother_name="Mother Beta",
        primary_phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        email=f"parent_b_{uuid.uuid4().hex[:6]}@schoolb.com",
        address_line1="789 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
    )
    db.add_all([parent1, parent2, parent_b])
    db.commit()

    # 4. Students in School A
    ay_a = AcademicYear(id=uuid.uuid4(), school_id=school_a.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc_a = SchoolClass(id=uuid.uuid4(), school_id=school_a.id, name="Class 10", display_order=1)
    db.add_all([ay_a, sc_a])
    db.commit()

    sec_a = Section(id=uuid.uuid4(), school_class_id=sc_a.id, name="Section A")
    db.add(sec_a)
    db.commit()

    student1_p1 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent1.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-P1-001",
        roll_number="01",
        first_name="Child1",
        last_name="One",
        gender=Gender.MALE,
        date_of_birth=date(2010, 1, 1),
        admission_date=date(2025, 4, 1),
        email="student1_p1@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    student2_p1 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent1.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-P1-002",
        roll_number="02",
        first_name="Child2",
        last_name="One",
        gender=Gender.FEMALE,
        date_of_birth=date(2012, 2, 2),
        admission_date=date(2025, 4, 1),
        email="student2_p1@schoola.com",
        address_line1="123 Main St",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )
    student_p2 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        parent_id=parent2.id,
        academic_year_id=ay_a.id,
        school_class_id=sc_a.id,
        section_id=sec_a.id,
        admission_number="ADM-P2-001",
        roll_number="03",
        first_name="Child",
        last_name="Two",
        gender=Gender.MALE,
        date_of_birth=date(2011, 3, 3),
        admission_date=date(2025, 4, 1),
        email="student_p2@schoola.com",
        address_line1="456 Park Ave",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110001",
        status=StudentStatus.ACTIVE,
    )

    # Student in School B
    ay_b = AcademicYear(id=uuid.uuid4(), school_id=school_b.id, name="2025-2026", start_date=date(2025, 4, 1), end_date=date(2026, 3, 31))
    sc_b = SchoolClass(id=uuid.uuid4(), school_id=school_b.id, name="Class 10", display_order=1)
    db.add_all([ay_b, sc_b])
    db.commit()
    sec_b = Section(id=uuid.uuid4(), school_class_id=sc_b.id, name="Section B")
    db.add(sec_b)
    db.commit()

    student_school_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        parent_id=parent_b.id,
        academic_year_id=ay_b.id,
        school_class_id=sc_b.id,
        section_id=sec_b.id,
        admission_number="ADM-B-001",
        roll_number="01",
        first_name="Child",
        last_name="Beta",
        gender=Gender.FEMALE,
        date_of_birth=date(2010, 5, 5),
        admission_date=date(2025, 4, 1),
        email="student_b@schoolb.com",
        address_line1="789 Beta Rd",
        city="Delhi",
        district="Central",
        state="Delhi",
        postal_code="110002",
        status=StudentStatus.ACTIVE,
    )
    db.add_all([student1_p1, student2_p1, student_p2, student_school_b])
    db.commit()

    # 5. Identity Users
    user_parent1 = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=parent1.email,
        phone=parent1.primary_phone,
        password_hash="hash123",
        first_name="Parent",
        last_name="One",
    )
    user_parent2 = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=parent2.email,
        phone=parent2.primary_phone,
        password_hash="hash123",
        first_name="Parent",
        last_name="Two",
    )
    user_parent_unmapped = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"unmapped_parent_{uuid.uuid4().hex[:6]}@schoola.com",
        phone=f"+919{uuid.uuid4().int % 1000000009:09d}",
        password_hash="hash123",
        first_name="Unmapped",
        last_name="Parent",
    )
    user_student1 = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="student1_p1@schoola.com",
        username="ADM-P1-001",
        password_hash="hash123",
        first_name="Student",
        last_name="One",
    )
    user_student2 = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="student2_p1@schoola.com",
        username="ADM-P1-002",
        password_hash="hash123",
        first_name="Student",
        last_name="Two",
    )
    user_student_unmapped = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="unmapped_student@schoola.com",
        username="ADM-UNMAPPED",
        password_hash="hash123",
        first_name="Unmapped",
        last_name="Student",
    )
    user_teacher = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="teacher@schoola.com",
        password_hash="hash123",
        first_name="Teacher",
        last_name="Alpha",
    )
    user_superadmin = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="admin@platform.com",
        password_hash="hash123",
        first_name="Super",
        last_name="Admin",
    )
    user_unknown_role = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email="guest@schoola.com",
        password_hash="hash123",
        first_name="Guest",
        last_name="User",
    )

    db.add_all([
        user_parent1, user_parent2, user_parent_unmapped,
        user_student1, user_student2, user_student_unmapped,
        user_teacher, user_superadmin, user_unknown_role
    ])
    db.commit()

    # Assign Roles
    db.add_all([
        IdentityUserRole(user_id=user_parent1.id, role_id=parent_role.id),
        IdentityUserRole(user_id=user_parent2.id, role_id=parent_role.id),
        IdentityUserRole(user_id=user_parent_unmapped.id, role_id=parent_role.id),
        IdentityUserRole(user_id=user_student1.id, role_id=student_role.id),
        IdentityUserRole(user_id=user_student2.id, role_id=student_role.id),
        IdentityUserRole(user_id=user_student_unmapped.id, role_id=student_role.id),
        IdentityUserRole(user_id=user_teacher.id, role_id=teacher_role.id),
        IdentityUserRole(user_id=user_superadmin.id, role_id=superadmin_role.id),
        IdentityUserRole(user_id=user_unknown_role.id, role_id=unknown_role.id),
    ])
    db.commit()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "parent1": parent1,
        "parent2": parent2,
        "student1_p1": student1_p1,
        "student2_p1": student2_p1,
        "student_p2": student_p2,
        "student_school_b": student_school_b,
        "user_parent1": user_parent1,
        "user_parent2": user_parent2,
        "user_parent_unmapped": user_parent_unmapped,
        "user_student1": user_student1,
        "user_student2": user_student2,
        "user_student_unmapped": user_student_unmapped,
        "user_teacher": user_teacher,
        "user_superadmin": user_superadmin,
        "user_unknown_role": user_unknown_role,
    }


# ============================================================================
# PARENT AUTHORIZATION PRIMITIVE TESTS
# ============================================================================

def test_parent_with_multiple_children_resolves_all_children(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    child_ids = resolve_parent_linked_student_ids(db, fx["school_a"].id, fx["user_parent1"])
    assert len(child_ids) == 2
    assert fx["student1_p1"].id in child_ids
    assert fx["student2_p1"].id in child_ids


def test_parent_with_one_child_resolves_correctly(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    child_ids = resolve_parent_linked_student_ids(db, fx["school_a"].id, fx["user_parent2"])
    assert len(child_ids) == 1
    assert child_ids[0] == fx["student_p2"].id


def test_parent_cannot_resolve_another_parents_child(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_parent2"],
            target_student_id=fx["student1_p1"].id,
        )


def test_parent_cannot_resolve_child_from_another_school(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_parent1"],
            target_student_id=fx["student_school_b"].id,
        )


def test_parent_with_missing_unmapped_identity_fails_closed(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    child_ids = resolve_parent_linked_student_ids(db, fx["school_a"].id, fx["user_parent_unmapped"])
    assert child_ids == []

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_parent_unmapped"],
            target_student_id=None,
        )


# ============================================================================
# STUDENT AUTHORIZATION PRIMITIVE TESTS
# ============================================================================

def test_student_resolves_own_student_record(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    student_id = resolve_student_id_for_user(db, fx["school_a"].id, fx["user_student1"])
    assert student_id == fx["student1_p1"].id

    res = enforce_relationship_access(
        db,
        school_id=fx["school_a"].id,
        current_user=fx["user_student1"],
        target_student_id=fx["student1_p1"].id,
    )
    assert res == fx["student1_p1"].id


def test_student_cannot_resolve_another_student(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_student1"],
            target_student_id=fx["student2_p1"].id,
        )


def test_student_cannot_resolve_student_from_another_school(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_student1"],
            target_student_id=fx["student_school_b"].id,
        )


def test_student_with_no_valid_mapping_fails_closed(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    resolved_id = resolve_student_id_for_user(db, fx["school_a"].id, fx["user_student_unmapped"])
    assert resolved_id is None

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_student_unmapped"],
            target_student_id=None,
        )


# ============================================================================
# GENERAL & STAFF / ADMIN COMPATIBILITY TESTS
# ============================================================================

def test_staff_behavior_remains_compatible(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    res = enforce_relationship_access(
        db,
        school_id=fx["school_a"].id,
        current_user=fx["user_teacher"],
        target_student_id=fx["student1_p1"].id,
    )
    assert res == fx["student1_p1"].id


def test_super_admin_behavior_remains_compatible(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    res = enforce_relationship_access(
        db,
        school_id=fx["school_a"].id,
        current_user=fx["user_superadmin"],
        target_student_id=fx["student1_p1"].id,
    )
    assert res == fx["student1_p1"].id


def test_unsupported_role_fails_closed(db_session, auth_fixture):
    db = db_session
    fx = auth_fixture

    with pytest.raises(ForbiddenException):
        enforce_relationship_access(
            db,
            school_id=fx["school_a"].id,
            current_user=fx["user_unknown_role"],
            target_student_id=fx["student1_p1"].id,
        )
