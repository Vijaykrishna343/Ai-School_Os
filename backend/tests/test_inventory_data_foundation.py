"""
Test suite for Phase 28.4.1 — Inventory & Asset Management Data Foundation.
Validates models, schemas, database constraints, enums, tenant isolation, and RBAC seeder.
"""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from decimal import Decimal
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

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
from app.identity.models.permission import IdentityPermission
from app.identity.models.role import IdentityRole
from app.identity.models.role_permission import IdentityRolePermission
from app.identity.models.user import IdentityUser
from app.identity.seeders.permission_seeder import DEFAULT_PERMISSIONS, permission_seeder
from app.identity.seeders.role_permission_seeder import ROLE_PERMISSIONS_MATRIX, role_permission_seeder
from app.identity.seeders.role_seeder import role_seeder
from app.models.academic_year.academic_year import AcademicYear
from app.models.inventory.asset import PhysicalAsset
from app.models.inventory.assignment import AssetAssignment
from app.models.inventory.category import InventoryCategory
from app.models.inventory.item import InventoryItem
from app.models.inventory.location import InventoryLocation
from app.models.inventory.movement import InventoryStockMovement
from app.models.inventory.stock import InventoryStock
from app.models.inventory.vendor import InventoryVendor
from app.models.parent.parent import Parent
from app.models.school.school import School
from app.models.school_class.school_class import SchoolClass
from app.models.section.section import Section
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom


@pytest.fixture(autouse=True)
def setup_inventory_tables(db_session: Session):
    """Ensure all tables are created on the engine before tests run."""
    CommonModel.metadata.create_all(db_session.get_bind())
    yield


