from datetime import date, time
from decimal import Decimal
import uuid
import pytest
from sqlalchemy import select

from app.common.enums import (
    AcademicYearStatus,
    BloodGroup,
    Gender,
    StudentStatus,
)
from app.common.enums.transport import (
    FuelType,
    TransportAllocationStatus,
    TransportAllocationType,
    VehicleStatus,
    VehicleType,
)
from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.database.common_model import CommonModel
from app.models.academic_year.academic_year import AcademicYear
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.transport.driver import TransportDriver
from app.models.transport.route import TransportRoute
from app.models.transport.stop import RouteStop
from app.models.transport.student_transport_allocation import StudentTransportAllocation
from app.models.transport.vehicle import Vehicle
from app.services.transport_service import transport_service


@pytest.fixture(autouse=True)
def setup_transport_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    yield


@pytest.fixture
def transport_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Oakridge International School A",
        code=f"OAK-A-{uuid.uuid4().hex[:4]}",
        address_line1="100 Express Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B (for cross-tenant rejection testing)
    school_b = School(
        id=uuid.uuid4(),
        name="Oakridge International School B",
        code=f"OAK-B-{uuid.uuid4().hex[:4]}",
        address_line1="200 Cyber Highway",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    # Academic Year for School A
    ay_a = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    # Academic Year for School B
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

    # Parents for School A and B
    from app.models.parent.parent import Parent
    from app.common.enums.teacher import TeacherStatus

    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Rajesh Sharma",
        primary_phone=f"98765{uuid.uuid4().hex[:5]}",
        email=f"rajesh.{uuid.uuid4().hex[:4]}@gmail.com",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Vikram Verma",
        primary_phone=f"98766{uuid.uuid4().hex[:5]}",
        email=f"vikram.{uuid.uuid4().hex[:4]}@gmail.com",
        address_line1="456 High St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([parent_a, parent_b])
    db_session.flush()

    # Classes and Sections for School A
    cls_a = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="Grade 5",
        display_order=5,
    )
    db_session.add(cls_a)
    db_session.flush()

    sec_a = Section(
        id=uuid.uuid4(),
        school_class_id=cls_a.id,
        name="Section A",
    )
    db_session.add(sec_a)
    db_session.flush()

    # Classes and Sections for School B
    cls_b = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name="Grade 5",
        display_order=5,
    )
    db_session.add(cls_b)
    db_session.flush()

    sec_b = Section(
        id=uuid.uuid4(),
        school_class_id=cls_b.id,
        name="Section B",
    )
    db_session.add(sec_b)
    db_session.flush()

    # Student A in School A
    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        admission_number=f"ADM-A-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="101",
        first_name="Rohan",
        last_name="Sharma",
        date_of_birth=date(2015, 5, 15),
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        address_line1="100 Express Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    # Student B in School B
    student_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        admission_number=f"ADM-B-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="102",
        first_name="Ananya",
        last_name="Verma",
        date_of_birth=date(2015, 8, 20),
        gender=Gender.FEMALE,
        blood_group=BloodGroup.A_POSITIVE,
        academic_year_id=ay_b.id,
        school_class_id=cls_b.id,
        section_id=sec_b.id,
        parent_id=parent_b.id,
        address_line1="200 Cyber Highway",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add_all([student_a, student_b])
    db_session.flush()

    # Staff Teacher in School A
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id=f"EMP-A-{uuid.uuid4().hex[:4]}",
        first_name="Venkatesh",
        last_name="Rao",
        email=f"venkat.{uuid.uuid4().hex[:4]}@school.com",
        phone=f"98765{uuid.uuid4().hex[:5]}",
        date_of_birth=date(1985, 1, 10),
        gender=Gender.MALE,
        joining_date=date(2020, 6, 1),
        qualification="B.Ed",
        address_line1="100 Express Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    # Staff Teacher in School B
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        employee_id=f"EMP-B-{uuid.uuid4().hex[:4]}",
        first_name="Suresh",
        last_name="Reddy",
        email=f"suresh.{uuid.uuid4().hex[:4]}@school.com",
        phone=f"98766{uuid.uuid4().hex[:5]}",
        date_of_birth=date(1986, 2, 12),
        gender=Gender.MALE,
        joining_date=date(2021, 6, 1),
        qualification="B.Ed",
        address_line1="200 Cyber Highway",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([teacher_a, teacher_b])
    db_session.flush()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "student_a": student_a,
        "student_b": student_b,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
    }


