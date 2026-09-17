from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, List, Optional
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.common.authorization import enforce_relationship_access
from app.common.responses import ApiResponse
from app.dependencies import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.common.enums.fees import PaymentMode
from app.services.hostel_service import hostel_service
from app.services.hostel_attendance_service import hostel_attendance_service
from app.services.hostel_outpass_service import hostel_outpass_service
from app.services.hostel_fee_service import hostel_fee_service


router = APIRouter()

# --- Pydantic Schemas ---
class BuildingCreateSchema(BaseModel):
    name: str
    code: str
    gender_designation: str = "BOYS"
    capacity: int = 100
    is_active: bool = True
    description: Optional[str] = None

class BuildingUpdateSchema(BaseModel):
    name: Optional[str] = None
    gender_designation: Optional[str] = None
    capacity: Optional[int] = None
    is_active: Optional[bool] = None
    description: Optional[str] = None

class RoomCreateSchema(BaseModel):
    room_number: str
    floor: int = 1
    room_type: str = "STANDARD"
    capacity: int = 4
    is_active: bool = True
    notes: Optional[str] = None

class BedCreateSchema(BaseModel):
    bed_number: str
    status: str = "AVAILABLE"
    is_active: bool = True

class AllocationCreateSchema(BaseModel):
    student_id: uuid.UUID
    building_id: uuid.UUID
    room_id: uuid.UUID
    bed_id: uuid.UUID
    allocated_at: date
    reason: Optional[str] = None

class AllocationReleaseSchema(BaseModel):
    released_at: date
    reason: Optional[str] = None

class HostelAttendanceRecordSchema(BaseModel):
    student_id: uuid.UUID
    status: str = "PRESENT"
    remarks: Optional[str] = None

class HostelAttendanceBulkSchema(BaseModel):
    attendance_date: date
    building_id: uuid.UUID
    room_id: uuid.UUID
    records: List[HostelAttendanceRecordSchema]

class OutpassCreateSchema(BaseModel):
    student_id: uuid.UUID
    reason: str
    destination: str
    departure_time: datetime
    expected_return_time: datetime
    emergency_contact: Optional[str] = None
    remarks: Optional[str] = None

class OutpassApprovalSchema(BaseModel):
    approve: bool
    remarks: Optional[str] = None

class FeeStructureCreateSchema(BaseModel):
    academic_year_id: uuid.UUID
    name: str
    amount: float
    description: Optional[str] = None

class FeeAllocationCreateSchema(BaseModel):
    student_id: uuid.UUID
    fee_structure_id: uuid.UUID
    due_date: date

class FeePaymentSchema(BaseModel):
    payment_amount: float
    payment_mode: Optional[str] = "CASH"
    reference_number: Optional[str] = None
    remarks: Optional[str] = None


# --- BUILDINGS ENDPOINTS ---
@router.post("/buildings", status_code=201)
def create_building(
    payload: BuildingCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.create")),
    db: Session = Depends(get_db),
):
    building = hostel_service.create_building(db, current_user.school_id, payload.model_dump())
    return ApiResponse.success(message="Hostel building created successfully.", data={"id": str(building.id), "code": building.code})

