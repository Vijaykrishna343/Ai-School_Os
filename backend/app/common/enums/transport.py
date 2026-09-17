from enum import Enum


class VehicleType(str, Enum):
    BUS = "BUS"
    VAN = "VAN"
    MINIBUS = "MINIBUS"
    AUTO = "AUTO"
    OTHER = "OTHER"


class VehicleStatus(str, Enum):
    ACTIVE = "ACTIVE"
    MAINTENANCE = "MAINTENANCE"
    DECOMMISSIONED = "DECOMMISSIONED"


class FuelType(str, Enum):
    DIESEL = "DIESEL"
    PETROL = "PETROL"
    CNG = "CNG"
    ELECTRIC = "ELECTRIC"
    HYBRID = "HYBRID"


class TransportAllocationType(str, Enum):
    TWO_WAY = "TWO_WAY"
    PICKUP_ONLY = "PICKUP_ONLY"
    DROP_ONLY = "DROP_ONLY"


class TransportAllocationStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    CANCELLED = "CANCELLED"
