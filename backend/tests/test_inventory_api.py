from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.common.enums import (
    AcademicYearStatus,
    BloodGroup,
    Gender,
    SchoolClassStatus,
    SectionStatus,
    StudentStatus,
    TeacherStatus,
)
from app.common.enums.parent import ParentRelationship
from app.common.enums.inventory import (
    AssetAssignmentStatus,
    AssetAssignmentType,
    AssetCondition,
    AssetStatus,
    InventoryItemType,
    InventoryLocationType,
    InventoryStockMovementType,
)
from app.database.common_model import CommonModel
from app.dependencies.database import get_db
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.user import IdentityUser
from app.identity.security.current_user import get_current_user
from app.main import app as fastapi_app
from app.models.academic_year.academic_year import AcademicYear
from app.models.inventory import (
    AssetAssignment,
    InventoryCategory,
    InventoryItem,
    InventoryLocation,
    InventoryStock,
    InventoryStockMovement,
    InventoryVendor,
    PhysicalAsset,
)
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom


@pytest.fixture(autouse=True)
def setup_inventory_api_tables(db_session):
    CommonModel.metadata.create_all(db_session.get_bind())
    fastapi_app.dependency_overrides[get_db] = lambda: db_session
    yield
    fastapi_app.dependency_overrides.pop(get_db, None)
    fastapi_app.dependency_overrides.pop(get_current_user, None)


