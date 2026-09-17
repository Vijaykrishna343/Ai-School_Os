from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.common.enums.inventory import (
    AssetAssignmentStatus,
    AssetAssignmentType,
    AssetCondition,
    AssetStatus,
    InventoryItemType,
    InventoryLocationType,
    InventoryStockMovementType,
)
from app.dependencies import get_db, get_inventory_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.inventory import (
    AssetAssignmentCreate,
    AssetAssignmentListResponse,
    AssetAssignmentResponse,
    AssetAssignmentReturnRequest,
    AssetAssignmentTransferRequest,
    InventoryCategoryCreate,
    InventoryCategoryListResponse,
    InventoryCategoryResponse,
    InventoryCategoryUpdate,
    InventoryItemCreate,
    InventoryItemListResponse,
    InventoryItemResponse,
    InventoryItemUpdate,
    InventoryLocationCreate,
    InventoryLocationListResponse,
    InventoryLocationResponse,
    InventoryLocationUpdate,
    InventoryStockListResponse,
    InventoryStockMovementListResponse,
    InventoryStockMovementResponse,
    InventoryStockResponse,
    InventoryStockSummaryResponse,
    InventoryVendorCreate,
    InventoryVendorListResponse,
    InventoryVendorResponse,
    InventoryVendorUpdate,
    PhysicalAssetCreate,
    PhysicalAssetListResponse,
    PhysicalAssetResponse,
    PhysicalAssetRetireRequest,
    PhysicalAssetUpdate,
    StockAdjustmentRequest,
    StockIssueRequest,
    StockReceiveRequest,
    StockReturnRequest,
    StockTransferRequest,
)
from app.services.inventory_service import InventoryService

router = APIRouter()


# =============================================================================
# 1. CATEGORIES ENDPOINTS
# =============================================================================

