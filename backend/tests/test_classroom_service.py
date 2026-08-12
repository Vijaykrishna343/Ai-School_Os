import uuid

import pytest

from app.common.enums.timetable import RoomType
from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.school.school import School
from app.models.timetable.classroom import Classroom
from app.schemas.timetable.classroom import (
    ClassroomCreate,
    ClassroomFilter,
    ClassroomUpdate,
)
from app.services.classroom_service import ClassroomService


def make_school(name: str, code: str) -> School:
    return School(
        id=uuid.uuid4(),
        name=name,
        code=f"{code}_{uuid.uuid4().hex[:4]}",
        address_line1="100 Room Way",
        city="New Delhi",
        district="Central",
        state="Delhi",
        country="India",
        postal_code="110001",
    )


@pytest.fixture
def room_setup(db_session):
    school_1 = make_school("Room School 1", "RS1")
    school_2 = make_school("Room School 2", "RS2")
    db_session.add_all([school_1, school_2])
    db_session.commit()
    return {"school_1": school_1, "school_2": school_2}


def test_create_classroom_success(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    payload = ClassroomCreate(
        school_id=school.id,
        room_number="101",
        building_name="Main Building",
        capacity=40,
        room_type=RoomType.CLASSROOM,
    )
    classroom = service.create_classroom(db_session, payload, current_school_id=school.id)

    assert classroom.id is not None
    assert classroom.room_number == "101"
    assert classroom.building_name == "Main Building"
    assert classroom.capacity == 40
    assert classroom.room_type == RoomType.CLASSROOM
    assert classroom.school_id == school.id


def test_create_classroom_blank_room_number_rejected(db_session, room_setup):
    school = room_setup["school_1"]

    with pytest.raises(ValueError):
        ClassroomCreate(
            school_id=school.id,
            room_number="",
            capacity=40,
        )


def test_create_classroom_zero_capacity_rejected(db_session, room_setup):
    school = room_setup["school_1"]

    with pytest.raises(ValueError):
        ClassroomCreate(
            school_id=school.id,
            room_number="101",
            capacity=0,
        )


def test_create_classroom_negative_capacity_rejected(db_session, room_setup):
    school = room_setup["school_1"]

    with pytest.raises(ValueError):
        ClassroomCreate(
            school_id=school.id,
            room_number="101",
            capacity=-5,
        )


def test_duplicate_room_number_same_school_rejected(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    payload = ClassroomCreate(
        school_id=school.id,
        room_number="101",
        capacity=40,
    )
    service.create_classroom(db_session, payload, current_school_id=school.id)

    dup = ClassroomCreate(
        school_id=school.id,
        room_number="101",
        capacity=30,
    )
    with pytest.raises(AlreadyExistsException):
        service.create_classroom(db_session, dup, current_school_id=school.id)


def test_same_room_number_different_school_allowed(db_session, room_setup):
    service = ClassroomService()
    school_1 = room_setup["school_1"]
    school_2 = room_setup["school_2"]

    p1 = ClassroomCreate(school_id=school_1.id, room_number="101", capacity=40)
    service.create_classroom(db_session, p1, current_school_id=school_1.id)

    p2 = ClassroomCreate(school_id=school_2.id, room_number="101", capacity=30)
    classroom = service.create_classroom(db_session, p2, current_school_id=school_2.id)
    assert classroom.school_id == school_2.id


def test_soft_deleted_classroom_allows_reuse(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    payload = ClassroomCreate(school_id=school.id, room_number="101", capacity=40)
    classroom = service.create_classroom(db_session, payload, current_school_id=school.id)
    service.delete_classroom(db_session, classroom.id, current_school_id=school.id)

    reuse = ClassroomCreate(school_id=school.id, room_number="101", capacity=50)
    new_classroom = service.create_classroom(db_session, reuse, current_school_id=school.id)
    assert new_classroom.room_number == "101"
    assert new_classroom.capacity == 50


def test_tenant_isolation_classroom(db_session, room_setup):
    service = ClassroomService()
    school_1 = room_setup["school_1"]
    school_2 = room_setup["school_2"]

    payload = ClassroomCreate(school_id=school_1.id, room_number="101", capacity=40)
    classroom = service.create_classroom(db_session, payload, current_school_id=school_1.id)

    # School 2 cannot read School 1's classroom
    with pytest.raises(NotFoundException):
        service.get_classroom(db_session, classroom.id, current_school_id=school_2.id)

    # School 2 cannot update School 1's classroom
    with pytest.raises(NotFoundException):
        service.update_classroom(
            db_session, classroom.id,
            ClassroomUpdate(room_number="HACKED"),
            current_school_id=school_2.id,
        )

    # School 2 cannot delete School 1's classroom
    with pytest.raises(NotFoundException):
        service.delete_classroom(db_session, classroom.id, current_school_id=school_2.id)


def test_cross_school_create_rejected(db_session, room_setup):
    service = ClassroomService()
    school_1 = room_setup["school_1"]
    school_2 = room_setup["school_2"]

    payload = ClassroomCreate(school_id=school_1.id, room_number="101", capacity=40)
    with pytest.raises(ForbiddenException):
        service.create_classroom(db_session, payload, current_school_id=school_2.id)


def test_update_classroom_success(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    payload = ClassroomCreate(school_id=school.id, room_number="101", capacity=40)
    classroom = service.create_classroom(db_session, payload, current_school_id=school.id)

    updated = service.update_classroom(
        db_session,
        classroom.id,
        ClassroomUpdate(
            room_number="102",
            building_name="Science Block",
            capacity=60,
            room_type=RoomType.LABORATORY,
        ),
        current_school_id=school.id,
    )
    assert updated.room_number == "102"
    assert updated.building_name == "Science Block"
    assert updated.capacity == 60
    assert updated.room_type == RoomType.LABORATORY


def test_update_classroom_duplicate_room_number_rejected(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    service.create_classroom(
        db_session,
        ClassroomCreate(school_id=school.id, room_number="101", capacity=40),
        current_school_id=school.id,
    )
    c2 = service.create_classroom(
        db_session,
        ClassroomCreate(school_id=school.id, room_number="102", capacity=40),
        current_school_id=school.id,
    )

    with pytest.raises(AlreadyExistsException):
        service.update_classroom(
            db_session,
            c2.id,
            ClassroomUpdate(room_number="101"),
            current_school_id=school.id,
        )


def test_list_classrooms(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    for i in range(3):
        service.create_classroom(
            db_session,
            ClassroomCreate(
                school_id=school.id,
                room_number=f"10{i + 1}",
                capacity=40,
            ),
            current_school_id=school.id,
        )

    result = service.list_classrooms(
        db_session,
        ClassroomFilter(page=1, page_size=10),
        current_school_id=school.id,
    )
    assert result.total == 3
    assert len(result.items) == 3


def test_delete_classroom_success(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    payload = ClassroomCreate(school_id=school.id, room_number="101", capacity=40)
    classroom = service.create_classroom(db_session, payload, current_school_id=school.id)
    service.delete_classroom(db_session, classroom.id, current_school_id=school.id)

    with pytest.raises(NotFoundException):
        service.get_classroom(db_session, classroom.id, current_school_id=school.id)


def test_get_nonexistent_classroom(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    with pytest.raises(NotFoundException):
        service.get_classroom(db_session, uuid.uuid4(), current_school_id=school.id)


def test_classroom_default_values(db_session, room_setup):
    service = ClassroomService()
    school = room_setup["school_1"]

    payload = ClassroomCreate(school_id=school.id, room_number="200")
    classroom = service.create_classroom(db_session, payload, current_school_id=school.id)

    assert classroom.capacity == 40
    assert classroom.room_type == RoomType.CLASSROOM
    assert classroom.building_name is None