@pytest.fixture
def inventory_api_fixture(db_session):
    # School A
    school_a = School(
        id=uuid.uuid4(),
        name="Oakridge Inventory Academy A",
        code=f"INV-SCH-A-{uuid.uuid4().hex[:4]}",
        address_line1="100 Logistics Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    # School B (for tenant isolation)
    school_b = School(
        id=uuid.uuid4(),
        name="Oakridge Inventory Academy B",
        code=f"INV-SCH-B-{uuid.uuid4().hex[:4]}",
        address_line1="200 Logistics Way",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([school_a, school_b])
    db_session.flush()

    # Teacher in School A & B
    teacher_a = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id=f"TCH-A-{uuid.uuid4().hex[:4]}",
        first_name="Rajesh",
        last_name="Sharma",
        email=f"rajesh.{uuid.uuid4().hex[:4]}@school.com",
        phone="9876543210",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.MALE,
        joining_date=date(2020, 6, 1),
        qualification="M.Sc, B.Ed",
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    teacher_b = Teacher(
        id=uuid.uuid4(),
        school_id=school_b.id,
        employee_id=f"TCH-B-{uuid.uuid4().hex[:4]}",
        first_name="Suresh",
        last_name="Verma",
        email=f"suresh.{uuid.uuid4().hex[:4]}@school.com",
        phone="9876543211",
        date_of_birth=date(1991, 2, 2),
        gender=Gender.MALE,
        joining_date=date(2021, 6, 1),
        qualification="M.A, B.Ed",
        address_line1="456 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add_all([teacher_a, teacher_b])

    # Academic years, classes, sections, parents for Students A and B
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

    cls_a = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Grade 10 {uuid.uuid4().hex[:4]}",
        display_order=10,
        status=SchoolClassStatus.ACTIVE,
    )
    cls_b = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name=f"Grade 10 {uuid.uuid4().hex[:4]}",
        display_order=10,
        status=SchoolClassStatus.ACTIVE,
    )
    db_session.add_all([cls_a, cls_b])
    db_session.flush()

    sec_a = Section(
        id=uuid.uuid4(),
        school_class_id=cls_a.id,
        name="A",
        status=SectionStatus.ACTIVE,
    )
    sec_b = Section(
        id=uuid.uuid4(),
        school_class_id=cls_b.id,
        name="B",
        status=SectionStatus.ACTIVE,
    )
    db_session.add_all([sec_a, sec_b])
    db_session.flush()

    parent_a = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Parent One",
        email=f"parent.a.{uuid.uuid4().hex[:4]}@school.com",
        primary_phone=f"987{uuid.uuid4().hex[:7]}",
        relationship=ParentRelationship.FATHER,
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    parent_b = Parent(
        id=uuid.uuid4(),
        school_id=school_b.id,
        father_name="Parent Two",
        email=f"parent.b.{uuid.uuid4().hex[:4]}@school.com",
        primary_phone=f"987{uuid.uuid4().hex[:7]}",
        relationship=ParentRelationship.FATHER,
        address_line1="456 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add_all([parent_a, parent_b])
    db_session.flush()

    # Student in School A & B
    student_a = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        admission_number=f"ADM-A-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number=f"101-{uuid.uuid4().hex[:2]}",
        first_name="Aarav",
        last_name="Kumar",
        date_of_birth=date(2010, 5, 15),
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
        academic_year_id=ay_a.id,
        school_class_id=cls_a.id,
        section_id=sec_a.id,
        parent_id=parent_a.id,
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    student_b = Student(
        id=uuid.uuid4(),
        school_id=school_b.id,
        admission_number=f"ADM-B-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number=f"102-{uuid.uuid4().hex[:2]}",
        first_name="Vihaan",
        last_name="Reddy",
        date_of_birth=date(2010, 5, 15),
        gender=Gender.MALE,
        blood_group=BloodGroup.A_POSITIVE,
        academic_year_id=ay_b.id,
        school_class_id=cls_b.id,
        section_id=sec_b.id,
        parent_id=parent_b.id,
        address_line1="456 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add_all([student_a, student_b])

    # Classroom in School A & B
    classroom_a = Classroom(
        id=uuid.uuid4(),
        school_id=school_a.id,
        room_number="Lab-101",
        building_name="Science Block",
        capacity=40,
    )
    classroom_b = Classroom(
        id=uuid.uuid4(),
        school_id=school_b.id,
        room_number="Lab-201",
        building_name="Science Block",
        capacity=40,
    )

    db_session.add_all([classroom_a, classroom_b])
    db_session.flush()

    # RBAC Helper
    def get_or_create_perm(name, action, module="inventory"):
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

    perm_view = get_or_create_perm("inventory.view", "view")
    perm_create = get_or_create_perm("inventory.create", "create")
    perm_update = get_or_create_perm("inventory.update", "update")
    perm_delete = get_or_create_perm("inventory.delete", "delete")
    perm_issue = get_or_create_perm("inventory.issue", "issue")
    perm_transfer = get_or_create_perm("inventory.transfer", "transfer")
    perm_manage = get_or_create_perm("inventory.manage", "manage")

    # Roles
    admin_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Inventory Admin A {uuid.uuid4().hex[:4]}",
        description="Full Inventory Admin",
        permissions=[perm_view, perm_create, perm_update, perm_delete, perm_issue, perm_transfer, perm_manage],
    )
    officer_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Inventory Officer A {uuid.uuid4().hex[:4]}",
        description="Officer with issue/create/update capabilities",
        permissions=[perm_view, perm_create, perm_update, perm_issue, perm_transfer],
    )
    viewer_role_a = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Inventory Viewer A {uuid.uuid4().hex[:4]}",
        description="View only",
        permissions=[perm_view],
    )
    admin_role_b = IdentityRole(
        id=uuid.uuid4(),
        school_id=school_b.id,
        name=f"Inventory Admin B {uuid.uuid4().hex[:4]}",
        description="Full Inventory Admin B",
        permissions=[perm_view, perm_create, perm_update, perm_delete, perm_issue, perm_transfer, perm_manage],
    )
    db_session.add_all([admin_role_a, officer_role_a, viewer_role_a, admin_role_b])
    db_session.flush()

    # Users
    user_admin_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"admin.inv.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Alice",
        last_name="Admin",
        is_active=True,
        roles=[admin_role_a],
    )
    user_officer_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"officer.inv.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Olivia",
        last_name="Officer",
        is_active=True,
        roles=[officer_role_a],
    )
    user_viewer_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"viewer.inv.a.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Victor",
        last_name="Viewer",
        is_active=True,
        roles=[viewer_role_a],
    )
    user_admin_b = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_b.id,
        email=f"admin.inv.b.{uuid.uuid4().hex[:4]}@school.com",
        password_hash="fakehash",
        first_name="Bob",
        last_name="Admin",
        is_active=True,
        roles=[admin_role_b],
    )
    user_inactive_a = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"inactive.inv.a.{uuid.uuid4().hex[:4]}@school.com",
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
        "teacher_a": teacher_a,
        "teacher_b": teacher_b,
        "student_a": student_a,
        "student_b": student_b,
        "classroom_a": classroom_a,
        "classroom_b": classroom_b,
        "user_admin_a": user_admin_a,
        "user_officer_a": user_officer_a,
        "user_viewer_a": user_viewer_a,
        "user_admin_b": user_admin_b,
        "user_inactive_a": user_inactive_a,
    }


