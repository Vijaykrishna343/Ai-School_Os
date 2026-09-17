from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, selectinload

from app.common.enums.inventory import (
    AssetAssignmentStatus,
    AssetAssignmentType,
    AssetCondition,
    AssetStatus,
    InventoryItemType,
    InventoryLocationType,
    InventoryStockMovementType,
)
from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
    ValidationException,
)
from app.identity.models.user import IdentityUser
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
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.timetable.classroom import Classroom
from app.schemas.inventory import (
    AssetAssignmentCreate,
    AssetAssignmentReturnRequest,
    AssetAssignmentTransferRequest,
    InventoryCategoryCreate,
    InventoryCategoryUpdate,
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryLocationCreate,
    InventoryLocationUpdate,
    InventoryStockSummaryResponse,
    InventoryVendorCreate,
    InventoryVendorUpdate,
    PhysicalAssetCreate,
    PhysicalAssetRetireRequest,
    PhysicalAssetUpdate,
    StockAdjustmentRequest,
    StockIssueRequest,
    StockReceiveRequest,
    StockReturnRequest,
    StockTransferRequest,
)


class InventoryService:
    """
    Comprehensive service handling business logic, validation, lifecycle state transitions,
    stock ledger transactions, and multi-tenant data management for the School ERP Inventory & Asset domain.
    """

    # =========================================================================
    # 1. INVENTORY CATEGORIES
    # =========================================================================

    def create_category(
        self,
        db: Session,
        school_id: UUID,
        payload: InventoryCategoryCreate,
    ) -> InventoryCategory:
        existing = db.scalars(
            select(InventoryCategory).where(
                InventoryCategory.school_id == school_id,
                InventoryCategory.code == payload.code,
                InventoryCategory.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Inventory Category with code", payload.code)

        category = InventoryCategory(
            school_id=school_id,
            name=payload.name,
            code=payload.code,
            description=payload.description,
            is_active=payload.is_active,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    def get_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
    ) -> InventoryCategory:
        category = db.scalars(
            select(InventoryCategory).where(
                InventoryCategory.id == category_id,
                InventoryCategory.school_id == school_id,
                InventoryCategory.is_deleted.is_(False),
            )
        ).first()
        if not category:
            raise NotFoundException("Inventory Category", str(category_id))
        return category

    def list_categories(
        self,
        db: Session,
        school_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InventoryCategory], int, int]:
        query = select(InventoryCategory).where(
            InventoryCategory.school_id == school_id,
            InventoryCategory.is_deleted.is_(False),
        )
        if is_active is not None:
            query = query.where(InventoryCategory.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InventoryCategory.name.ilike(term),
                    InventoryCategory.code.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(InventoryCategory.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
        payload: InventoryCategoryUpdate,
    ) -> InventoryCategory:
        category = self.get_category(db, school_id, category_id)

        if payload.code and payload.code != category.code:
            existing = db.scalars(
                select(InventoryCategory).where(
                    InventoryCategory.school_id == school_id,
                    InventoryCategory.code == payload.code,
                    InventoryCategory.id != category_id,
                    InventoryCategory.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Inventory Category with code", payload.code)
            category.code = payload.code

        if payload.name is not None:
            category.name = payload.name
        if payload.description is not None:
            category.description = payload.description
        if payload.is_active is not None:
            category.is_active = payload.is_active

        db.commit()
        db.refresh(category)
        return category

    def delete_category(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID,
    ) -> None:
        category = self.get_category(db, school_id, category_id)

        # Ensure no active items depend on this category
        active_items = db.scalars(
            select(InventoryItem).where(
                InventoryItem.category_id == category_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if active_items:
            raise BadRequestException("Cannot delete category with associated inventory items.")

        category.is_deleted = True
        category.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 2. INVENTORY LOCATIONS
    # =========================================================================

    def create_location(
        self,
        db: Session,
        school_id: UUID,
        payload: InventoryLocationCreate,
    ) -> InventoryLocation:
        if payload.parent_location_id:
            parent = db.scalars(
                select(InventoryLocation).where(
                    InventoryLocation.id == payload.parent_location_id,
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            ).first()
            if not parent:
                raise NotFoundException("Parent Location", str(payload.parent_location_id))

        existing = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.school_id == school_id,
                InventoryLocation.code == payload.code,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Inventory Location with code", payload.code)

        location = InventoryLocation(
            school_id=school_id,
            name=payload.name,
            code=payload.code,
            location_type=payload.location_type,
            parent_location_id=payload.parent_location_id,
            building_name=payload.building_name,
            description=payload.description,
            is_active=payload.is_active,
        )
        db.add(location)
        db.commit()
        db.refresh(location)
        return location

    def get_location(
        self,
        db: Session,
        school_id: UUID,
        location_id: UUID,
    ) -> InventoryLocation:
        location = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not location:
            raise NotFoundException("Inventory Location", str(location_id))
        return location

    def list_locations(
        self,
        db: Session,
        school_id: UUID,
        location_type: InventoryLocationType | None = None,
        parent_location_id: UUID | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InventoryLocation], int, int]:
        query = select(InventoryLocation).where(
            InventoryLocation.school_id == school_id,
            InventoryLocation.is_deleted.is_(False),
        )
        if location_type is not None:
            query = query.where(InventoryLocation.location_type == location_type)
        if parent_location_id is not None:
            query = query.where(InventoryLocation.parent_location_id == parent_location_id)
        if is_active is not None:
            query = query.where(InventoryLocation.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InventoryLocation.name.ilike(term),
                    InventoryLocation.code.ilike(term),
                    InventoryLocation.building_name.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(InventoryLocation.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_location(
        self,
        db: Session,
        school_id: UUID,
        location_id: UUID,
        payload: InventoryLocationUpdate,
    ) -> InventoryLocation:
        location = self.get_location(db, school_id, location_id)

        if payload.parent_location_id:
            if payload.parent_location_id == location_id:
                raise BadRequestException("A location cannot be its own parent.")
            parent = db.scalars(
                select(InventoryLocation).where(
                    InventoryLocation.id == payload.parent_location_id,
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            ).first()
            if not parent:
                raise NotFoundException("Parent Location", str(payload.parent_location_id))
            location.parent_location_id = payload.parent_location_id
        elif payload.parent_location_id is None and "parent_location_id" in payload.model_fields_set:
            location.parent_location_id = None

        if payload.code and payload.code != location.code:
            existing = db.scalars(
                select(InventoryLocation).where(
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.code == payload.code,
                    InventoryLocation.id != location_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Inventory Location with code", payload.code)
            location.code = payload.code

        if payload.name is not None:
            location.name = payload.name
        if payload.location_type is not None:
            location.location_type = payload.location_type
        if payload.building_name is not None:
            location.building_name = payload.building_name
        if payload.description is not None:
            location.description = payload.description
        if payload.is_active is not None:
            location.is_active = payload.is_active

        db.commit()
        db.refresh(location)
        return location

    def delete_location(
        self,
        db: Session,
        school_id: UUID,
        location_id: UUID,
    ) -> None:
        location = self.get_location(db, school_id, location_id)

        # Check for active stock balances
        active_stock = db.scalars(
            select(InventoryStock).where(
                InventoryStock.location_id == location_id,
                InventoryStock.school_id == school_id,
                InventoryStock.quantity > 0,
                InventoryStock.is_deleted.is_(False),
            )
        ).first()
        if active_stock:
            raise BadRequestException("Cannot delete location with active stock balances.")

        # Check for active physical assets
        active_assets = db.scalars(
            select(PhysicalAsset).where(
                PhysicalAsset.location_id == location_id,
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.is_deleted.is_(False),
            )
        ).first()
        if active_assets:
            raise BadRequestException("Cannot delete location with associated physical assets.")

        location.is_deleted = True
        location.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 3. INVENTORY VENDORS
    # =========================================================================

    def create_vendor(
        self,
        db: Session,
        school_id: UUID,
        payload: InventoryVendorCreate,
    ) -> InventoryVendor:
        existing = db.scalars(
            select(InventoryVendor).where(
                InventoryVendor.school_id == school_id,
                InventoryVendor.code == payload.code,
                InventoryVendor.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Inventory Vendor with code", payload.code)

        vendor = InventoryVendor(
            school_id=school_id,
            name=payload.name,
            code=payload.code,
            contact_name=payload.contact_name,
            email=payload.email,
            phone=payload.phone,
            address=payload.address,
            tax_id=payload.tax_id,
            is_active=payload.is_active,
        )
        db.add(vendor)
        db.commit()
        db.refresh(vendor)
        return vendor

    def get_vendor(
        self,
        db: Session,
        school_id: UUID,
        vendor_id: UUID,
    ) -> InventoryVendor:
        vendor = db.scalars(
            select(InventoryVendor).where(
                InventoryVendor.id == vendor_id,
                InventoryVendor.school_id == school_id,
                InventoryVendor.is_deleted.is_(False),
            )
        ).first()
        if not vendor:
            raise NotFoundException("Inventory Vendor", str(vendor_id))
        return vendor

    def list_vendors(
        self,
        db: Session,
        school_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InventoryVendor], int, int]:
        query = select(InventoryVendor).where(
            InventoryVendor.school_id == school_id,
            InventoryVendor.is_deleted.is_(False),
        )
        if is_active is not None:
            query = query.where(InventoryVendor.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InventoryVendor.name.ilike(term),
                    InventoryVendor.code.ilike(term),
                    InventoryVendor.contact_name.ilike(term),
                    InventoryVendor.email.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(InventoryVendor.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_vendor(
        self,
        db: Session,
        school_id: UUID,
        vendor_id: UUID,
        payload: InventoryVendorUpdate,
    ) -> InventoryVendor:
        vendor = self.get_vendor(db, school_id, vendor_id)

        if payload.code and payload.code != vendor.code:
            existing = db.scalars(
                select(InventoryVendor).where(
                    InventoryVendor.school_id == school_id,
                    InventoryVendor.code == payload.code,
                    InventoryVendor.id != vendor_id,
                    InventoryVendor.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Inventory Vendor with code", payload.code)
            vendor.code = payload.code

        if payload.name is not None:
            vendor.name = payload.name
        if payload.contact_name is not None:
            vendor.contact_name = payload.contact_name
        if payload.email is not None:
            vendor.email = payload.email
        if payload.phone is not None:
            vendor.phone = payload.phone
        if payload.address is not None:
            vendor.address = payload.address
        if payload.tax_id is not None:
            vendor.tax_id = payload.tax_id
        if payload.is_active is not None:
            vendor.is_active = payload.is_active

        db.commit()
        db.refresh(vendor)
        return vendor

    def delete_vendor(
        self,
        db: Session,
        school_id: UUID,
        vendor_id: UUID,
    ) -> None:
        vendor = self.get_vendor(db, school_id, vendor_id)

        # Check for referencing assets
        referencing_assets = db.scalars(
            select(PhysicalAsset).where(
                PhysicalAsset.vendor_id == vendor_id,
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.is_deleted.is_(False),
            )
        ).first()
        if referencing_assets:
            raise BadRequestException("Cannot delete vendor with associated physical assets.")

        vendor.is_deleted = True
        vendor.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 4. INVENTORY ITEMS (CATALOG)
    # =========================================================================

    def create_item(
        self,
        db: Session,
        school_id: UUID,
        payload: InventoryItemCreate,
    ) -> InventoryItem:
        # Validate category belongs to this school
        category = db.scalars(
            select(InventoryCategory).where(
                InventoryCategory.id == payload.category_id,
                InventoryCategory.school_id == school_id,
                InventoryCategory.is_deleted.is_(False),
            )
        ).first()
        if not category:
            raise NotFoundException("Inventory Category", str(payload.category_id))

        existing = db.scalars(
            select(InventoryItem).where(
                InventoryItem.school_id == school_id,
                InventoryItem.item_code == payload.item_code,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise AlreadyExistsException("Inventory Item with code", payload.item_code)

        item = InventoryItem(
            school_id=school_id,
            category_id=payload.category_id,
            item_code=payload.item_code,
            name=payload.name,
            description=payload.description,
            item_type=payload.item_type,
            unit_of_measure=payload.unit_of_measure,
            track_individually=payload.track_individually,
            reorder_level=payload.reorder_level,
            is_active=payload.is_active,
        )
        db.add(item)
        db.commit()
        db.refresh(item)
        return item

    def get_item(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID,
    ) -> InventoryItem:
        item = db.scalars(
            select(InventoryItem)
            .options(selectinload(InventoryItem.category))
            .where(
                InventoryItem.id == item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(item_id))
        return item

    def list_items(
        self,
        db: Session,
        school_id: UUID,
        category_id: UUID | None = None,
        item_type: InventoryItemType | None = None,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InventoryItem], int, int]:
        query = (
            select(InventoryItem)
            .options(selectinload(InventoryItem.category))
            .where(
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        )
        if category_id is not None:
            query = query.where(InventoryItem.category_id == category_id)
        if item_type is not None:
            query = query.where(InventoryItem.item_type == item_type)
        if is_active is not None:
            query = query.where(InventoryItem.is_active == is_active)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InventoryItem.name.ilike(term),
                    InventoryItem.item_code.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(InventoryItem.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_item(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID,
        payload: InventoryItemUpdate,
    ) -> InventoryItem:
        item = self.get_item(db, school_id, item_id)

        if payload.category_id:
            category = db.scalars(
                select(InventoryCategory).where(
                    InventoryCategory.id == payload.category_id,
                    InventoryCategory.school_id == school_id,
                    InventoryCategory.is_deleted.is_(False),
                )
            ).first()
            if not category:
                raise NotFoundException("Inventory Category", str(payload.category_id))
            item.category_id = payload.category_id

        if payload.item_code and payload.item_code != item.item_code:
            existing = db.scalars(
                select(InventoryItem).where(
                    InventoryItem.school_id == school_id,
                    InventoryItem.item_code == payload.item_code,
                    InventoryItem.id != item_id,
                    InventoryItem.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Inventory Item with code", payload.item_code)
            item.item_code = payload.item_code

        if payload.name is not None:
            item.name = payload.name
        if payload.description is not None:
            item.description = payload.description
        if payload.item_type is not None:
            item.item_type = payload.item_type
        if payload.unit_of_measure is not None:
            item.unit_of_measure = payload.unit_of_measure
        if payload.track_individually is not None:
            item.track_individually = payload.track_individually
        if payload.reorder_level is not None:
            item.reorder_level = payload.reorder_level
        if payload.is_active is not None:
            item.is_active = payload.is_active

        db.commit()
        db.refresh(item)
        return item

    def delete_item(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID,
    ) -> None:
        item = self.get_item(db, school_id, item_id)

        # Check for active stock balances
        active_stock = db.scalars(
            select(InventoryStock).where(
                InventoryStock.item_id == item_id,
                InventoryStock.school_id == school_id,
                InventoryStock.quantity > 0,
                InventoryStock.is_deleted.is_(False),
            )
        ).first()
        if active_stock:
            raise BadRequestException("Cannot delete item with active stock balances.")

        # Check for active physical assets
        active_assets = db.scalars(
            select(PhysicalAsset).where(
                PhysicalAsset.item_id == item_id,
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.is_deleted.is_(False),
            )
        ).first()
        if active_assets:
            raise BadRequestException("Cannot delete item with associated physical assets.")

        item.is_deleted = True
        item.deleted_at = datetime.now(timezone.utc)
        db.commit()

    # =========================================================================
    # 5. STOCK VISIBILITY & QUERIES
    # =========================================================================

    def list_stock(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID | None = None,
        location_id: UUID | None = None,
        category_id: UUID | None = None,
        low_stock: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InventoryStock], int, int]:
        query = (
            select(InventoryStock)
            .join(InventoryItem, InventoryStock.item_id == InventoryItem.id)
            .options(
                selectinload(InventoryStock.item).selectinload(InventoryItem.category),
                selectinload(InventoryStock.location),
            )
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
                InventoryItem.is_deleted.is_(False),
            )
        )

        if item_id is not None:
            query = query.where(InventoryStock.item_id == item_id)
        if location_id is not None:
            query = query.where(InventoryStock.location_id == location_id)
        if category_id is not None:
            query = query.where(InventoryItem.category_id == category_id)
        if low_stock is True:
            query = query.where(InventoryStock.quantity <= InventoryItem.reorder_level)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    InventoryItem.name.ilike(term),
                    InventoryItem.item_code.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(InventoryItem.name.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def get_stock(
        self,
        db: Session,
        school_id: UUID,
        stock_id: UUID,
    ) -> InventoryStock:
        stock = db.scalars(
            select(InventoryStock)
            .options(
                selectinload(InventoryStock.item).selectinload(InventoryItem.category),
                selectinload(InventoryStock.location),
            )
            .where(
                InventoryStock.id == stock_id,
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
            )
        ).first()
        if not stock:
            raise NotFoundException("Inventory Stock", str(stock_id))
        return stock

    def get_stock_by_item(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID,
    ) -> list[InventoryStock]:
        stocks = db.scalars(
            select(InventoryStock)
            .options(
                selectinload(InventoryStock.item),
                selectinload(InventoryStock.location),
            )
            .where(
                InventoryStock.item_id == item_id,
                InventoryStock.school_id == school_id,
                InventoryStock.is_deleted.is_(False),
            )
            .order_by(InventoryStock.quantity.desc())
        ).all()
        return list(stocks)

    def get_stock_summary(
        self,
        db: Session,
        school_id: UUID,
    ) -> InventoryStockSummaryResponse:
        total_items = (
            db.scalar(
                select(func.count(InventoryItem.id)).where(
                    InventoryItem.school_id == school_id,
                    InventoryItem.is_deleted.is_(False),
                )
            )
            or 0
        )

        total_stock_units = (
            db.scalar(
                select(func.coalesce(func.sum(InventoryStock.quantity), 0)).where(
                    InventoryStock.school_id == school_id,
                    InventoryStock.is_deleted.is_(False),
                )
            )
            or 0
        )

        total_locations = (
            db.scalar(
                select(func.count(InventoryLocation.id)).where(
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            )
            or 0
        )

        # Low stock query: item quantity <= reorder_level
        low_stock_count = (
            db.scalar(
                select(func.count(InventoryStock.id))
                .join(InventoryItem, InventoryStock.item_id == InventoryItem.id)
                .where(
                    InventoryStock.school_id == school_id,
                    InventoryStock.is_deleted.is_(False),
                    InventoryItem.is_deleted.is_(False),
                    InventoryStock.quantity <= InventoryItem.reorder_level,
                    InventoryStock.quantity > 0,
                )
            )
            or 0
        )

        out_of_stock_count = (
            db.scalar(
                select(func.count(InventoryStock.id)).where(
                    InventoryStock.school_id == school_id,
                    InventoryStock.is_deleted.is_(False),
                    InventoryStock.quantity == 0,
                )
            )
            or 0
        )

        return InventoryStockSummaryResponse(
            total_items=total_items,
            total_stock_units=int(total_stock_units),
            total_locations=total_locations,
            low_stock_items_count=low_stock_count,
            out_of_stock_items_count=out_of_stock_count,
        )

    # =========================================================================
    # 6. STOCK LEDGER MUTATIONS (TRANSACTIONAL + CONCURRENCY SAFE)
    # =========================================================================

    def receive_stock(
        self,
        db: Session,
        school_id: UUID,
        payload: StockReceiveRequest,
        performed_by_user_id: UUID | None = None,
    ) -> InventoryStock:
        if payload.quantity <= 0:
            raise ValidationException("Receipt quantity must be greater than 0.")

        # Idempotency check: if reference_number provided, check if already recorded
        if payload.reference_number:
            existing_movement = db.scalars(
                select(InventoryStockMovement).where(
                    InventoryStockMovement.school_id == school_id,
                    InventoryStockMovement.reference_number == payload.reference_number,
                    InventoryStockMovement.movement_type == InventoryStockMovementType.PURCHASE_RECEIPT,
                )
            ).first()
            if existing_movement:
                # Return the corresponding stock record
                existing_stock = db.scalars(
                    select(InventoryStock)
                    .options(
                        selectinload(InventoryStock.item),
                        selectinload(InventoryStock.location),
                    )
                    .where(
                        InventoryStock.item_id == payload.item_id,
                        InventoryStock.location_id == payload.location_id,
                        InventoryStock.school_id == school_id,
                    )
                ).first()
                if existing_stock:
                    return existing_stock

        # Validate item
        item = db.scalars(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(payload.item_id))

        # Validate destination location
        location = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == payload.location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not location:
            raise NotFoundException("Inventory Location", str(payload.location_id))

        # Validate vendor if provided
        if payload.vendor_id:
            vendor = db.scalars(
                select(InventoryVendor).where(
                    InventoryVendor.id == payload.vendor_id,
                    InventoryVendor.school_id == school_id,
                    InventoryVendor.is_deleted.is_(False),
                )
            ).first()
            if not vendor:
                raise NotFoundException("Inventory Vendor", str(payload.vendor_id))

        # Lock or create stock row
        stock = db.scalars(
            select(InventoryStock)
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.item_id == payload.item_id,
                InventoryStock.location_id == payload.location_id,
                InventoryStock.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()

        if not stock:
            stock = InventoryStock(
                school_id=school_id,
                item_id=payload.item_id,
                location_id=payload.location_id,
                quantity=payload.quantity,
                reserved_quantity=0,
                unit_price=payload.unit_price,
                last_counted_at=datetime.now(timezone.utc),
            )
            db.add(stock)
        else:
            stock.quantity += payload.quantity
            if payload.unit_price is not None:
                stock.unit_price = payload.unit_price
            stock.last_counted_at = datetime.now(timezone.utc)

        # Create immutable movement entry
        movement = InventoryStockMovement(
            school_id=school_id,
            item_id=payload.item_id,
            destination_location_id=payload.location_id,
            movement_type=InventoryStockMovementType.PURCHASE_RECEIPT,
            quantity=payload.quantity,
            unit_price=payload.unit_price,
            reference_number=payload.reference_number,
            vendor_id=payload.vendor_id,
            performed_by_user_id=performed_by_user_id,
            movement_date=datetime.now(timezone.utc),
            remarks=payload.remarks,
        )
        db.add(movement)

        db.commit()
        db.refresh(stock)
        return stock

    def issue_stock(
        self,
        db: Session,
        school_id: UUID,
        payload: StockIssueRequest,
        performed_by_user_id: UUID | None = None,
    ) -> InventoryStock:
        if payload.quantity <= 0:
            raise ValidationException("Issue quantity must be greater than 0.")

        # Idempotency check
        if payload.reference_number:
            existing_movement = db.scalars(
                select(InventoryStockMovement).where(
                    InventoryStockMovement.school_id == school_id,
                    InventoryStockMovement.reference_number == payload.reference_number,
                    InventoryStockMovement.movement_type == InventoryStockMovementType.ISSUE,
                )
            ).first()
            if existing_movement:
                existing_stock = db.scalars(
                    select(InventoryStock)
                    .options(
                        selectinload(InventoryStock.item),
                        selectinload(InventoryStock.location),
                    )
                    .where(
                        InventoryStock.item_id == payload.item_id,
                        InventoryStock.location_id == payload.location_id,
                        InventoryStock.school_id == school_id,
                    )
                ).first()
                if existing_stock:
                    return existing_stock

        # Validate item & location
        item = db.scalars(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(payload.item_id))

        location = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == payload.location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not location:
            raise NotFoundException("Inventory Location", str(payload.location_id))

        # Lock stock row
        stock = db.scalars(
            select(InventoryStock)
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.item_id == payload.item_id,
                InventoryStock.location_id == payload.location_id,
                InventoryStock.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()

        if not stock or stock.quantity < payload.quantity:
            available = stock.quantity if stock else 0
            raise BadRequestException(
                f"Insufficient stock available at specified location (Available: {available}, Requested: {payload.quantity})."
            )

        stock.quantity -= payload.quantity

        movement = InventoryStockMovement(
            school_id=school_id,
            item_id=payload.item_id,
            source_location_id=payload.location_id,
            movement_type=InventoryStockMovementType.ISSUE,
            quantity=payload.quantity,
            reference_number=payload.reference_number,
            performed_by_user_id=performed_by_user_id,
            movement_date=datetime.now(timezone.utc),
            remarks=payload.remarks,
        )
        db.add(movement)

        db.commit()
        db.refresh(stock)
        return stock

    def return_stock(
        self,
        db: Session,
        school_id: UUID,
        payload: StockReturnRequest,
        performed_by_user_id: UUID | None = None,
    ) -> InventoryStock:
        if payload.quantity <= 0:
            raise ValidationException("Return quantity must be greater than 0.")

        # Idempotency check
        if payload.reference_number:
            existing_movement = db.scalars(
                select(InventoryStockMovement).where(
                    InventoryStockMovement.school_id == school_id,
                    InventoryStockMovement.reference_number == payload.reference_number,
                    InventoryStockMovement.movement_type == InventoryStockMovementType.RETURN,
                )
            ).first()
            if existing_movement:
                existing_stock = db.scalars(
                    select(InventoryStock)
                    .options(
                        selectinload(InventoryStock.item),
                        selectinload(InventoryStock.location),
                    )
                    .where(
                        InventoryStock.item_id == payload.item_id,
                        InventoryStock.location_id == payload.location_id,
                        InventoryStock.school_id == school_id,
                    )
                ).first()
                if existing_stock:
                    return existing_stock

        item = db.scalars(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(payload.item_id))

        location = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == payload.location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not location:
            raise NotFoundException("Inventory Location", str(payload.location_id))

        stock = db.scalars(
            select(InventoryStock)
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.item_id == payload.item_id,
                InventoryStock.location_id == payload.location_id,
                InventoryStock.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()

        if not stock:
            stock = InventoryStock(
                school_id=school_id,
                item_id=payload.item_id,
                location_id=payload.location_id,
                quantity=payload.quantity,
                reserved_quantity=0,
                last_counted_at=datetime.now(timezone.utc),
            )
            db.add(stock)
        else:
            stock.quantity += payload.quantity

        movement = InventoryStockMovement(
            school_id=school_id,
            item_id=payload.item_id,
            destination_location_id=payload.location_id,
            movement_type=InventoryStockMovementType.RETURN,
            quantity=payload.quantity,
            reference_number=payload.reference_number,
            performed_by_user_id=performed_by_user_id,
            movement_date=datetime.now(timezone.utc),
            remarks=payload.remarks,
        )
        db.add(movement)

        db.commit()
        db.refresh(stock)
        return stock

    def adjust_stock(
        self,
        db: Session,
        school_id: UUID,
        payload: StockAdjustmentRequest,
        performed_by_user_id: UUID | None = None,
    ) -> InventoryStock:
        if payload.quantity <= 0:
            raise ValidationException("Adjustment quantity must be greater than 0.")
        if not payload.reason or not payload.reason.strip():
            raise ValidationException("Adjustment reason is mandatory.")

        item = db.scalars(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(payload.item_id))

        location = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == payload.location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not location:
            raise NotFoundException("Inventory Location", str(payload.location_id))

        stock = db.scalars(
            select(InventoryStock)
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.item_id == payload.item_id,
                InventoryStock.location_id == payload.location_id,
                InventoryStock.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()

        if payload.adjustment_type == "SUBTRACT":
            if not stock or stock.quantity < payload.quantity:
                available = stock.quantity if stock else 0
                raise BadRequestException(
                    f"Cannot adjust stock below 0. Available: {available}, subtraction requested: {payload.quantity}."
                )
            stock.quantity -= payload.quantity
            source_loc = payload.location_id
            dest_loc = None
        else:  # ADD
            if not stock:
                stock = InventoryStock(
                    school_id=school_id,
                    item_id=payload.item_id,
                    location_id=payload.location_id,
                    quantity=payload.quantity,
                    reserved_quantity=0,
                    last_counted_at=datetime.now(timezone.utc),
                )
                db.add(stock)
            else:
                stock.quantity += payload.quantity
            source_loc = None
            dest_loc = payload.location_id

        movement = InventoryStockMovement(
            school_id=school_id,
            item_id=payload.item_id,
            source_location_id=source_loc,
            destination_location_id=dest_loc,
            movement_type=InventoryStockMovementType.ADJUSTMENT,
            quantity=payload.quantity,
            reference_number=payload.reference_number,
            performed_by_user_id=performed_by_user_id,
            movement_date=datetime.now(timezone.utc),
            remarks=f"[{payload.adjustment_type}] {payload.reason.strip()}",
        )
        db.add(movement)

        db.commit()
        db.refresh(stock)
        return stock

    def transfer_stock(
        self,
        db: Session,
        school_id: UUID,
        payload: StockTransferRequest,
        performed_by_user_id: UUID | None = None,
    ) -> InventoryStock:
        if payload.quantity <= 0:
            raise ValidationException("Transfer quantity must be greater than 0.")
        if payload.source_location_id == payload.destination_location_id:
            raise BadRequestException("Source and destination locations cannot be identical.")

        # Validate item & both locations
        item = db.scalars(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(payload.item_id))

        src_loc = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == payload.source_location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not src_loc:
            raise NotFoundException("Source Location", str(payload.source_location_id))

        dst_loc = db.scalars(
            select(InventoryLocation).where(
                InventoryLocation.id == payload.destination_location_id,
                InventoryLocation.school_id == school_id,
                InventoryLocation.is_deleted.is_(False),
            )
        ).first()
        if not dst_loc:
            raise NotFoundException("Destination Location", str(payload.destination_location_id))

        # Lock source stock
        src_stock = db.scalars(
            select(InventoryStock)
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.item_id == payload.item_id,
                InventoryStock.location_id == payload.source_location_id,
                InventoryStock.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()

        if not src_stock or src_stock.quantity < payload.quantity:
            available = src_stock.quantity if src_stock else 0
            raise BadRequestException(
                f"Insufficient stock in source location for transfer (Available: {available}, Transfer: {payload.quantity})."
            )

        # Lock or create destination stock
        dst_stock = db.scalars(
            select(InventoryStock)
            .where(
                InventoryStock.school_id == school_id,
                InventoryStock.item_id == payload.item_id,
                InventoryStock.location_id == payload.destination_location_id,
                InventoryStock.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()

        if not dst_stock:
            dst_stock = InventoryStock(
                school_id=school_id,
                item_id=payload.item_id,
                location_id=payload.destination_location_id,
                quantity=payload.quantity,
                reserved_quantity=0,
                unit_price=src_stock.unit_price,
                last_counted_at=datetime.now(timezone.utc),
            )
            db.add(dst_stock)
        else:
            dst_stock.quantity += payload.quantity

        src_stock.quantity -= payload.quantity

        # Create movement record
        movement = InventoryStockMovement(
            school_id=school_id,
            item_id=payload.item_id,
            source_location_id=payload.source_location_id,
            destination_location_id=payload.destination_location_id,
            movement_type=InventoryStockMovementType.TRANSFER,
            quantity=payload.quantity,
            unit_price=src_stock.unit_price,
            reference_number=payload.reference_number,
            performed_by_user_id=performed_by_user_id,
            movement_date=datetime.now(timezone.utc),
            remarks=payload.remarks,
        )
        db.add(movement)

        db.commit()
        db.refresh(src_stock)
        return src_stock

    # =========================================================================
    # 7. MOVEMENT HISTORY (AUDIT TRAIL)
    # =========================================================================

    def list_movements(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID | None = None,
        source_location_id: UUID | None = None,
        destination_location_id: UUID | None = None,
        movement_type: InventoryStockMovementType | None = None,
        reference_number: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[InventoryStockMovement], int, int]:
        query = (
            select(InventoryStockMovement)
            .options(
                selectinload(InventoryStockMovement.item),
                selectinload(InventoryStockMovement.source_location),
                selectinload(InventoryStockMovement.destination_location),
                selectinload(InventoryStockMovement.vendor),
            )
            .where(
                InventoryStockMovement.school_id == school_id,
                InventoryStockMovement.is_deleted.is_(False),
            )
        )
        if item_id is not None:
            query = query.where(InventoryStockMovement.item_id == item_id)
        if source_location_id is not None:
            query = query.where(InventoryStockMovement.source_location_id == source_location_id)
        if destination_location_id is not None:
            query = query.where(InventoryStockMovement.destination_location_id == destination_location_id)
        if movement_type is not None:
            query = query.where(InventoryStockMovement.movement_type == movement_type)
        if reference_number is not None:
            query = query.where(InventoryStockMovement.reference_number == reference_number)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(InventoryStockMovement.movement_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def get_movement(
        self,
        db: Session,
        school_id: UUID,
        movement_id: UUID,
    ) -> InventoryStockMovement:
        movement = db.scalars(
            select(InventoryStockMovement)
            .options(
                selectinload(InventoryStockMovement.item),
                selectinload(InventoryStockMovement.source_location),
                selectinload(InventoryStockMovement.destination_location),
                selectinload(InventoryStockMovement.vendor),
            )
            .where(
                InventoryStockMovement.id == movement_id,
                InventoryStockMovement.school_id == school_id,
                InventoryStockMovement.is_deleted.is_(False),
            )
        ).first()
        if not movement:
            raise NotFoundException("Stock Movement", str(movement_id))
        return movement

    # =========================================================================
    # 8. PHYSICAL ASSETS
    # =========================================================================

    def create_asset(
        self,
        db: Session,
        school_id: UUID,
        payload: PhysicalAssetCreate,
    ) -> PhysicalAsset:
        item = db.scalars(
            select(InventoryItem).where(
                InventoryItem.id == payload.item_id,
                InventoryItem.school_id == school_id,
                InventoryItem.is_deleted.is_(False),
            )
        ).first()
        if not item:
            raise NotFoundException("Inventory Item", str(payload.item_id))

        if payload.location_id:
            loc = db.scalars(
                select(InventoryLocation).where(
                    InventoryLocation.id == payload.location_id,
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            ).first()
            if not loc:
                raise NotFoundException("Inventory Location", str(payload.location_id))

        if payload.vendor_id:
            vendor = db.scalars(
                select(InventoryVendor).where(
                    InventoryVendor.id == payload.vendor_id,
                    InventoryVendor.school_id == school_id,
                    InventoryVendor.is_deleted.is_(False),
                )
            ).first()
            if not vendor:
                raise NotFoundException("Inventory Vendor", str(payload.vendor_id))

        existing_tag = db.scalars(
            select(PhysicalAsset).where(
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.asset_tag == payload.asset_tag,
                PhysicalAsset.is_deleted.is_(False),
            )
        ).first()
        if existing_tag:
            raise AlreadyExistsException("Physical Asset with tag", payload.asset_tag)

        asset = PhysicalAsset(
            school_id=school_id,
            item_id=payload.item_id,
            location_id=payload.location_id,
            vendor_id=payload.vendor_id,
            asset_tag=payload.asset_tag,
            serial_number=payload.serial_number,
            model_number=payload.model_number,
            status=payload.status,
            condition=payload.condition,
            purchase_date=payload.purchase_date,
            purchase_cost=payload.purchase_cost,
            warranty_expiry_date=payload.warranty_expiry_date,
            notes=payload.notes,
        )
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset

    def get_asset(
        self,
        db: Session,
        school_id: UUID,
        asset_id: UUID,
    ) -> PhysicalAsset:
        asset = db.scalars(
            select(PhysicalAsset)
            .options(
                selectinload(PhysicalAsset.item),
                selectinload(PhysicalAsset.location),
                selectinload(PhysicalAsset.vendor),
            )
            .where(
                PhysicalAsset.id == asset_id,
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.is_deleted.is_(False),
            )
        ).first()
        if not asset:
            raise NotFoundException("Physical Asset", str(asset_id))
        return asset

    def list_assets(
        self,
        db: Session,
        school_id: UUID,
        item_id: UUID | None = None,
        location_id: UUID | None = None,
        vendor_id: UUID | None = None,
        status: AssetStatus | None = None,
        condition: AssetCondition | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[PhysicalAsset], int, int]:
        query = (
            select(PhysicalAsset)
            .options(
                selectinload(PhysicalAsset.item),
                selectinload(PhysicalAsset.location),
                selectinload(PhysicalAsset.vendor),
            )
            .where(
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.is_deleted.is_(False),
            )
        )
        if item_id is not None:
            query = query.where(PhysicalAsset.item_id == item_id)
        if location_id is not None:
            query = query.where(PhysicalAsset.location_id == location_id)
        if vendor_id is not None:
            query = query.where(PhysicalAsset.vendor_id == vendor_id)
        if status is not None:
            query = query.where(PhysicalAsset.status == status)
        if condition is not None:
            query = query.where(PhysicalAsset.condition == condition)
        if search:
            term = f"%{search.strip()}%"
            query = query.where(
                or_(
                    PhysicalAsset.asset_tag.ilike(term),
                    PhysicalAsset.serial_number.ilike(term),
                    PhysicalAsset.model_number.ilike(term),
                )
            )

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(PhysicalAsset.asset_tag.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def update_asset(
        self,
        db: Session,
        school_id: UUID,
        asset_id: UUID,
        payload: PhysicalAssetUpdate,
    ) -> PhysicalAsset:
        asset = self.get_asset(db, school_id, asset_id)

        if payload.location_id:
            loc = db.scalars(
                select(InventoryLocation).where(
                    InventoryLocation.id == payload.location_id,
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            ).first()
            if not loc:
                raise NotFoundException("Inventory Location", str(payload.location_id))
            asset.location_id = payload.location_id
        elif payload.location_id is None and "location_id" in payload.model_fields_set:
            asset.location_id = None

        if payload.vendor_id:
            vendor = db.scalars(
                select(InventoryVendor).where(
                    InventoryVendor.id == payload.vendor_id,
                    InventoryVendor.school_id == school_id,
                    InventoryVendor.is_deleted.is_(False),
                )
            ).first()
            if not vendor:
                raise NotFoundException("Inventory Vendor", str(payload.vendor_id))
            asset.vendor_id = payload.vendor_id
        elif payload.vendor_id is None and "vendor_id" in payload.model_fields_set:
            asset.vendor_id = None

        if payload.asset_tag and payload.asset_tag != asset.asset_tag:
            existing = db.scalars(
                select(PhysicalAsset).where(
                    PhysicalAsset.school_id == school_id,
                    PhysicalAsset.asset_tag == payload.asset_tag,
                    PhysicalAsset.id != asset_id,
                    PhysicalAsset.is_deleted.is_(False),
                )
            ).first()
            if existing:
                raise AlreadyExistsException("Physical Asset with tag", payload.asset_tag)
            asset.asset_tag = payload.asset_tag

        if payload.serial_number is not None:
            asset.serial_number = payload.serial_number
        if payload.model_number is not None:
            asset.model_number = payload.model_number
        if payload.condition is not None:
            asset.condition = payload.condition
        if payload.purchase_date is not None:
            asset.purchase_date = payload.purchase_date
        if payload.purchase_cost is not None:
            asset.purchase_cost = payload.purchase_cost
        if payload.warranty_expiry_date is not None:
            asset.warranty_expiry_date = payload.warranty_expiry_date
        if payload.notes is not None:
            asset.notes = payload.notes

        # Status update lifecycle check
        if payload.status is not None and payload.status != asset.status:
            if payload.status == AssetStatus.ASSIGNED:
                raise BadRequestException("Cannot manually change status to ASSIGNED. Use asset assignment endpoint.")
            if asset.status == AssetStatus.ASSIGNED and payload.status != AssetStatus.ASSIGNED:
                # Must return assignment first
                active_assign = db.scalars(
                    select(AssetAssignment).where(
                        AssetAssignment.asset_id == asset_id,
                        AssetAssignment.school_id == school_id,
                        AssetAssignment.status == AssetAssignmentStatus.ACTIVE,
                        AssetAssignment.is_deleted.is_(False),
                    )
                ).first()
                if active_assign:
                    raise BadRequestException("Cannot change status of currently assigned asset. Return the assignment first.")
            asset.status = payload.status

        db.commit()
        db.refresh(asset)
        return asset

    def delete_asset(
        self,
        db: Session,
        school_id: UUID,
        asset_id: UUID,
    ) -> None:
        asset = self.get_asset(db, school_id, asset_id)

        active_assign = db.scalars(
            select(AssetAssignment).where(
                AssetAssignment.asset_id == asset_id,
                AssetAssignment.school_id == school_id,
                AssetAssignment.status == AssetAssignmentStatus.ACTIVE,
                AssetAssignment.is_deleted.is_(False),
            )
        ).first()
        if active_assign:
            raise BadRequestException("Cannot delete asset with an active assignment. Return the asset first.")

        asset.is_deleted = True
        asset.deleted_at = datetime.now(timezone.utc)
        db.commit()

    def retire_asset(
        self,
        db: Session,
        school_id: UUID,
        asset_id: UUID,
        payload: PhysicalAssetRetireRequest,
    ) -> PhysicalAsset:
        asset = self.get_asset(db, school_id, asset_id)

        if asset.status == AssetStatus.ASSIGNED:
            raise BadRequestException("Cannot retire or dispose an assigned asset. Return the assignment first.")

        if payload.status not in [AssetStatus.RETIRED, AssetStatus.DISPOSED]:
            raise BadRequestException("Retirement status must be RETIRED or DISPOSED.")

        asset.status = payload.status
        if payload.notes:
            asset.notes = f"{asset.notes or ''}\n[RETIRED/DISPOSED] {payload.notes}".strip()

        db.commit()
        db.refresh(asset)
        return asset

    # =========================================================================
    # 9. ASSET ASSIGNMENT LIFECYCLE
    # =========================================================================

    def assign_asset(
        self,
        db: Session,
        school_id: UUID,
        payload: AssetAssignmentCreate,
        assigned_by_user_id: UUID | None = None,
    ) -> AssetAssignment:
        asset = db.scalars(
            select(PhysicalAsset)
            .where(
                PhysicalAsset.id == payload.asset_id,
                PhysicalAsset.school_id == school_id,
                PhysicalAsset.is_deleted.is_(False),
            )
            .with_for_update()
        ).first()
        if not asset:
            raise NotFoundException("Physical Asset", str(payload.asset_id))

        if asset.status != AssetStatus.AVAILABLE:
            raise BadRequestException(f"Asset is not available for assignment (current status: {asset.status.value}).")

        # Check existing active assignment
        existing = db.scalars(
            select(AssetAssignment).where(
                AssetAssignment.asset_id == payload.asset_id,
                AssetAssignment.school_id == school_id,
                AssetAssignment.status == AssetAssignmentStatus.ACTIVE,
                AssetAssignment.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise BadRequestException("Asset already has an active assignment.")

        # Validate target according to assignment_type
        if payload.assignment_type == AssetAssignmentType.STAFF:
            if payload.teacher_id:
                teacher = db.scalars(
                    select(Teacher).where(
                        Teacher.id == payload.teacher_id,
                        Teacher.school_id == school_id,
                        Teacher.is_deleted.is_(False),
                    )
                ).first()
                if not teacher:
                    raise NotFoundException("Teacher", str(payload.teacher_id))
            elif payload.user_id:
                user = db.scalars(
                    select(IdentityUser).where(
                        IdentityUser.id == payload.user_id,
                        IdentityUser.school_id == school_id,
                        IdentityUser.is_deleted.is_(False),
                    )
                ).first()
                if not user:
                    raise NotFoundException("User", str(payload.user_id))
            else:
                raise ValidationException("STAFF assignment requires teacher_id or user_id.")

        elif payload.assignment_type == AssetAssignmentType.STUDENT:
            if not payload.student_id:
                raise ValidationException("STUDENT assignment requires student_id.")
            student = db.scalars(
                select(Student).where(
                    Student.id == payload.student_id,
                    Student.school_id == school_id,
                    Student.is_deleted.is_(False),
                )
            ).first()
            if not student:
                raise NotFoundException("Student", str(payload.student_id))

        elif payload.assignment_type == AssetAssignmentType.CLASSROOM:
            if not payload.classroom_id:
                raise ValidationException("CLASSROOM assignment requires classroom_id.")
            classroom = db.scalars(
                select(Classroom).where(
                    Classroom.id == payload.classroom_id,
                    Classroom.school_id == school_id,
                    Classroom.is_deleted.is_(False),
                )
            ).first()
            if not classroom:
                raise NotFoundException("Classroom", str(payload.classroom_id))

        assignment = AssetAssignment(
            school_id=school_id,
            asset_id=payload.asset_id,
            assignment_type=payload.assignment_type,
            teacher_id=payload.teacher_id,
            student_id=payload.student_id,
            classroom_id=payload.classroom_id,
            user_id=payload.user_id,
            department_name=payload.department_name,
            assigned_date=payload.assigned_date,
            expected_return_date=payload.expected_return_date,
            assigned_by_user_id=assigned_by_user_id,
            status=AssetAssignmentStatus.ACTIVE,
            condition_on_assignment=payload.condition_on_assignment,
            remarks=payload.remarks,
        )
        asset.status = AssetStatus.ASSIGNED
        asset.condition = payload.condition_on_assignment

        db.add(assignment)
        db.commit()
        db.refresh(assignment)
        return assignment

    def return_asset(
        self,
        db: Session,
        school_id: UUID,
        assignment_id: UUID,
        payload: AssetAssignmentReturnRequest,
        received_by_user_id: UUID | None = None,
    ) -> AssetAssignment:
        assignment = db.scalars(
            select(AssetAssignment)
            .options(selectinload(AssetAssignment.asset))
            .where(
                AssetAssignment.id == assignment_id,
                AssetAssignment.school_id == school_id,
                AssetAssignment.is_deleted.is_(False),
            )
        ).first()
        if not assignment:
            raise NotFoundException("Asset Assignment", str(assignment_id))

        if assignment.status != AssetAssignmentStatus.ACTIVE:
            raise BadRequestException(f"Assignment is not active (current status: {assignment.status.value}).")

        assignment.status = AssetAssignmentStatus.RETURNED
        assignment.actual_return_date = payload.actual_return_date
        assignment.condition_on_return = payload.condition_on_return
        if payload.remarks:
            assignment.remarks = f"{assignment.remarks or ''}\n[RETURN] {payload.remarks}".strip()

        # Update physical asset
        asset = assignment.asset
        asset.condition = payload.condition_on_return
        if payload.condition_on_return == AssetCondition.DAMAGED:
            asset.status = AssetStatus.DAMAGED
        else:
            asset.status = AssetStatus.AVAILABLE

        if payload.return_location_id:
            loc = db.scalars(
                select(InventoryLocation).where(
                    InventoryLocation.id == payload.return_location_id,
                    InventoryLocation.school_id == school_id,
                    InventoryLocation.is_deleted.is_(False),
                )
            ).first()
            if not loc:
                raise NotFoundException("Inventory Location", str(payload.return_location_id))
            asset.location_id = payload.return_location_id

        db.commit()
        db.refresh(assignment)
        return assignment

    def transfer_asset_assignment(
        self,
        db: Session,
        school_id: UUID,
        assignment_id: UUID,
        payload: AssetAssignmentTransferRequest,
        performed_by_user_id: UUID | None = None,
    ) -> AssetAssignment:
        assignment = db.scalars(
            select(AssetAssignment)
            .options(selectinload(AssetAssignment.asset))
            .where(
                AssetAssignment.id == assignment_id,
                AssetAssignment.school_id == school_id,
                AssetAssignment.is_deleted.is_(False),
            )
        ).first()
        if not assignment:
            raise NotFoundException("Asset Assignment", str(assignment_id))

        if assignment.status != AssetAssignmentStatus.ACTIVE:
            raise BadRequestException(f"Cannot transfer an inactive assignment (current status: {assignment.status.value}).")

        # Validate new target
        if payload.new_assignment_type == AssetAssignmentType.STAFF:
            if payload.new_teacher_id:
                teacher = db.scalars(
                    select(Teacher).where(
                        Teacher.id == payload.new_teacher_id,
                        Teacher.school_id == school_id,
                        Teacher.is_deleted.is_(False),
                    )
                ).first()
                if not teacher:
                    raise NotFoundException("Teacher", str(payload.new_teacher_id))
            elif payload.new_user_id:
                user = db.scalars(
                    select(IdentityUser).where(
                        IdentityUser.id == payload.new_user_id,
                        IdentityUser.school_id == school_id,
                        IdentityUser.is_deleted.is_(False),
                    )
                ).first()
                if not user:
                    raise NotFoundException("User", str(payload.new_user_id))
            else:
                raise ValidationException("STAFF assignment requires new_teacher_id or new_user_id.")

        elif payload.new_assignment_type == AssetAssignmentType.STUDENT:
            if not payload.new_student_id:
                raise ValidationException("STUDENT assignment requires new_student_id.")
            student = db.scalars(
                select(Student).where(
                    Student.id == payload.new_student_id,
                    Student.school_id == school_id,
                    Student.is_deleted.is_(False),
                )
            ).first()
            if not student:
                raise NotFoundException("Student", str(payload.new_student_id))

        elif payload.new_assignment_type == AssetAssignmentType.CLASSROOM:
            if not payload.new_classroom_id:
                raise ValidationException("CLASSROOM assignment requires new_classroom_id.")
            classroom = db.scalars(
                select(Classroom).where(
                    Classroom.id == payload.new_classroom_id,
                    Classroom.school_id == school_id,
                    Classroom.is_deleted.is_(False),
                )
            ).first()
            if not classroom:
                raise NotFoundException("Classroom", str(payload.new_classroom_id))

        # Close previous assignment
        assignment.status = AssetAssignmentStatus.TRANSFERRED
        assignment.actual_return_date = payload.transfer_date
        assignment.condition_on_return = payload.condition

        # Create new assignment
        new_assignment = AssetAssignment(
            school_id=school_id,
            asset_id=assignment.asset_id,
            assignment_type=payload.new_assignment_type,
            teacher_id=payload.new_teacher_id,
            student_id=payload.new_student_id,
            classroom_id=payload.new_classroom_id,
            user_id=payload.new_user_id,
            department_name=payload.new_department_name,
            assigned_date=payload.transfer_date,
            assigned_by_user_id=performed_by_user_id,
            status=AssetAssignmentStatus.ACTIVE,
            condition_on_assignment=payload.condition,
            remarks=payload.remarks,
        )
        db.add(new_assignment)

        asset = assignment.asset
        asset.condition = payload.condition
        asset.status = AssetStatus.ASSIGNED

        db.commit()
        db.refresh(new_assignment)
        return new_assignment

    def get_assignment(
        self,
        db: Session,
        school_id: UUID,
        assignment_id: UUID,
    ) -> AssetAssignment:
        assignment = db.scalars(
            select(AssetAssignment)
            .options(
                selectinload(AssetAssignment.asset),
                selectinload(AssetAssignment.teacher),
                selectinload(AssetAssignment.student),
                selectinload(AssetAssignment.classroom),
            )
            .where(
                AssetAssignment.id == assignment_id,
                AssetAssignment.school_id == school_id,
                AssetAssignment.is_deleted.is_(False),
            )
        ).first()
        if not assignment:
            raise NotFoundException("Asset Assignment", str(assignment_id))
        return assignment

    def list_assignments(
        self,
        db: Session,
        school_id: UUID,
        asset_id: UUID | None = None,
        assignment_type: AssetAssignmentType | None = None,
        status: AssetAssignmentStatus | None = None,
        teacher_id: UUID | None = None,
        student_id: UUID | None = None,
        classroom_id: UUID | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[AssetAssignment], int, int]:
        query = (
            select(AssetAssignment)
            .options(
                selectinload(AssetAssignment.asset),
                selectinload(AssetAssignment.teacher),
                selectinload(AssetAssignment.student),
                selectinload(AssetAssignment.classroom),
            )
            .where(
                AssetAssignment.school_id == school_id,
                AssetAssignment.is_deleted.is_(False),
            )
        )
        if asset_id is not None:
            query = query.where(AssetAssignment.asset_id == asset_id)
        if assignment_type is not None:
            query = query.where(AssetAssignment.assignment_type == assignment_type)
        if status is not None:
            query = query.where(AssetAssignment.status == status)
        if teacher_id is not None:
            query = query.where(AssetAssignment.teacher_id == teacher_id)
        if student_id is not None:
            query = query.where(AssetAssignment.student_id == student_id)
        if classroom_id is not None:
            query = query.where(AssetAssignment.classroom_id == classroom_id)

        total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
        total_pages = (total + page_size - 1) // page_size if total > 0 else 0

        items = db.scalars(
            query.order_by(AssetAssignment.assigned_date.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        ).all()

        return list(items), total, total_pages

    def get_asset_history(
        self,
        db: Session,
        school_id: UUID,
        asset_id: UUID,
    ) -> list[AssetAssignment]:
        # Validate asset
        self.get_asset(db, school_id, asset_id)
        assignments = db.scalars(
            select(AssetAssignment)
            .options(
                selectinload(AssetAssignment.asset),
                selectinload(AssetAssignment.teacher),
                selectinload(AssetAssignment.student),
                selectinload(AssetAssignment.classroom),
            )
            .where(
                AssetAssignment.asset_id == asset_id,
                AssetAssignment.school_id == school_id,
                AssetAssignment.is_deleted.is_(False),
            )
            .order_by(AssetAssignment.assigned_date.desc())
        ).all()
        return list(assignments)


inventory_service = InventoryService()