# =============================================================================
# 1. VEHICLE TESTS
# =============================================================================
def test_vehicle_valid_creation(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    vehicle = transport_service.create_vehicle(
        db=db_session,
        school_id=school_a.id,
        registration_number="TS09AB1234",
        vehicle_code="BUS-01",
        seating_capacity=45,
        vehicle_type=VehicleType.BUS,
        fuel_type=FuelType.DIESEL,
        insurance_expiry_date=date(2027, 12, 31),
        fitness_expiry_date=date(2027, 10, 31),
        gps_device_id="GPS-DEV-9988",
        status=VehicleStatus.ACTIVE,
        description="Main campus primary transit bus",
    )
    assert vehicle.id is not None
    assert vehicle.school_id == school_a.id
    assert vehicle.registration_number == "TS09AB1234"
    assert vehicle.vehicle_code == "BUS-01"
    assert vehicle.seating_capacity == 45
    assert vehicle.fuel_type == FuelType.DIESEL
    assert vehicle.status == VehicleStatus.ACTIVE


def test_vehicle_invalid_capacity(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    with pytest.raises(ValidationException) as exc_info:
        transport_service.create_vehicle(
            db=db_session,
            school_id=school_a.id,
            registration_number="TS09AB9999",
            vehicle_code="BUS-BAD",
            seating_capacity=0,
        )
    assert "positive integer" in str(exc_info.value)

    with pytest.raises(ValidationException):
        transport_service.create_vehicle(
            db=db_session,
            school_id=school_a.id,
            registration_number="TS09AB9998",
            vehicle_code="BUS-NEG",
            seating_capacity=-5,
        )


def test_vehicle_tenant_uniqueness(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    school_b = transport_fixture["school_b"]

    # Create in School A
    transport_service.create_vehicle(
        db=db_session,
        school_id=school_a.id,
        registration_number="TS09XY1111",
        vehicle_code="BUS-UNIQUE",
        seating_capacity=30,
    )

    # Duplicate registration in School A fails
    with pytest.raises(AlreadyExistsException) as exc_reg:
        transport_service.create_vehicle(
            db=db_session,
            school_id=school_a.id,
            registration_number="ts09xy1111",  # case-insensitive check
            vehicle_code="BUS-DIFF",
            seating_capacity=30,
        )
    assert "registration" in str(exc_reg.value)

    # Duplicate vehicle_code in School A fails
    with pytest.raises(AlreadyExistsException) as exc_code:
        transport_service.create_vehicle(
            db=db_session,
            school_id=school_a.id,
            registration_number="TS09XY2222",
            vehicle_code="bus-unique",  # case-insensitive check
            seating_capacity=30,
        )
    assert "code" in str(exc_code.value)

    # Same registration in School B succeeds (tenant isolation)
    v_b = transport_service.create_vehicle(
        db=db_session,
        school_id=school_b.id,
        registration_number="TS09XY1111",
        vehicle_code="BUS-UNIQUE",
        seating_capacity=30,
    )
    assert v_b.id is not None
    assert v_b.school_id == school_b.id


def test_vehicle_soft_delete_uniqueness(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    v = transport_service.create_vehicle(
        db=db_session,
        school_id=school_a.id,
        registration_number="TS09REUSE",
        vehicle_code="BUS-REUSE",
        seating_capacity=32,
    )
    # Soft-delete the vehicle
    v.is_deleted = True
    db_session.flush()

    # Reuse registration number and vehicle code on active record
    v_new = transport_service.create_vehicle(
        db=db_session,
        school_id=school_a.id,
        registration_number="TS09REUSE",
        vehicle_code="BUS-REUSE",
        seating_capacity=35,
    )
    assert v_new.id != v.id
    assert v_new.seating_capacity == 35


# =============================================================================
# 2. DRIVER TESTS
# =============================================================================
def test_driver_valid_creation(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    driver = transport_service.create_driver(
        db=db_session,
        school_id=school_a.id,
        name="Ramesh Kumar",
        license_number="DL-TS-2020-0012345",
        license_expiry_date=date(2030, 5, 20),
        contact_number="9876543210",
        emergency_contact="9876543219",
        remarks="Senior heavy vehicle driver",
    )
    assert driver.id is not None
    assert driver.name == "Ramesh Kumar"
    assert driver.license_number == "DL-TS-2020-0012345"
    assert driver.is_active is True


def test_driver_same_tenant_staff_link(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    teacher_a = transport_fixture["teacher_a"]

    driver = transport_service.create_driver(
        db=db_session,
        school_id=school_a.id,
        name="Venkat Rao",
        license_number="DL-STAFF-12345",
        contact_number="9876543210",
        staff_id=teacher_a.id,
    )
    assert driver.staff_id == teacher_a.id
    assert driver.staff.first_name == "Venkatesh"


def test_driver_cross_tenant_staff_rejection(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    teacher_b = transport_fixture["teacher_b"]  # belongs to School B

    with pytest.raises(ValidationException) as exc_info:
        transport_service.create_driver(
            db=db_session,
            school_id=school_a.id,
            name="Impostor Driver",
            license_number="DL-IMPOSTOR-1",
            contact_number="9876543210",
            staff_id=teacher_b.id,  # Cross-tenant violation
        )
    assert "does not exist in this school" in str(exc_info.value)


# =============================================================================
# 3. ROUTE TESTS
# =============================================================================
def test_route_valid_creation(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    vehicle_a = transport_service.create_vehicle(
        db=db_session,
        school_id=school_a.id,
        registration_number="TS09RT1234",
        vehicle_code="BUS-RT-1",
        seating_capacity=40,
    )
    driver_a = transport_service.create_driver(
        db=db_session,
        school_id=school_a.id,
        name="Shankar Driver",
        license_number="DL-TS-RT-1",
        contact_number="9988776655",
    )

    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-01",
        route_name="Madhapur to Campus North",
        description="Morning pickup and evening drop for Madhapur cluster",
        vehicle_id=vehicle_a.id,
        driver_id=driver_a.id,
        attendant_name="Laxmi",
        attendant_phone="9988776650",
        morning_start_time=time(6, 45),
        evening_start_time=time(15, 30),
        is_active=True,
    )
    assert route.id is not None
    assert route.route_code == "RT-01"
    assert route.vehicle_id == vehicle_a.id
    assert route.driver_id == driver_a.id


def test_route_cross_tenant_vehicle_rejection(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    school_b = transport_fixture["school_b"]

    vehicle_b = transport_service.create_vehicle(
        db=db_session,
        school_id=school_b.id,
        registration_number="TS09CROSS01",
        vehicle_code="BUS-B-1",
        seating_capacity=40,
    )

    with pytest.raises(ValidationException) as exc_info:
        transport_service.create_route(
            db=db_session,
            school_id=school_a.id,
            route_code="RT-FAIL-VEH",
            route_name="Route Fail Vehicle",
            vehicle_id=vehicle_b.id,  # School B vehicle referenced by School A route
        )
    assert "Referenced vehicle does not exist in this school" in str(exc_info.value)


def test_route_cross_tenant_driver_rejection(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    school_b = transport_fixture["school_b"]

    driver_b = transport_service.create_driver(
        db=db_session,
        school_id=school_b.id,
        name="Driver B",
        license_number="DL-CROSS-DRV",
        contact_number="9123456780",
    )

    with pytest.raises(ValidationException) as exc_info:
        transport_service.create_route(
            db=db_session,
            school_id=school_a.id,
            route_code="RT-FAIL-DRV",
            route_name="Route Fail Driver",
            driver_id=driver_b.id,  # School B driver referenced by School A route
        )
    assert "Referenced driver does not exist in this school" in str(exc_info.value)


# =============================================================================
# 4. STOP TESTS
# =============================================================================
def test_stop_valid_creation(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-STOPS",
        route_name="Stops Testing Route",
    )

    stop1 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Madhapur Metro Station",
        stop_code="STP-MDH-1",
        sequence_order=1,
        morning_pickup_time=time(7, 0),
        afternoon_drop_time=time(16, 0),
        landmark="Near Pillar 12",
        pickup_fee_amount=Decimal("1500.00"),
    )
    stop2 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Cyber Towers",
        stop_code="STP-CYB-2",
        sequence_order=2,
        morning_pickup_time=time(7, 15),
        afternoon_drop_time=time(15, 45),
        landmark="Opposite main gate",
        pickup_fee_amount=Decimal("1800.00"),
    )
    assert stop1.id is not None
    assert stop2.id is not None
    assert stop1.sequence_order == 1
    assert stop2.sequence_order == 2
    assert stop1.pickup_fee_amount == Decimal("1500.00")


def test_stop_sequence_uniqueness(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-SEQ",
        route_name="Sequence Test Route",
    )
    transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Stop Alpha",
        stop_code="STP-A",
        sequence_order=1,
    )

    with pytest.raises(AlreadyExistsException) as exc_info:
        transport_service.create_stop(
            db=db_session,
            school_id=school_a.id,
            route_id=route.id,
            stop_name="Stop Duplicate Sequence",
            stop_code="STP-B",
            sequence_order=1,  # Duplicate sequence on same route
        )
    assert "sequence order 1 already exists" in str(exc_info.value)


def test_stop_sequence_and_fee_validations(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-VAL",
        route_name="Validation Route",
    )

    # Invalid sequence order <= 0
    with pytest.raises(ValidationException):
        transport_service.create_stop(
            db=db_session,
            school_id=school_a.id,
            route_id=route.id,
            stop_name="Invalid Seq Stop",
            stop_code="STP-INV",
            sequence_order=0,
        )

    # Negative fee
    with pytest.raises(ValidationException):
        transport_service.create_stop(
            db=db_session,
            school_id=school_a.id,
            route_id=route.id,
            stop_name="Negative Fee Stop",
            stop_code="STP-NEG",
            sequence_order=1,
            pickup_fee_amount=Decimal("-100.00"),
        )


def test_stop_cross_tenant_route_rejection(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    school_b = transport_fixture["school_b"]

    route_b = transport_service.create_route(
        db=db_session,
        school_id=school_b.id,
        route_code="RT-SCH-B",
        route_name="School B Route",
    )

    with pytest.raises(ValidationException) as exc_info:
        transport_service.create_stop(
            db=db_session,
            school_id=school_a.id,  # School A tenant context
            route_id=route_b.id,   # School B route
            stop_name="Cross Stop",
            stop_code="STP-CROSS",
            sequence_order=1,
        )
    assert "Referenced route does not exist in this school" in str(exc_info.value)


# =============================================================================
# 5. STUDENT TRANSPORT ALLOCATION TESTS
# =============================================================================
def test_allocation_valid_two_way(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    ay_a = transport_fixture["ay_a"]
    student_a = transport_fixture["student_a"]

    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-ALLOC-1",
        route_name="Allocation Route",
    )
    stop1 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Pickup Landmark",
        stop_code="STP-PK",
        sequence_order=1,
    )
    stop2 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Drop Landmark",
        stop_code="STP-DP",
        sequence_order=2,
    )

    alloc = transport_service.allocate_student(
        db=db_session,
        school_id=school_a.id,
        student_id=student_a.id,
        route_id=route.id,
        academic_year_id=ay_a.id,
        allocation_type=TransportAllocationType.TWO_WAY,
        pickup_stop_id=stop1.id,
        drop_stop_id=stop2.id,
        start_date=date(2026, 6, 1),
    )
    assert alloc.id is not None
    assert alloc.status == TransportAllocationStatus.ACTIVE
    assert alloc.allocation_type == TransportAllocationType.TWO_WAY
    assert alloc.pickup_stop_id == stop1.id
    assert alloc.drop_stop_id == stop2.id


def test_allocation_valid_pickup_and_drop_only(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    ay_a = transport_fixture["ay_a"]

    # Create additional student for testing
    cls_a = db_session.scalar(select(SchoolClass).where(SchoolClass.school_id == school_a.id))
    sec_a = db_session.scalar(select(Section).where(Section.school_class_id == cls_a.id))
    parent_a = transport_fixture["student_a"].parent_id

    student2 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        admission_number=f"ADM-A2-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="103",
        first_name="Pooja",
        last_name="Nair",
        date_of_birth=date(2015, 6, 10),
        gender=Gender.FEMALE,
        blood_group=BloodGroup.B_POSITIVE,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a,
        address_line1="100 Express Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    student3 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        admission_number=f"ADM-A3-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="104",
        first_name="Kiran",
        last_name="Kumar",
        date_of_birth=date(2015, 9, 12),
        gender=Gender.MALE,
        blood_group=BloodGroup.AB_POSITIVE,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a,
        address_line1="100 Express Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add_all([student2, student3])
    db_session.flush()

    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-ONEWAY",
        route_name="One Way Route",
    )
    stop = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Single Stop",
        stop_code="STP-SGL",
        sequence_order=1,
    )

    # 1. PICKUP_ONLY
    alloc_pickup = transport_service.allocate_student(
        db=db_session,
        school_id=school_a.id,
        student_id=student2.id,
        route_id=route.id,
        academic_year_id=ay_a.id,
        allocation_type=TransportAllocationType.PICKUP_ONLY,
        pickup_stop_id=stop.id,
        drop_stop_id=None,
        start_date=date(2026, 6, 1),
    )
    assert alloc_pickup.allocation_type == TransportAllocationType.PICKUP_ONLY
    assert alloc_pickup.pickup_stop_id == stop.id
    assert alloc_pickup.drop_stop_id is None

    # 2. DROP_ONLY
    alloc_drop = transport_service.allocate_student(
        db=db_session,
        school_id=school_a.id,
        student_id=student3.id,
        route_id=route.id,
        academic_year_id=ay_a.id,
        allocation_type=TransportAllocationType.DROP_ONLY,
        pickup_stop_id=None,
        drop_stop_id=stop.id,
        start_date=date(2026, 6, 1),
    )
    assert alloc_drop.allocation_type == TransportAllocationType.DROP_ONLY
    assert alloc_drop.drop_stop_id == stop.id
    assert alloc_drop.pickup_stop_id is None


def test_allocation_invalid_type_combinations(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    ay_a = transport_fixture["ay_a"]
    student_a = transport_fixture["student_a"]

    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-INVALID",
        route_name="Invalid Combos Route",
    )
    stop1 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Stop One",
        stop_code="STP-1",
        sequence_order=1,
    )
    stop2 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Stop Two",
        stop_code="STP-2",
        sequence_order=2,
    )

    # TWO_WAY missing drop stop
    with pytest.raises(ValidationException) as exc_two_way:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_a.id,
            route_id=route.id,
            academic_year_id=ay_a.id,
            allocation_type=TransportAllocationType.TWO_WAY,
            pickup_stop_id=stop1.id,
            drop_stop_id=None,
            start_date=date(2026, 6, 1),
        )
    assert "TWO_WAY allocation requires both" in str(exc_two_way.value)

    # PICKUP_ONLY supplying drop stop
    with pytest.raises(ValidationException) as exc_pk:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_a.id,
            route_id=route.id,
            academic_year_id=ay_a.id,
            allocation_type=TransportAllocationType.PICKUP_ONLY,
            pickup_stop_id=stop1.id,
            drop_stop_id=stop2.id,  # Invalid
            start_date=date(2026, 6, 1),
        )
    assert "PICKUP_ONLY allocation must not have drop_stop_id" in str(exc_pk.value)

    # DROP_ONLY supplying pickup stop
    with pytest.raises(ValidationException) as exc_dp:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_a.id,
            route_id=route.id,
            academic_year_id=ay_a.id,
            allocation_type=TransportAllocationType.DROP_ONLY,
            pickup_stop_id=stop1.id,  # Invalid
            drop_stop_id=stop2.id,
            start_date=date(2026, 6, 1),
        )
    assert "DROP_ONLY allocation must not have pickup_stop_id" in str(exc_dp.value)


