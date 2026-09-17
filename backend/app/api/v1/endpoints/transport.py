from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.common.enums.transport import (
    FuelType,
    TransportAllocationStatus,
    TransportAllocationType,
    VehicleStatus,
    VehicleType,
)
from app.common.exceptions import NotFoundException
from app.dependencies import get_db, get_transport_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.transport import (
    DriverCreate,
    DriverListResponse,
    DriverResponse,
    DriverUpdate,
    RouteCreate,
    RouteDetailResponse,
    RouteListResponse,
    RouteResponse,
    RouteStopCreate,
    RouteStopListResponse,
    RouteStopResponse,
    RouteStopUpdate,
    RouteUpdate,
    StudentTransportAllocationCreate,
    StudentTransportAllocationListResponse,
    StudentTransportAllocationResponse,
    StudentTransportAllocationStatusUpdate,
    StudentTransportAllocationUpdate,
    TransportDashboardStatsResponse,
    VehicleCreate,
    VehicleListResponse,
    VehicleOccupancyResponse,
    VehicleResponse,
    VehicleUpdate,
)
from app.services.transport_service import TransportService

router = APIRouter()


def _get_user_role(current_user: IdentityUser) -> str:
    if hasattr(current_user, "roles") and current_user.roles:
        return current_user.roles[0].name
    return "User"


# =============================================================================
# 1. VEHICLE ENDPOINTS
# =============================================================================

