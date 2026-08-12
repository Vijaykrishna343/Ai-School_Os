from datetime import time
import uuid

import pytest

from app.common.enums.timetable import PeriodType
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.school.school import School
from app.models.timetable.period_slot import PeriodSlot
from app.schemas.timetable.period_slot import (
    PeriodSlotCreate,
    PeriodSlotFilter,
    PeriodSlotUpdate,
)
from app.services.period_slot_service import PeriodSlotService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Timetable Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def slot_setup(db_session):
    school_1 = make_school("Slot School 1", "SS1")
    school_2 = make_school("Slot School 2", "SS2")
    db_session.add_all([school_1, school_2])
    db_session.commit()
    return {"school_1": school_1, "school_2": school_2}


def test_create_period_slot_success(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    payload = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1",
        period_type=PeriodType.REGULAR,
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, payload, current_school_id=school.id)

    assert slot.id is not None
    assert slot.name == "Period 1"
    assert slot.period_type == PeriodType.REGULAR
    assert slot.start_time == time(8, 30)
    assert slot.end_time == time(9, 15)
    assert slot.display_order == 1
    assert slot.school_id == school.id


def test_create_period_slot_invalid_time_range(db_session, slot_setup):
    school = slot_setup["school_1"]

    with pytest.raises(ValueError, match="start_time must be before end_time"):
        PeriodSlotCreate(
            school_id=school.id,
            name="Bad Slot",
            start_time=time(10, 0),
            end_time=time(9, 0),
            display_order=1,
        )


def test_create_period_slot_equal_times(db_session, slot_setup):
    school = slot_setup["school_1"]

    with pytest.raises(ValueError, match="start_time must be before end_time"):
        PeriodSlotCreate(
            school_id=school.id,
            name="Equal Slot",
            start_time=time(10, 0),
            end_time=time(10, 0),
            display_order=1,
        )


def test_create_period_slot_zero_display_order(db_session, slot_setup):
    school = slot_setup["school_1"]

    with pytest.raises(ValueError):
        PeriodSlotCreate(
            school_id=school.id,
            name="Zero Order",
            start_time=time(8, 0),
            end_time=time(9, 0),
            display_order=0,
        )


def test_create_period_slot_negative_display_order(db_session, slot_setup):
    school = slot_setup["school_1"]

    with pytest.raises(ValueError):
        PeriodSlotCreate(
            school_id=school.id,
            name="Negative Order",
            start_time=time(8, 0),
            end_time=time(9, 0),
            display_order=-1,
        )


def test_duplicate_display_order_same_school_rejected(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    payload = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    service.create_period_slot(db_session, payload, current_school_id=school.id)

    dup = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1 Dup",
        start_time=time(9, 15),
        end_time=time(10, 0),
        display_order=1,
    )
    with pytest.raises(AlreadyExistsException):
        service.create_period_slot(db_session, dup, current_school_id=school.id)


def test_same_display_order_different_school_allowed(db_session, slot_setup):
    service = PeriodSlotService()
    school_1 = slot_setup["school_1"]
    school_2 = slot_setup["school_2"]

    p1 = PeriodSlotCreate(
        school_id=school_1.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    service.create_period_slot(db_session, p1, current_school_id=school_1.id)

    p2 = PeriodSlotCreate(
        school_id=school_2.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, p2, current_school_id=school_2.id)
    assert slot.school_id == school_2.id


def test_soft_deleted_slot_allows_reuse(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    payload = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, payload, current_school_id=school.id)
    service.delete_period_slot(db_session, slot.id, current_school_id=school.id)

    # Same display_order should now be available
    reuse = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1 Reused",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    new_slot = service.create_period_slot(db_session, reuse, current_school_id=school.id)
    assert new_slot.display_order == 1
    assert new_slot.name == "Period 1 Reused"


def test_tenant_isolation_period_slot(db_session, slot_setup):
    service = PeriodSlotService()
    school_1 = slot_setup["school_1"]
    school_2 = slot_setup["school_2"]

    payload = PeriodSlotCreate(
        school_id=school_1.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, payload, current_school_id=school_1.id)

    # School 2 cannot read School 1's slot
    with pytest.raises(NotFoundException):
        service.get_period_slot(db_session, slot.id, current_school_id=school_2.id)

    # School 2 cannot update School 1's slot
    with pytest.raises(NotFoundException):
        service.update_period_slot(
            db_session, slot.id,
            PeriodSlotUpdate(name="Hacked"),
            current_school_id=school_2.id,
        )

    # School 2 cannot delete School 1's slot
    with pytest.raises(NotFoundException):
        service.delete_period_slot(db_session, slot.id, current_school_id=school_2.id)


def test_cross_school_create_rejected(db_session, slot_setup):
    service = PeriodSlotService()
    school_1 = slot_setup["school_1"]
    school_2 = slot_setup["school_2"]

    payload = PeriodSlotCreate(
        school_id=school_1.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    with pytest.raises(ForbiddenException):
        service.create_period_slot(db_session, payload, current_school_id=school_2.id)


def test_update_period_slot_success(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    payload = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, payload, current_school_id=school.id)

    updated = service.update_period_slot(
        db_session,
        slot.id,
        PeriodSlotUpdate(name="Period 1 Updated", period_type=PeriodType.ASSEMBLY),
        current_school_id=school.id,
    )
    assert updated.name == "Period 1 Updated"
    assert updated.period_type == PeriodType.ASSEMBLY


def test_update_period_slot_invalid_time_rejected(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    payload = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, payload, current_school_id=school.id)

    with pytest.raises(ValidationException, match="start_time must be before end_time"):
        service.update_period_slot(
            db_session,
            slot.id,
            PeriodSlotUpdate(start_time=time(10, 0)),
            current_school_id=school.id,
        )


def test_list_period_slots(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    for i in range(3):
        service.create_period_slot(
            db_session,
            PeriodSlotCreate(
                school_id=school.id,
                name=f"Period {i + 1}",
                start_time=time(8 + i, 0),
                end_time=time(8 + i, 45),
                display_order=i + 1,
            ),
            current_school_id=school.id,
        )

    result = service.list_period_slots(
        db_session,
        PeriodSlotFilter(page=1, page_size=10),
        current_school_id=school.id,
    )
    assert result.total == 3
    assert len(result.items) == 3
    assert result.items[0].display_order == 1


def test_delete_period_slot_success(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    payload = PeriodSlotCreate(
        school_id=school.id,
        name="Period 1",
        start_time=time(8, 30),
        end_time=time(9, 15),
        display_order=1,
    )
    slot = service.create_period_slot(db_session, payload, current_school_id=school.id)
    service.delete_period_slot(db_session, slot.id, current_school_id=school.id)

    with pytest.raises(NotFoundException):
        service.get_period_slot(db_session, slot.id, current_school_id=school.id)


def test_get_nonexistent_period_slot(db_session, slot_setup):
    service = PeriodSlotService()
    school = slot_setup["school_1"]

    with pytest.raises(NotFoundException):
        service.get_period_slot(db_session, uuid.uuid4(), current_school_id=school.id)
