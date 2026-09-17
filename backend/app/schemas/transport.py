from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.common.enums.transport import (
    FuelType,
    TransportAllocationStatus,
    TransportAllocationType,
    VehicleStatus,
    VehicleType,
)


# =============================================================================
# VEHICLE SCHEMAS
# =============================================================================

class VehicleCreate(BaseModel):
    """
    Payload for registering a transport vehicle.
    """
    registration_number: str = Field(..., min_length=1, max_length=50)
    vehicle_code: str = Field(..., min_length=1, max_length=50)
    vehicle_type: VehicleType = Field(default=VehicleType.BUS)
    seating_capacity: int = Field(..., gt=0)
    fuel_type: FuelType = Field(default=FuelType.DIESEL)
    insurance_expiry_date: date | None = Field(default=None)
    fitness_expiry_date: date | None = Field(default=None)
    gps_device_id: str | None = Field(default=None, max_length=100)
    status: VehicleStatus = Field(default=VehicleStatus.ACTIVE)
    description: str | None = Field(default=None, max_length=255)


class VehicleUpdate(BaseModel):
    """
    Payload for updating vehicle attributes.
    """
    registration_number: str | None = Field(default=None, min_length=1, max_length=50)
    vehicle_code: str | None = Field(default=None, min_length=1, max_length=50)
    vehicle_type: VehicleType | None = Field(default=None)
    seating_capacity: int | None = Field(default=None, gt=0)
    fuel_type: FuelType | None = Field(default=None)
    insurance_expiry_date: date | None = Field(default=None)
    fitness_expiry_date: date | None = Field(default=None)
    gps_device_id: str | None = Field(default=None, max_length=100)
    status: VehicleStatus | None = Field(default=None)
    description: str | None = Field(default=None, max_length=255)


class VehicleResponse(BaseModel):
    """
    Serialized vehicle data response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    registration_number: str
    vehicle_code: str
    vehicle_type: VehicleType
    seating_capacity: int
    fuel_type: FuelType
    insurance_expiry_date: date | None
    fitness_expiry_date: date | None
    gps_device_id: str | None
    status: VehicleStatus
    description: str | None
    created_at: datetime
    updated_at: datetime


class VehicleOccupancyResponse(BaseModel):
    """
    Vehicle capacity vs allocated passengers occupancy response.
    """
    vehicle_id: UUID
    vehicle_code: str
    registration_number: str
    seating_capacity: int
    total_allocated: int
    available_seats: int
    is_overbooked: bool
    assigned_route_count: int


class VehicleListResponse(BaseModel):
    """
    Paginated list of vehicles.
    """
    items: list[VehicleResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# DRIVER SCHEMAS
# =============================================================================

class DriverCreate(BaseModel):
    """
    Payload for registering a transport driver.
    """
    name: str = Field(..., min_length=1, max_length=150)
    license_number: str = Field(..., min_length=1, max_length=100)
    license_expiry_date: date | None = Field(default=None)
    contact_number: str = Field(..., min_length=3, max_length=30)
    emergency_contact: str | None = Field(default=None, max_length=30)
    staff_id: UUID | None = Field(default=None)
    is_active: bool = Field(default=True)
    remarks: str | None = Field(default=None, max_length=255)


class DriverUpdate(BaseModel):
    """
    Payload for updating a transport driver.
    """
    name: str | None = Field(default=None, min_length=1, max_length=150)
    license_number: str | None = Field(default=None, min_length=1, max_length=100)
    license_expiry_date: date | None = Field(default=None)
    contact_number: str | None = Field(default=None, min_length=3, max_length=30)
    emergency_contact: str | None = Field(default=None, max_length=30)
    staff_id: UUID | None = Field(default=None)
    is_active: bool | None = Field(default=None)
    remarks: str | None = Field(default=None, max_length=255)


class DriverResponse(BaseModel):
    """
    Serialized transport driver data response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    license_number: str
    license_expiry_date: date | None
    contact_number: str
    emergency_contact: str | None
    staff_id: UUID | None
    is_active: bool
    remarks: str | None
    created_at: datetime
    updated_at: datetime


