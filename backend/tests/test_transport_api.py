from datetime import date, time
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.common.enums import (
    AcademicYearStatus,
    BloodGroup,
    Gender,
    StudentStatus,
    TeacherStatus,
)
from app.common.enums.transport import (
    FuelType,
    TransportAllocationStatus,
    TransportAllocationType,
    VehicleStatus,
    VehicleType,
)
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.academic_year.academic_year import AcademicYear
from app.models.audit_log import AuditLog
from app.models.parent.parent import Parent
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


@pytest.fixture(autouse=True)
def setup_transport_api_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def transport_api_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Transport Academy A",
        code=f"TRA-{uuid.uuid4().hex[:4]}",
        address_line1="100 Transport Ave",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B (for tenant isolation tests)
    school_b = School(
        id=uuid.uuid4(),
        name="Transport Academy B",
        code=f"TRB-{uuid.uuid4().hex[:4]}",
        address_line1="200 Fleet Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    # Academic Year for School A and B
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

    # Parents
    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Father A",
        primary_phone=f"98765{uuid.uuid4().hex[:5]}",
        email=f"parent_a.{uuid.uuid4().hex[:4]}@gmail.com",
        address_line1="100 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Father B",
        primary_phone=f"98766{uuid.uuid4().hex[:5]}",
        email=f"parent_b.{uuid.uuid4().hex[:4]}@gmail.com",
        address_line1="200 Fleet St",
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

    # Students
    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        admission_number=f"ADM-A-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="1",
        first_name="Rohan",
        last_name="Sharma",
        date_of_birth=date(2015, 5, 10),
        gender=Gender.MALE,
        address_line1="100 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    student_a2 = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        admission_number=f"ADM-A2-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="2",
        first_name="Pooja",
        last_name="Sharma",
        date_of_birth=date(2016, 3, 15),
        gender=Gender.FEMALE,
        address_line1="100 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    student_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        academic_year_id=ay_b.id,
        school_class_id=cls_b.id,
        section_id=sec_b.id,
        parent_id=parent_b.id,
        admission_number=f"ADM-B-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="1",
        first_name="Anil",
        last_name="Verma",
        date_of_birth=date(2015, 8, 20),
        gender=Gender.MALE,
        address_line1="200 Fleet St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add_all([student_a, student_a2, student_b])
    db_session.flush()

    # Staff Teacher for driver link
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id=f"EMP-A-{uuid.uuid4().hex[:4]}",
        first_name="Sunil",
        last_name="Kumar",
        phone=f"98111{uuid.uuid4().hex[:5]}",
        email=f"sunil.{uuid.uuid4().hex[:4]}@school.com",
        date_of_birth=date(1985, 1, 10),
        gender=Gender.MALE,
        joining_date=date(2022, 1, 1),
        qualification="B.Ed",
        address_line1="100 Transport Ave",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        employee_id=f"EMP-B-{uuid.uuid4().hex[:4]}",
        first_name="Manoj",
        last_name="Singh",
        phone=f"98222{uuid.uuid4().hex[:5]}",
        email=f"manoj.{uuid.uuid4().hex[:4]}@school.com",
        date_of_birth=date(1986, 2, 15),
        gender=Gender.MALE,
        joining_date=date(2022, 1, 1),
        qualification="B.Ed",
        address_line1="200 Fleet Rd",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([teacher_a, teacher_b])
    db_session.flush()

    # Permissions
    def get_or_create_perm(name, action, module="transport"):
        p = db_session.query(IdentityPermission).filter_by(name=name).first()
        if not p:
            p = IdentityPermission(id=uuid.uuid4(), name=name, action=action, module=module, description=f"{action} {module}")
            db_session.add(p)
            db_session.flush()
        return p

    perm_view = get_or_create_perm("transport.view", "view")
    perm_create = get_or_create_perm("transport.create", "create")
    perm_update = get_or_create_perm("transport.update", "update")
    perm_delete = get_or_create_perm("transport.delete", "delete")
    perm_allocate = get_or_create_perm("transport.allocate", "allocate")
    perm_manage = get_or_create_perm("transport.manage", "manage")

    # Roles
    role_admin = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name=f"School Admin {uuid.uuid4().hex[:4]}")
    role_admin.permissions = [perm_view, perm_create, perm_update, perm_delete, perm_allocate, perm_manage]

    role_viewer = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name=f"TransportViewer {uuid.uuid4().hex[:4]}")
    role_viewer.permissions = [perm_view]

    role_unauthorized = IdentityRole(id=uuid.uuid4(), school_id=school_a.id, name=f"UnauthorizedRole {uuid.uuid4().hex[:4]}")
    role_unauthorized.permissions = []

    role_admin_b = IdentityRole(id=uuid.uuid4(), school_id=school_b.id, name=f"School Admin B {uuid.uuid4().hex[:4]}")
    role_admin_b.permissions = [perm_view, perm_create, perm_update, perm_delete, perm_allocate, perm_manage]

    db_session.add_all([role_admin, role_viewer, role_unauthorized, role_admin_b])
    db_session.flush()

    # Users
    user_admin_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"admin_a.{uuid.uuid4().hex[:4]}@transport.com",
        first_name="AdminA",
        password_hash="hash",
        is_active=True,
    )
    user_admin_a.roles = [role_admin]

    user_viewer_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"viewer_a.{uuid.uuid4().hex[:4]}@transport.com",
        first_name="ViewerA",
        password_hash="hash",
        is_active=True,
    )
    user_viewer_a.roles = [role_viewer]

    user_unauthorized_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"unauth_a.{uuid.uuid4().hex[:4]}@transport.com",
        first_name="UnauthA",
        password_hash="hash",
        is_active=True,
    )
    user_unauthorized_a.roles = [role_unauthorized]

    user_admin_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"admin_b.{uuid.uuid4().hex[:4]}@transport.com",
        first_name="AdminB",
        password_hash="hash",
        is_active=True,
    )
    user_admin_b.roles = [role_admin_b]

    db_session.add_all([user_admin_a, user_viewer_a, user_unauthorized_a, user_admin_b])
    db_session.flush()

    return {
        "school_a": school_a,
        "school_b": school_b,
        "ay_a": ay_a,
        "ay_b": ay_b,
        "student_a": student_a,
        "student_a2": student_a2,
        "student_b": student_b,
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "user_admin_a": user_admin_a,
        "user_viewer_a": user_viewer_a,
        "user_unauthorized_a": user_unauthorized_a,
        "user_admin_b": user_admin_b,
    }


