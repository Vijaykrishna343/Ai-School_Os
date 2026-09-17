from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.inventory import (
    AssetAssignmentStatus,
    AssetAssignmentType,
    AssetCondition,
    AssetStatus,
    InventoryItemType,
    InventoryLocationType,
    InventoryStockMovementType,
)


# =============================================================================
# 1. CATEGORY SCHEMAS
# =============================================================================

class InventoryCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)


class InventoryCategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class InventoryCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    code: str
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InventoryCategoryListResponse(BaseModel):
    items: list[InventoryCategoryResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 2. LOCATION SCHEMAS
# =============================================================================

class InventoryLocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    code: str = Field(..., min_length=1, max_length=50)
    location_type: InventoryLocationType = Field(default=InventoryLocationType.STORE_ROOM)
    parent_location_id: UUID | None = None
    building_name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool = Field(default=True)


class InventoryLocationUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    location_type: InventoryLocationType | None = None
    parent_location_id: UUID | None = None
    building_name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    is_active: bool | None = None


class InventoryLocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    code: str
    location_type: InventoryLocationType
    parent_location_id: UUID | None = None
    building_name: str | None = None
    description: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InventoryLocationListResponse(BaseModel):
    items: list[InventoryLocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 3. VENDOR SCHEMAS
# =============================================================================

class InventoryVendorCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=150)
    code: str = Field(..., min_length=1, max_length=50)
    contact_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    tax_id: str | None = Field(default=None, max_length=50)
    is_active: bool = Field(default=True)


class InventoryVendorUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    code: str | None = Field(default=None, min_length=1, max_length=50)
    contact_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=500)
    tax_id: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class InventoryVendorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    code: str
    contact_name: str | None = None
    email: str | None = None
    phone: str | None = None
    address: str | None = None
    tax_id: str | None = None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class InventoryVendorListResponse(BaseModel):
    items: list[InventoryVendorResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 4. ITEM SCHEMAS
# =============================================================================

class InventoryItemCreate(BaseModel):
    category_id: UUID
    item_code: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    item_type: InventoryItemType = Field(default=InventoryItemType.CONSUMABLE)
    unit_of_measure: str = Field(default="PCS", min_length=1, max_length=30)
    track_individually: bool = Field(default=False)
    reorder_level: int = Field(default=0, ge=0)
    is_active: bool = Field(default=True)


class InventoryItemUpdate(BaseModel):
    category_id: UUID | None = None
    item_code: str | None = Field(default=None, min_length=1, max_length=50)
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=500)
    item_type: InventoryItemType | None = None
    unit_of_measure: str | None = Field(default=None, min_length=1, max_length=30)
    track_individually: bool | None = None
    reorder_level: int | None = Field(default=None, ge=0)
    is_active: bool | None = None


class InventoryItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    category_id: UUID
    item_code: str
    name: str
    description: str | None = None
    item_type: InventoryItemType
    unit_of_measure: str
    track_individually: bool
    reorder_level: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    category: InventoryCategoryResponse | None = None


