from enum import Enum


class InventoryItemType(str, Enum):
    CONSUMABLE = "CONSUMABLE"
    ASSET = "ASSET"


class InventoryLocationType(str, Enum):
    WAREHOUSE = "WAREHOUSE"
    STORE_ROOM = "STORE_ROOM"
    LAB = "LAB"
    LIBRARY_STORE = "LIBRARY_STORE"
    OFFICE = "OFFICE"
    CLASSROOM = "CLASSROOM"
    SPORTS_ROOM = "SPORTS_ROOM"
    OTHER = "OTHER"


class InventoryStockMovementType(str, Enum):
    PURCHASE_RECEIPT = "PURCHASE_RECEIPT"
    ISSUE = "ISSUE"
    TRANSFER = "TRANSFER"
    RETURN = "RETURN"
    ADJUSTMENT = "ADJUSTMENT"
    DISCARD = "DISCARD"


class AssetStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    IN_REPAIR = "IN_REPAIR"
    DAMAGED = "DAMAGED"
    LOST = "LOST"
    RETIRED = "RETIRED"
    DISPOSED = "DISPOSED"


class AssetCondition(str, Enum):
    EXCELLENT = "EXCELLENT"
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    DAMAGED = "DAMAGED"


class AssetAssignmentType(str, Enum):
    STAFF = "STAFF"
    STUDENT = "STUDENT"
    CLASSROOM = "CLASSROOM"
    DEPARTMENT = "DEPARTMENT"
    LOCATION = "LOCATION"
    OTHER = "OTHER"


class AssetAssignmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RETURNED = "RETURNED"
    TRANSFERRED = "TRANSFERRED"