def test_allocation_cross_tenant_rejections(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    school_b = transport_fixture["school_b"]
    ay_a = transport_fixture["ay_a"]
    ay_b = transport_fixture["ay_b"]
    student_a = transport_fixture["student_a"]
    student_b = transport_fixture["student_b"]

    route_a = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-TENANT-A",
        route_name="Route Tenant A",
    )
    stop_a = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route_a.id,
        stop_name="Stop A",
        stop_code="STP-TA",
        sequence_order=1,
    )

    # Cross-tenant student (School B student in School A allocation)
    with pytest.raises(ValidationException) as exc_student:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_b.id,  # School B student
            route_id=route_a.id,
            academic_year_id=ay_a.id,
            allocation_type=TransportAllocationType.PICKUP_ONLY,
            pickup_stop_id=stop_a.id,
            start_date=date(2026, 6, 1),
        )
    assert "Student does not exist in this school" in str(exc_student.value)

    # Cross-tenant academic year (School B AY in School A allocation)
    with pytest.raises(ValidationException) as exc_ay:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_a.id,
            route_id=route_a.id,
            academic_year_id=ay_b.id,  # School B AY
            allocation_type=TransportAllocationType.PICKUP_ONLY,
            pickup_stop_id=stop_a.id,
            start_date=date(2026, 6, 1),
        )
    assert "Academic year does not exist in this school" in str(exc_ay.value)