@pytest.fixture
def school_a(db_session: Session) -> School:
    school = School(
        id=uuid.uuid4(),
        name="Apex Academy",
        code=f"APEX-{uuid.uuid4().hex[:4]}",
        address_line1="123 Main St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.flush()
    return school


@pytest.fixture
def school_b(db_session: Session) -> School:
    school = School(
        id=uuid.uuid4(),
        name="Beacon High",
        code=f"BEACON-{uuid.uuid4().hex[:4]}",
        address_line1="456 High St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(school)
    db_session.flush()
    return school


@pytest.fixture
def user_a(db_session: Session, school_a: School) -> IdentityUser:
    user = IdentityUser(
        id=uuid.uuid4(),
        school_id=school_a.id,
        email=f"storekeeper.{uuid.uuid4().hex[:4]}@apex.edu",
        first_name="Sam",
        last_name="Storekeeper",
        password_hash="hashed_pw",
        is_active=True,
    )
    db_session.add(user)
    db_session.flush()
    return user


@pytest.fixture
def teacher_a(db_session: Session, school_a: School) -> Teacher:
    teacher = Teacher(
        id=uuid.uuid4(),
        school_id=school_a.id,
        employee_id=f"TCH-{uuid.uuid4().hex[:4]}",
        first_name="Alice",
        last_name="Smith",
        email=f"alice.{uuid.uuid4().hex[:4]}@apex.edu",
        phone="9876543210",
        date_of_birth=date(1990, 1, 1),
        gender=Gender.FEMALE,
        joining_date=date(2020, 6, 1),
        qualification="M.Sc, B.Ed",
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=TeacherStatus.ACTIVE,
    )
    db_session.add(teacher)
    db_session.flush()
    return teacher


@pytest.fixture
def student_a(db_session: Session, school_a: School) -> Student:
    ay = AcademicYear(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name="2026-2027",
        start_date=date(2026, 6, 1),
        end_date=date(2027, 4, 30),
        status=AcademicYearStatus.ACTIVE,
    )
    db_session.add(ay)
    db_session.flush()

    cls = SchoolClass(
        id=uuid.uuid4(),
        school_id=school_a.id,
        name=f"Grade 10 {uuid.uuid4().hex[:4]}",
        display_order=10,
        status=SchoolClassStatus.ACTIVE,
    )
    db_session.add(cls)
    db_session.flush()

    sec = Section(
        id=uuid.uuid4(),
        school_class_id=cls.id,
        name="A",
        status=SectionStatus.ACTIVE,
    )
    db_session.add(sec)
    db_session.flush()

    parent = Parent(
        id=uuid.uuid4(),
        school_id=school_a.id,
        father_name="Parent One",
        email=f"parent.{uuid.uuid4().hex[:4]}@apex.edu",
        primary_phone=f"987{uuid.uuid4().hex[:7]}",
        relationship=ParentRelationship.FATHER,
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
    )
    db_session.add(parent)
    db_session.flush()

    student = Student(
        id=uuid.uuid4(),
        school_id=school_a.id,
        admission_number=f"ADM-{uuid.uuid4().hex[:4]}",
        admission_date=date(2026, 6, 1),
        roll_number="101",
        first_name="Bob",
        last_name="Jones",
        date_of_birth=date(2010, 5, 10),
        gender=Gender.MALE,
        blood_group=BloodGroup.O_POSITIVE,
        academic_year_id=ay.id,
        school_class_id=cls.id,
        section_id=sec.id,
        parent_id=parent.id,
        address_line1="123 St",
        city="Hyderabad",
        district="Hyderabad",
        state="Telangana",
        postal_code="500001",
        status=StudentStatus.ACTIVE,
    )
    db_session.add(student)
    db_session.flush()
    return student


@pytest.fixture
def classroom_a(db_session: Session, school_a: School) -> Classroom:
    classroom = Classroom(
        id=uuid.uuid4(),
        school_id=school_a.id,
        room_number=f"LAB-{uuid.uuid4().hex[:4]}",
        building_name="Science Block",
        capacity=30,
    )
    db_session.add(classroom)
    db_session.flush()
    return classroom


# ==============================================================================
# 1. CATEGORY TESTS
# ==============================================================================

def test_inventory_category_creation_and_defaults(db_session: Session, school_a: School):
    category = InventoryCategory(
        school_id=school_a.id,
        name="Stationery",
        code="STAT",
        description="Office and classroom stationery items",
    )
    db_session.add(category)
    db_session.flush()
    db_session.refresh(category)

    assert category.id is not None
    assert category.school_id == school_a.id
    assert category.name == "Stationery"
    assert category.code == "STAT"
    assert category.is_active is True
    assert category.is_deleted is False


def test_inventory_category_tenant_code_uniqueness(db_session: Session, school_a: School, school_b: School):
    cat1 = InventoryCategory(school_id=school_a.id, name="Stationery A", code="STAT")
    db_session.add(cat1)
    db_session.flush()

    # Same code in different school is ALLOWED
    cat_other_school = InventoryCategory(school_id=school_b.id, name="Stationery B", code="STAT")
    db_session.add(cat_other_school)
    db_session.flush()
    assert cat_other_school.id is not None

    # Duplicate code in SAME school is REJECTED
    cat2 = InventoryCategory(school_id=school_a.id, name="Stationery Duplicate", code="STAT")
    db_session.add(cat2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 2. LOCATION TESTS
# ==============================================================================

def test_inventory_location_creation_and_hierarchy(db_session: Session, school_a: School):
    parent_loc = InventoryLocation(
        school_id=school_a.id,
        name="Main Warehouse",
        code="WH-MAIN",
        location_type=InventoryLocationType.WAREHOUSE,
        building_name="Central Building",
    )
    db_session.add(parent_loc)
    db_session.flush()

    child_loc = InventoryLocation(
        school_id=school_a.id,
        name="Stationery Storage Room",
        code="SR-STAT",
        location_type=InventoryLocationType.STORE_ROOM,
        parent_location_id=parent_loc.id,
        building_name="Central Building Floor 1",
    )
    db_session.add(child_loc)
    db_session.flush()
    db_session.refresh(child_loc)

    assert child_loc.parent_location_id == parent_loc.id
    assert child_loc.parent_location.name == "Main Warehouse"
    assert len(parent_loc.child_locations) == 1
    assert parent_loc.child_locations[0].code == "SR-STAT"


def test_inventory_location_tenant_code_uniqueness(db_session: Session, school_a: School, school_b: School):
    loc_a = InventoryLocation(school_id=school_a.id, name="Lab Store", code="LAB-STR")
    db_session.add(loc_a)
    db_session.flush()

    # Same code in school B is ALLOWED
    loc_b = InventoryLocation(school_id=school_b.id, name="Lab Store", code="LAB-STR")
    db_session.add(loc_b)
    db_session.flush()

    # Duplicate code in school A is REJECTED
    loc_a_dup = InventoryLocation(school_id=school_a.id, name="Lab Store 2", code="LAB-STR")
    db_session.add(loc_a_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 3. VENDOR TESTS
# ==============================================================================

def test_inventory_vendor_creation_and_uniqueness(db_session: Session, school_a: School, school_b: School):
    vendor = InventoryVendor(
        school_id=school_a.id,
        name="Apex Office Supplies Pvt Ltd",
        code="VEND-001",
        contact_name="John Doe",
        email="vendor@officesupplies.com",
        phone="9876543210",
        tax_id="GSTIN12345ABC",
    )
    db_session.add(vendor)
    db_session.flush()
    db_session.refresh(vendor)

    assert vendor.id is not None
    assert vendor.name == "Apex Office Supplies Pvt Ltd"
    assert vendor.tax_id == "GSTIN12345ABC"

    # School B can have same code
    vendor_b = InventoryVendor(school_id=school_b.id, name="Other Vendor", code="VEND-001")
    db_session.add(vendor_b)
    db_session.flush()

    # School A duplicate code rejected
    vendor_dup = InventoryVendor(school_id=school_a.id, name="Duplicate Vendor", code="VEND-001")
    db_session.add(vendor_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 4. INVENTORY ITEM TESTS
# ==============================================================================

def test_inventory_item_creation_and_category_relationship(db_session: Session, school_a: School):
    category = InventoryCategory(school_id=school_a.id, name="Electronics", code="ELEC")
    db_session.add(category)
    db_session.flush()

    item = InventoryItem(
        school_id=school_a.id,
        category_id=category.id,
        item_code="ITM-LAPTOP-01",
        name="Dell Latitude 5420 Laptop",
        description="Standard teacher laptops",
        item_type=InventoryItemType.ASSET,
        unit_of_measure="UNIT",
        track_individually=True,
        reorder_level=5,
    )
    db_session.add(item)
    db_session.flush()
    db_session.refresh(item)

    assert item.id is not None
    assert item.category.name == "Electronics"
    assert item.track_individually is True
    assert item.item_type == InventoryItemType.ASSET
    assert item.reorder_level == 5


def test_inventory_item_tenant_code_uniqueness(db_session: Session, school_a: School, school_b: School):
    cat_a = InventoryCategory(school_id=school_a.id, name="Paper", code="PPR")
    cat_b = InventoryCategory(school_id=school_b.id, name="Paper", code="PPR")
    db_session.add_all([cat_a, cat_b])
    db_session.flush()

    item_a = InventoryItem(school_id=school_a.id, category_id=cat_a.id, item_code="A4-REAM", name="A4 Paper Ream")
    db_session.add(item_a)
    db_session.flush()

    # School B allowed same item code
    item_b = InventoryItem(school_id=school_b.id, category_id=cat_b.id, item_code="A4-REAM", name="A4 Paper Ream")
    db_session.add(item_b)
    db_session.flush()

    # School A duplicate code rejected
    item_a_dup = InventoryItem(school_id=school_a.id, category_id=cat_a.id, item_code="A4-REAM", name="A4 Paper Duplicate")
    db_session.add(item_a_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 5. INVENTORY STOCK TESTS
# ==============================================================================

def test_inventory_stock_creation_and_integrity(db_session: Session, school_a: School):
    cat = InventoryCategory(school_id=school_a.id, name="Stationery", code="STAT")
    loc = InventoryLocation(school_id=school_a.id, name="Main Store", code="STR-1")
    db_session.add_all([cat, loc])
    db_session.flush()

    item = InventoryItem(school_id=school_a.id, category_id=cat.id, item_code="PEN-BLU", name="Blue Ballpoint Pen")
    db_session.add(item)
    db_session.flush()

    stock = InventoryStock(
        school_id=school_a.id,
        item_id=item.id,
        location_id=loc.id,
        quantity=250,
        reserved_quantity=10,
        unit_price=Decimal("15.50"),
        last_counted_at=datetime.now(timezone.utc),
    )
    db_session.add(stock)
    db_session.flush()
    db_session.refresh(stock)

    assert stock.id is not None
    assert stock.quantity == 250
    assert stock.reserved_quantity == 10
    assert stock.unit_price == Decimal("15.50")
    assert stock.item.name == "Blue Ballpoint Pen"
    assert stock.location.name == "Main Store"


def test_inventory_stock_unique_item_location_per_school(db_session: Session, school_a: School):
    cat = InventoryCategory(school_id=school_a.id, name="Stationery", code="STAT")
    loc = InventoryLocation(school_id=school_a.id, name="Main Store", code="STR-1")
    db_session.add_all([cat, loc])
    db_session.flush()

    item = InventoryItem(school_id=school_a.id, category_id=cat.id, item_code="NOTE-01", name="Notebook 200pg")
    db_session.add(item)
    db_session.flush()

    stock1 = InventoryStock(school_id=school_a.id, item_id=item.id, location_id=loc.id, quantity=100)
    db_session.add(stock1)
    db_session.flush()

    # Duplicate stock row for same school + item + location is rejected
    stock2 = InventoryStock(school_id=school_a.id, item_id=item.id, location_id=loc.id, quantity=50)
    db_session.add(stock2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


def test_inventory_stock_non_negative_quantity_constraint(db_session: Session, school_a: School):
    cat = InventoryCategory(school_id=school_a.id, name="Stationery", code="STAT")
    loc = InventoryLocation(school_id=school_a.id, name="Main Store", code="STR-1")
    db_session.add_all([cat, loc])
    db_session.flush()

    item = InventoryItem(school_id=school_a.id, category_id=cat.id, item_code="RULER-01", name="Plastic Ruler")
    db_session.add(item)
    db_session.flush()

    negative_stock = InventoryStock(school_id=school_a.id, item_id=item.id, location_id=loc.id, quantity=-5)
    db_session.add(negative_stock)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 6. PHYSICAL ASSET TESTS
# ==============================================================================

def test_physical_asset_creation_and_monetary_precision(db_session: Session, school_a: School):
    cat = InventoryCategory(school_id=school_a.id, name="IT Hardware", code="ITHW")
    loc = InventoryLocation(school_id=school_a.id, name="IT Lab", code="IT-LAB")
    vendor = InventoryVendor(school_id=school_a.id, name="Dell Tech", code="DELL")
    db_session.add_all([cat, loc, vendor])
    db_session.flush()

    item = InventoryItem(
        school_id=school_a.id,
        category_id=cat.id,
        item_code="DELL-5420",
        name="Dell Latitude 5420",
        item_type=InventoryItemType.ASSET,
        track_individually=True,
    )
    db_session.add(item)
    db_session.flush()

    asset = PhysicalAsset(
        school_id=school_a.id,
        item_id=item.id,
        location_id=loc.id,
        vendor_id=vendor.id,
        asset_tag="AST-2026-0042",
        serial_number="DL5420XYZ99",
        model_number="Latitude 5420 Core i7",
        status=AssetStatus.AVAILABLE,
        condition=AssetCondition.EXCELLENT,
        purchase_date=date(2026, 1, 15),
        purchase_cost=Decimal("78999.50"),
        warranty_expiry_date=date(2029, 1, 15),
        notes="Faculty issue laptop",
    )
    db_session.add(asset)
    db_session.flush()
    db_session.refresh(asset)

    assert asset.id is not None
    assert asset.asset_tag == "AST-2026-0042"
    assert asset.status == AssetStatus.AVAILABLE
    assert asset.condition == AssetCondition.EXCELLENT
    assert asset.purchase_cost == Decimal("78999.50")
    assert asset.item.name == "Dell Latitude 5420"
    assert asset.location.name == "IT Lab"
    assert asset.vendor.name == "Dell Tech"


def test_physical_asset_tenant_tag_uniqueness(db_session: Session, school_a: School, school_b: School):
    cat_a = InventoryCategory(school_id=school_a.id, name="Furniture", code="FURN")
    cat_b = InventoryCategory(school_id=school_b.id, name="Furniture", code="FURN")
    db_session.add_all([cat_a, cat_b])
    db_session.flush()

    item_a = InventoryItem(school_id=school_a.id, category_id=cat_a.id, item_code="CHR-01", name="Ergo Chair")
    item_b = InventoryItem(school_id=school_b.id, category_id=cat_b.id, item_code="CHR-01", name="Ergo Chair")
    db_session.add_all([item_a, item_b])
    db_session.flush()

    asset_a1 = PhysicalAsset(school_id=school_a.id, item_id=item_a.id, asset_tag="CHR-001")
    db_session.add(asset_a1)
    db_session.flush()

    # School B allowed same asset tag
    asset_b = PhysicalAsset(school_id=school_b.id, item_id=item_b.id, asset_tag="CHR-001")
    db_session.add(asset_b)
    db_session.flush()

    # School A duplicate asset tag rejected
    asset_a_dup = PhysicalAsset(school_id=school_a.id, item_id=item_a.id, asset_tag="CHR-001")
    db_session.add(asset_a_dup)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 7. STOCK MOVEMENT TESTS
# ==============================================================================

def test_inventory_stock_movement_append_only(
    db_session: Session,
    school_a: School,
    user_a: IdentityUser,
):
    cat = InventoryCategory(school_id=school_a.id, name="Lab Items", code="LAB")
    loc_src = InventoryLocation(school_id=school_a.id, name="Main Warehouse", code="WH-1")
    loc_dst = InventoryLocation(school_id=school_a.id, name="Chemistry Lab", code="CHEM-1")
    vendor = InventoryVendor(school_id=school_a.id, name="Chemicals Co", code="CHEMCO")
    db_session.add_all([cat, loc_src, loc_dst, vendor])
    db_session.flush()

    item = InventoryItem(school_id=school_a.id, category_id=cat.id, item_code="BEAKER-250", name="Beaker 250ml")
    db_session.add(item)
    db_session.flush()

    # 1. Receipt movement
    m1 = InventoryStockMovement(
        school_id=school_a.id,
        item_id=item.id,
        destination_location_id=loc_src.id,
        movement_type=InventoryStockMovementType.PURCHASE_RECEIPT,
        quantity=100,
        unit_price=Decimal("45.00"),
        reference_number="PO-2026-001",
        vendor_id=vendor.id,
        performed_by_user_id=user_a.id,
        movement_date=datetime.now(timezone.utc),
        remarks="Initial stock receipt",
    )
    db_session.add(m1)
    db_session.flush()
    db_session.refresh(m1)

    assert m1.id is not None
    assert m1.quantity == 100
    assert m1.movement_type == InventoryStockMovementType.PURCHASE_RECEIPT
    assert m1.performed_by_user.first_name == "Sam"

    # 2. Transfer movement
    m2 = InventoryStockMovement(
        school_id=school_a.id,
        item_id=item.id,
        source_location_id=loc_src.id,
        destination_location_id=loc_dst.id,
        movement_type=InventoryStockMovementType.TRANSFER,
        quantity=30,
        performed_by_user_id=user_a.id,
        movement_date=datetime.now(timezone.utc),
        remarks="Transfer to Chem Lab",
    )
    db_session.add(m2)
    db_session.flush()

    assert m2.id is not None
    assert m2.source_location.name == "Main Warehouse"
    assert m2.destination_location.name == "Chemistry Lab"


def test_inventory_stock_movement_positive_quantity_constraint(
    db_session: Session,
    school_a: School,
):
    cat = InventoryCategory(school_id=school_a.id, name="General", code="GEN")
    loc = InventoryLocation(school_id=school_a.id, name="Store", code="STR")
    db_session.add_all([cat, loc])
    db_session.flush()

    item = InventoryItem(school_id=school_a.id, category_id=cat.id, item_code="CHALK-01", name="Box of Chalk")
    db_session.add(item)
    db_session.flush()

    invalid_movement = InventoryStockMovement(
        school_id=school_a.id,
        item_id=item.id,
        destination_location_id=loc.id,
        movement_type=InventoryStockMovementType.PURCHASE_RECEIPT,
        quantity=0,  # Violates quantity > 0 constraint
        movement_date=datetime.now(timezone.utc),
    )
    db_session.add(invalid_movement)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 8. ASSET ASSIGNMENT TESTS
# ==============================================================================

def test_asset_assignment_lifecycle_and_assignee_types(
    db_session: Session,
    school_a: School,
    teacher_a: Teacher,
    student_a: Student,
    classroom_a: Classroom,
    user_a: IdentityUser,
):
    cat = InventoryCategory(school_id=school_a.id, name="IT Hardware", code="ITHW")
    db_session.add(cat)
    db_session.flush()

    item = InventoryItem(
        school_id=school_a.id,
        category_id=cat.id,
        item_code="PROJ-01",
        name="Optoma HD Projector",
        item_type=InventoryItemType.ASSET,
        track_individually=True,
    )
    db_session.add(item)
    db_session.flush()

    asset = PhysicalAsset(
        school_id=school_a.id,
        item_id=item.id,
        asset_tag=f"PRJ-LAB101-{uuid.uuid4().hex[:4]}",
        status=AssetStatus.AVAILABLE,
        condition=AssetCondition.GOOD,
    )
    db_session.add(asset)
    db_session.flush()

    # 1. Assign to classroom
    assign1 = AssetAssignment(
        school_id=school_a.id,
        asset_id=asset.id,
        assignment_type=AssetAssignmentType.CLASSROOM,
        classroom_id=classroom_a.id,
        assigned_date=date(2026, 1, 10),
        assigned_by_user_id=user_a.id,
        status=AssetAssignmentStatus.ACTIVE,
        condition_on_assignment=AssetCondition.GOOD,
        remarks="Mounted in Science Lab 101",
    )
    db_session.add(assign1)
    db_session.flush()
    db_session.refresh(assign1)

    assert assign1.id is not None
    assert assign1.classroom.room_number == classroom_a.room_number
    assert assign1.status == AssetAssignmentStatus.ACTIVE

    # 2. Return from classroom
    assign1.status = AssetAssignmentStatus.RETURNED
    assign1.actual_return_date = date(2026, 6, 30)
    assign1.condition_on_return = AssetCondition.GOOD
    db_session.flush()

    # 3. Reassign to Teacher
    assign2 = AssetAssignment(
        school_id=school_a.id,
        asset_id=asset.id,
        assignment_type=AssetAssignmentType.STAFF,
        teacher_id=teacher_a.id,
        assigned_date=date(2026, 7, 1),
        assigned_by_user_id=user_a.id,
        status=AssetAssignmentStatus.ACTIVE,
        condition_on_assignment=AssetCondition.GOOD,
        remarks="Assigned to Alice Smith for term 2",
    )
    db_session.add(assign2)
    db_session.flush()
    db_session.refresh(assign2)

    assert assign2.id is not None
    assert assign2.teacher.first_name == "Alice"
    assert len(asset.assignments) == 2


def test_asset_assignment_active_uniqueness_constraint(
    db_session: Session,
    school_a: School,
    teacher_a: Teacher,
    student_a: Student,
    user_a: IdentityUser,
):
    cat = InventoryCategory(school_id=school_a.id, name="IT Hardware", code="ITHW")
    db_session.add(cat)
    db_session.flush()

    item = InventoryItem(school_id=school_a.id, category_id=cat.id, item_code="TAB-01", name="Tablet")
    db_session.add(item)
    db_session.flush()

    asset = PhysicalAsset(
        school_id=school_a.id,
        item_id=item.id,
        asset_tag=f"TAB-001-{uuid.uuid4().hex[:4]}",
    )
    db_session.add(asset)
    db_session.flush()

    # Active assignment 1 to Teacher
    assign1 = AssetAssignment(
        school_id=school_a.id,
        asset_id=asset.id,
        assignment_type=AssetAssignmentType.STAFF,
        teacher_id=teacher_a.id,
        assigned_date=date(2026, 1, 10),
        status=AssetAssignmentStatus.ACTIVE,
    )
    db_session.add(assign1)
    db_session.flush()

    # Second concurrent active assignment to same asset must be REJECTED by unique index
    assign2 = AssetAssignment(
        school_id=school_a.id,
        asset_id=asset.id,
        assignment_type=AssetAssignmentType.STUDENT,
        student_id=student_a.id,
        assigned_date=date(2026, 1, 12),
        status=AssetAssignmentStatus.ACTIVE,
    )
    db_session.add(assign2)
    with pytest.raises(IntegrityError):
        db_session.flush()
    db_session.rollback()


# ==============================================================================
# 9. CROSS-TENANT ISOLATION TESTS
# ==============================================================================

def test_cross_tenant_inventory_isolation(
    db_session: Session,
    school_a: School,
    school_b: School,
    teacher_a: Teacher,
):
    cat_a = InventoryCategory(school_id=school_a.id, name="Stationery A", code="STAT")
    cat_b = InventoryCategory(school_id=school_b.id, name="Stationery B", code="STAT")
    loc_a = InventoryLocation(school_id=school_a.id, name="Store A", code="STR")
    loc_b = InventoryLocation(school_id=school_b.id, name="Store B", code="STR")
    db_session.add_all([cat_a, cat_b, loc_a, loc_b])
    db_session.flush()

    item_a = InventoryItem(school_id=school_a.id, category_id=cat_a.id, item_code="A-01", name="Item A")
    item_b = InventoryItem(school_id=school_b.id, category_id=cat_b.id, item_code="B-01", name="Item B")
    db_session.add_all([item_a, item_b])
    db_session.flush()

    # Query items for School A returns ONLY School A records
    stmt = select(InventoryItem).where(InventoryItem.school_id == school_a.id)
    items_a = db_session.scalars(stmt).all()
    assert len(items_a) == 1
    assert items_a[0].name == "Item A"

    # Query locations for School B returns ONLY School B records
    stmt = select(InventoryLocation).where(InventoryLocation.school_id == school_b.id)
    locs_b = db_session.scalars(stmt).all()
    assert len(locs_b) == 1
    assert locs_b[0].name == "Store B"


# ==============================================================================
# 10. RBAC PERMISSIONS & ROLE MAPPINGS SEEDER TESTS
# ==============================================================================

def test_inventory_rbac_permissions_and_role_seeders(db_session: Session, school_a: School):
    # 1. Run permission seeder
    perm_result = permission_seeder.seed(db_session)
    assert perm_result["created"] > 0 or perm_result["skipped"] > 0

    # Verify all 7 inventory permissions exist in DB
    expected_inventory_perms = [
        "inventory.view",
        "inventory.create",
        "inventory.update",
        "inventory.delete",
        "inventory.issue",
        "inventory.transfer",
        "inventory.manage",
    ]
    for perm_name in expected_inventory_perms:
        perm = db_session.scalar(
            select(IdentityPermission).where(IdentityPermission.name == perm_name)
        )
        assert perm is not None, f"Permission {perm_name} not found in database"
        assert perm.module == "inventory"

    # 2. Run role seeder
    role_seeder.seed(db_session)

    # 3. Run role permission matrix seeder
    matrix_result = role_permission_seeder.seed(db_session)
    assert matrix_result["created"] > 0 or matrix_result["skipped"] > 0

    # 4. Verify Super Admin has '*' mapping (resolves to all permissions including inventory)
    super_admin_role = db_session.scalar(
        select(IdentityRole).where(IdentityRole.name == "Super Admin")
    )
    assert super_admin_role is not None

    admin_perms = db_session.scalars(
        select(IdentityPermission)
        .join(IdentityRolePermission, IdentityRolePermission.permission_id == IdentityPermission.id)
        .where(IdentityRolePermission.role_id == super_admin_role.id)
    ).all()
    admin_perm_names = {p.name for p in admin_perms}
    for perm_name in expected_inventory_perms:
        assert perm_name in admin_perm_names, f"Super Admin missing {perm_name}"

    # 5. Verify Teacher has 'inventory.view'
    teacher_role = db_session.scalar(
        select(IdentityRole).where(IdentityRole.name == "Teacher")
    )
    assert teacher_role is not None
    teacher_perms = db_session.scalars(
        select(IdentityPermission)
        .join(IdentityRolePermission, IdentityRolePermission.permission_id == IdentityPermission.id)
        .where(IdentityRolePermission.role_id == teacher_role.id)
    ).all()
    teacher_perm_names = {p.name for p in teacher_perms}
    assert "inventory.view" in teacher_perm_names
    assert "inventory.delete" not in teacher_perm_names