class AuthenticatedClient:
    def __init__(self, user: IdentityUser):
        self.user = user
        self.client = TestClient(fastapi_app)

    def _set_auth(self):
        fastapi_app.dependency_overrides[get_current_user] = lambda: self.user

    def get(self, *args, **kwargs):
        self._set_auth()
        return self.client.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        self._set_auth()
        return self.client.post(*args, **kwargs)

    def put(self, *args, **kwargs):
        self._set_auth()
        return self.client.put(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self._set_auth()
        return self.client.delete(*args, **kwargs)


def auth_client(user: IdentityUser) -> AuthenticatedClient:
    return AuthenticatedClient(user)



# =============================================================================
# 1. AUTHENTICATION & RBAC TESTS
# =============================================================================

def test_unauthenticated_request_rejected():
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(fastapi_app)
    response = client.get("/api/v1/inventory/categories")
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_inactive_user_rejected(inventory_api_fixture):
    from app.identity.security.jwt_manager import jwt_manager
    user_inactive = inventory_api_fixture["user_inactive_a"]
    fastapi_app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(fastapi_app)

    token = jwt_manager.create_access_token(
        user_id=user_inactive.id, school_id=user_inactive.school_id
    )
    response = client.get("/api/v1/inventory/categories", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code in (status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN)


def test_rbac_permission_boundaries(inventory_api_fixture):
    user_viewer = inventory_api_fixture["user_viewer_a"]
    user_officer = inventory_api_fixture["user_officer_a"]
    user_admin = inventory_api_fixture["user_admin_a"]

    client_viewer = auth_client(user_viewer)
    client_officer = auth_client(user_officer)
    client_admin = auth_client(user_admin)

    # Viewer can read categories
    res = client_viewer.get("/api/v1/inventory/categories")
    assert res.status_code == status.HTTP_200_OK

    # Viewer cannot create category
    res = client_viewer.post("/api/v1/inventory/categories", json={"name": "Stationery", "code": "STAT-01"})
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # Officer can create category
    res = client_officer.post("/api/v1/inventory/categories", json={"name": "Stationery", "code": "STAT-01"})
    assert res.status_code == status.HTTP_201_CREATED
    cat_id = res.json()["id"]

    # Officer does not have inventory.delete -> cannot delete category
    res = client_officer.delete(f"/api/v1/inventory/categories/{cat_id}")
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # Officer does not have inventory.manage -> cannot adjust stock
    res = client_officer.post(
        "/api/v1/inventory/stock/adjust",
        json={
            "item_id": str(uuid.uuid4()),
            "location_id": str(uuid.uuid4()),
            "adjustment_type": "ADD",
            "quantity": 5,
            "reason": "Audit count",
        },
    )
    assert res.status_code == status.HTTP_403_FORBIDDEN

    # Admin with inventory.delete can delete category
    res = client_admin.delete(f"/api/v1/inventory/categories/{cat_id}")
    assert res.status_code == status.HTTP_204_NO_CONTENT


# =============================================================================
# 2. MASTER DATA CRUD TESTS
# =============================================================================

def test_category_crud_lifecycle(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    # Create
    res = client.post(
        "/api/v1/inventory/categories",
        json={"name": "IT Equipment", "code": "IT-EQ", "description": "Laptops and accessories"},
    )
    assert res.status_code == status.HTTP_201_CREATED
    cat = res.json()
    assert cat["name"] == "IT Equipment"
    assert cat["code"] == "IT-EQ"
    cat_id = cat["id"]

    # Duplicate code rejected
    res_dup = client.post(
        "/api/v1/inventory/categories",
        json={"name": "Duplicate IT", "code": "IT-EQ"},
    )
    assert res_dup.status_code in (status.HTTP_400_BAD_REQUEST, status.HTTP_409_CONFLICT)

    # Retrieve
    res_get = client.get(f"/api/v1/inventory/categories/{cat_id}")
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["id"] == cat_id

    # List
    res_list = client.get("/api/v1/inventory/categories?search=IT")
    assert res_list.status_code == status.HTTP_200_OK
    assert res_list.json()["total"] >= 1

    # Update
    res_update = client.put(
        f"/api/v1/inventory/categories/{cat_id}",
        json={"name": "IT & AV Equipment"},
    )
    assert res_update.status_code == status.HTTP_200_OK
    assert res_update.json()["name"] == "IT & AV Equipment"

    # Delete
    res_del = client.delete(f"/api/v1/inventory/categories/{cat_id}")
    assert res_del.status_code == status.HTTP_204_NO_CONTENT

    # Verify not found after delete
    res_get_deleted = client.get(f"/api/v1/inventory/categories/{cat_id}")
    assert res_get_deleted.status_code == status.HTTP_404_NOT_FOUND


def test_location_crud_and_hierarchy(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    # Create main warehouse
    res_wh = client.post(
        "/api/v1/inventory/locations",
        json={
            "name": "Main Warehouse",
            "code": "WH-01",
            "location_type": InventoryLocationType.WAREHOUSE.value,
            "building_name": "Block A",
        },
    )
    assert res_wh.status_code == status.HTTP_201_CREATED
    wh_id = res_wh.json()["id"]

    # Create child storeroom
    res_child = client.post(
        "/api/v1/inventory/locations",
        json={
            "name": "Electronics Store",
            "code": "ST-ELEC-01",
            "location_type": InventoryLocationType.STORE_ROOM.value,
            "parent_location_id": wh_id,
            "building_name": "Block A",
        },
    )
    assert res_child.status_code == status.HTTP_201_CREATED
    child_id = res_child.json()["id"]
    assert res_child.json()["parent_location_id"] == wh_id

    # Reject self-parenting
    res_self = client.put(
        f"/api/v1/inventory/locations/{child_id}",
        json={"parent_location_id": child_id},
    )
    assert res_self.status_code == status.HTTP_400_BAD_REQUEST

    # List with parent filter
    res_list = client.get(f"/api/v1/inventory/locations?parent_location_id={wh_id}")
    assert res_list.status_code == status.HTTP_200_OK
    assert res_list.json()["total"] == 1


def test_vendor_crud_lifecycle(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    res = client.post(
        "/api/v1/inventory/vendors",
        json={
            "name": "Dell Technologies",
            "code": "VEND-DELL",
            "contact_name": "Ravi Kumar",
            "email": "ravi@dell-vendor.com",
            "phone": "+91-9876543210",
            "tax_id": "GSTIN36AAACD1234F1Z5",
        },
    )
    assert res.status_code == status.HTTP_201_CREATED
    vendor_id = res.json()["id"]

    res_get = client.get(f"/api/v1/inventory/vendors/{vendor_id}")
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["tax_id"] == "GSTIN36AAACD1234F1Z5"

    res_upd = client.put(
        f"/api/v1/inventory/vendors/{vendor_id}",
        json={"contact_name": "Anita Roy"},
    )
    assert res_upd.status_code == status.HTTP_200_OK
    assert res_upd.json()["contact_name"] == "Anita Roy"


def test_item_crud_lifecycle(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    # Create category first
    cat_res = client.post("/api/v1/inventory/categories", json={"name": "Books & Stationery", "code": "CAT-STN"})
    cat_id = cat_res.json()["id"]

    # Create consumable item
    res_item = client.post(
        "/api/v1/inventory/items",
        json={
            "category_id": cat_id,
            "item_code": "NOTE-A4-100",
            "name": "A4 Ruled Notebook (100 pgs)",
            "item_type": InventoryItemType.CONSUMABLE.value,
            "unit_of_measure": "PCS",
            "reorder_level": 50,
        },
    )
    assert res_item.status_code == status.HTTP_201_CREATED
    item = res_item.json()
    assert item["item_code"] == "NOTE-A4-100"
    assert item["reorder_level"] == 50
    item_id = item["id"]

    # Retrieve
    res_get = client.get(f"/api/v1/inventory/items/{item_id}")
    assert res_get.status_code == status.HTTP_200_OK
    assert res_get.json()["category"]["name"] == "Books & Stationery"

    # List by category
    res_list = client.get(f"/api/v1/inventory/items?category_id={cat_id}")
    assert res_list.status_code == status.HTTP_200_OK
    assert res_list.json()["total"] == 1


# =============================================================================
# 3. TENANT ISOLATION TESTS
# =============================================================================

def test_cross_tenant_read_isolation(inventory_api_fixture):
    client_a = auth_client(inventory_api_fixture["user_admin_a"])
    client_b = auth_client(inventory_api_fixture["user_admin_b"])

    # School A creates category, location, vendor, item
    cat_a = client_a.post("/api/v1/inventory/categories", json={"name": "A Cat", "code": "CAT-A"}).json()
    loc_a = client_a.post("/api/v1/inventory/locations", json={"name": "A Loc", "code": "LOC-A"}).json()
    vend_a = client_a.post("/api/v1/inventory/vendors", json={"name": "A Vend", "code": "VEND-A"}).json()
    item_a = client_a.post(
        "/api/v1/inventory/items",
        json={"category_id": cat_a["id"], "item_code": "ITEM-A", "name": "A Item", "item_type": "CONSUMABLE"},
    ).json()

    # School B should get 404 for School A objects
    assert client_b.get(f"/api/v1/inventory/categories/{cat_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client_b.get(f"/api/v1/inventory/locations/{loc_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client_b.get(f"/api/v1/inventory/vendors/{vend_a['id']}").status_code == status.HTTP_404_NOT_FOUND
    assert client_b.get(f"/api/v1/inventory/items/{item_a['id']}").status_code == status.HTTP_404_NOT_FOUND

    # School B list endpoints do not include School A data
    b_cats = client_b.get("/api/v1/inventory/categories").json()
    assert not any(c["id"] == cat_a["id"] for c in b_cats["items"])


def test_cross_tenant_mutation_and_fk_rejection(inventory_api_fixture):
    client_a = auth_client(inventory_api_fixture["user_admin_a"])
    client_b = auth_client(inventory_api_fixture["user_admin_b"])

    cat_a = client_a.post("/api/v1/inventory/categories", json={"name": "A Cat", "code": "CAT-A2"}).json()

    # School B cannot update or delete School A's category
    assert (
        client_b.put(f"/api/v1/inventory/categories/{cat_a['id']}", json={"name": "Hacked"}).status_code
        == status.HTTP_404_NOT_FOUND
    )
    assert client_b.delete(f"/api/v1/inventory/categories/{cat_a['id']}").status_code == status.HTTP_404_NOT_FOUND

    # School B cannot create an item using School A's category
    res_b_item = client_b.post(
        "/api/v1/inventory/items",
        json={"category_id": cat_a["id"], "item_code": "ITEM-B", "name": "B Item", "item_type": "CONSUMABLE"},
    )
    assert res_b_item.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST)


# =============================================================================
# 4. STOCK OPERATIONS (RECEIVE, ISSUE, RETURN, ADJUST, TRANSFER, IDEMPOTENCY)
# =============================================================================

def test_stock_receive_issue_return_adjust_transfer_lifecycle(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    cat = client.post("/api/v1/inventory/categories", json={"name": "Stationery", "code": "CAT-STN-OPS"}).json()
    loc1 = client.post("/api/v1/inventory/locations", json={"name": "Storeroom 1", "code": "LOC-SR-1"}).json()
    loc2 = client.post("/api/v1/inventory/locations", json={"name": "Storeroom 2", "code": "LOC-SR-2"}).json()
    vend = client.post("/api/v1/inventory/vendors", json={"name": "Paper Supplier", "code": "VEND-PAP"}).json()
    item = client.post(
        "/api/v1/inventory/items",
        json={
            "category_id": cat["id"],
            "item_code": "ITEM-PEN-BLUE",
            "name": "Blue Ballpoint Pen",
            "item_type": InventoryItemType.CONSUMABLE.value,
            "reorder_level": 20,
        },
    ).json()

    item_id = item["id"]
    loc1_id = loc1["id"]
    loc2_id = loc2["id"]

    # 1. RECEIVE STOCK (100 units into Loc 1)
    res_rec = client.post(
        "/api/v1/inventory/stock/receive",
        json={
            "item_id": item_id,
            "location_id": loc1_id,
            "quantity": 100,
            "unit_price": "2.50",
            "vendor_id": vend["id"],
            "reference_number": "PO-1001",
            "remarks": "Initial stock order",
        },
    )
    assert res_rec.status_code == status.HTTP_200_OK
    assert res_rec.json()["quantity"] == 100

    # Summary check
    summary = client.get("/api/v1/inventory/stock/summary").json()
    assert summary["total_stock_units"] >= 100

    # 2. ISSUE STOCK (25 units issued)
    res_issue = client.post(
        "/api/v1/inventory/stock/issue",
        json={
            "item_id": item_id,
            "location_id": loc1_id,
            "quantity": 25,
            "remarks": "Issued to Exam Dept",
        },
    )
    assert res_issue.status_code == status.HTTP_200_OK
    assert res_issue.json()["quantity"] == 75

    # Attempt to issue more than available (80 > 75)
    res_excess = client.post(
        "/api/v1/inventory/stock/issue",
        json={"item_id": item_id, "location_id": loc1_id, "quantity": 80},
    )
    assert res_excess.status_code == status.HTTP_400_BAD_REQUEST

    # 3. RETURN STOCK (5 unused pens returned)
    res_ret = client.post(
        "/api/v1/inventory/stock/return",
        json={
            "item_id": item_id,
            "location_id": loc1_id,
            "quantity": 5,
            "remarks": "Unused pens returned",
        },
    )
    assert res_ret.status_code == status.HTTP_200_OK
    assert res_ret.json()["quantity"] == 80

    # 4. ADJUST STOCK (Add 10 found in physical count)
    res_adj_add = client.post(
        "/api/v1/inventory/stock/adjust",
        json={
            "item_id": item_id,
            "location_id": loc1_id,
            "adjustment_type": "ADD",
            "quantity": 10,
            "reason": "Found extra box in shelf B",
        },
    )
    assert res_adj_add.status_code == status.HTTP_200_OK
    assert res_adj_add.json()["quantity"] == 90

    # Adjust subtract 5 damaged
    res_adj_sub = client.post(
        "/api/v1/inventory/stock/adjust",
        json={
            "item_id": item_id,
            "location_id": loc1_id,
            "adjustment_type": "SUBTRACT",
            "quantity": 5,
            "reason": "Damaged by water leak",
        },
    )
    assert res_adj_sub.status_code == status.HTTP_200_OK
    assert res_adj_sub.json()["quantity"] == 85

    # 5. TRANSFER STOCK (Transfer 30 units from Loc 1 to Loc 2)
    res_trans = client.post(
        "/api/v1/inventory/stock/transfer",
        json={
            "item_id": item_id,
            "source_location_id": loc1_id,
            "destination_location_id": loc2_id,
            "quantity": 30,
            "remarks": "Stock transfer to Branch store",
        },
    )
    assert res_trans.status_code == status.HTTP_200_OK
    assert res_trans.json()["quantity"] == 55

    # Verify destination location has 30
    stocks_item = client.get(f"/api/v1/inventory/stock/items/{item_id}").json()
    loc2_stock = next(s for s in stocks_item if s["location_id"] == loc2_id)
    assert loc2_stock["quantity"] == 30

    # Same location transfer rejection
    res_same = client.post(
        "/api/v1/inventory/stock/transfer",
        json={"item_id": item_id, "source_location_id": loc1_id, "destination_location_id": loc1_id, "quantity": 5},
    )
    assert res_same.status_code == status.HTTP_400_BAD_REQUEST

    # Check movement history
    movements = client.get(f"/api/v1/inventory/movements?item_id={item_id}").json()
    assert movements["total"] >= 5


def test_stock_operation_idempotency(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    cat = client.post("/api/v1/inventory/categories", json={"name": "Idemp Cat", "code": "CAT-IDEM"}).json()
    loc = client.post("/api/v1/inventory/locations", json={"name": "Idemp Loc", "code": "LOC-IDEM"}).json()
    item = client.post(
        "/api/v1/inventory/items",
        json={"category_id": cat["id"], "item_code": "ITEM-IDEM", "name": "Idemp Item", "item_type": "CONSUMABLE"},
    ).json()

    # First receive with reference PO-IDEM-001
    res1 = client.post(
        "/api/v1/inventory/stock/receive",
        json={
            "item_id": item["id"],
            "location_id": loc["id"],
            "quantity": 50,
            "reference_number": "PO-IDEM-001",
        },
    )
    assert res1.status_code == status.HTTP_200_OK
    assert res1.json()["quantity"] == 50

    # Retry same receipt with exact same reference
    res2 = client.post(
        "/api/v1/inventory/stock/receive",
        json={
            "item_id": item["id"],
            "location_id": loc["id"],
            "quantity": 50,
            "reference_number": "PO-IDEM-001",
        },
    )
    assert res2.status_code == status.HTTP_200_OK
    # Quantity must remain 50, not 100!
    assert res2.json()["quantity"] == 50


# =============================================================================
# 5. PHYSICAL ASSET LIFECYCLE & ASSIGNMENT TESTS
# =============================================================================

def test_physical_asset_lifecycle_and_assignment_to_teacher(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])
    teacher_a = inventory_api_fixture["teacher_a"]

    cat = client.post("/api/v1/inventory/categories", json={"name": "Laptops", "code": "CAT-LAP"}).json()
    loc = client.post("/api/v1/inventory/locations", json={"name": "IT Depot", "code": "LOC-IT"}).json()
    vend = client.post("/api/v1/inventory/vendors", json={"name": "Lenovo India", "code": "VEND-LEN"}).json()
    item = client.post(
        "/api/v1/inventory/items",
        json={
            "category_id": cat["id"],
            "item_code": "LAP-THINKPAD-T14",
            "name": "Lenovo ThinkPad T14",
            "item_type": InventoryItemType.ASSET.value,
            "track_individually": True,
        },
    ).json()

    # 1. Create Physical Asset
    res_asset = client.post(
        "/api/v1/inventory/assets",
        json={
            "item_id": item["id"],
            "location_id": loc["id"],
            "vendor_id": vend["id"],
            "asset_tag": "AST-LAP-001",
            "serial_number": "PF-29X381",
            "model_number": "T14-GEN3",
            "purchase_cost": "75000.00",
            "purchase_date": "2026-01-10",
            "condition": AssetCondition.EXCELLENT.value,
        },
    )
    assert res_asset.status_code == status.HTTP_201_CREATED
    asset = res_asset.json()
    assert asset["status"] == AssetStatus.AVAILABLE.value
    asset_id = asset["id"]

    # 2. Assign to Teacher
    res_assign = client.post(
        "/api/v1/inventory/assignments",
        json={
            "asset_id": asset_id,
            "assignment_type": AssetAssignmentType.STAFF.value,
            "teacher_id": str(teacher_a.id),
            "assigned_date": "2026-02-01",
            "expected_return_date": "2027-02-01",
            "condition_on_assignment": AssetCondition.EXCELLENT.value,
            "remarks": "Issued for senior computer science faculty",
        },
    )
    assert res_assign.status_code == status.HTTP_201_CREATED
    assignment = res_assign.json()
    assert assignment["status"] == AssetAssignmentStatus.ACTIVE.value
    assign_id = assignment["id"]

    # Verify Asset is now ASSIGNED
    asset_after_assign = client.get(f"/api/v1/inventory/assets/{asset_id}").json()
    assert asset_after_assign["status"] == AssetStatus.ASSIGNED.value

    # Attempt to assign already assigned asset -> rejected
    res_dup_assign = client.post(
        "/api/v1/inventory/assignments",
        json={
            "asset_id": asset_id,
            "assignment_type": AssetAssignmentType.STAFF.value,
            "teacher_id": str(teacher_a.id),
            "assigned_date": "2026-02-02",
        },
    )
    assert res_dup_assign.status_code == status.HTTP_400_BAD_REQUEST

    # 3. Return Asset
    res_return = client.post(
        f"/api/v1/inventory/assignments/{assign_id}/return",
        json={
            "actual_return_date": "2026-08-30",
            "condition_on_return": AssetCondition.GOOD.value,
            "return_location_id": loc["id"],
            "remarks": "Returned in good working order",
        },
    )
    assert res_return.status_code == status.HTTP_200_OK
    assert res_return.json()["status"] == AssetAssignmentStatus.RETURNED.value

    # Verify Asset is back to AVAILABLE
    asset_after_return = client.get(f"/api/v1/inventory/assets/{asset_id}").json()
    assert asset_after_return["status"] == AssetStatus.AVAILABLE.value

    # Check History
    history = client.get(f"/api/v1/inventory/assets/{asset_id}/history").json()
    assert len(history) == 1


def test_asset_assignment_transfer_and_target_validation(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])
    teacher_a = inventory_api_fixture["teacher_a"]
    student_a = inventory_api_fixture["student_a"]
    classroom_a = inventory_api_fixture["classroom_a"]
    teacher_b = inventory_api_fixture["teacher_b"]

    cat = client.post("/api/v1/inventory/categories", json={"name": "Tablets", "code": "CAT-TAB"}).json()
    loc = client.post("/api/v1/inventory/locations", json={"name": "Depot", "code": "LOC-TAB"}).json()
    item = client.post(
        "/api/v1/inventory/items",
        json={"category_id": cat["id"], "item_code": "TAB-IPAD-10", "name": "Apple iPad 10th Gen", "item_type": "ASSET"},
    ).json()

    asset = client.post(
        "/api/v1/inventory/assets",
        json={"item_id": item["id"], "location_id": loc["id"], "asset_tag": "AST-TAB-042"},
    ).json()
    asset_id = asset["id"]

    # Reject assigning School A asset to School B teacher
    res_cross_target = client.post(
        "/api/v1/inventory/assignments",
        json={
            "asset_id": asset_id,
            "assignment_type": AssetAssignmentType.STAFF.value,
            "teacher_id": str(teacher_b.id),
            "assigned_date": "2026-03-01",
        },
    )
    assert res_cross_target.status_code in (status.HTTP_404_NOT_FOUND, status.HTTP_400_BAD_REQUEST)

    # Assign to Student A
    res_assign_st = client.post(
        "/api/v1/inventory/assignments",
        json={
            "asset_id": asset_id,
            "assignment_type": AssetAssignmentType.STUDENT.value,
            "student_id": str(student_a.id),
            "assigned_date": "2026-03-01",
        },
    )
    assert res_assign_st.status_code == status.HTTP_201_CREATED
    assign_id = res_assign_st.json()["id"]

    # Transfer assignment from Student A to Classroom A
    res_trans_assign = client.post(
        f"/api/v1/inventory/assignments/{assign_id}/transfer",
        json={
            "new_assignment_type": AssetAssignmentType.CLASSROOM.value,
            "new_classroom_id": str(classroom_a.id),
            "transfer_date": "2026-04-01",
            "condition": AssetCondition.GOOD.value,
            "remarks": "Transferred to smart classroom",
        },
    )
    assert res_trans_assign.status_code == status.HTTP_200_OK
    assert res_trans_assign.json()["status"] == AssetAssignmentStatus.ACTIVE.value

    # Verify previous assignment is now TRANSFERRED
    prev_assign = client.get(f"/api/v1/inventory/assignments/{assign_id}").json()
    assert prev_assign["status"] == AssetAssignmentStatus.TRANSFERRED.value

    # Verify Asset History has both assignments
    history = client.get(f"/api/v1/inventory/assets/{asset_id}/history").json()
    assert len(history) == 2


def test_asset_retirement(inventory_api_fixture):
    client = auth_client(inventory_api_fixture["user_admin_a"])

    cat = client.post("/api/v1/inventory/categories", json={"name": "Projectors", "code": "CAT-PROJ"}).json()
    loc = client.post("/api/v1/inventory/locations", json={"name": "AV Room", "code": "LOC-AV"}).json()
    item = client.post(
        "/api/v1/inventory/items",
        json={"category_id": cat["id"], "item_code": "PROJ-EPSON", "name": "Epson EB-X06", "item_type": "ASSET"},
    ).json()

    asset = client.post(
        "/api/v1/inventory/assets",
        json={"item_id": item["id"], "location_id": loc["id"], "asset_tag": "AST-PROJ-999"},
    ).json()
    asset_id = asset["id"]

    res_retire = client.post(
        f"/api/v1/inventory/assets/{asset_id}/retire",
        json={"status": AssetStatus.RETIRED.value, "notes": "End of life - replaced by interactive display"},
    )
    assert res_retire.status_code == status.HTTP_200_OK
    assert res_retire.json()["status"] == AssetStatus.RETIRED.value