# =============================================================================
# 1. AUTHENTICATION & RBAC TESTS
# =============================================================================

def test_unauthenticated_request_rejected():
    client = TestClient(fastapi_app)
    response = client.get("/api/v1/transport/vehicles")
    assert response.status_code == 401


def test_rbac_view_permission_required(transport_api_fixture):
    client = TestClient(fastapi_app)
    user_unauth = transport_api_fixture["user_unauthorized_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_unauth

    res = client.get("/api/v1/transport/vehicles")
    assert res.status_code == 403


def test_rbac_create_permission_required(transport_api_fixture):
    client = TestClient(fastapi_app)
    user_viewer = transport_api_fixture["user_viewer_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_viewer

    payload = {
        "registration_number": "TS09AB1001",
        "vehicle_code": "BUS-01",
        "seating_capacity": 40,
        "vehicle_type": "BUS",
        "fuel_type": "DIESEL",
    }
    res = client.post("/api/v1/transport/vehicles", json=payload)
    assert res.status_code == 403


def test_rbac_allocate_permission_required(transport_api_fixture):
    client = TestClient(fastapi_app)
    user_viewer = transport_api_fixture["user_viewer_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_viewer

    payload = {
        "student_id": str(transport_api_fixture["student_a"].id),
        "route_id": str(uuid.uuid4()),
        "academic_year_id": str(transport_api_fixture["ay_a"].id),
        "allocation_type": "TWO_WAY",
        "start_date": "2026-06-01",
    }
    res = client.post("/api/v1/transport/allocations", json=payload)
    assert res.status_code == 403


# =============================================================================
# 2. VEHICLE CRUD & OCCUPANCY TESTS
# =============================================================================

def test_vehicle_crud_and_validation(transport_api_fixture, db_session):
    client = TestClient(fastapi_app)
    user_admin = transport_api_fixture["user_admin_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_admin

    # 1. Create vehicle
    create_payload = {
        "registration_number": "TS09AB1001",
        "vehicle_code": "BUS-01",
        "seating_capacity": 30,
        "vehicle_type": "BUS",
        "fuel_type": "DIESEL",
        "status": "ACTIVE",
        "description": "Primary AC campus bus",
    }
    res = client.post("/api/v1/transport/vehicles", json=create_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["registration_number"] == "TS09AB1001"
    assert data["vehicle_code"] == "BUS-01"
    assert data["seating_capacity"] == 30
    vehicle_id = data["id"]

    # 2. Duplicate registration rejected
    dup_res = client.post("/api/v1/transport/vehicles", json={
        "registration_number": "ts09ab1001",
        "vehicle_code": "BUS-02",
        "seating_capacity": 20,
    })
    assert dup_res.status_code == 409

    # 3. Duplicate vehicle code rejected
    dup_code_res = client.post("/api/v1/transport/vehicles", json={
        "registration_number": "TS09AB1002",
        "vehicle_code": "bus-01",
        "seating_capacity": 20,
    })
    assert dup_code_res.status_code == 409

    # 4. Invalid seating capacity <= 0 rejected
    inv_cap_res = client.post("/api/v1/transport/vehicles", json={
        "registration_number": "TS09AB9999",
        "vehicle_code": "BUS-99",
        "seating_capacity": 0,
    })
    assert inv_cap_res.status_code == 422

    # 5. List vehicles
    list_res = client.get("/api/v1/transport/vehicles?search=BUS")
    assert list_res.status_code == 200
    list_data = list_res.json()
    assert list_data["total"] >= 1
    assert any(v["id"] == vehicle_id for v in list_data["items"])

    # 6. Get vehicle detail
    get_res = client.get(f"/api/v1/transport/vehicles/{vehicle_id}")
    assert get_res.status_code == 200
    assert get_res.json()["vehicle_code"] == "BUS-01"

    # 7. Update vehicle
    update_res = client.patch(f"/api/v1/transport/vehicles/{vehicle_id}", json={
        "seating_capacity": 35,
        "description": "Updated AC campus bus",
    })
    assert update_res.status_code == 200
    assert update_res.json()["seating_capacity"] == 35
    assert update_res.json()["description"] == "Updated AC campus bus"

    # 8. Get occupancy stats
    occ_res = client.get(f"/api/v1/transport/vehicles/{vehicle_id}/occupancy")
    assert occ_res.status_code == 200
    occ_data = occ_res.json()
    assert occ_data["seating_capacity"] == 35
    assert occ_data["total_allocated"] == 0
    assert occ_data["available_seats"] == 35
    assert occ_data["is_overbooked"] is False

    # 9. Delete vehicle
    del_res = client.delete(f"/api/v1/transport/vehicles/{vehicle_id}")
    assert del_res.status_code == 200
    assert del_res.json()["success"] is True

    # 10. Verify deleted vehicle returns 404
    get_del_res = client.get(f"/api/v1/transport/vehicles/{vehicle_id}")
    assert get_del_res.status_code == 404


# =============================================================================
# 3. DRIVER CRUD & VALIDATION TESTS
# =============================================================================

def test_driver_crud_and_validation(transport_api_fixture):
    client = TestClient(fastapi_app)
    user_admin = transport_api_fixture["user_admin_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_admin

    # 1. Create driver
    create_payload = {
        "name": "Ramesh Yadav",
        "license_number": "DL-TS-2020-001234",
        "contact_number": "9876543210",
        "staff_id": str(transport_api_fixture["teacher_a"].id),
        "is_active": True,
        "remarks": "Senior lead driver",
    }
    res = client.post("/api/v1/transport/drivers", json=create_payload)
    assert res.status_code == 201
    driver_data = res.json()
    assert driver_data["name"] == "Ramesh Yadav"
    assert driver_data["license_number"] == "DL-TS-2020-001234"
    driver_id = driver_data["id"]

    # 2. Duplicate license rejected
    dup_res = client.post("/api/v1/transport/drivers", json={
        "name": "Another Driver",
        "license_number": "dl-ts-2020-001234",
        "contact_number": "9876543211",
    })
    assert dup_res.status_code == 409

    # 3. Cross-school staff link rejected
    cross_staff_res = client.post("/api/v1/transport/drivers", json={
        "name": "Cross Driver",
        "license_number": "DL-TS-9999-009999",
        "contact_number": "9876543212",
        "staff_id": str(transport_api_fixture["teacher_b"].id),  # School B teacher
    })
    assert cross_staff_res.status_code == 422

    # 4. List drivers
    list_res = client.get("/api/v1/transport/drivers?is_active=true")
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 5. Get detail & update
    get_res = client.get(f"/api/v1/transport/drivers/{driver_id}")
    assert get_res.status_code == 200

    update_res = client.put(f"/api/v1/transport/drivers/{driver_id}", json={
        "name": "Ramesh Kumar Yadav",
        "contact_number": "9876543999",
    })
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Ramesh Kumar Yadav"

    # 6. Delete driver
    del_res = client.delete(f"/api/v1/transport/drivers/{driver_id}")
    assert del_res.status_code == 200
    assert client.get(f"/api/v1/transport/drivers/{driver_id}").status_code == 404


# =============================================================================
# 4. ROUTE & STOPS CRUD TESTS
# =============================================================================

def test_route_and_stops_lifecycle(transport_api_fixture, db_session):
    client = TestClient(fastapi_app)
    user_admin = transport_api_fixture["user_admin_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_admin

    # Setup vehicle and driver for route
    vehicle_res = client.post("/api/v1/transport/vehicles", json={
        "registration_number": "TS09RT1001",
        "vehicle_code": "BUS-RT1",
        "seating_capacity": 25,
    })
    vehicle_id = vehicle_res.json()["id"]

    driver_res = client.post("/api/v1/transport/drivers", json={
        "name": "Route Driver",
        "license_number": "DL-RT-1111",
        "contact_number": "9812345678",
    })
    driver_id = driver_res.json()["id"]

    # 1. Create Route
    route_payload = {
        "route_code": "R-101",
        "route_name": "Kondapur to School Campus",
        "description": "Morning and evening daily route",
        "vehicle_id": vehicle_id,
        "driver_id": driver_id,
        "morning_start_time": "07:30:00",
        "evening_start_time": "15:45:00",
        "is_active": True,
    }
    route_res = client.post("/api/v1/transport/routes", json=route_payload)
    assert route_res.status_code == 201
    route_id = route_res.json()["id"]

    # 2. Duplicate route code rejected
    dup_route = client.post("/api/v1/transport/routes", json={
        "route_code": "r-101",
        "route_name": "Duplicate Route",
    })
    assert dup_route.status_code == 409

    # 3. Create Stops
    stop1_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Kondapur Junction",
        "stop_code": "ST-01",
        "sequence_order": 1,
        "morning_pickup_time": "07:45:00",
        "afternoon_drop_time": "16:00:00",
        "landmark": "Near Metro Pillar 42",
        "pickup_fee_amount": "1200.50",
    })
    assert stop1_res.status_code == 201
    stop1_id = stop1_res.json()["id"]
    assert Decimal(str(stop1_res.json()["pickup_fee_amount"])) == Decimal("1200.50")

    stop2_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Gachibowli Stadium",
        "stop_code": "ST-02",
        "sequence_order": 2,
        "morning_pickup_time": "08:00:00",
        "afternoon_drop_time": "15:45:00",
        "pickup_fee_amount": "1500.00",
    })
    assert stop2_res.status_code == 201
    stop2_id = stop2_res.json()["id"]

    # 4. Duplicate stop sequence on same route rejected
    dup_seq_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Duplicate Stop",
        "stop_code": "ST-03",
        "sequence_order": 1,
        "pickup_fee_amount": "500.00",
    })
    assert dup_seq_res.status_code == 409

    # 5. Invalid stop sequence <= 0 or negative fee rejected
    inv_seq_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Zero Stop",
        "stop_code": "ST-04",
        "sequence_order": 0,
        "pickup_fee_amount": "500.00",
    })
    assert inv_seq_res.status_code == 422

    neg_fee_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Negative Fee Stop",
        "stop_code": "ST-05",
        "sequence_order": 3,
        "pickup_fee_amount": "-10.00",
    })
    assert neg_fee_res.status_code == 422

    # 6. List Stops
    stops_res = client.get(f"/api/v1/transport/routes/{route_id}/stops")
    assert stops_res.status_code == 200
    stops_data = stops_res.json()
    assert stops_data["total"] == 2
    assert stops_data["items"][0]["sequence_order"] == 1
    assert stops_data["items"][1]["sequence_order"] == 2

    # 7. Route Detail with nested stops
    detail_res = client.get(f"/api/v1/transport/routes/{route_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["route_code"] == "R-101"
    assert len(detail_data["stops"]) == 2
    assert detail_data["vehicle"]["id"] == vehicle_id
    assert detail_data["driver"]["id"] == driver_id

    # 8. Update Stop
    up_stop_res = client.patch(f"/api/v1/transport/routes/{route_id}/stops/{stop1_id}", json={
        "stop_name": "Kondapur RTA Junction",
        "pickup_fee_amount": "1250.00",
    })
    assert up_stop_res.status_code == 200
    assert up_stop_res.json()["stop_name"] == "Kondapur RTA Junction"

    # 9. Delete Stop 2
    del_stop_res = client.delete(f"/api/v1/transport/routes/{route_id}/stops/{stop2_id}")
    assert del_stop_res.status_code == 200
    assert client.get(f"/api/v1/transport/routes/{route_id}/stops/{stop2_id}").status_code == 404

    # 10. Delete Route
    del_route_res = client.delete(f"/api/v1/transport/routes/{route_id}")
    assert del_route_res.status_code == 200
    assert client.get(f"/api/v1/transport/routes/{route_id}").status_code == 404


# =============================================================================
# 5. ALLOCATION LIFECYCLE & CAPACITY ENFORCEMENT TESTS
# =============================================================================

def test_allocation_lifecycle_and_capacity_enforcement(transport_api_fixture, db_session):
    client = TestClient(fastapi_app)
    user_admin = transport_api_fixture["user_admin_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_admin

    # Setup small capacity vehicle (capacity = 1)
    veh_res = client.post("/api/v1/transport/vehicles", json={
        "registration_number": "TS09MINI1",
        "vehicle_code": "MINI-01",
        "seating_capacity": 1,
    })
    veh_id = veh_res.json()["id"]

    # Setup Route
    route_res = client.post("/api/v1/transport/routes", json={
        "route_code": "R-MINI",
        "route_name": "Mini Bus Route",
        "vehicle_id": veh_id,
    })
    route_id = route_res.json()["id"]

    # Setup 2 stops
    s1_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Pickup A",
        "stop_code": "PA",
        "sequence_order": 1,
        "pickup_fee_amount": "500.00",
    })
    pickup_id = s1_res.json()["id"]

    s2_res = client.post(f"/api/v1/transport/routes/{route_id}/stops", json={
        "stop_name": "Drop B",
        "stop_code": "DB",
        "sequence_order": 2,
        "pickup_fee_amount": "500.00",
    })
    drop_id = s2_res.json()["id"]

    student1 = transport_api_fixture["student_a"]
    student2 = transport_api_fixture["student_a2"]
    ay_id = str(transport_api_fixture["ay_a"].id)

    # 1. Allocation Type Invariants: TWO_WAY missing drop_stop_id rejected
    inv_tw_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(student1.id),
        "route_id": route_id,
        "academic_year_id": ay_id,
        "allocation_type": "TWO_WAY",
        "pickup_stop_id": pickup_id,
        "start_date": "2026-06-01",
    })
    assert inv_tw_res.status_code == 422

    # 2. PICKUP_ONLY specifying drop_stop_id rejected
    inv_po_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(student1.id),
        "route_id": route_id,
        "academic_year_id": ay_id,
        "allocation_type": "PICKUP_ONLY",
        "pickup_stop_id": pickup_id,
        "drop_stop_id": drop_id,
        "start_date": "2026-06-01",
    })
    assert inv_po_res.status_code == 422

    # 3. Successful Allocation for Student 1 (fills capacity 1/1)
    alloc1_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(student1.id),
        "route_id": route_id,
        "academic_year_id": ay_id,
        "allocation_type": "TWO_WAY",
        "pickup_stop_id": pickup_id,
        "drop_stop_id": drop_id,
        "start_date": "2026-06-01",
        "status": "ACTIVE",
    })
    assert alloc1_res.status_code == 201
    alloc1_data = alloc1_res.json()
    alloc1_id = alloc1_data["id"]
    assert alloc1_data["student_name"] == "Rohan Sharma"
    assert alloc1_data["route_code"] == "R-MINI"

    # 4. Duplicate Active Allocation for same Student in same AY rejected
    dup_student_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(student1.id),
        "route_id": route_id,
        "academic_year_id": ay_id,
        "allocation_type": "TWO_WAY",
        "pickup_stop_id": pickup_id,
        "drop_stop_id": drop_id,
        "start_date": "2026-06-01",
        "status": "ACTIVE",
    })
    assert dup_student_res.status_code == 409

    # 5. Capacity Limit Enforcement: Student 2 allocation rejected because capacity is 1
    cap_exceeded_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(student2.id),
        "route_id": route_id,
        "academic_year_id": ay_id,
        "allocation_type": "TWO_WAY",
        "pickup_stop_id": pickup_id,
        "drop_stop_id": drop_id,
        "start_date": "2026-06-01",
        "status": "ACTIVE",
    })
    assert cap_exceeded_res.status_code == 422
    err_body = cap_exceeded_res.json()
    err_text = ""
    if isinstance(err_body.get("error"), dict):
        err_text = err_body["error"].get("message", "")
    elif err_body.get("detail"):
        err_text = str(err_body.get("detail"))
    elif err_body.get("message"):
        err_text = str(err_body.get("message"))
    else:
        err_text = str(err_body)
    assert "capacity" in err_text.lower()

    # 6. Delete Route or Stop with active allocation rejected
    del_route_fail = client.delete(f"/api/v1/transport/routes/{route_id}")
    assert del_route_fail.status_code == 400

    del_stop_fail = client.delete(f"/api/v1/transport/routes/{route_id}/stops/{pickup_id}")
    assert del_stop_fail.status_code == 400

    # 7. Transition Allocation Status (ACTIVE -> SUSPENDED -> CANCELLED)
    suspend_res = client.patch(f"/api/v1/transport/allocations/{alloc1_id}/status", json={
        "status": "SUSPENDED",
        "remarks": "Temporarily on leave",
    })
    assert suspend_res.status_code == 200
    assert suspend_res.json()["status"] == "SUSPENDED"

    # Now that student1 is SUSPENDED, Student 2 can be allocated (capacity freed)
    alloc2_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(student2.id),
        "route_id": route_id,
        "academic_year_id": ay_id,
        "allocation_type": "TWO_WAY",
        "pickup_stop_id": pickup_id,
        "drop_stop_id": drop_id,
        "start_date": "2026-06-01",
        "status": "ACTIVE",
    })
    assert alloc2_res.status_code == 201

    # Reactivating student 1 while student 2 is active now hits capacity limit
    reactivate_fail = client.patch(f"/api/v1/transport/allocations/{alloc1_id}/status", json={
        "status": "ACTIVE",
    })
    assert reactivate_fail.status_code == 422

    # 8. Delete Allocation
    del_alloc_res = client.delete(f"/api/v1/transport/allocations/{alloc1_id}")
    assert del_alloc_res.status_code == 200
    assert client.get(f"/api/v1/transport/allocations/{alloc1_id}").status_code == 404