@router.post(
    "/categories",
    response_model=InventoryCategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory category",
)
def create_category(
    payload: InventoryCategoryCreate,
    current_user: IdentityUser = Depends(require_permission("inventory.create")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryCategoryResponse:
    category = service.create_category(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return InventoryCategoryResponse.model_validate(category)


@router.get(
    "/categories",
    response_model=InventoryCategoryListResponse,
    summary="List inventory categories",
)
def list_categories(
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name or code"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryCategoryListResponse:
    items, total, total_pages = service.list_categories(
        db=db,
        school_id=current_user.school_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return InventoryCategoryListResponse(
        items=[InventoryCategoryResponse.model_validate(c) for c in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/categories/{category_id}",
    response_model=InventoryCategoryResponse,
    summary="Retrieve inventory category",
)
def get_category(
    category_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryCategoryResponse:
    category = service.get_category(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
    )
    return InventoryCategoryResponse.model_validate(category)


@router.put(
    "/categories/{category_id}",
    response_model=InventoryCategoryResponse,
    summary="Update inventory category",
)
def update_category(
    category_id: UUID,
    payload: InventoryCategoryUpdate,
    current_user: IdentityUser = Depends(require_permission("inventory.update")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryCategoryResponse:
    category = service.update_category(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
        payload=payload,
    )
    return InventoryCategoryResponse.model_validate(category)


@router.delete(
    "/categories/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inventory category",
)
def delete_category(
    category_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.delete")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> Response:
    service.delete_category(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 2. LOCATIONS ENDPOINTS
# =============================================================================

@router.post(
    "/locations",
    response_model=InventoryLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory location",
)
def create_location(
    payload: InventoryLocationCreate,
    current_user: IdentityUser = Depends(require_permission("inventory.create")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryLocationResponse:
    location = service.create_location(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return InventoryLocationResponse.model_validate(location)


@router.get(
    "/locations",
    response_model=InventoryLocationListResponse,
    summary="List inventory locations",
)
def list_locations(
    location_type: InventoryLocationType | None = Query(default=None, description="Filter by location type"),
    parent_location_id: UUID | None = Query(default=None, description="Filter by parent location"),
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name, code, or building"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryLocationListResponse:
    items, total, total_pages = service.list_locations(
        db=db,
        school_id=current_user.school_id,
        location_type=location_type,
        parent_location_id=parent_location_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return InventoryLocationListResponse(
        items=[InventoryLocationResponse.model_validate(loc) for loc in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/locations/{location_id}",
    response_model=InventoryLocationResponse,
    summary="Retrieve inventory location",
)
def get_location(
    location_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryLocationResponse:
    location = service.get_location(
        db=db,
        school_id=current_user.school_id,
        location_id=location_id,
    )
    return InventoryLocationResponse.model_validate(location)


@router.put(
    "/locations/{location_id}",
    response_model=InventoryLocationResponse,
    summary="Update inventory location",
)
def update_location(
    location_id: UUID,
    payload: InventoryLocationUpdate,
    current_user: IdentityUser = Depends(require_permission("inventory.update")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryLocationResponse:
    location = service.update_location(
        db=db,
        school_id=current_user.school_id,
        location_id=location_id,
        payload=payload,
    )
    return InventoryLocationResponse.model_validate(location)


@router.delete(
    "/locations/{location_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inventory location",
)
def delete_location(
    location_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.delete")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> Response:
    service.delete_location(
        db=db,
        school_id=current_user.school_id,
        location_id=location_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 3. VENDORS ENDPOINTS
# =============================================================================

@router.post(
    "/vendors",
    response_model=InventoryVendorResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory vendor",
)
def create_vendor(
    payload: InventoryVendorCreate,
    current_user: IdentityUser = Depends(require_permission("inventory.create")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryVendorResponse:
    vendor = service.create_vendor(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return InventoryVendorResponse.model_validate(vendor)


@router.get(
    "/vendors",
    response_model=InventoryVendorListResponse,
    summary="List inventory vendors",
)
def list_vendors(
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name, code, contact, email"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryVendorListResponse:
    items, total, total_pages = service.list_vendors(
        db=db,
        school_id=current_user.school_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return InventoryVendorListResponse(
        items=[InventoryVendorResponse.model_validate(v) for v in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/vendors/{vendor_id}",
    response_model=InventoryVendorResponse,
    summary="Retrieve inventory vendor",
)
def get_vendor(
    vendor_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryVendorResponse:
    vendor = service.get_vendor(
        db=db,
        school_id=current_user.school_id,
        vendor_id=vendor_id,
    )
    return InventoryVendorResponse.model_validate(vendor)


@router.put(
    "/vendors/{vendor_id}",
    response_model=InventoryVendorResponse,
    summary="Update inventory vendor",
)
def update_vendor(
    vendor_id: UUID,
    payload: InventoryVendorUpdate,
    current_user: IdentityUser = Depends(require_permission("inventory.update")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryVendorResponse:
    vendor = service.update_vendor(
        db=db,
        school_id=current_user.school_id,
        vendor_id=vendor_id,
        payload=payload,
    )
    return InventoryVendorResponse.model_validate(vendor)


@router.delete(
    "/vendors/{vendor_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inventory vendor",
)
def delete_vendor(
    vendor_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.delete")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> Response:
    service.delete_vendor(
        db=db,
        school_id=current_user.school_id,
        vendor_id=vendor_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 4. ITEMS (CATALOG) ENDPOINTS
# =============================================================================

@router.post(
    "/items",
    response_model=InventoryItemResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create inventory item",
)
def create_item(
    payload: InventoryItemCreate,
    current_user: IdentityUser = Depends(require_permission("inventory.create")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryItemResponse:
    item = service.create_item(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return InventoryItemResponse.model_validate(item)


@router.get(
    "/items",
    response_model=InventoryItemListResponse,
    summary="List inventory items",
)
def list_items(
    category_id: UUID | None = Query(default=None, description="Filter by category"),
    item_type: InventoryItemType | None = Query(default=None, description="Filter by item type"),
    is_active: bool | None = Query(default=None, description="Filter by active state"),
    search: str | None = Query(default=None, description="Search by name or code"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryItemListResponse:
    items, total, total_pages = service.list_items(
        db=db,
        school_id=current_user.school_id,
        category_id=category_id,
        item_type=item_type,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return InventoryItemListResponse(
        items=[InventoryItemResponse.model_validate(it) for it in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/items/{item_id}",
    response_model=InventoryItemResponse,
    summary="Retrieve inventory item",
)
def get_item(
    item_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryItemResponse:
    item = service.get_item(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
    )
    return InventoryItemResponse.model_validate(item)


@router.put(
    "/items/{item_id}",
    response_model=InventoryItemResponse,
    summary="Update inventory item",
)
def update_item(
    item_id: UUID,
    payload: InventoryItemUpdate,
    current_user: IdentityUser = Depends(require_permission("inventory.update")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryItemResponse:
    item = service.update_item(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
        payload=payload,
    )
    return InventoryItemResponse.model_validate(item)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete inventory item",
)
def delete_item(
    item_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.delete")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> Response:
    service.delete_item(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# =============================================================================
# 5. STOCK VISIBILITY & MUTATION ENDPOINTS
# =============================================================================

@router.get(
    "/stock/summary",
    response_model=InventoryStockSummaryResponse,
    summary="Retrieve inventory stock summary KPI metrics",
)
def get_stock_summary(
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockSummaryResponse:
    return service.get_stock_summary(
        db=db,
        school_id=current_user.school_id,
    )


@router.get(
    "/stock",
    response_model=InventoryStockListResponse,
    summary="List stock records with filtering",
)
def list_stock(
    item_id: UUID | None = Query(default=None, description="Filter by item"),
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    category_id: UUID | None = Query(default=None, description="Filter by category"),
    low_stock: bool | None = Query(default=None, description="Filter items at or below reorder level"),
    search: str | None = Query(default=None, description="Search item name or code"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockListResponse:
    items, total, total_pages = service.list_stock(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
        location_id=location_id,
        category_id=category_id,
        low_stock=low_stock,
        search=search,
        page=page,
        page_size=page_size,
    )
    return InventoryStockListResponse(
        items=[InventoryStockResponse.model_validate(st) for st in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/stock/{stock_id}",
    response_model=InventoryStockResponse,
    summary="Retrieve single stock record",
)
def get_stock(
    stock_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockResponse:
    stock = service.get_stock(
        db=db,
        school_id=current_user.school_id,
        stock_id=stock_id,
    )
    return InventoryStockResponse.model_validate(stock)


@router.get(
    "/stock/items/{item_id}",
    response_model=list[InventoryStockResponse],
    summary="Retrieve stock levels for an item across all locations",
)
def get_stock_by_item(
    item_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> list[InventoryStockResponse]:
    stocks = service.get_stock_by_item(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
    )
    return [InventoryStockResponse.model_validate(s) for s in stocks]


@router.post(
    "/stock/receive",
    response_model=InventoryStockResponse,
    status_code=status.HTTP_200_OK,
    summary="Receive stock (purchase receipt) into location",
)
def receive_stock(
    payload: StockReceiveRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.create")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockResponse:
    stock = service.receive_stock(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        performed_by_user_id=current_user.id,
    )
    return InventoryStockResponse.model_validate(stock)


@router.post(
    "/stock/issue",
    response_model=InventoryStockResponse,
    status_code=status.HTTP_200_OK,
    summary="Issue stock (consumables) from location",
)
def issue_stock(
    payload: StockIssueRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.issue")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockResponse:
    stock = service.issue_stock(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        performed_by_user_id=current_user.id,
    )
    return InventoryStockResponse.model_validate(stock)


@router.post(
    "/stock/return",
    response_model=InventoryStockResponse,
    status_code=status.HTTP_200_OK,
    summary="Return previously issued stock back to location",
)
def return_stock(
    payload: StockReturnRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.issue")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockResponse:
    stock = service.return_stock(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        performed_by_user_id=current_user.id,
    )
    return InventoryStockResponse.model_validate(stock)


@router.post(
    "/stock/adjust",
    response_model=InventoryStockResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform controlled stock adjustment (ADD or SUBTRACT) with audit reason",
)
def adjust_stock(
    payload: StockAdjustmentRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockResponse:
    stock = service.adjust_stock(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        performed_by_user_id=current_user.id,
    )
    return InventoryStockResponse.model_validate(stock)


@router.post(
    "/stock/transfer",
    response_model=InventoryStockResponse,
    status_code=status.HTTP_200_OK,
    summary="Transfer stock between two physical storage locations",
)
def transfer_stock(
    payload: StockTransferRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.transfer")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockResponse:
    stock = service.transfer_stock(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        performed_by_user_id=current_user.id,
    )
    return InventoryStockResponse.model_validate(stock)


# =============================================================================
# 6. MOVEMENT HISTORY (AUDIT TRAIL) ENDPOINTS
# =============================================================================

@router.get(
    "/movements",
    response_model=InventoryStockMovementListResponse,
    summary="List stock movement history (read-only audit trail)",
)
def list_movements(
    item_id: UUID | None = Query(default=None, description="Filter by item"),
    source_location_id: UUID | None = Query(default=None, description="Filter by source location"),
    destination_location_id: UUID | None = Query(default=None, description="Filter by destination location"),
    movement_type: InventoryStockMovementType | None = Query(default=None, description="Filter by movement type"),
    reference_number: str | None = Query(default=None, description="Filter by reference number"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockMovementListResponse:
    items, total, total_pages = service.list_movements(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
        source_location_id=source_location_id,
        destination_location_id=destination_location_id,
        movement_type=movement_type,
        reference_number=reference_number,
        page=page,
        page_size=page_size,
    )
    return InventoryStockMovementListResponse(
        items=[InventoryStockMovementResponse.model_validate(m) for m in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/movements/{movement_id}",
    response_model=InventoryStockMovementResponse,
    summary="Retrieve single stock movement entry",
)
def get_movement(
    movement_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> InventoryStockMovementResponse:
    movement = service.get_movement(
        db=db,
        school_id=current_user.school_id,
        movement_id=movement_id,
    )
    return InventoryStockMovementResponse.model_validate(movement)


# =============================================================================
# 7. PHYSICAL ASSETS ENDPOINTS
# =============================================================================

@router.post(
    "/assets",
    response_model=PhysicalAssetResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create physical asset",
)
def create_asset(
    payload: PhysicalAssetCreate,
    current_user: IdentityUser = Depends(require_permission("inventory.create")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> PhysicalAssetResponse:
    asset = service.create_asset(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
    )
    return PhysicalAssetResponse.model_validate(asset)


@router.get(
    "/assets",
    response_model=PhysicalAssetListResponse,
    summary="List physical assets",
)
def list_assets(
    item_id: UUID | None = Query(default=None, description="Filter by item"),
    location_id: UUID | None = Query(default=None, description="Filter by location"),
    vendor_id: UUID | None = Query(default=None, description="Filter by vendor"),
    status: AssetStatus | None = Query(default=None, description="Filter by asset status"),
    condition: AssetCondition | None = Query(default=None, description="Filter by asset condition"),
    search: str | None = Query(default=None, description="Search by asset tag, serial, or model"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> PhysicalAssetListResponse:
    items, total, total_pages = service.list_assets(
        db=db,
        school_id=current_user.school_id,
        item_id=item_id,
        location_id=location_id,
        vendor_id=vendor_id,
        status=status,
        condition=condition,
        search=search,
        page=page,
        page_size=page_size,
    )
    return PhysicalAssetListResponse(
        items=[PhysicalAssetResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/assets/{asset_id}",
    response_model=PhysicalAssetResponse,
    summary="Retrieve physical asset",
)
def get_asset(
    asset_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> PhysicalAssetResponse:
    asset = service.get_asset(
        db=db,
        school_id=current_user.school_id,
        asset_id=asset_id,
    )
    return PhysicalAssetResponse.model_validate(asset)


@router.put(
    "/assets/{asset_id}",
    response_model=PhysicalAssetResponse,
    summary="Update physical asset",
)
def update_asset(
    asset_id: UUID,
    payload: PhysicalAssetUpdate,
    current_user: IdentityUser = Depends(require_permission("inventory.update")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> PhysicalAssetResponse:
    asset = service.update_asset(
        db=db,
        school_id=current_user.school_id,
        asset_id=asset_id,
        payload=payload,
    )
    return PhysicalAssetResponse.model_validate(asset)


@router.delete(
    "/assets/{asset_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete physical asset",
)
def delete_asset(
    asset_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.delete")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> Response:
    service.delete_asset(
        db=db,
        school_id=current_user.school_id,
        asset_id=asset_id,
    )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post(
    "/assets/{asset_id}/retire",
    response_model=PhysicalAssetResponse,
    summary="Retire or dispose physical asset",
)
def retire_asset(
    asset_id: UUID,
    payload: PhysicalAssetRetireRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.manage")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> PhysicalAssetResponse:
    asset = service.retire_asset(
        db=db,
        school_id=current_user.school_id,
        asset_id=asset_id,
        payload=payload,
    )
    return PhysicalAssetResponse.model_validate(asset)


@router.get(
    "/assets/{asset_id}/history",
    response_model=list[AssetAssignmentResponse],
    summary="Retrieve assignment history for a physical asset",
)
def get_asset_history(
    asset_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> list[AssetAssignmentResponse]:
    assignments = service.get_asset_history(
        db=db,
        school_id=current_user.school_id,
        asset_id=asset_id,
    )
    return [AssetAssignmentResponse.model_validate(a) for a in assignments]


# =============================================================================
# 8. ASSET ASSIGNMENTS ENDPOINTS
# =============================================================================

@router.post(
    "/assignments",
    response_model=AssetAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Assign physical asset to Staff/Teacher, Student, Classroom, or Department",
)
def assign_asset(
    payload: AssetAssignmentCreate,
    current_user: IdentityUser = Depends(require_permission("inventory.issue")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> AssetAssignmentResponse:
    assignment = service.assign_asset(
        db=db,
        school_id=current_user.school_id,
        payload=payload,
        assigned_by_user_id=current_user.id,
    )
    return AssetAssignmentResponse.model_validate(assignment)


@router.get(
    "/assignments",
    response_model=AssetAssignmentListResponse,
    summary="List asset assignments",
)
def list_assignments(
    asset_id: UUID | None = Query(default=None, description="Filter by asset"),
    assignment_type: AssetAssignmentType | None = Query(default=None, description="Filter by assignment type"),
    status: AssetAssignmentStatus | None = Query(default=None, description="Filter by assignment status"),
    teacher_id: UUID | None = Query(default=None, description="Filter by teacher"),
    student_id: UUID | None = Query(default=None, description="Filter by student"),
    classroom_id: UUID | None = Query(default=None, description="Filter by classroom"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> AssetAssignmentListResponse:
    items, total, total_pages = service.list_assignments(
        db=db,
        school_id=current_user.school_id,
        asset_id=asset_id,
        assignment_type=assignment_type,
        status=status,
        teacher_id=teacher_id,
        student_id=student_id,
        classroom_id=classroom_id,
        page=page,
        page_size=page_size,
    )
    return AssetAssignmentListResponse(
        items=[AssetAssignmentResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssetAssignmentResponse,
    summary="Retrieve single asset assignment",
)
def get_assignment(
    assignment_id: UUID,
    current_user: IdentityUser = Depends(require_permission("inventory.view")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> AssetAssignmentResponse:
    assignment = service.get_assignment(
        db=db,
        school_id=current_user.school_id,
        assignment_id=assignment_id,
    )
    return AssetAssignmentResponse.model_validate(assignment)


@router.post(
    "/assignments/{assignment_id}/return",
    response_model=AssetAssignmentResponse,
    summary="Return assigned physical asset back to available status",
)
def return_asset(
    assignment_id: UUID,
    payload: AssetAssignmentReturnRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.issue")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> AssetAssignmentResponse:
    assignment = service.return_asset(
        db=db,
        school_id=current_user.school_id,
        assignment_id=assignment_id,
        payload=payload,
        received_by_user_id=current_user.id,
    )
    return AssetAssignmentResponse.model_validate(assignment)


@router.post(
    "/assignments/{assignment_id}/transfer",
    response_model=AssetAssignmentResponse,
    summary="Transfer active asset assignment to a new target",
)
def transfer_asset_assignment(
    assignment_id: UUID,
    payload: AssetAssignmentTransferRequest,
    current_user: IdentityUser = Depends(require_permission("inventory.transfer")),
    db: Session = Depends(get_db),
    service: InventoryService = Depends(get_inventory_service),
) -> AssetAssignmentResponse:
    assignment = service.transfer_asset_assignment(
        db=db,
        school_id=current_user.school_id,
        assignment_id=assignment_id,
        payload=payload,
        performed_by_user_id=current_user.id,
    )
    return AssetAssignmentResponse.model_validate(assignment)