def test_allocation_stop_from_different_route_rejected(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    ay_a = transport_fixture["ay_a"]
    student_a = transport_fixture["student_a"]

    route_1 = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-1-STP",
        route_name="Route 1",
    )
    route_2 = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-2-STP",
        route_name="Route 2",
    )
    stop_route_2 = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route_2.id,
        stop_name="Stop On Route 2",
        stop_code="STP-R2",
        sequence_order=1,
    )

    # Allocating to Route 1 with a stop belonging to Route 2 fails
    with pytest.raises(ValidationException) as exc_info:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_a.id,
            route_id=route_1.id,  # Route 1
            academic_year_id=ay_a.id,
            allocation_type=TransportAllocationType.PICKUP_ONLY,
            pickup_stop_id=stop_route_2.id,  # Stop belongs to Route 2
            start_date=date(2026, 6, 1),
        )
    assert "Pickup stop does not belong to the selected route" in str(exc_info.value)


def test_allocation_duplicate_active_rejection(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    ay_a = transport_fixture["ay_a"]
    student_a = transport_fixture["student_a"]

    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-DUP",
        route_name="Duplicate Test Route",
    )
    stop = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Stop One",
        stop_code="STP-DUP",
        sequence_order=1,
    )

    # First allocation succeeds
    transport_service.allocate_student(
        db=db_session,
        school_id=school_a.id,
        student_id=student_a.id,
        route_id=route.id,
        academic_year_id=ay_a.id,
        allocation_type=TransportAllocationType.PICKUP_ONLY,
        pickup_stop_id=stop.id,
        start_date=date(2026, 6, 1),
    )

    # Second active allocation for same student & academic year fails
    with pytest.raises(AlreadyExistsException) as exc_info:
        transport_service.allocate_student(
            db=db_session,
            school_id=school_a.id,
            student_id=student_a.id,
            route_id=route.id,
            academic_year_id=ay_a.id,
            allocation_type=TransportAllocationType.PICKUP_ONLY,
            pickup_stop_id=stop.id,
            start_date=date(2026, 7, 1),
        )
    assert "already has an active transport allocation" in str(exc_info.value)