# =============================================================================
# 6. TENANT ISOLATION TESTS
# =============================================================================

def test_strict_tenant_isolation(transport_api_fixture):
    client = TestClient(fastapi_app)
    user_a = transport_api_fixture["user_admin_a"]
    user_b = transport_api_fixture["user_admin_b"]

    # 1. School B creates a vehicle, driver, route, and stop
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_b

    veh_b_res = client.post("/api/v1/transport/vehicles", json={
        "registration_number": "TS09SCHB01",
        "vehicle_code": "BUS-SCHB",
        "seating_capacity": 40,
    })
    assert veh_b_res.status_code == 201
    veh_b_id = veh_b_res.json()["id"]

    drv_b_res = client.post("/api/v1/transport/drivers", json={
        "name": "Driver B",
        "license_number": "DL-SCHB-001",
        "contact_number": "9876500002",
    })
    assert drv_b_res.status_code == 201
    drv_b_id = drv_b_res.json()["id"]

    rt_b_res = client.post("/api/v1/transport/routes", json={
        "route_code": "R-SCHB",
        "route_name": "School B Route",
        "vehicle_id": veh_b_id,
        "driver_id": drv_b_id,
    })
    assert rt_b_res.status_code == 201
    rt_b_id = rt_b_res.json()["id"]

    stp_b_res = client.post(f"/api/v1/transport/routes/{rt_b_id}/stops", json={
        "stop_name": "School B Stop",
        "stop_code": "ST-SCHB",
        "sequence_order": 1,
        "pickup_fee_amount": "500.00",
    })
    assert stp_b_res.status_code == 201
    stp_b_id = stp_b_res.json()["id"]

    # 2. Switch to User School A: must NOT be able to view, update, or delete School B resources
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_a

    # Vehicle isolation
    assert client.get(f"/api/v1/transport/vehicles/{veh_b_id}").status_code == 404
    assert client.put(f"/api/v1/transport/vehicles/{veh_b_id}", json={"seating_capacity": 50}).status_code == 404
    assert client.delete(f"/api/v1/transport/vehicles/{veh_b_id}").status_code == 404

    # Driver isolation
    assert client.get(f"/api/v1/transport/drivers/{drv_b_id}").status_code == 404
    assert client.put(f"/api/v1/transport/drivers/{drv_b_id}", json={"name": "Hacked"}).status_code == 404
    assert client.delete(f"/api/v1/transport/drivers/{drv_b_id}").status_code == 404

    # Route isolation
    assert client.get(f"/api/v1/transport/routes/{rt_b_id}").status_code == 404
    assert client.put(f"/api/v1/transport/routes/{rt_b_id}", json={"route_name": "Hacked"}).status_code == 404
    assert client.delete(f"/api/v1/transport/routes/{rt_b_id}").status_code == 404

    # Stop isolation
    assert client.get(f"/api/v1/transport/routes/{rt_b_id}/stops/{stp_b_id}").status_code == 404
    assert client.put(f"/api/v1/transport/routes/{rt_b_id}/stops/{stp_b_id}", json={"stop_name": "Hacked"}).status_code == 404
    assert client.delete(f"/api/v1/transport/routes/{rt_b_id}/stops/{stp_b_id}").status_code == 404

    # Cross-tenant allocation creation rejected (School A user trying to allocate School B student / route)
    cross_alloc_res = client.post("/api/v1/transport/allocations", json={
        "student_id": str(transport_api_fixture["student_b"].id),  # School B student
        "route_id": rt_b_id,
        "academic_year_id": str(transport_api_fixture["ay_a"].id),
        "allocation_type": "PICKUP_ONLY",
        "pickup_stop_id": stp_b_id,
        "start_date": "2026-06-01",
    })
    assert cross_alloc_res.status_code == 422


# =============================================================================
# 7. DASHBOARD OVERVIEW STATS TESTS
# =============================================================================

def test_dashboard_overview_stats(transport_api_fixture):
    client = TestClient(fastapi_app)
    user_admin = transport_api_fixture["user_admin_a"]
    fastapi_app.dependency_overrides[get_current_user] = lambda: user_admin

    res = client.get("/api/v1/transport/dashboard-stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_vehicles" in stats
    assert "active_vehicles" in stats
    assert "active_drivers" in stats
    assert "active_routes" in stats
    assert "total_allocated_students" in stats
    assert "overall_occupancy_percentage" in stats
