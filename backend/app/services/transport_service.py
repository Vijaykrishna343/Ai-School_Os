from __future__ import annotations

import math
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.common.enums.transport import (
    FuelType,
    TransportAllocationStatus,
    TransportAllocationType,
    VehicleStatus,
    VehicleType,
)
from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.academic_year.academic_year import AcademicYear
from app.models.audit_log import AuditLog
from app.models.student.student import Student
from app.models.teacher.teacher import Teacher
from app.models.transport.driver import TransportDriver
from app.models.transport.route import TransportRoute
from app.models.transport.stop import RouteStop
from app.models.transport.student_transport_allocation import StudentTransportAllocation
from app.models.transport.vehicle import Vehicle

logger = get_logger(__name__)



class TransportService:
    """
    Core Domain Service for Transport & Fleet Management.
    Enforces strict multi-tenant isolation, relationship integrity,
    and business invariants for vehicles, drivers, routes, stops, and student allocations.
    """

    @staticmethod
    def _write_audit_log(
        db: Session,
        school_id: UUID,
        action: str,
        entity_type: str,
        entity_id: str,
        details: str,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> None:
        """
        Records an administrative audit log entry if an authenticated user is provided.
        """
        if current_user and getattr(current_user, "id", None):
            audit = AuditLog(
                school_id=school_id,
                user_id=current_user.id,
                user_email=getattr(current_user, "email", "system"),
                role_name=user_role or "User",
                action=action,
                module="TRANSPORT",
                entity_type=entity_type,
                entity_id=entity_id,
                status_code=200,
                details=details,
            )
            db.add(audit)

    @staticmethod
    def _check_vehicle_capacity(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        academic_year_id: UUID,
        exclude_allocation_id: UUID | None = None,
    ) -> None:
        """
        Validates that adding or activating an allocation on the route does not exceed
        the assigned vehicle's seating capacity across all routes sharing the vehicle for this academic year.
        """
        route = db.scalar(
            select(TransportRoute).where(
                TransportRoute.id == route_id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        )
        if not route or not route.vehicle_id:
            return

        vehicle = db.scalar(
            select(Vehicle).where(
                Vehicle.id == route.vehicle_id,
                Vehicle.school_id == school_id,
                Vehicle.is_deleted == False,
            )
        )
        if not vehicle or vehicle.seating_capacity <= 0:
            return

        routes_with_vehicle = db.scalars(
            select(TransportRoute.id).where(
                TransportRoute.vehicle_id == vehicle.id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        ).all()

        if not routes_with_vehicle:
            return

        query = select(func.count(StudentTransportAllocation.id)).where(
            StudentTransportAllocation.school_id == school_id,
            StudentTransportAllocation.route_id.in_(routes_with_vehicle),
            StudentTransportAllocation.academic_year_id == academic_year_id,
            StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
            StudentTransportAllocation.is_deleted == False,
        )
        if exclude_allocation_id is not None:
            query = query.where(StudentTransportAllocation.id != exclude_allocation_id)

        current_allocated = db.scalar(query) or 0
        if current_allocated >= vehicle.seating_capacity:
            raise ValidationException(
                f"Vehicle capacity of {vehicle.seating_capacity} seats would be exceeded on route '{route.route_code}' (current allocations: {current_allocated})"
            )

    # =========================================================================
    # VEHICLE MANAGEMENT & CRUD
    # =========================================================================

    @staticmethod
    def create_vehicle(
        db: Session,
        school_id: UUID,
        registration_number: str,
        vehicle_code: str,
        seating_capacity: int,
        vehicle_type: VehicleType = VehicleType.BUS,
        fuel_type: FuelType = FuelType.DIESEL,
        insurance_expiry_date: date | None = None,
        fitness_expiry_date: date | None = None,
        gps_device_id: str | None = None,
        status: VehicleStatus = VehicleStatus.ACTIVE,
        description: str | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> Vehicle:
        """
        Creates a vehicle with seating capacity validation and tenant-unique registration/code.
        """
        if seating_capacity <= 0:
            raise ValidationException("Seating capacity must be a positive integer greater than zero")

        clean_reg = registration_number.strip().upper()
        clean_code = vehicle_code.strip().upper()

        # Check duplicate registration number within tenant
        existing_reg = db.scalar(
            select(Vehicle).where(
                Vehicle.school_id == school_id,
                func.upper(Vehicle.registration_number) == clean_reg,
                Vehicle.is_deleted == False,
            )
        )
        if existing_reg:
            raise AlreadyExistsException(f"Vehicle with registration '{clean_reg}' already exists for this school")

        # Check duplicate vehicle code within tenant
        existing_code = db.scalar(
            select(Vehicle).where(
                Vehicle.school_id == school_id,
                func.upper(Vehicle.vehicle_code) == clean_code,
                Vehicle.is_deleted == False,
            )
        )
        if existing_code:
            raise AlreadyExistsException(f"Vehicle with code '{clean_code}' already exists for this school")

        vehicle = Vehicle(
            school_id=school_id,
            registration_number=clean_reg,
            vehicle_code=clean_code,
            vehicle_type=vehicle_type,
            seating_capacity=seating_capacity,
            fuel_type=fuel_type,
            insurance_expiry_date=insurance_expiry_date,
            fitness_expiry_date=fitness_expiry_date,
            gps_device_id=gps_device_id.strip() if gps_device_id else None,
            status=status,
            description=description.strip() if description else None,
        )
        db.add(vehicle)
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="VEHICLE_CREATED",
            entity_type="Vehicle",
            entity_id=str(vehicle.id),
            details=f"Created vehicle {vehicle.vehicle_code} ({vehicle.registration_number})",
            current_user=current_user,
            user_role=user_role,
        )

        return vehicle

    @staticmethod
    def get_vehicle(db: Session, school_id: UUID, vehicle_id: UUID) -> Vehicle:
        """
        Retrieves a vehicle by ID enforcing tenant isolation.
        """
        vehicle = db.scalar(
            select(Vehicle).where(
                Vehicle.id == vehicle_id,
                Vehicle.school_id == school_id,
                Vehicle.is_deleted == False,
            )
        )
        if not vehicle:
            raise NotFoundException("Vehicle not found in this school")
        return vehicle

    @staticmethod
    def list_vehicles(
        db: Session,
        school_id: UUID,
        status: VehicleStatus | None = None,
        vehicle_type: VehicleType | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Vehicle], int, int]:
        """
        Lists vehicles with filtering and pagination.
        Returns: (items, total_count, total_pages)
        """
        query = select(Vehicle).where(
            Vehicle.school_id == school_id,
            Vehicle.is_deleted == False,
        )

        if status is not None:
            query = query.where(Vehicle.status == status)

        if vehicle_type is not None:
            query = query.where(Vehicle.vehicle_type == vehicle_type)

        if search:
            search_pattern = f"%{search.strip().upper()}%"
            query = query.where(
                or_(
                    func.upper(Vehicle.registration_number).ilike(search_pattern),
                    func.upper(Vehicle.vehicle_code).ilike(search_pattern),
                    func.upper(Vehicle.description).ilike(search_pattern),
                )
            )

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total_count = db.scalar(count_query) or 0

        # Pagination
        offset = (page - 1) * page_size
        items = db.scalars(
            query.order_by(Vehicle.created_at.desc()).offset(offset).limit(page_size)
        ).all()

        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        return list(items), total_count, total_pages

    @staticmethod
    def update_vehicle(
        db: Session,
        school_id: UUID,
        vehicle_id: UUID,
        registration_number: str | None = None,
        vehicle_code: str | None = None,
        vehicle_type: VehicleType | None = None,
        seating_capacity: int | None = None,
        fuel_type: FuelType | None = None,
        insurance_expiry_date: date | None = None,
        fitness_expiry_date: date | None = None,
        gps_device_id: str | None = None,
        status: VehicleStatus | None = None,
        description: str | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> Vehicle:
        """
        Updates an existing vehicle ensuring unique constraints and positive capacity.
        """
        vehicle = TransportService.get_vehicle(db, school_id, vehicle_id)

        if seating_capacity is not None:
            if seating_capacity <= 0:
                raise ValidationException("Seating capacity must be a positive integer greater than zero")
            vehicle.seating_capacity = seating_capacity

        if registration_number is not None:
            clean_reg = registration_number.strip().upper()
            if clean_reg != vehicle.registration_number:
                existing_reg = db.scalar(
                    select(Vehicle).where(
                        Vehicle.school_id == school_id,
                        Vehicle.id != vehicle_id,
                        func.upper(Vehicle.registration_number) == clean_reg,
                        Vehicle.is_deleted == False,
                    )
                )
                if existing_reg:
                    raise AlreadyExistsException(f"Vehicle with registration '{clean_reg}' already exists")
                vehicle.registration_number = clean_reg

        if vehicle_code is not None:
            clean_code = vehicle_code.strip().upper()
            if clean_code != vehicle.vehicle_code:
                existing_code = db.scalar(
                    select(Vehicle).where(
                        Vehicle.school_id == school_id,
                        Vehicle.id != vehicle_id,
                        func.upper(Vehicle.vehicle_code) == clean_code,
                        Vehicle.is_deleted == False,
                    )
                )
                if existing_code:
                    raise AlreadyExistsException(f"Vehicle with code '{clean_code}' already exists")
                vehicle.vehicle_code = clean_code

        if vehicle_type is not None:
            vehicle.vehicle_type = vehicle_type
        if fuel_type is not None:
            vehicle.fuel_type = fuel_type
        if insurance_expiry_date is not None:
            vehicle.insurance_expiry_date = insurance_expiry_date
        if fitness_expiry_date is not None:
            vehicle.fitness_expiry_date = fitness_expiry_date
        if gps_device_id is not None:
            vehicle.gps_device_id = gps_device_id.strip() if gps_device_id else None
        if status is not None:
            vehicle.status = status
        if description is not None:
            vehicle.description = description.strip() if description else None

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="VEHICLE_UPDATED",
            entity_type="Vehicle",
            entity_id=str(vehicle.id),
            details=f"Updated vehicle {vehicle.vehicle_code}",
            current_user=current_user,
            user_role=user_role,
        )

        return vehicle

    @staticmethod
    def delete_vehicle(
        db: Session,
        school_id: UUID,
        vehicle_id: UUID,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> bool:
        """
        Soft-deletes a vehicle and unlinks it from any assigned routes.
        """
        vehicle = TransportService.get_vehicle(db, school_id, vehicle_id)

        # Unassign vehicle from active routes
        routes = db.scalars(
            select(TransportRoute).where(
                TransportRoute.vehicle_id == vehicle_id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        ).all()
        for r in routes:
            r.vehicle_id = None

        vehicle.is_deleted = True
        vehicle.deleted_at = datetime.utcnow()
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="VEHICLE_DELETED",
            entity_type="Vehicle",
            entity_id=str(vehicle.id),
            details=f"Deleted vehicle {vehicle.vehicle_code}",
            current_user=current_user,
            user_role=user_role,
        )

        return True

    # =========================================================================
    # DRIVER MANAGEMENT & CRUD
    # =========================================================================

    @staticmethod
    def create_driver(
        db: Session,
        school_id: UUID,
        name: str,
        license_number: str,
        contact_number: str,
        license_expiry_date: date | None = None,
        emergency_contact: str | None = None,
        staff_id: UUID | None = None,
        is_active: bool = True,
        remarks: str | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> TransportDriver:
        """
        Creates a transport driver. If linked to an internal staff member, enforces same-tenant boundary.
        """
        clean_license = license_number.strip().upper()

        if staff_id:
            staff = db.scalar(
                select(Teacher).where(
                    Teacher.id == staff_id,
                    Teacher.school_id == school_id,
                    Teacher.is_deleted == False,
                )
            )
            if not staff:
                raise ValidationException("Linked staff member does not exist in this school or is inactive")

        existing_license = db.scalar(
            select(TransportDriver).where(
                TransportDriver.school_id == school_id,
                func.upper(TransportDriver.license_number) == clean_license,
                TransportDriver.is_deleted == False,
            )
        )
        if existing_license:
            raise AlreadyExistsException(f"Driver with license '{clean_license}' already exists for this school")

        driver = TransportDriver(
            school_id=school_id,
            name=name.strip(),
            license_number=clean_license,
            license_expiry_date=license_expiry_date,
            contact_number=contact_number.strip(),
            emergency_contact=emergency_contact.strip() if emergency_contact else None,
            staff_id=staff_id,
            is_active=is_active,
            remarks=remarks.strip() if remarks else None,
        )
        db.add(driver)
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="DRIVER_CREATED",
            entity_type="TransportDriver",
            entity_id=str(driver.id),
            details=f"Created driver {driver.name} ({driver.license_number})",
            current_user=current_user,
            user_role=user_role,
        )

        return driver

    @staticmethod
    def get_driver(db: Session, school_id: UUID, driver_id: UUID) -> TransportDriver:
        """
        Retrieves a driver by ID enforcing tenant isolation.
        """
        driver = db.scalar(
            select(TransportDriver).where(
                TransportDriver.id == driver_id,
                TransportDriver.school_id == school_id,
                TransportDriver.is_deleted == False,
            )
        )
        if not driver:
            raise NotFoundException("Driver not found in this school")
        return driver

    @staticmethod
    def list_drivers(
        db: Session,
        school_id: UUID,
        is_active: bool | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TransportDriver], int, int]:
        """
        Lists drivers with filtering and pagination.
        """
        query = select(TransportDriver).where(
            TransportDriver.school_id == school_id,
            TransportDriver.is_deleted == False,
        )

        if is_active is not None:
            query = query.where(TransportDriver.is_active == is_active)

        if search:
            search_pattern = f"%{search.strip().upper()}%"
            query = query.where(
                or_(
                    func.upper(TransportDriver.name).ilike(search_pattern),
                    func.upper(TransportDriver.license_number).ilike(search_pattern),
                    func.upper(TransportDriver.contact_number).ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_count = db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        items = db.scalars(
            query.order_by(TransportDriver.created_at.desc()).offset(offset).limit(page_size)
        ).all()

        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        return list(items), total_count, total_pages

    @staticmethod
    def update_driver(
        db: Session,
        school_id: UUID,
        driver_id: UUID,
        name: str | None = None,
        license_number: str | None = None,
        license_expiry_date: date | None = None,
        contact_number: str | None = None,
        emergency_contact: str | None = None,
        staff_id: UUID | None = None,
        is_active: bool | None = None,
        remarks: str | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> TransportDriver:
        """
        Updates driver details.
        """
        driver = TransportService.get_driver(db, school_id, driver_id)

        if staff_id is not None:
            staff = db.scalar(
                select(Teacher).where(
                    Teacher.id == staff_id,
                    Teacher.school_id == school_id,
                    Teacher.is_deleted == False,
                )
            )
            if not staff:
                raise ValidationException("Linked staff member does not exist in this school or is inactive")
            driver.staff_id = staff_id

        if license_number is not None:
            clean_license = license_number.strip().upper()
            if clean_license != driver.license_number:
                existing_license = db.scalar(
                    select(TransportDriver).where(
                        TransportDriver.school_id == school_id,
                        TransportDriver.id != driver_id,
                        func.upper(TransportDriver.license_number) == clean_license,
                        TransportDriver.is_deleted == False,
                    )
                )
                if existing_license:
                    raise AlreadyExistsException(f"Driver with license '{clean_license}' already exists")
                driver.license_number = clean_license

        if name is not None:
            driver.name = name.strip()
        if license_expiry_date is not None:
            driver.license_expiry_date = license_expiry_date
        if contact_number is not None:
            driver.contact_number = contact_number.strip()
        if emergency_contact is not None:
            driver.emergency_contact = emergency_contact.strip() if emergency_contact else None
        if is_active is not None:
            driver.is_active = is_active
        if remarks is not None:
            driver.remarks = remarks.strip() if remarks else None

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="DRIVER_UPDATED",
            entity_type="TransportDriver",
            entity_id=str(driver.id),
            details=f"Updated driver {driver.name}",
            current_user=current_user,
            user_role=user_role,
        )

        return driver

    @staticmethod
    def delete_driver(
        db: Session,
        school_id: UUID,
        driver_id: UUID,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> bool:
        """
        Soft-deletes a driver and unlinks from assigned routes.
        """
        driver = TransportService.get_driver(db, school_id, driver_id)

        routes = db.scalars(
            select(TransportRoute).where(
                TransportRoute.driver_id == driver_id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        ).all()
        for r in routes:
            r.driver_id = None

        driver.is_deleted = True
        driver.deleted_at = datetime.utcnow()
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="DRIVER_DELETED",
            entity_type="TransportDriver",
            entity_id=str(driver.id),
            details=f"Deleted driver {driver.name}",
            current_user=current_user,
            user_role=user_role,
        )

        return True

    # =========================================================================
    # ROUTE MANAGEMENT & CRUD
    # =========================================================================

    @staticmethod
    def create_route(
        db: Session,
        school_id: UUID,
        route_code: str,
        route_name: str,
        description: str | None = None,
        vehicle_id: UUID | None = None,
        driver_id: UUID | None = None,
        attendant_name: str | None = None,
        attendant_phone: str | None = None,
        morning_start_time: time | None = None,
        evening_start_time: time | None = None,
        is_active: bool = True,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> TransportRoute:
        """
        Creates a transit route. Strictly validates that referenced vehicle and driver belong to the same school.
        """
        clean_code = route_code.strip().upper()

        existing_code = db.scalar(
            select(TransportRoute).where(
                TransportRoute.school_id == school_id,
                func.upper(TransportRoute.route_code) == clean_code,
                TransportRoute.is_deleted == False,
            )
        )
        if existing_code:
            raise AlreadyExistsException(f"Route with code '{clean_code}' already exists for this school")

        if vehicle_id:
            vehicle = db.scalar(
                select(Vehicle).where(
                    Vehicle.id == vehicle_id,
                    Vehicle.school_id == school_id,
                    Vehicle.is_deleted == False,
                )
            )
            if not vehicle:
                raise ValidationException("Referenced vehicle does not exist in this school or has been deleted")

        if driver_id:
            driver = db.scalar(
                select(TransportDriver).where(
                    TransportDriver.id == driver_id,
                    TransportDriver.school_id == school_id,
                    TransportDriver.is_deleted == False,
                )
            )
            if not driver:
                raise ValidationException("Referenced driver does not exist in this school or has been deleted")

        route = TransportRoute(
            school_id=school_id,
            route_code=clean_code,
            route_name=route_name.strip(),
            description=description.strip() if description else None,
            vehicle_id=vehicle_id,
            driver_id=driver_id,
            attendant_name=attendant_name.strip() if attendant_name else None,
            attendant_phone=attendant_phone.strip() if attendant_phone else None,
            morning_start_time=morning_start_time,
            evening_start_time=evening_start_time,
            is_active=is_active,
        )
        db.add(route)
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="ROUTE_CREATED",
            entity_type="TransportRoute",
            entity_id=str(route.id),
            details=f"Created route {route.route_code} ({route.route_name})",
            current_user=current_user,
            user_role=user_role,
        )

        return route

    @staticmethod
    def get_route(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        include_details: bool = False,
    ) -> TransportRoute:
        """
        Retrieves a route by ID enforcing tenant isolation.
        Optionally preloads vehicle, driver, and ordered stops.
        """
        query = select(TransportRoute).where(
            TransportRoute.id == route_id,
            TransportRoute.school_id == school_id,
            TransportRoute.is_deleted == False,
        )
        if include_details:
            query = query.options(
                joinedload(TransportRoute.vehicle),
                joinedload(TransportRoute.driver),
                selectinload(TransportRoute.stops),
            )

        route = db.scalar(query)
        if not route:
            raise NotFoundException("Route not found in this school")
        return route

    @staticmethod
    def list_routes(
        db: Session,
        school_id: UUID,
        is_active: bool | None = None,
        vehicle_id: UUID | None = None,
        driver_id: UUID | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[TransportRoute], int, int]:
        """
        Lists transit routes with filtering and pagination.
        """
        query = select(TransportRoute).where(
            TransportRoute.school_id == school_id,
            TransportRoute.is_deleted == False,
        )

        if is_active is not None:
            query = query.where(TransportRoute.is_active == is_active)
        if vehicle_id is not None:
            query = query.where(TransportRoute.vehicle_id == vehicle_id)
        if driver_id is not None:
            query = query.where(TransportRoute.driver_id == driver_id)

        if search:
            search_pattern = f"%{search.strip().upper()}%"
            query = query.where(
                or_(
                    func.upper(TransportRoute.route_code).ilike(search_pattern),
                    func.upper(TransportRoute.route_name).ilike(search_pattern),
                    func.upper(TransportRoute.description).ilike(search_pattern),
                )
            )

        count_query = select(func.count()).select_from(query.subquery())
        total_count = db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        items = db.scalars(
            query.order_by(TransportRoute.created_at.desc()).offset(offset).limit(page_size)
        ).all()

        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        return list(items), total_count, total_pages

    @staticmethod
    def update_route(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        route_code: str | None = None,
        route_name: str | None = None,
        description: str | None = None,
        vehicle_id: UUID | None = None,
        driver_id: UUID | None = None,
        attendant_name: str | None = None,
        attendant_phone: str | None = None,
        morning_start_time: time | None = None,
        evening_start_time: time | None = None,
        is_active: bool | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> TransportRoute:
        """
        Updates a route ensuring code uniqueness and valid tenant relations.
        """
        route = TransportService.get_route(db, school_id, route_id)

        if route_code is not None:
            clean_code = route_code.strip().upper()
            if clean_code != route.route_code:
                existing_code = db.scalar(
                    select(TransportRoute).where(
                        TransportRoute.school_id == school_id,
                        TransportRoute.id != route_id,
                        func.upper(TransportRoute.route_code) == clean_code,
                        TransportRoute.is_deleted == False,
                    )
                )
                if existing_code:
                    raise AlreadyExistsException(f"Route with code '{clean_code}' already exists")
                route.route_code = clean_code

        if vehicle_id is not None:
            vehicle = db.scalar(
                select(Vehicle).where(
                    Vehicle.id == vehicle_id,
                    Vehicle.school_id == school_id,
                    Vehicle.is_deleted == False,
                )
            )
            if not vehicle:
                raise ValidationException("Referenced vehicle does not exist in this school or has been deleted")
            route.vehicle_id = vehicle_id

        if driver_id is not None:
            driver = db.scalar(
                select(TransportDriver).where(
                    TransportDriver.id == driver_id,
                    TransportDriver.school_id == school_id,
                    TransportDriver.is_deleted == False,
                )
            )
            if not driver:
                raise ValidationException("Referenced driver does not exist in this school or has been deleted")
            route.driver_id = driver_id

        if route_name is not None:
            route.route_name = route_name.strip()
        if description is not None:
            route.description = description.strip() if description else None
        if attendant_name is not None:
            route.attendant_name = attendant_name.strip() if attendant_name else None
        if attendant_phone is not None:
            route.attendant_phone = attendant_phone.strip() if attendant_phone else None
        if morning_start_time is not None:
            route.morning_start_time = morning_start_time
        if evening_start_time is not None:
            route.evening_start_time = evening_start_time
        if is_active is not None:
            route.is_active = is_active

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="ROUTE_UPDATED",
            entity_type="TransportRoute",
            entity_id=str(route.id),
            details=f"Updated route {route.route_code}",
            current_user=current_user,
            user_role=user_role,
        )

        return route

    @staticmethod
    def delete_route(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> bool:
        """
        Soft-deletes a route. Rejects deletion if active student allocations exist on this route.
        """
        route = TransportService.get_route(db, school_id, route_id)

        active_alloc_count = db.scalar(
            select(func.count(StudentTransportAllocation.id)).where(
                StudentTransportAllocation.route_id == route_id,
                StudentTransportAllocation.school_id == school_id,
                StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
                StudentTransportAllocation.is_deleted == False,
            )
        )
        if active_alloc_count and active_alloc_count > 0:
            raise BadRequestException(
                f"Cannot delete route with {active_alloc_count} active student allocations. Reassign or cancel allocations first."
            )

        route.is_deleted = True
        route.deleted_at = datetime.utcnow()

        # Also soft-delete all stops belonging to this route
        stops = db.scalars(
            select(RouteStop).where(
                RouteStop.route_id == route_id,
                RouteStop.school_id == school_id,
                RouteStop.is_deleted == False,
            )
        ).all()
        for stop in stops:
            stop.is_deleted = True
            stop.deleted_at = datetime.utcnow()

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="ROUTE_DELETED",
            entity_type="TransportRoute",
            entity_id=str(route.id),
            details=f"Deleted route {route.route_code}",
            current_user=current_user,
            user_role=user_role,
        )

        return True

    # =========================================================================
    # ROUTE STOP MANAGEMENT & CRUD
    # =========================================================================

    @staticmethod
    def create_stop(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        stop_name: str,
        stop_code: str,
        sequence_order: int,
        morning_pickup_time: time | None = None,
        afternoon_drop_time: time | None = None,
        landmark: str | None = None,
        pickup_fee_amount: Decimal = Decimal("0.00"),
        is_active: bool = True,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> RouteStop:
        """
        Creates a stop for a route. Validates sequence order (> 0), non-negative fee, and route tenant boundary.
        """
        if sequence_order <= 0:
            raise ValidationException("Stop sequence order must be a positive integer greater than zero")

        if pickup_fee_amount < Decimal("0.00"):
            raise ValidationException("Pickup fee amount cannot be negative")

        route = db.scalar(
            select(TransportRoute).where(
                TransportRoute.id == route_id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        )
        if not route:
            raise ValidationException("Referenced route does not exist in this school or has been deleted")

        existing_seq = db.scalar(
            select(RouteStop).where(
                RouteStop.route_id == route_id,
                RouteStop.sequence_order == sequence_order,
                RouteStop.is_deleted == False,
            )
        )
        if existing_seq:
            raise AlreadyExistsException(f"Stop with sequence order {sequence_order} already exists for this route")

        stop = RouteStop(
            school_id=school_id,
            route_id=route_id,
            stop_name=stop_name.strip(),
            stop_code=stop_code.strip().upper(),
            sequence_order=sequence_order,
            morning_pickup_time=morning_pickup_time,
            afternoon_drop_time=afternoon_drop_time,
            landmark=landmark.strip() if landmark else None,
            pickup_fee_amount=pickup_fee_amount,
            is_active=is_active,
        )
        db.add(stop)
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="STOP_CREATED",
            entity_type="RouteStop",
            entity_id=str(stop.id),
            details=f"Created stop {stop.stop_name} on route {route.route_code}",
            current_user=current_user,
            user_role=user_role,
        )

        return stop

    @staticmethod
    def get_stop(db: Session, school_id: UUID, stop_id: UUID) -> RouteStop:
        """
        Retrieves a stop by ID enforcing tenant isolation.
        """
        stop = db.scalar(
            select(RouteStop).where(
                RouteStop.id == stop_id,
                RouteStop.school_id == school_id,
                RouteStop.is_deleted == False,
            )
        )
        if not stop:
            raise NotFoundException("Route stop not found in this school")
        return stop

    @staticmethod
    def list_stops(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        is_active: bool | None = None,
    ) -> list[RouteStop]:
        """
        Lists all stops for a specific route ordered by sequence_order.
        """
        # Validate route exists and belongs to school
        TransportService.get_route(db, school_id, route_id)

        query = select(RouteStop).where(
            RouteStop.school_id == school_id,
            RouteStop.route_id == route_id,
            RouteStop.is_deleted == False,
        )
        if is_active is not None:
            query = query.where(RouteStop.is_active == is_active)

        return list(db.scalars(query.order_by(RouteStop.sequence_order.asc())).all())

    @staticmethod
    def update_stop(
        db: Session,
        school_id: UUID,
        stop_id: UUID,
        stop_name: str | None = None,
        stop_code: str | None = None,
        sequence_order: int | None = None,
        morning_pickup_time: time | None = None,
        afternoon_drop_time: time | None = None,
        landmark: str | None = None,
        pickup_fee_amount: Decimal | None = None,
        is_active: bool | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> RouteStop:
        """
        Updates a route stop.
        """
        stop = TransportService.get_stop(db, school_id, stop_id)

        if sequence_order is not None:
            if sequence_order <= 0:
                raise ValidationException("Stop sequence order must be a positive integer greater than zero")
            if sequence_order != stop.sequence_order:
                existing_seq = db.scalar(
                    select(RouteStop).where(
                        RouteStop.route_id == stop.route_id,
                        RouteStop.id != stop_id,
                        RouteStop.sequence_order == sequence_order,
                        RouteStop.is_deleted == False,
                    )
                )
                if existing_seq:
                    raise AlreadyExistsException(
                        f"Stop with sequence order {sequence_order} already exists for this route"
                    )
                stop.sequence_order = sequence_order

        if pickup_fee_amount is not None:
            if pickup_fee_amount < Decimal("0.00"):
                raise ValidationException("Pickup fee amount cannot be negative")
            stop.pickup_fee_amount = pickup_fee_amount

        if stop_name is not None:
            stop.stop_name = stop_name.strip()
        if stop_code is not None:
            stop.stop_code = stop_code.strip().upper()
        if morning_pickup_time is not None:
            stop.morning_pickup_time = morning_pickup_time
        if afternoon_drop_time is not None:
            stop.afternoon_drop_time = afternoon_drop_time
        if landmark is not None:
            stop.landmark = landmark.strip() if landmark else None
        if is_active is not None:
            stop.is_active = is_active

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="STOP_UPDATED",
            entity_type="RouteStop",
            entity_id=str(stop.id),
            details=f"Updated stop {stop.stop_name}",
            current_user=current_user,
            user_role=user_role,
        )

        return stop

    @staticmethod
    def delete_stop(
        db: Session,
        school_id: UUID,
        stop_id: UUID,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> bool:
        """
        Soft-deletes a route stop. Rejects deletion if any active allocations use this stop.
        """
        stop = TransportService.get_stop(db, school_id, stop_id)

        active_alloc_count = db.scalar(
            select(func.count(StudentTransportAllocation.id)).where(
                or_(
                    StudentTransportAllocation.pickup_stop_id == stop_id,
                    StudentTransportAllocation.drop_stop_id == stop_id,
                ),
                StudentTransportAllocation.school_id == school_id,
                StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
                StudentTransportAllocation.is_deleted == False,
            )
        )
        if active_alloc_count and active_alloc_count > 0:
            raise BadRequestException(
                f"Cannot delete stop referenced by {active_alloc_count} active student allocations."
            )

        stop.is_deleted = True
        stop.deleted_at = datetime.utcnow()
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="STOP_DELETED",
            entity_type="RouteStop",
            entity_id=str(stop.id),
            details=f"Deleted stop {stop.stop_name}",
            current_user=current_user,
            user_role=user_role,
        )

        return True

    # =========================================================================
    # STUDENT TRANSPORT ALLOCATION & BUSINESS INVARIANTS
    # =========================================================================

    @staticmethod
    def allocate_student(
        db: Session,
        school_id: UUID,
        student_id: UUID,
        route_id: UUID,
        academic_year_id: UUID,
        allocation_type: TransportAllocationType,
        start_date: date,
        pickup_stop_id: UUID | None = None,
        drop_stop_id: UUID | None = None,
        end_date: date | None = None,
        remarks: str | None = None,
        status: TransportAllocationStatus = TransportAllocationStatus.ACTIVE,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> StudentTransportAllocation:
        """
        Allocates a student to a transport route.
        Enforces:
        1. Allocation type rules (TWO_WAY, PICKUP_ONLY, DROP_ONLY).
        2. Strict tenant isolation.
        3. Stops belong to route.
        4. Unique active allocation per student per academic year.
        5. Vehicle seating capacity limit enforcement.
        """
        if allocation_type == TransportAllocationType.TWO_WAY:
            if not pickup_stop_id or not drop_stop_id:
                raise ValidationException("TWO_WAY allocation requires both pickup_stop_id and drop_stop_id")
        elif allocation_type == TransportAllocationType.PICKUP_ONLY:
            if not pickup_stop_id:
                raise ValidationException("PICKUP_ONLY allocation requires pickup_stop_id")
            if drop_stop_id is not None:
                raise ValidationException("PICKUP_ONLY allocation must not have drop_stop_id specified")
        elif allocation_type == TransportAllocationType.DROP_ONLY:
            if not drop_stop_id:
                raise ValidationException("DROP_ONLY allocation requires drop_stop_id")
            if pickup_stop_id is not None:
                raise ValidationException("DROP_ONLY allocation must not have pickup_stop_id specified")
        else:
            raise ValidationException(f"Unsupported allocation type: {allocation_type}")

        student = db.scalar(
            select(Student).where(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        )
        if not student:
            raise ValidationException("Student does not exist in this school or has been deleted")

        academic_year = db.scalar(
            select(AcademicYear).where(
                AcademicYear.id == academic_year_id,
                AcademicYear.school_id == school_id,
                AcademicYear.is_deleted == False,
            )
        )
        if not academic_year:
            raise ValidationException("Academic year does not exist in this school or has been deleted")

        route = db.scalar(
            select(TransportRoute).where(
                TransportRoute.id == route_id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        )
        if not route:
            raise ValidationException("Route does not exist in this school or has been deleted")

        if pickup_stop_id:
            pickup_stop = db.scalar(
                select(RouteStop).where(
                    RouteStop.id == pickup_stop_id,
                    RouteStop.route_id == route_id,
                    RouteStop.school_id == school_id,
                    RouteStop.is_deleted == False,
                )
            )
            if not pickup_stop:
                raise ValidationException("Pickup stop does not belong to the selected route or school")

        if drop_stop_id:
            drop_stop = db.scalar(
                select(RouteStop).where(
                    RouteStop.id == drop_stop_id,
                    RouteStop.route_id == route_id,
                    RouteStop.school_id == school_id,
                    RouteStop.is_deleted == False,
                )
            )
            if not drop_stop:
                raise ValidationException("Drop stop does not belong to the selected route or school")

        if status == TransportAllocationStatus.ACTIVE:
            existing_active = db.scalar(
                select(StudentTransportAllocation).where(
                    StudentTransportAllocation.school_id == school_id,
                    StudentTransportAllocation.student_id == student_id,
                    StudentTransportAllocation.academic_year_id == academic_year_id,
                    StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
                    StudentTransportAllocation.is_deleted == False,
                )
            )
            if existing_active:
                raise AlreadyExistsException(
                    "Student already has an active transport allocation for this academic year"
                )

            TransportService._check_vehicle_capacity(
                db=db,
                school_id=school_id,
                route_id=route_id,
                academic_year_id=academic_year_id,
            )

        allocation = StudentTransportAllocation(
            school_id=school_id,
            student_id=student_id,
            route_id=route_id,
            pickup_stop_id=pickup_stop_id,
            drop_stop_id=drop_stop_id,
            academic_year_id=academic_year_id,
            allocation_type=allocation_type,
            status=status,
            start_date=start_date,
            end_date=end_date,
            remarks=remarks.strip() if remarks else None,
        )
        db.add(allocation)
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="STUDENT_ALLOCATED",
            entity_type="StudentTransportAllocation",
            entity_id=str(allocation.id),
            details=f"Allocated student {student_id} to route {route.route_code}",
            current_user=current_user,
            user_role=user_role,
        )

        return allocation

    @staticmethod
    def get_allocation(
        db: Session,
        school_id: UUID,
        allocation_id: UUID,
    ) -> StudentTransportAllocation:
        """
        Retrieves a student transport allocation by ID enforcing tenant isolation.
        """
        allocation = db.scalar(
            select(StudentTransportAllocation)
            .options(
                joinedload(StudentTransportAllocation.student),
                joinedload(StudentTransportAllocation.route),
                joinedload(StudentTransportAllocation.pickup_stop),
                joinedload(StudentTransportAllocation.drop_stop),
            )
            .where(
                StudentTransportAllocation.id == allocation_id,
                StudentTransportAllocation.school_id == school_id,
                StudentTransportAllocation.is_deleted == False,
            )
        )
        if not allocation:
            raise NotFoundException("Transport allocation not found in this school")
        return allocation

    @staticmethod
    def list_allocations(
        db: Session,
        school_id: UUID,
        student_id: UUID | None = None,
        route_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        status: TransportAllocationStatus | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[StudentTransportAllocation], int, int]:
        """
        Lists student transport allocations with filtering and pagination.
        """
        query = select(StudentTransportAllocation).where(
            StudentTransportAllocation.school_id == school_id,
            StudentTransportAllocation.is_deleted == False,
        )

        if student_id is not None:
            query = query.where(StudentTransportAllocation.student_id == student_id)
        if route_id is not None:
            query = query.where(StudentTransportAllocation.route_id == route_id)
        if academic_year_id is not None:
            query = query.where(StudentTransportAllocation.academic_year_id == academic_year_id)
        if status is not None:
            query = query.where(StudentTransportAllocation.status == status)

        count_query = select(func.count()).select_from(query.subquery())
        total_count = db.scalar(count_query) or 0

        offset = (page - 1) * page_size
        items = db.scalars(
            query.options(
                joinedload(StudentTransportAllocation.student),
                joinedload(StudentTransportAllocation.route),
                joinedload(StudentTransportAllocation.pickup_stop),
                joinedload(StudentTransportAllocation.drop_stop),
            )
            .order_by(StudentTransportAllocation.created_at.desc())
            .offset(offset)
            .limit(page_size)
        ).all()

        total_pages = math.ceil(total_count / page_size) if page_size > 0 else 1
        return list(items), total_count, total_pages

    @staticmethod
    def update_allocation(
        db: Session,
        school_id: UUID,
        allocation_id: UUID,
        route_id: UUID | None = None,
        allocation_type: TransportAllocationType | None = None,
        pickup_stop_id: UUID | None = None,
        drop_stop_id: UUID | None = None,
        start_date: date | None = None,
        end_date: date | None = None,
        remarks: str | None = None,
        status: TransportAllocationStatus | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> StudentTransportAllocation:
        """
        Updates student transport allocation parameters.
        """
        allocation = TransportService.get_allocation(db, school_id, allocation_id)

        target_route_id = route_id if route_id is not None else allocation.route_id
        target_type = allocation_type if allocation_type is not None else allocation.allocation_type
        target_pickup = pickup_stop_id if pickup_stop_id is not None else allocation.pickup_stop_id
        target_drop = drop_stop_id if drop_stop_id is not None else allocation.drop_stop_id
        target_status = status if status is not None else allocation.status

        # Validate target route if changed
        if route_id is not None and route_id != allocation.route_id:
            route = db.scalar(
                select(TransportRoute).where(
                    TransportRoute.id == route_id,
                    TransportRoute.school_id == school_id,
                    TransportRoute.is_deleted == False,
                )
            )
            if not route:
                raise ValidationException("Route does not exist in this school or has been deleted")
            allocation.route_id = route_id

        # Validate stops with respect to allocation type
        if target_type == TransportAllocationType.TWO_WAY:
            if not target_pickup or not target_drop:
                raise ValidationException("TWO_WAY allocation requires both pickup_stop_id and drop_stop_id")
        elif target_type == TransportAllocationType.PICKUP_ONLY:
            if not target_pickup:
                raise ValidationException("PICKUP_ONLY allocation requires pickup_stop_id")
            target_drop = None
        elif target_type == TransportAllocationType.DROP_ONLY:
            if not target_drop:
                raise ValidationException("DROP_ONLY allocation requires drop_stop_id")
            target_pickup = None

        if target_pickup:
            stop = db.scalar(
                select(RouteStop).where(
                    RouteStop.id == target_pickup,
                    RouteStop.route_id == target_route_id,
                    RouteStop.school_id == school_id,
                    RouteStop.is_deleted == False,
                )
            )
            if not stop:
                raise ValidationException("Pickup stop does not belong to the route or school")

        if target_drop:
            stop = db.scalar(
                select(RouteStop).where(
                    RouteStop.id == target_drop,
                    RouteStop.route_id == target_route_id,
                    RouteStop.school_id == school_id,
                    RouteStop.is_deleted == False,
                )
            )
            if not stop:
                raise ValidationException("Drop stop does not belong to the route or school")

        # Capacity check if target state is active
        if target_status == TransportAllocationStatus.ACTIVE:
            TransportService._check_vehicle_capacity(
                db=db,
                school_id=school_id,
                route_id=target_route_id,
                academic_year_id=allocation.academic_year_id,
                exclude_allocation_id=allocation.id,
            )

        # If status changed to ACTIVE, verify no other active exists
        if status == TransportAllocationStatus.ACTIVE and allocation.status != TransportAllocationStatus.ACTIVE:
            existing_active = db.scalar(
                select(StudentTransportAllocation).where(
                    StudentTransportAllocation.school_id == school_id,
                    StudentTransportAllocation.student_id == allocation.student_id,
                    StudentTransportAllocation.academic_year_id == allocation.academic_year_id,
                    StudentTransportAllocation.id != allocation.id,
                    StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
                    StudentTransportAllocation.is_deleted == False,
                )
            )
            if existing_active:
                raise AlreadyExistsException(
                    "Student already has another active transport allocation for this academic year"
                )

        allocation.allocation_type = target_type
        allocation.pickup_stop_id = target_pickup
        allocation.drop_stop_id = target_drop

        if start_date is not None:
            allocation.start_date = start_date
        if end_date is not None:
            allocation.end_date = end_date
        if remarks is not None:
            allocation.remarks = remarks.strip() if remarks else None
        if status is not None:
            allocation.status = status

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="ALLOCATION_UPDATED",
            entity_type="StudentTransportAllocation",
            entity_id=str(allocation.id),
            details=f"Updated transport allocation for student {allocation.student_id}",
            current_user=current_user,
            user_role=user_role,
        )

        return allocation

    @staticmethod
    def update_allocation_status(
        db: Session,
        school_id: UUID,
        allocation_id: UUID,
        status: TransportAllocationStatus,
        remarks: str | None = None,
        end_date: date | None = None,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> StudentTransportAllocation:
        """
        Updates the status of an allocation (e.g. SUSPENDED, CANCELLED, COMPLETED).
        """
        allocation = TransportService.get_allocation(db, school_id, allocation_id)

        if status == TransportAllocationStatus.ACTIVE and allocation.status != TransportAllocationStatus.ACTIVE:
            TransportService._check_vehicle_capacity(
                db=db,
                school_id=school_id,
                route_id=allocation.route_id,
                academic_year_id=allocation.academic_year_id,
                exclude_allocation_id=allocation.id,
            )

            existing_active = db.scalar(
                select(StudentTransportAllocation).where(
                    StudentTransportAllocation.school_id == school_id,
                    StudentTransportAllocation.student_id == allocation.student_id,
                    StudentTransportAllocation.academic_year_id == allocation.academic_year_id,
                    StudentTransportAllocation.id != allocation.id,
                    StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
                    StudentTransportAllocation.is_deleted == False,
                )
            )
            if existing_active:
                raise AlreadyExistsException(
                    "Student already has another active transport allocation for this academic year"
                )

        allocation.status = status
        if remarks:
            allocation.remarks = remarks.strip()
        if end_date:
            allocation.end_date = end_date
        elif status == TransportAllocationStatus.CANCELLED and not allocation.end_date:
            allocation.end_date = date.today()

        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="ALLOCATION_STATUS_UPDATED",
            entity_type="StudentTransportAllocation",
            entity_id=str(allocation.id),
            details=f"Updated allocation status to {status.value if hasattr(status, 'value') else status}",
            current_user=current_user,
            user_role=user_role,
        )

        return allocation

    @staticmethod
    def delete_allocation(
        db: Session,
        school_id: UUID,
        allocation_id: UUID,
        current_user: Any = None,
        user_role: str | None = None,
    ) -> bool:
        """
        Soft-deletes a student transport allocation.
        """
        allocation = TransportService.get_allocation(db, school_id, allocation_id)
        allocation.is_deleted = True
        allocation.deleted_at = datetime.utcnow()
        db.flush()

        TransportService._write_audit_log(
            db=db,
            school_id=school_id,
            action="ALLOCATION_DELETED",
            entity_type="StudentTransportAllocation",
            entity_id=str(allocation.id),
            details=f"Deleted transport allocation for student {allocation.student_id}",
            current_user=current_user,
            user_role=user_role,
        )

        return True

    # =========================================================================
    # CAPACITY, OCCUPANCY & DASHBOARD ANALYTICS
    # =========================================================================

    @staticmethod
    def get_route_active_allocation_count(
        db: Session,
        school_id: UUID,
        route_id: UUID,
        academic_year_id: UUID | None = None,
    ) -> int:
        """
        Derives the number of active student passengers allocated to a route.
        """
        query = select(func.count(StudentTransportAllocation.id)).where(
            StudentTransportAllocation.school_id == school_id,
            StudentTransportAllocation.route_id == route_id,
            StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
            StudentTransportAllocation.is_deleted == False,
        )
        if academic_year_id:
            query = query.where(StudentTransportAllocation.academic_year_id == academic_year_id)

        count = db.scalar(query)
        return count or 0

    @staticmethod
    def get_vehicle_occupancy_stats(
        db: Session,
        school_id: UUID,
        vehicle_id: UUID,
        academic_year_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Derives occupancy and remaining capacity for a vehicle across all its assigned routes.
        """
        vehicle = TransportService.get_vehicle(db, school_id, vehicle_id)

        routes = db.scalars(
            select(TransportRoute).where(
                TransportRoute.vehicle_id == vehicle_id,
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        ).all()

        route_ids = [r.id for r in routes]
        total_allocated = 0
        if route_ids:
            query = select(func.count(StudentTransportAllocation.id)).where(
                StudentTransportAllocation.school_id == school_id,
                StudentTransportAllocation.route_id.in_(route_ids),
                StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
                StudentTransportAllocation.is_deleted == False,
            )
            if academic_year_id:
                query = query.where(StudentTransportAllocation.academic_year_id == academic_year_id)
            total_allocated = db.scalar(query) or 0

        available_seats = max(0, vehicle.seating_capacity - total_allocated)
        is_overbooked = total_allocated > vehicle.seating_capacity

        return {
            "vehicle_id": vehicle.id,
            "vehicle_code": vehicle.vehicle_code,
            "registration_number": vehicle.registration_number,
            "seating_capacity": vehicle.seating_capacity,
            "total_allocated": total_allocated,
            "available_seats": available_seats,
            "is_overbooked": is_overbooked,
            "assigned_route_count": len(routes),
        }

    @staticmethod
    def get_transport_dashboard_stats(
        db: Session,
        school_id: UUID,
        academic_year_id: UUID | None = None,
    ) -> dict[str, Any]:
        """
        Aggregates dashboard KPIs for vehicles, drivers, routes, and passenger occupancy.
        """
        # Vehicle metrics
        total_vehicles = db.scalar(
            select(func.count(Vehicle.id)).where(
                Vehicle.school_id == school_id,
                Vehicle.is_deleted == False,
            )
        ) or 0

        active_vehicles = db.scalar(
            select(func.count(Vehicle.id)).where(
                Vehicle.school_id == school_id,
                Vehicle.status == VehicleStatus.ACTIVE,
                Vehicle.is_deleted == False,
            )
        ) or 0

        maintenance_vehicles = db.scalar(
            select(func.count(Vehicle.id)).where(
                Vehicle.school_id == school_id,
                Vehicle.status == VehicleStatus.MAINTENANCE,
                Vehicle.is_deleted == False,
            )
        ) or 0

        total_seating_capacity = db.scalar(
            select(func.sum(Vehicle.seating_capacity)).where(
                Vehicle.school_id == school_id,
                Vehicle.status == VehicleStatus.ACTIVE,
                Vehicle.is_deleted == False,
            )
        ) or 0

        # Driver metrics
        total_drivers = db.scalar(
            select(func.count(TransportDriver.id)).where(
                TransportDriver.school_id == school_id,
                TransportDriver.is_deleted == False,
            )
        ) or 0

        active_drivers = db.scalar(
            select(func.count(TransportDriver.id)).where(
                TransportDriver.school_id == school_id,
                TransportDriver.is_active == True,
                TransportDriver.is_deleted == False,
            )
        ) or 0

        # Route metrics
        total_routes = db.scalar(
            select(func.count(TransportRoute.id)).where(
                TransportRoute.school_id == school_id,
                TransportRoute.is_deleted == False,
            )
        ) or 0

        active_routes = db.scalar(
            select(func.count(TransportRoute.id)).where(
                TransportRoute.school_id == school_id,
                TransportRoute.is_active == True,
                TransportRoute.is_deleted == False,
            )
        ) or 0

        # Student allocation metrics
        alloc_query = select(func.count(StudentTransportAllocation.id)).where(
            StudentTransportAllocation.school_id == school_id,
            StudentTransportAllocation.status == TransportAllocationStatus.ACTIVE,
            StudentTransportAllocation.is_deleted == False,
        )
        if academic_year_id:
            alloc_query = alloc_query.where(StudentTransportAllocation.academic_year_id == academic_year_id)
        total_allocated_students = db.scalar(alloc_query) or 0

        overall_occupancy_percentage = (
            round((total_allocated_students / total_seating_capacity) * 100.0, 2)
            if total_seating_capacity > 0
            else 0.0
        )

        return {
            "total_vehicles": total_vehicles,
            "active_vehicles": active_vehicles,
            "maintenance_vehicles": maintenance_vehicles,
            "total_drivers": total_drivers,
            "active_drivers": active_drivers,
            "total_routes": total_routes,
            "active_routes": active_routes,
            "total_allocated_students": total_allocated_students,
            "total_seating_capacity": total_seating_capacity,
            "overall_occupancy_percentage": overall_occupancy_percentage,
        }


transport_service = TransportService()
