import uuid
from datetime import datetime

import pytest
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.academic_year.class_progression_rule import ClassProgressionRule
from app.repositories.academic_year.class_progression_rule_repository import (
    class_progression_rule_repository,
)
from app.repositories.school.school_repository import school_repository
from app.repositories.school_class.school_class_repository import school_class_repository
from app.schemas.academic_year.class_progression_rule_schema import (
    ClassProgressionRuleCreate,
    ClassProgressionRuleUpdate,
)
from app.services.class_progression_rule_service import (
    ClassProgressionRuleService,
    class_progression_rule_service,
)


@pytest.fixture
def setup_progression_test_data(db_session):
    db = db_session

    # School 1
    school1 = School(
        id=uuid.uuid4(),
        name="Primary Alpha School",
        code="ALPHA",
        address_line1="100 Alpha Way",
        city="Pune",
        district="Pune",
        state="Maharashtra",
        country="India",
        postal_code="411001",
    )
    db.add(school1)

    # School 2 (Tenant Isolation)
    school2 = School(
        id=uuid.uuid4(),
        name="Secondary Beta School",
        code="BETA",
        address_line1="200 Beta Way",
        city="Mumbai",
        district="Mumbai",
        state="Maharashtra",
        country="India",
        postal_code="400001",
    )
    db.add(school2)
    db.commit()

    # School 1 Classes
    sc1_c1 = SchoolClass(id=uuid.uuid4(), school_id=school1.id, name="Class 1", display_order=1)
    sc1_c2 = SchoolClass(id=uuid.uuid4(), school_id=school1.id, name="Class 2", display_order=2)
    sc1_c12 = SchoolClass(id=uuid.uuid4(), school_id=school1.id, name="Class 12", display_order=12)
    db.add_all([sc1_c1, sc1_c2, sc1_c12])

    # School 2 Class
    sc2_c1 = SchoolClass(id=uuid.uuid4(), school_id=school2.id, name="Class 1", display_order=1)
    db.add(sc2_c1)

    db.commit()

    return {
        "s1": school1,
        "s2": school2,
        "s1_c1": sc1_c1,
        "s1_c2": sc1_c2,
        "s1_c12": sc1_c12,
        "s2_c1": sc2_c1,
    }


def test_create_normal_progression_rule(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    dto = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c2"].id,
        is_terminal=False,
        description="Standard Class 1 to Class 2 promotion",
    )

    created = service.create_rule(db_session, dto, current_school_id=data["s1"].id)
    assert created.id is not None
    assert created.school_id == data["s1"].id
    assert created.source_class_id == data["s1_c1"].id
    assert created.target_class_id == data["s1_c2"].id
    assert created.is_terminal is False
    assert created.description == "Standard Class 1 to Class 2 promotion"