@router.get(
    "/vehicles",
    response_model=VehicleListResponse,
    summary="List transport vehicles",
)
def list_vehicles(
    status: VehicleStatus | None = Query(default=None, description="Filter by vehicle status"),
    vehicle_type: VehicleType | None = Query(default=None, description="Filter by vehicle type"),
    search: str | None = Query(default=None, description="Search by registration number, code, or description"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> VehicleListResponse:
    """
    Retrieves a paginated list of transport vehicles for the authenticated school.
    """
    items, total, total_pages = service.list_vehicles(
        db=db,
        school_id=current_user.school_id,
        status=status,
        vehicle_type=vehicle_type,
        search=search,
        page=page,
        page_size=page_size,
    )
    return VehicleListResponse(
        items=[VehicleResponse.model_validate(v) for v in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/vehicles",
    response_model=VehicleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transport vehicle",
)
def create_vehicle(
    payload: VehicleCreate,
    current_user: IdentityUser = Depends(require_permission("transport.create")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> VehicleResponse:
    """
    Registers a new vehicle in the school's fleet with seating capacity validation.
    """
    vehicle = service.create_vehicle(
        db=db,
        school_id=current_user.school_id,
        registration_number=payload.registration_number,
        vehicle_code=payload.vehicle_code,
        seating_capacity=payload.seating_capacity,
        vehicle_type=payload.vehicle_type,
        fuel_type=payload.fuel_type,
        insurance_expiry_date=payload.insurance_expiry_date,
        fitness_expiry_date=payload.fitness_expiry_date,
        gps_device_id=payload.gps_device_id,
        status=payload.status,
        description=payload.description,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.get(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Get vehicle details",
)
def get_vehicle(
    vehicle_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> VehicleResponse:
    """
    Retrieves detailed information for a single transport vehicle.
    """
    vehicle = service.get_vehicle(
        db=db,
        school_id=current_user.school_id,
        vehicle_id=vehicle_id,
    )
    return VehicleResponse.model_validate(vehicle)


@router.put(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update vehicle details (full)",
)
@router.patch(
    "/vehicles/{vehicle_id}",
    response_model=VehicleResponse,
    summary="Update vehicle details (partial)",
)
def update_vehicle(
    vehicle_id: UUID,
    payload: VehicleUpdate,
    current_user: IdentityUser = Depends(require_permission("transport.update")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> VehicleResponse:
    """
    Updates transport vehicle details, maintaining tenant unique constraints.
    """
    vehicle = service.update_vehicle(
        db=db,
        school_id=current_user.school_id,
        vehicle_id=vehicle_id,
        registration_number=payload.registration_number,
        vehicle_code=payload.vehicle_code,
        vehicle_type=payload.vehicle_type,
        seating_capacity=payload.seating_capacity,
        fuel_type=payload.fuel_type,
        insurance_expiry_date=payload.insurance_expiry_date,
        fitness_expiry_date=payload.fitness_expiry_date,
        gps_device_id=payload.gps_device_id,
        status=payload.status,
        description=payload.description,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(vehicle)
    return VehicleResponse.model_validate(vehicle)


@router.delete(
    "/vehicles/{vehicle_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete transport vehicle",
)
def delete_vehicle(
    vehicle_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.delete")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> dict[str, Any]:
    """
    Soft-deletes a transport vehicle and unlinks it from active routes.
    """
    service.delete_vehicle(
        db=db,
        school_id=current_user.school_id,
        vehicle_id=vehicle_id,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    return {"success": True, "message": "Vehicle deleted successfully"}


@router.get(
    "/vehicles/{vehicle_id}/occupancy",
    response_model=VehicleOccupancyResponse,
    summary="Get vehicle occupancy stats",
)
def get_vehicle_occupancy(
    vehicle_id: UUID,
    academic_year_id: UUID | None = Query(default=None, description="Academic year for occupancy metrics"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> VehicleOccupancyResponse:
    """
    Derives real-time occupancy and remaining capacity for a vehicle.
    """
    stats = service.get_vehicle_occupancy_stats(
        db=db,
        school_id=current_user.school_id,
        vehicle_id=vehicle_id,
        academic_year_id=academic_year_id,
    )
    return VehicleOccupancyResponse(**stats)


# =============================================================================
# 2. DRIVER ENDPOINTS
# =============================================================================

@router.get(
    "/drivers",
    response_model=DriverListResponse,
    summary="List transport drivers",
)
def list_drivers(
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    search: str | None = Query(default=None, description="Search by name, license number, or phone"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> DriverListResponse:
    """
    Retrieves a paginated list of drivers for the school.
    """
    items, total, total_pages = service.list_drivers(
        db=db,
        school_id=current_user.school_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return DriverListResponse(
        items=[DriverResponse.model_validate(d) for d in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/drivers",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transport driver",
)
def create_driver(
    payload: DriverCreate,
    current_user: IdentityUser = Depends(require_permission("transport.create")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> DriverResponse:
    """
    Registers a new transport driver.
    """
    driver = service.create_driver(
        db=db,
        school_id=current_user.school_id,
        name=payload.name,
        license_number=payload.license_number,
        contact_number=payload.contact_number,
        license_expiry_date=payload.license_expiry_date,
        emergency_contact=payload.emergency_contact,
        staff_id=payload.staff_id,
        is_active=payload.is_active,
        remarks=payload.remarks,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.get(
    "/drivers/{driver_id}",
    response_model=DriverResponse,
    summary="Get driver details",
)
def get_driver(
    driver_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> DriverResponse:
    """
    Retrieves details for a single driver.
    """
    driver = service.get_driver(
        db=db,
        school_id=current_user.school_id,
        driver_id=driver_id,
    )
    return DriverResponse.model_validate(driver)


@router.put(
    "/drivers/{driver_id}",
    response_model=DriverResponse,
    summary="Update driver details (full)",
)
@router.patch(
    "/drivers/{driver_id}",
    response_model=DriverResponse,
    summary="Update driver details (partial)",
)
def update_driver(
    driver_id: UUID,
    payload: DriverUpdate,
    current_user: IdentityUser = Depends(require_permission("transport.update")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> DriverResponse:
    """
    Updates driver attributes.
    """
    driver = service.update_driver(
        db=db,
        school_id=current_user.school_id,
        driver_id=driver_id,
        name=payload.name,
        license_number=payload.license_number,
        license_expiry_date=payload.license_expiry_date,
        contact_number=payload.contact_number,
        emergency_contact=payload.emergency_contact,
        staff_id=payload.staff_id,
        is_active=payload.is_active,
        remarks=payload.remarks,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(driver)
    return DriverResponse.model_validate(driver)


@router.delete(
    "/drivers/{driver_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete transport driver",
)
def delete_driver(
    driver_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.delete")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> dict[str, Any]:
    """
    Soft-deletes a driver and unlinks from assigned routes.
    """
    service.delete_driver(
        db=db,
        school_id=current_user.school_id,
        driver_id=driver_id,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    return {"success": True, "message": "Driver deleted successfully"}


# =============================================================================
# 3. ROUTE ENDPOINTS
# =============================================================================

@router.get(
    "/routes",
    response_model=RouteListResponse,
    summary="List transport routes",
)
def list_routes(
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    vehicle_id: UUID | None = Query(default=None, description="Filter by assigned vehicle"),
    driver_id: UUID | None = Query(default=None, description="Filter by assigned driver"),
    search: str | None = Query(default=None, description="Search by route code, name, or description"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteListResponse:
    """
    Retrieves a paginated list of transit routes.
    """
    items, total, total_pages = service.list_routes(
        db=db,
        school_id=current_user.school_id,
        is_active=is_active,
        vehicle_id=vehicle_id,
        driver_id=driver_id,
        search=search,
        page=page,
        page_size=page_size,
    )
    return RouteListResponse(
        items=[RouteResponse.model_validate(r) for r in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/routes",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create transport route",
)
def create_route(
    payload: RouteCreate,
    current_user: IdentityUser = Depends(require_permission("transport.create")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteResponse:
    """
    Creates a new transit route with same-school vehicle and driver validation.
    """
    route = service.create_route(
        db=db,
        school_id=current_user.school_id,
        route_code=payload.route_code,
        route_name=payload.route_name,
        description=payload.description,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        attendant_name=payload.attendant_name,
        attendant_phone=payload.attendant_phone,
        morning_start_time=payload.morning_start_time,
        evening_start_time=payload.evening_start_time,
        is_active=payload.is_active,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(route)
    return RouteResponse.model_validate(route)


@router.get(
    "/routes/{route_id}",
    response_model=RouteDetailResponse,
    summary="Get route details with stops",
)
def get_route(
    route_id: UUID,
    include_details: bool = Query(default=True, description="Preload nested stops, vehicle, and driver"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteDetailResponse:
    """
    Retrieves full details of a route including its ordered stops, assigned vehicle, driver, and active passengers.
    """
    route = service.get_route(
        db=db,
        school_id=current_user.school_id,
        route_id=route_id,
        include_details=include_details,
    )
    active_count = service.get_route_active_allocation_count(
        db=db,
        school_id=current_user.school_id,
        route_id=route_id,
    )
    response_data = RouteDetailResponse.model_validate(route)
    response_data.active_allocation_count = active_count
    return response_data


@router.put(
    "/routes/{route_id}",
    response_model=RouteResponse,
    summary="Update route details (full)",
)
@router.patch(
    "/routes/{route_id}",
    response_model=RouteResponse,
    summary="Update route details (partial)",
)
def update_route(
    route_id: UUID,
    payload: RouteUpdate,
    current_user: IdentityUser = Depends(require_permission("transport.update")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteResponse:
    """
    Updates route parameters.
    """
    route = service.update_route(
        db=db,
        school_id=current_user.school_id,
        route_id=route_id,
        route_code=payload.route_code,
        route_name=payload.route_name,
        description=payload.description,
        vehicle_id=payload.vehicle_id,
        driver_id=payload.driver_id,
        attendant_name=payload.attendant_name,
        attendant_phone=payload.attendant_phone,
        morning_start_time=payload.morning_start_time,
        evening_start_time=payload.evening_start_time,
        is_active=payload.is_active,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(route)
    return RouteResponse.model_validate(route)


@router.delete(
    "/routes/{route_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete transport route",
)
def delete_route(
    route_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.delete")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> dict[str, Any]:
    """
    Soft-deletes a route. Rejects deletion if active student allocations are assigned.
    """
    service.delete_route(
        db=db,
        school_id=current_user.school_id,
        route_id=route_id,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    return {"success": True, "message": "Route deleted successfully"}


# =============================================================================
# 4. ROUTE STOP ENDPOINTS
# =============================================================================

@router.get(
    "/routes/{route_id}/stops",
    response_model=RouteStopListResponse,
    summary="List stops for a route",
)
def list_stops(
    route_id: UUID,
    is_active: bool | None = Query(default=None, description="Filter by active status"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteStopListResponse:
    """
    Lists all stops along a designated route in sequence order.
    """
    stops = service.list_stops(
        db=db,
        school_id=current_user.school_id,
        route_id=route_id,
        is_active=is_active,
    )
    return RouteStopListResponse(
        items=[RouteStopResponse.model_validate(s) for s in stops],
        total=len(stops),
    )


@router.post(
    "/routes/{route_id}/stops",
    response_model=RouteStopResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add stop to route",
)
def create_stop(
    route_id: UUID,
    payload: RouteStopCreate,
    current_user: IdentityUser = Depends(require_permission("transport.create")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteStopResponse:
    """
    Appends a new stop to a route with unique sequence order and positive fee validation.
    """
    stop = service.create_stop(
        db=db,
        school_id=current_user.school_id,
        route_id=route_id,
        stop_name=payload.stop_name,
        stop_code=payload.stop_code,
        sequence_order=payload.sequence_order,
        morning_pickup_time=payload.morning_pickup_time,
        afternoon_drop_time=payload.afternoon_drop_time,
        landmark=payload.landmark,
        pickup_fee_amount=payload.pickup_fee_amount,
        is_active=payload.is_active,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(stop)
    return RouteStopResponse.model_validate(stop)


@router.get(
    "/routes/{route_id}/stops/{stop_id}",
    response_model=RouteStopResponse,
    summary="Get route stop details",
)
def get_stop(
    route_id: UUID,
    stop_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteStopResponse:
    """
    Retrieves details for a single route stop.
    """
    stop = service.get_stop(
        db=db,
        school_id=current_user.school_id,
        stop_id=stop_id,
    )
    if stop.route_id != route_id:
        raise NotFoundException("Route stop not found in this route")
    return RouteStopResponse.model_validate(stop)


@router.put(
    "/routes/{route_id}/stops/{stop_id}",
    response_model=RouteStopResponse,
    summary="Update route stop (full)",
)
@router.patch(
    "/routes/{route_id}/stops/{stop_id}",
    response_model=RouteStopResponse,
    summary="Update route stop (partial)",
)
def update_stop(
    route_id: UUID,
    stop_id: UUID,
    payload: RouteStopUpdate,
    current_user: IdentityUser = Depends(require_permission("transport.update")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> RouteStopResponse:
    """
    Updates stop details, maintaining route-scoped sequence uniqueness.
    """
    stop = service.get_stop(db, current_user.school_id, stop_id)
    if stop.route_id != route_id:
        raise NotFoundException("Route stop not found in this route")

    updated_stop = service.update_stop(
        db=db,
        school_id=current_user.school_id,
        stop_id=stop_id,
        stop_name=payload.stop_name,
        stop_code=payload.stop_code,
        sequence_order=payload.sequence_order,
        morning_pickup_time=payload.morning_pickup_time,
        afternoon_drop_time=payload.afternoon_drop_time,
        landmark=payload.landmark,
        pickup_fee_amount=payload.pickup_fee_amount,
        is_active=payload.is_active,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(updated_stop)
    return RouteStopResponse.model_validate(updated_stop)


@router.delete(
    "/routes/{route_id}/stops/{stop_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete route stop",
)
def delete_stop(
    route_id: UUID,
    stop_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.delete")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> dict[str, Any]:
    """
    Soft-deletes a route stop. Rejects deletion if active allocations reference this stop.
    """
    stop = service.get_stop(db, current_user.school_id, stop_id)
    if stop.route_id != route_id:
        raise NotFoundException("Route stop not found in this route")

    service.delete_stop(
        db=db,
        school_id=current_user.school_id,
        stop_id=stop_id,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    return {"success": True, "message": "Route stop deleted successfully"}


# =============================================================================
# 5. STUDENT TRANSPORT ALLOCATION ENDPOINTS
# =============================================================================

@router.get(
    "/allocations",
    response_model=StudentTransportAllocationListResponse,
    summary="List student transport allocations",
)
def list_allocations(
    student_id: UUID | None = Query(default=None, description="Filter by student ID"),
    route_id: UUID | None = Query(default=None, description="Filter by route ID"),
    academic_year_id: UUID | None = Query(default=None, description="Filter by academic year ID"),
    status: TransportAllocationStatus | None = Query(default=None, description="Filter by allocation status"),
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> StudentTransportAllocationListResponse:
    """
    Lists student transport allocations with filtering and pagination.
    """
    items, total, total_pages = service.list_allocations(
        db=db,
        school_id=current_user.school_id,
        student_id=student_id,
        route_id=route_id,
        academic_year_id=academic_year_id,
        status=status,
        page=page,
        page_size=page_size,
    )
    return StudentTransportAllocationListResponse(
        items=[StudentTransportAllocationResponse.model_validate(a) for a in items],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "/allocations",
    response_model=StudentTransportAllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allocate student seat on route",
)
def allocate_student(
    payload: StudentTransportAllocationCreate,
    current_user: IdentityUser = Depends(require_permission("transport.allocate")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> StudentTransportAllocationResponse:
    """
    Allocates a student to a route seat, strictly enforcing:
    1. One active allocation per student per academic year.
    2. Allocation type rules (TWO_WAY, PICKUP_ONLY, DROP_ONLY).
    3. Stops belong to requested route.
    4. Vehicle seating capacity limits.
    """
    allocation = service.allocate_student(
        db=db,
        school_id=current_user.school_id,
        student_id=payload.student_id,
        route_id=payload.route_id,
        academic_year_id=payload.academic_year_id,
        allocation_type=payload.allocation_type,
        start_date=payload.start_date,
        pickup_stop_id=payload.pickup_stop_id,
        drop_stop_id=payload.drop_stop_id,
        end_date=payload.end_date,
        remarks=payload.remarks,
        status=payload.status,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    # Eagerly load relationships for response serialization
    db.refresh(allocation)
    loaded_allocation = service.get_allocation(db, current_user.school_id, allocation.id)
    return StudentTransportAllocationResponse.model_validate(loaded_allocation)


@router.get(
    "/allocations/{allocation_id}",
    response_model=StudentTransportAllocationResponse,
    summary="Get allocation details",
)
def get_allocation(
    allocation_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> StudentTransportAllocationResponse:
    """
    Retrieves a single student transport allocation record.
    """
    allocation = service.get_allocation(
        db=db,
        school_id=current_user.school_id,
        allocation_id=allocation_id,
    )
    return StudentTransportAllocationResponse.model_validate(allocation)


@router.put(
    "/allocations/{allocation_id}",
    response_model=StudentTransportAllocationResponse,
    summary="Update allocation details (full)",
)
@router.patch(
    "/allocations/{allocation_id}",
    response_model=StudentTransportAllocationResponse,
    summary="Update allocation details (partial)",
)
def update_allocation(
    allocation_id: UUID,
    payload: StudentTransportAllocationUpdate,
    current_user: IdentityUser = Depends(require_permission("transport.allocate")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> StudentTransportAllocationResponse:
    """
    Updates student transport allocation parameters, re-validating stops, allocation type, and capacity.
    """
    allocation = service.update_allocation(
        db=db,
        school_id=current_user.school_id,
        allocation_id=allocation_id,
        route_id=payload.route_id,
        allocation_type=payload.allocation_type,
        pickup_stop_id=payload.pickup_stop_id,
        drop_stop_id=payload.drop_stop_id,
        start_date=payload.start_date,
        end_date=payload.end_date,
        remarks=payload.remarks,
        status=payload.status,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(allocation)
    loaded_allocation = service.get_allocation(db, current_user.school_id, allocation.id)
    return StudentTransportAllocationResponse.model_validate(loaded_allocation)


@router.patch(
    "/allocations/{allocation_id}/status",
    response_model=StudentTransportAllocationResponse,
    summary="Update allocation status (e.g. SUSPENDED, CANCELLED)",
)
def update_allocation_status(
    allocation_id: UUID,
    payload: StudentTransportAllocationStatusUpdate,
    current_user: IdentityUser = Depends(require_permission("transport.allocate")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> StudentTransportAllocationResponse:
    """
    Transitions the lifecycle status of an allocation (ACTIVE, SUSPENDED, CANCELLED).
    """
    allocation = service.update_allocation_status(
        db=db,
        school_id=current_user.school_id,
        allocation_id=allocation_id,
        status=payload.status,
        remarks=payload.remarks,
        end_date=payload.end_date,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    db.refresh(allocation)
    loaded_allocation = service.get_allocation(db, current_user.school_id, allocation.id)
    return StudentTransportAllocationResponse.model_validate(loaded_allocation)


@router.delete(
    "/allocations/{allocation_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete transport allocation",
)
def delete_allocation(
    allocation_id: UUID,
    current_user: IdentityUser = Depends(require_permission("transport.delete")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> dict[str, Any]:
    """
    Soft-deletes a student transport allocation.
    """
    service.delete_allocation(
        db=db,
        school_id=current_user.school_id,
        allocation_id=allocation_id,
        current_user=current_user,
        user_role=_get_user_role(current_user),
    )
    db.commit()
    return {"success": True, "message": "Transport allocation deleted successfully"}


# =============================================================================
# 6. DASHBOARD STATS ENDPOINT
# =============================================================================

@router.get(
    "/dashboard-stats",
    response_model=TransportDashboardStatsResponse,
    summary="Get transport overview dashboard statistics",
)
def get_dashboard_stats(
    academic_year_id: UUID | None = Query(default=None, description="Optional academic year filter"),
    current_user: IdentityUser = Depends(require_permission("transport.view")),
    db: Session = Depends(get_db),
    service: TransportService = Depends(get_transport_service),
) -> TransportDashboardStatsResponse:
    """
    Returns aggregated KPIs for the school's fleet, driver availability, active routes, and seating occupancy.
    """
    stats = service.get_transport_dashboard_stats(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
    )
    return TransportDashboardStatsResponse(**stats)