class InventoryItemListResponse(BaseModel):
    items: list[InventoryItemResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 5. STOCK & MUTATION SCHEMAS
# =============================================================================

class InventoryStockResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    item_id: UUID
    location_id: UUID
    quantity: int
    reserved_quantity: int
    unit_price: Decimal | None = None
    last_counted_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    item: InventoryItemResponse | None = None
    location: InventoryLocationResponse | None = None


class InventoryStockListResponse(BaseModel):
    items: list[InventoryStockResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class InventoryStockSummaryResponse(BaseModel):
    total_items: int
    total_stock_units: int
    total_locations: int
    low_stock_items_count: int
    out_of_stock_items_count: int


class StockReceiveRequest(BaseModel):
    item_id: UUID
    location_id: UUID
    quantity: int = Field(..., gt=0, description="Must be greater than 0")
    unit_price: Decimal | None = Field(default=None, ge=0)
    vendor_id: UUID | None = None
    reference_number: str | None = Field(default=None, max_length=100)
    remarks: str | None = Field(default=None, max_length=500)


class StockIssueRequest(BaseModel):
    item_id: UUID
    location_id: UUID
    quantity: int = Field(..., gt=0, description="Must be greater than 0")
    reference_number: str | None = Field(default=None, max_length=100)
    remarks: str | None = Field(default=None, max_length=500)


class StockReturnRequest(BaseModel):
    item_id: UUID
    location_id: UUID
    quantity: int = Field(..., gt=0, description="Must be greater than 0")
    reference_number: str | None = Field(default=None, max_length=100)
    remarks: str | None = Field(default=None, max_length=500)


class StockAdjustmentRequest(BaseModel):
    item_id: UUID
    location_id: UUID
    adjustment_type: str = Field(..., pattern="^(ADD|SUBTRACT)$", description="ADD or SUBTRACT")
    quantity: int = Field(..., gt=0, description="Quantity to add or subtract (> 0)")
    reason: str = Field(..., min_length=3, max_length=500, description="Mandatory reason for audit trail")
    reference_number: str | None = Field(default=None, max_length=100)


class StockTransferRequest(BaseModel):
    item_id: UUID
    source_location_id: UUID
    destination_location_id: UUID
    quantity: int = Field(..., gt=0, description="Must be greater than 0")
    reference_number: str | None = Field(default=None, max_length=100)
    remarks: str | None = Field(default=None, max_length=500)


# =============================================================================
# 6. MOVEMENT SCHEMAS
# =============================================================================

class InventoryStockMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    item_id: UUID
    source_location_id: UUID | None = None
    destination_location_id: UUID | None = None
    movement_type: InventoryStockMovementType
    quantity: int
    unit_price: Decimal | None = None
    reference_number: str | None = None
    vendor_id: UUID | None = None
    performed_by_user_id: UUID | None = None
    movement_date: datetime
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
    item: InventoryItemResponse | None = None
    source_location: InventoryLocationResponse | None = None
    destination_location: InventoryLocationResponse | None = None
    vendor: InventoryVendorResponse | None = None


class InventoryStockMovementListResponse(BaseModel):
    items: list[InventoryStockMovementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 7. PHYSICAL ASSET SCHEMAS
# =============================================================================

class PhysicalAssetCreate(BaseModel):
    item_id: UUID
    location_id: UUID | None = None
    vendor_id: UUID | None = None
    asset_tag: str = Field(..., min_length=1, max_length=50)
    serial_number: str | None = Field(default=None, max_length=100)
    model_number: str | None = Field(default=None, max_length=100)
    status: AssetStatus = Field(default=AssetStatus.AVAILABLE)
    condition: AssetCondition = Field(default=AssetCondition.GOOD)
    purchase_date: date | None = None
    purchase_cost: Decimal | None = Field(default=None, ge=0)
    warranty_expiry_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class PhysicalAssetUpdate(BaseModel):
    location_id: UUID | None = None
    vendor_id: UUID | None = None
    asset_tag: str | None = Field(default=None, min_length=1, max_length=50)
    serial_number: str | None = Field(default=None, max_length=100)
    model_number: str | None = Field(default=None, max_length=100)
    status: AssetStatus | None = None
    condition: AssetCondition | None = None
    purchase_date: date | None = None
    purchase_cost: Decimal | None = Field(default=None, ge=0)
    warranty_expiry_date: date | None = None
    notes: str | None = Field(default=None, max_length=1000)


class PhysicalAssetRetireRequest(BaseModel):
    status: AssetStatus = Field(
        default=AssetStatus.RETIRED,
        description="Must be RETIRED or DISPOSED",
    )
    notes: str | None = Field(default=None, max_length=1000)


class PhysicalAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    item_id: UUID
    location_id: UUID | None = None
    vendor_id: UUID | None = None
    asset_tag: str
    serial_number: str | None = None
    model_number: str | None = None
    status: AssetStatus
    condition: AssetCondition
    purchase_date: date | None = None
    purchase_cost: Decimal | None = None
    warranty_expiry_date: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
    item: InventoryItemResponse | None = None
    location: InventoryLocationResponse | None = None
    vendor: InventoryVendorResponse | None = None


class PhysicalAssetListResponse(BaseModel):
    items: list[PhysicalAssetResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# 8. ASSET ASSIGNMENT SCHEMAS
# =============================================================================

class AssetAssignmentCreate(BaseModel):
    asset_id: UUID
    assignment_type: AssetAssignmentType = Field(default=AssetAssignmentType.STAFF)
    teacher_id: UUID | None = None
    student_id: UUID | None = None
    classroom_id: UUID | None = None
    user_id: UUID | None = None
    department_name: str | None = Field(default=None, max_length=100)
    assigned_date: date
    expected_return_date: date | None = None
    condition_on_assignment: AssetCondition = Field(default=AssetCondition.GOOD)
    remarks: str | None = Field(default=None, max_length=500)


class AssetAssignmentReturnRequest(BaseModel):
    actual_return_date: date
    condition_on_return: AssetCondition = Field(default=AssetCondition.GOOD)
    return_location_id: UUID | None = None
    remarks: str | None = Field(default=None, max_length=500)


class AssetAssignmentTransferRequest(BaseModel):
    new_assignment_type: AssetAssignmentType = Field(default=AssetAssignmentType.STAFF)
    new_teacher_id: UUID | None = None
    new_student_id: UUID | None = None
    new_classroom_id: UUID | None = None
    new_user_id: UUID | None = None
    new_department_name: str | None = Field(default=None, max_length=100)
    transfer_date: date
    condition: AssetCondition = Field(default=AssetCondition.GOOD)
    remarks: str | None = Field(default=None, max_length=500)


class AssetAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    asset_id: UUID
    assignment_type: AssetAssignmentType
    teacher_id: UUID | None = None
    student_id: UUID | None = None
    classroom_id: UUID | None = None
    user_id: UUID | None = None
    department_name: str | None = None
    assigned_date: date
    expected_return_date: date | None = None
    actual_return_date: date | None = None
    assigned_by_user_id: UUID | None = None
    status: AssetAssignmentStatus
    condition_on_assignment: AssetCondition
    condition_on_return: AssetCondition | None = None
    remarks: str | None = None
    created_at: datetime
    updated_at: datetime
    asset: PhysicalAssetResponse | None = None


class AssetAssignmentListResponse(BaseModel):
    items: list[AssetAssignmentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