# =============================================================================
# 6. CAPACITY DERIVATION TESTS
# =============================================================================
def test_vehicle_occupancy_derivation(db_session, transport_fixture):
    school_a = transport_fixture["school_a"]
    ay_a = transport_fixture["ay_a"]

    # Vehicle with capacity 30
    vehicle = transport_service.create_vehicle(
        db=db_session,
        school_id=school_a.id,
        registration_number="TS09CAP01",
        vehicle_code="BUS-CAP-30",
        seating_capacity=30,
    )

    # Route assigned to vehicle
    route = transport_service.create_route(
        db=db_session,
        school_id=school_a.id,
        route_code="RT-CAP-1",
        route_name="Capacity Route 1",
        vehicle_id=vehicle.id,
    )
    stop = transport_service.create_stop(
        db=db_session,
        school_id=school_a.id,
        route_id=route.id,
        stop_name="Central Stop",
        stop_code="STP-CEN",
        sequence_order=1,
    )

    # Initially 0 allocations
    stats_empty = transport_service.get_vehicle_occupancy_stats(
        db=db_session,
        school_id=school_a.id,
        vehicle_id=vehicle.id,
        academic_year_id=ay_a.id,
    )
    assert stats_empty["seating_capacity"] == 30
    assert stats_empty["total_allocated"] == 0
    assert stats_empty["available_seats"] == 30
    assert stats_empty["is_overbooked"] is False

    # Allocate student A
    student_a = transport_fixture["student_a"]
    transport_service.allocate_student(
        db=db_session,
        school_id=school_a.id,
        student_id=student_a.id,
        route_id=route.id,
        academic_year_id=ay_a.id,
        allocation_type=TransportAllocationType.PICKUP_ONLY,
        pickup_stop_id=stop.id,
        start_date=date(2026, 6, 1),
    )

    stats_1 = transport_service.get_vehicle_occupancy_stats(
        db=db_session,
        school_id=school_a.id,
        vehicle_id=vehicle.id,
        academic_year_id=ay_a.id,
    )
    assert stats_1["total_allocated"] == 1
    assert stats_1["available_seats"] == 29
    assert stats_1["is_overbooked"] is False


def test_transport_models_schema_introspection():
    """
    Verifies that all 5 models have proper tables and primary keys registered in SQLAlchemy metadata.
    """
    tables = CommonModel.metadata.tables
    expected_tables = [
        "transport_vehicles",
        "transport_drivers",
        "transport_routes",
        "transport_route_stops",
        "student_transport_allocations",
    ]
    for table_name in expected_tables:
        assert table_name in tables, f"Table {table_name} missing from metadata"
        table = tables[table_name]
        assert "id" in table.columns
        assert "school_id" in table.columns
        assert "is_deleted" in table.columns
        assert "created_at" in table.columns
        assert "updated_at" in table.columns