@router.get("/buildings")
def get_buildings(
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    buildings = hostel_service.get_buildings(db, current_user.school_id)
    data = [
        {
            "id": str(b.id),
            "name": b.name,
            "code": b.code,
            "gender_designation": b.gender_designation,
            "capacity": b.capacity,
            "is_active": b.is_active,
            "description": b.description,
        }
        for b in buildings
    ]
    return ApiResponse.success(data=data)

@router.put("/buildings/{building_id}")
def update_building(
    building_id: uuid.UUID,
    payload: BuildingUpdateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.update")),
    db: Session = Depends(get_db),
):
    building = hostel_service.update_building(db, current_user.school_id, building_id, payload.model_dump(exclude_unset=True))
    return ApiResponse.success(message="Hostel building updated successfully.", data={"id": str(building.id)})


# --- ROOMS ENDPOINTS ---
@router.post("/buildings/{building_id}/rooms", status_code=201)
def create_room(
    building_id: uuid.UUID,
    payload: RoomCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.create")),
    db: Session = Depends(get_db),
):
    room = hostel_service.create_room(db, current_user.school_id, building_id, payload.model_dump())
    return ApiResponse.success(message="Hostel room created successfully.", data={"id": str(room.id)})

@router.get("/rooms")
def get_rooms(
    building_id: Optional[uuid.UUID] = Query(None),
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    rooms = hostel_service.get_rooms(db, current_user.school_id, building_id)
    data = [
        {
            "id": str(r.id),
            "building_id": str(r.building_id),
            "room_number": r.room_number,
            "floor": r.floor,
            "room_type": r.room_type,
            "capacity": r.capacity,
            "is_active": r.is_active,
            "notes": r.notes,
        }
        for r in rooms
    ]
    return ApiResponse.success(data=data)


# --- BEDS ENDPOINTS ---
@router.post("/rooms/{room_id}/beds", status_code=201)
def create_bed(
    room_id: uuid.UUID,
    payload: BedCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.create")),
    db: Session = Depends(get_db),
):
    bed = hostel_service.create_bed(db, current_user.school_id, room_id, payload.model_dump())
    return ApiResponse.success(message="Hostel bed created successfully.", data={"id": str(bed.id)})

@router.get("/beds")
def get_beds(
    room_id: Optional[uuid.UUID] = Query(None),
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    beds = hostel_service.get_beds(db, current_user.school_id, room_id)
    data = [
        {
            "id": str(b.id),
            "room_id": str(b.room_id),
            "bed_number": b.bed_number,
            "status": b.status,
            "is_active": b.is_active,
        }
        for b in beds
    ]
    return ApiResponse.success(data=data)


# --- ALLOCATIONS ENDPOINTS ---
@router.post("/allocations", status_code=201)
def allocate_student(
    payload: AllocationCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.allocate")),
    db: Session = Depends(get_db),
):
    alloc = hostel_service.allocate_student(
        db=db,
        school_id=current_user.school_id,
        student_id=payload.student_id,
        building_id=payload.building_id,
        room_id=payload.room_id,
        bed_id=payload.bed_id,
        allocated_at=payload.allocated_at,
        reason=payload.reason,
    )
    return ApiResponse.success(message="Student allocated to hostel bed successfully.", data={"id": str(alloc.id)})

@router.put("/allocations/{allocation_id}/release")
def release_allocation(
    allocation_id: uuid.UUID,
    payload: AllocationReleaseSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.allocate")),
    db: Session = Depends(get_db),
):
    alloc = hostel_service.release_student_allocation(
        db=db,
        school_id=current_user.school_id,
        allocation_id=allocation_id,
        released_at=payload.released_at,
        reason=payload.reason,
    )
    return ApiResponse.success(message="Hostel allocation released successfully.", data={"id": str(alloc.id)})

@router.get("/allocations")
def get_allocations(
    student_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query("ACTIVE"),
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    if student_id:
        enforce_relationship_access(db, current_user.school_id, current_user, student_id)

    allocations = hostel_service.get_allocations(db, current_user.school_id, student_id, status)
    data = [
        {
            "id": str(a.id),
            "student_id": str(a.student_id),
            "building_id": str(a.building_id),
            "room_id": str(a.room_id),
            "bed_id": str(a.bed_id),
            "allocated_at": str(a.allocated_at),
            "released_at": str(a.released_at) if a.released_at else None,
            "status": a.status,
            "reason": a.reason,
        }
        for a in allocations
    ]
    return ApiResponse.success(data=data)


# --- ATTENDANCE ENDPOINTS ---
@router.post("/attendance/bulk", status_code=201)
def record_hostel_attendance(
    payload: HostelAttendanceBulkSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.attendance")),
    db: Session = Depends(get_db),
):
    records_dict = [r.model_dump() for r in payload.records]
    results = hostel_attendance_service.bulk_record_attendance(
        db=db,
        school_id=current_user.school_id,
        attendance_date=payload.attendance_date,
        building_id=payload.building_id,
        room_id=payload.room_id,
        records=records_dict,
        recorded_by_id=current_user.id,
    )
    return ApiResponse.success(message=f"Hostel attendance recorded for {len(results)} students.", data={"count": len(results)})

@router.get("/attendance")
def get_hostel_attendance(
    attendance_date: Optional[date] = Query(None),
    building_id: Optional[uuid.UUID] = Query(None),
    student_id: Optional[uuid.UUID] = Query(None),
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    if student_id:
        enforce_relationship_access(db, current_user.school_id, current_user, student_id)

    records = hostel_attendance_service.get_attendance(db, current_user.school_id, attendance_date, building_id, student_id)
    data = [
        {
            "id": str(r.id),
            "attendance_date": str(r.attendance_date),
            "building_id": str(r.building_id),
            "room_id": str(r.room_id),
            "student_id": str(r.student_id),
            "status": r.status,
            "remarks": r.remarks,
        }
        for r in records
    ]
    return ApiResponse.success(data=data)


# --- OUTPASS ENDPOINTS ---
@router.post("/outpasses", status_code=201)
def create_outpass(
    payload: OutpassCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.outpass.create")),
    db: Session = Depends(get_db),
):
    enforce_relationship_access(db, current_user.school_id, current_user, payload.student_id)

    outpass = hostel_outpass_service.create_outpass_request(
        db=db,
        school_id=current_user.school_id,
        student_id=payload.student_id,
        requested_by_id=current_user.id,
        reason=payload.reason,
        destination=payload.destination,
        departure_time=payload.departure_time,
        expected_return_time=payload.expected_return_time,
        emergency_contact=payload.emergency_contact,
        remarks=payload.remarks,
    )
    return ApiResponse.success(message="Hostel outpass requested successfully.", data={"id": str(outpass.id), "status": outpass.status})

@router.put("/outpasses/{outpass_id}/approve")
def approve_outpass(
    outpass_id: uuid.UUID,
    payload: OutpassApprovalSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.outpass.approve")),
    db: Session = Depends(get_db),
):
    outpass = hostel_outpass_service.approve_outpass(
        db=db,
        school_id=current_user.school_id,
        outpass_id=outpass_id,
        approved_by_id=current_user.id,
        approve=payload.approve,
        remarks=payload.remarks,
    )
    return ApiResponse.success(message=f"Outpass status updated to '{outpass.status}'.", data={"id": str(outpass.id), "status": outpass.status})

@router.put("/outpasses/{outpass_id}/checkout")
def checkout_outpass(
    outpass_id: uuid.UUID,
    current_user: IdentityUser = Depends(require_permission("hostel.outpass.approve")),
    db: Session = Depends(get_db),
):
    outpass = hostel_outpass_service.checkout_student(db, current_user.school_id, outpass_id)
    return ApiResponse.success(message="Student checked out successfully.", data={"id": str(outpass.id), "status": outpass.status})

@router.put("/outpasses/{outpass_id}/return")
def return_outpass(
    outpass_id: uuid.UUID,
    current_user: IdentityUser = Depends(require_permission("hostel.outpass.approve")),
    db: Session = Depends(get_db),
):
    outpass = hostel_outpass_service.return_student(db, current_user.school_id, outpass_id)
    return ApiResponse.success(message="Student returned successfully.", data={"id": str(outpass.id), "status": outpass.status})

@router.get("/outpasses")
def get_outpasses(
    student_id: Optional[uuid.UUID] = Query(None),
    status: Optional[str] = Query(None),
    current_user: IdentityUser = Depends(require_permission("hostel.outpass.view")),
    db: Session = Depends(get_db),
):
    if student_id:
        enforce_relationship_access(db, current_user.school_id, current_user, student_id)

    outpasses = hostel_outpass_service.get_outpasses(db, current_user.school_id, student_id, status)
    data = [
        {
            "id": str(o.id),
            "student_id": str(o.student_id),
            "building_id": str(o.building_id),
            "room_id": str(o.room_id),
            "reason": o.reason,
            "destination": o.destination,
            "departure_time": o.departure_time.isoformat(),
            "expected_return_time": o.expected_return_time.isoformat(),
            "actual_checkout_time": o.actual_checkout_time.isoformat() if o.actual_checkout_time else None,
            "actual_return_time": o.actual_return_time.isoformat() if o.actual_return_time else None,
            "status": o.status,
            "remarks": o.remarks,
        }
        for o in outpasses
    ]
    return ApiResponse.success(data=data)


# --- FEES ENDPOINTS ---
@router.post("/fees/structures", status_code=201)
def create_fee_structure(
    payload: FeeStructureCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.fees.manage")),
    db: Session = Depends(get_db),
):
    struct = hostel_fee_service.create_fee_structure(
        db=db,
        school_id=current_user.school_id,
        academic_year_id=payload.academic_year_id,
        name=payload.name,
        amount=payload.amount,
        description=payload.description,
    )
    return ApiResponse.success(message="Hostel fee structure created successfully.", data={"id": str(struct.id)})

@router.get("/fees/structures")
def get_fee_structures(
    academic_year_id: Optional[uuid.UUID] = Query(None),
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    structures = hostel_fee_service.get_fee_structures(db, current_user.school_id, academic_year_id)
    data = [
        {
            "id": str(s.id),
            "academic_year_id": str(s.academic_year_id),
            "name": s.name,
            "amount": float(s.amount),
            "description": s.description,
        }
        for s in structures
    ]
    return ApiResponse.success(data=data)

@router.post("/fees/allocations", status_code=201)
def allocate_fee_to_student(
    payload: FeeAllocationCreateSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.fees.manage")),
    db: Session = Depends(get_db),
):
    alloc = hostel_fee_service.allocate_fee_to_student(
        db=db,
        school_id=current_user.school_id,
        student_id=payload.student_id,
        fee_structure_id=payload.fee_structure_id,
        due_date=payload.due_date,
    )
    return ApiResponse.success(message="Hostel fee allocated to student successfully.", data={"id": str(alloc.id)})

@router.put("/fees/allocations/{allocation_id}/pay")
def record_fee_payment(
    allocation_id: uuid.UUID,
    payload: FeePaymentSchema,
    current_user: IdentityUser = Depends(require_permission("hostel.fees.manage")),
    db: Session = Depends(get_db),
):
    payment_mode = PaymentMode.CASH
    if payload.payment_mode:
        try:
            payment_mode = PaymentMode(payload.payment_mode.upper())
        except ValueError:
            payment_mode = PaymentMode.CASH

    alloc = hostel_fee_service.record_fee_payment(
        db=db,
        school_id=current_user.school_id,
        allocation_id=allocation_id,
        payment_amount=payload.payment_amount,
        payment_mode=payment_mode,
        reference_number=payload.reference_number,
        remarks=payload.remarks,
    )
    return ApiResponse.success(
        message="Fee payment recorded successfully.",
        data={
            "id": str(alloc.id),
            "status": alloc.status,
            "paid_amount": float(alloc.paid_amount),
            "amount_due": float(alloc.amount_due),
        },
    )

@router.get("/fees/allocations")
def get_fee_allocations(
    student_id: Optional[uuid.UUID] = Query(None),
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    if student_id:
        enforce_relationship_access(db, current_user.school_id, current_user, student_id)

    allocations = hostel_fee_service.get_student_fee_allocations(db, current_user.school_id, student_id)
    data = [
        {
            "id": str(a.id),
            "student_id": str(a.student_id),
            "fee_structure_id": str(a.fee_structure_id),
            "due_date": str(a.due_date),
            "amount_due": float(a.amount_due),
            "paid_amount": float(a.paid_amount),
            "status": a.status,
        }
        for a in allocations
    ]
    return ApiResponse.success(data=data)


# --- DASHBOARD ENDPOINT ---
@router.get("/dashboard")
def get_hostel_dashboard(
    current_user: IdentityUser = Depends(require_permission("hostel.view")),
    db: Session = Depends(get_db),
):
    metrics = hostel_service.get_dashboard_metrics(db, current_user.school_id)
    return ApiResponse.success(data=metrics)