def test_create_terminal_progression_rule(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    dto = ClassProgressionRuleCreate(
        source_class_id=data["s1_c12"].id,
        target_class_id=None,
        is_terminal=True,
        description="Class 12 Graduation Rule",
    )

    created = service.create_rule(db_session, dto, current_school_id=data["s1"].id)
    assert created.id is not None
    assert created.source_class_id == data["s1_c12"].id
    assert created.target_class_id is None
    assert created.is_terminal is True


def test_reject_terminal_rule_with_target_class(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    with pytest.raises(ValueError, match="Terminal progression rules must not specify a target class"):
        ClassProgressionRuleCreate(
            source_class_id=data["s1_c12"].id,
            target_class_id=data["s1_c2"].id,
            is_terminal=True,
        )


def test_reject_non_terminal_rule_without_target(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    with pytest.raises(ValueError, match="Non-terminal progression rules must specify a target class"):
        ClassProgressionRuleCreate(
            source_class_id=data["s1_c1"].id,
            target_class_id=None,
            is_terminal=False,
        )


def test_reject_self_progression(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    with pytest.raises(ValueError, match="Source class and target class cannot be the same"):
        ClassProgressionRuleCreate(
            source_class_id=data["s1_c1"].id,
            target_class_id=data["s1_c1"].id,
            is_terminal=False,
        )


def test_reject_duplicate_active_source_rule(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    dto = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c2"].id,
        is_terminal=False,
    )
    service.create_rule(db_session, dto, current_school_id=data["s1"].id)

    # Attempt second rule for same source class
    dto_dup = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c12"].id,
        is_terminal=False,
    )

    with pytest.raises(AlreadyExistsException, match="Class Progression Rule for source class"):
        service.create_rule(db_session, dto_dup, current_school_id=data["s1"].id)


def test_update_rule_valid(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    dto = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c2"].id,
        is_terminal=False,
        description="Original description",
    )
    created = service.create_rule(db_session, dto, current_school_id=data["s1"].id)

    update_dto = ClassProgressionRuleUpdate(description="Updated description")
    updated = service.update_rule(db_session, created.id, update_dto, current_school_id=data["s1"].id)
    assert updated.description == "Updated description"


def test_update_rule_terminal_transitions(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    # 1. Start Non-terminal
    dto = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c2"].id,
        is_terminal=False,
    )
    rule = service.create_rule(db_session, dto, current_school_id=data["s1"].id)

    # 2. Switch to Terminal
    rule_term = service.update_rule(
        db_session,
        rule.id,
        ClassProgressionRuleUpdate(is_terminal=True, target_class_id=None),
        current_school_id=data["s1"].id,
    )
    assert rule_term.is_terminal is True
    assert rule_term.target_class_id is None

    # 3. Switch back to Non-terminal with target
    rule_non_term = service.update_rule(
        db_session,
        rule.id,
        ClassProgressionRuleUpdate(is_terminal=False, target_class_id=data["s1_c2"].id),
        current_school_id=data["s1"].id,
    )
    assert rule_non_term.is_terminal is False
    assert rule_non_term.target_class_id == data["s1_c2"].id


def test_soft_delete_and_replacement_rule(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    dto = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c2"].id,
        is_terminal=False,
    )
    created = service.create_rule(db_session, dto, current_school_id=data["s1"].id)

    # Soft delete
    service.delete_rule(db_session, created.id, current_school_id=data["s1"].id)

    # Verify not found in active list
    rules, total, _ = service.get_paginated_rules(db_session, current_school_id=data["s1"].id)
    assert total == 0

    # Replacement rule creation for same source class succeeds
    replacement = service.create_rule(db_session, dto, current_school_id=data["s1"].id)
    assert replacement.id != created.id


def test_tenant_isolation_cross_school(db_session, setup_progression_test_data):
    data = setup_progression_test_data
    service = ClassProgressionRuleService(
        repository=class_progression_rule_repository,
        school_repository=school_repository,
        school_class_repository=school_class_repository,
    )

    # 1. School 1 rule
    dto1 = ClassProgressionRuleCreate(
        source_class_id=data["s1_c1"].id,
        target_class_id=data["s1_c2"].id,
        is_terminal=False,
    )
    rule1 = service.create_rule(db_session, dto1, current_school_id=data["s1"].id)

    # 2. School 2 attempts to read School 1 rule -> NotFound
    with pytest.raises(NotFoundException):
        service.get_rule(db_session, rule1.id, current_school_id=data["s2"].id)

    # 3. School 2 attempts update on School 1 rule -> NotFound
    with pytest.raises(NotFoundException):
        service.update_rule(
            db_session,
            rule1.id,
            ClassProgressionRuleUpdate(description="Hack"),
            current_school_id=data["s2"].id,
        )

    # 4. School 2 attempts delete on School 1 rule -> NotFound
    with pytest.raises(NotFoundException):
        service.delete_rule(db_session, rule1.id, current_school_id=data["s2"].id)

    # 5. School 1 attempts creating rule using School 2 target class -> ValidationException
    dto_cross = ClassProgressionRuleCreate(
        source_class_id=data["s1_c12"].id,
        target_class_id=data["s2_c1"].id,
        is_terminal=False,
    )
    with pytest.raises(ValidationException, match="Target class not found or belongs to another school"):
        service.create_rule(db_session, dto_cross, current_school_id=data["s1"].id)