class DriverListResponse(BaseModel):
    """
    Paginated list of drivers.
    """
    items: list[DriverResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# ROUTE STOP SCHEMAS
# =============================================================================

class RouteStopCreate(BaseModel):
    """
    Payload for adding a stop to a route.
    """
    stop_name: str = Field(..., min_length=1, max_length=150)
    stop_code: str = Field(..., min_length=1, max_length=50)
    sequence_order: int = Field(..., gt=0)
    morning_pickup_time: time | None = Field(default=None)
    afternoon_drop_time: time | None = Field(default=None)
    landmark: str | None = Field(default=None, max_length=255)
    pickup_fee_amount: Decimal = Field(default=Decimal("0.00"), ge=Decimal("0.00"))
    is_active: bool = Field(default=True)


class RouteStopUpdate(BaseModel):
    """
    Payload for updating an existing route stop.
    """
    stop_name: str | None = Field(default=None, min_length=1, max_length=150)
    stop_code: str | None = Field(default=None, min_length=1, max_length=50)
    sequence_order: int | None = Field(default=None, gt=0)
    morning_pickup_time: time | None = Field(default=None)
    afternoon_drop_time: time | None = Field(default=None)
    landmark: str | None = Field(default=None, max_length=255)
    pickup_fee_amount: Decimal | None = Field(default=None, ge=Decimal("0.00"))
    is_active: bool | None = Field(default=None)


class RouteStopResponse(BaseModel):
    """
    Serialized route stop data response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    route_id: UUID
    stop_name: str
    stop_code: str
    sequence_order: int
    morning_pickup_time: time | None
    afternoon_drop_time: time | None
    landmark: str | None
    pickup_fee_amount: Decimal
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RouteStopListResponse(BaseModel):
    """
    List of route stops.
    """
    items: list[RouteStopResponse]
    total: int


# =============================================================================
# ROUTE SCHEMAS
# =============================================================================

class RouteCreate(BaseModel):
    """
    Payload for creating a transit route.
    """
    route_code: str = Field(..., min_length=1, max_length=50)
    route_name: str = Field(..., min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    vehicle_id: UUID | None = Field(default=None)
    driver_id: UUID | None = Field(default=None)
    attendant_name: str | None = Field(default=None, max_length=150)
    attendant_phone: str | None = Field(default=None, max_length=30)
    morning_start_time: time | None = Field(default=None)
    evening_start_time: time | None = Field(default=None)
    is_active: bool = Field(default=True)


class RouteUpdate(BaseModel):
    """
    Payload for updating a transit route.
    """
    route_code: str | None = Field(default=None, min_length=1, max_length=50)
    route_name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = Field(default=None, max_length=255)
    vehicle_id: UUID | None = Field(default=None)
    driver_id: UUID | None = Field(default=None)
    attendant_name: str | None = Field(default=None, max_length=150)
    attendant_phone: str | None = Field(default=None, max_length=30)
    morning_start_time: time | None = Field(default=None)
    evening_start_time: time | None = Field(default=None)
    is_active: bool | None = Field(default=None)


class RouteResponse(BaseModel):
    """
    Serialized basic route response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    route_code: str
    route_name: str
    description: str | None
    vehicle_id: UUID | None
    driver_id: UUID | None
    attendant_name: str | None
    attendant_phone: str | None
    morning_start_time: time | None
    evening_start_time: time | None
    is_active: bool
    created_at: datetime
    updated_at: datetime


class RouteDetailResponse(RouteResponse):
    """
    Detailed route response with nested stops, vehicle, driver, and active passenger metrics.
    """
    stops: list[RouteStopResponse] = Field(default_factory=list)
    vehicle: VehicleResponse | None = Field(default=None)
    driver: DriverResponse | None = Field(default=None)
    active_allocation_count: int = Field(default=0)


class RouteListResponse(BaseModel):
    """
    Paginated list of routes.
    """
    items: list[RouteResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# STUDENT TRANSPORT ALLOCATION SCHEMAS
# =============================================================================

class StudentTransportAllocationCreate(BaseModel):
    """
    Payload for allocating a student seat on a transport route.
    """
    student_id: UUID
    route_id: UUID
    academic_year_id: UUID
    allocation_type: TransportAllocationType = Field(default=TransportAllocationType.TWO_WAY)
    start_date: date
    pickup_stop_id: UUID | None = Field(default=None)
    drop_stop_id: UUID | None = Field(default=None)
    end_date: date | None = Field(default=None)
    remarks: str | None = Field(default=None, max_length=255)
    status: TransportAllocationStatus = Field(default=TransportAllocationStatus.ACTIVE)


class StudentTransportAllocationUpdate(BaseModel):
    """
    Payload for updating an allocation's details (stops, dates, remarks).
    """
    route_id: UUID | None = Field(default=None)
    allocation_type: TransportAllocationType | None = Field(default=None)
    pickup_stop_id: UUID | None = Field(default=None)
    drop_stop_id: UUID | None = Field(default=None)
    start_date: date | None = Field(default=None)
    end_date: date | None = Field(default=None)
    remarks: str | None = Field(default=None, max_length=255)
    status: TransportAllocationStatus | None = Field(default=None)


class StudentTransportAllocationStatusUpdate(BaseModel):
    """
    Payload for updating only the allocation status (e.g. suspend or cancel).
    """
    status: TransportAllocationStatus
    remarks: str | None = Field(default=None, max_length=255)
    end_date: date | None = Field(default=None)


class StudentTransportAllocationResponse(BaseModel):
    """
    Serialized student transport allocation response.
    """
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    student_id: UUID
    route_id: UUID
    pickup_stop_id: UUID | None
    drop_stop_id: UUID | None
    academic_year_id: UUID
    allocation_type: TransportAllocationType
    status: TransportAllocationStatus
    start_date: date
    end_date: date | None
    remarks: str | None
    created_at: datetime
    updated_at: datetime

    # Expanded details
    student_name: str | None = Field(default=None)
    admission_number: str | None = Field(default=None)
    route_code: str | None = Field(default=None)
    route_name: str | None = Field(default=None)
    pickup_stop_name: str | None = Field(default=None)
    drop_stop_name: str | None = Field(default=None)


class StudentTransportAllocationListResponse(BaseModel):
    """
    Paginated list of student transport allocations.
    """
    items: list[StudentTransportAllocationResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# =============================================================================
# DASHBOARD STATS SCHEMAS
# =============================================================================

class TransportDashboardStatsResponse(BaseModel):
    """
    Subsystem-wide metrics and KPIs for the transport overview dashboard.
    """
    total_vehicles: int
    active_vehicles: int
    maintenance_vehicles: int
    total_drivers: int
    active_drivers: int
    total_routes: int
    active_routes: int
    total_allocated_students: int
    total_seating_capacity: int
    overall_occupancy_percentage: float
