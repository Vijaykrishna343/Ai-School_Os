from __future__ import annotations

import uuid
from datetime import date
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, func, and_

from app.models.hostel.hostel_building import HostelBuilding
from app.models.hostel.hostel_room import HostelRoom
from app.models.hostel.hostel_bed import HostelBed
from app.models.hostel.hostel_allocation import HostelAllocation
from app.models.hostel.hostel_attendance import HostelAttendance
from app.models.hostel.hostel_outpass import HostelOutpass
from app.models.hostel.hostel_fee import HostelFeeAllocation
from app.models.student.student import Student
from app.common.exceptions import (
    AlreadyExistsException,
    BadRequestException,
    NotFoundException,
)


class HostelService:
    """
    Service layer for Hostel buildings, rooms, beds, allocations, and dashboard metrics.
    Strictly tenant-scoped by school_id.
    """

    # BUILDINGS
    def create_building(self, db: Session, school_id: uuid.UUID, data: dict) -> HostelBuilding:
        existing = db.execute(
            select(HostelBuilding).where(
                HostelBuilding.school_id == school_id,
                HostelBuilding.code == data["code"],
                HostelBuilding.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing:
            raise AlreadyExistsException(f"Building with code '{data['code']}' already exists.")

        building = HostelBuilding(
            school_id=school_id,
            name=data["name"],
            code=data["code"],
            gender_designation=data.get("gender_designation", "BOYS"),
            capacity=data.get("capacity", 100),
            is_active=data.get("is_active", True),
            description=data.get("description"),
        )
        db.add(building)
        db.commit()
        db.refresh(building)
        return building

    def get_buildings(self, db: Session, school_id: uuid.UUID) -> Sequence[HostelBuilding]:
        return db.execute(
            select(HostelBuilding).where(
                HostelBuilding.school_id == school_id,
                HostelBuilding.is_deleted.is_(False),
            ).order_by(HostelBuilding.code)
        ).scalars().all()

    def get_building_by_id(self, db: Session, school_id: uuid.UUID, building_id: uuid.UUID) -> HostelBuilding:
        building = db.execute(
            select(HostelBuilding).where(
                HostelBuilding.id == building_id,
                HostelBuilding.school_id == school_id,
                HostelBuilding.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not building:
            raise NotFoundException("Hostel building not found.")
        return building

    def update_building(self, db: Session, school_id: uuid.UUID, building_id: uuid.UUID, data: dict) -> HostelBuilding:
        building = self.get_building_by_id(db, school_id, building_id)
        for key, value in data.items():
            if hasattr(building, key) and value is not None:
                setattr(building, key, value)
        db.commit()
        db.refresh(building)
        return building

    # ROOMS
    def create_room(self, db: Session, school_id: uuid.UUID, building_id: uuid.UUID, data: dict) -> HostelRoom:
        building = self.get_building_by_id(db, school_id, building_id)
        existing = db.execute(
            select(HostelRoom).where(
                HostelRoom.building_id == building_id,
                HostelRoom.room_number == data["room_number"],
                HostelRoom.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing:
            raise AlreadyExistsException(f"Room '{data['room_number']}' already exists in building '{building.code}'.")

        room = HostelRoom(
            school_id=school_id,
            building_id=building_id,
            room_number=data["room_number"],
            floor=data.get("floor", 1),
            room_type=data.get("room_type", "STANDARD"),
            capacity=data.get("capacity", 4),
            is_active=data.get("is_active", True),
            notes=data.get("notes"),
        )
        db.add(room)
        db.commit()
        db.refresh(room)
        return room

    def get_rooms(self, db: Session, school_id: uuid.UUID, building_id: uuid.UUID | None = None) -> Sequence[HostelRoom]:
        query = select(HostelRoom).where(
            HostelRoom.school_id == school_id,
            HostelRoom.is_deleted.is_(False),
        )
        if building_id:
            query = query.where(HostelRoom.building_id == building_id)
        return db.execute(query.order_by(HostelRoom.room_number)).scalars().all()

    def get_room_by_id(self, db: Session, school_id: uuid.UUID, room_id: uuid.UUID) -> HostelRoom:
        room = db.execute(
            select(HostelRoom).where(
                HostelRoom.id == room_id,
                HostelRoom.school_id == school_id,
                HostelRoom.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not room:
            raise NotFoundException("Hostel room not found.")
        return room

    # BEDS
    def create_bed(self, db: Session, school_id: uuid.UUID, room_id: uuid.UUID, data: dict) -> HostelBed:
        room = self.get_room_by_id(db, school_id, room_id)
        existing = db.execute(
            select(HostelBed).where(
                HostelBed.room_id == room_id,
                HostelBed.bed_number == data["bed_number"],
                HostelBed.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing:
            raise AlreadyExistsException(f"Bed '{data['bed_number']}' already exists in room '{room.room_number}'.")

        bed = HostelBed(
            school_id=school_id,
            room_id=room_id,
            bed_number=data["bed_number"],
            status=data.get("status", "AVAILABLE"),
            is_active=data.get("is_active", True),
        )
        db.add(bed)
        db.commit()
        db.refresh(bed)
        return bed

    def get_beds(self, db: Session, school_id: uuid.UUID, room_id: uuid.UUID | None = None) -> Sequence[HostelBed]:
        query = select(HostelBed).where(
            HostelBed.school_id == school_id,
            HostelBed.is_deleted.is_(False),
        )
        if room_id:
            query = query.where(HostelBed.room_id == room_id)
        return db.execute(query.order_by(HostelBed.bed_number)).scalars().all()

    # ALLOCATIONS
    def allocate_student(
        self,
        db: Session,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        building_id: uuid.UUID,
        room_id: uuid.UUID,
        bed_id: uuid.UUID,
        allocated_at: date,
        reason: str | None = None,
    ) -> HostelAllocation:
        # 1. Verify student exists in same school
        student = db.execute(
            select(Student).where(
                Student.id == student_id,
                Student.school_id == school_id,
                Student.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not student:
            raise NotFoundException("Student not found in this school.")

        # 2. Check if student already has active allocation
        existing_alloc = db.execute(
            select(HostelAllocation).where(
                HostelAllocation.school_id == school_id,
                HostelAllocation.student_id == student_id,
                HostelAllocation.status == "ACTIVE",
                HostelAllocation.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if existing_alloc:
            raise BadRequestException("Student already has an active hostel allocation.")

        # 3. Verify bed, room, building match school and are active
        bed = db.execute(
            select(HostelBed).where(
                HostelBed.id == bed_id,
                HostelBed.room_id == room_id,
                HostelBed.school_id == school_id,
                HostelBed.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not bed:
            raise NotFoundException("Hostel bed not found or cross-tenant invalid.")
        if bed.status != "AVAILABLE" or not bed.is_active:
            raise BadRequestException(f"Bed '{bed.bed_number}' is not available for allocation (status: {bed.status}).")

        room = self.get_room_by_id(db, school_id, room_id)
        if not room.is_active:
            raise BadRequestException("Cannot allocate bed in an inactive room.")

        building = self.get_building_by_id(db, school_id, building_id)
        if not building.is_active:
            raise BadRequestException("Cannot allocate bed in an inactive building.")

        # 4. Check room capacity
        current_occupied_count = db.execute(
            select(func.count(HostelBed.id)).where(
                HostelBed.room_id == room_id,
                HostelBed.status == "OCCUPIED",
                HostelBed.is_deleted.is_(False),
            )
        ).scalar() or 0
        if current_occupied_count >= room.capacity:
            raise BadRequestException(f"Room '{room.room_number}' has reached maximum capacity ({room.capacity}).")

        # Create allocation
        allocation = HostelAllocation(
            school_id=school_id,
            student_id=student_id,
            building_id=building_id,
            room_id=room_id,
            bed_id=bed_id,
            allocated_at=allocated_at,
            status="ACTIVE",
            reason=reason,
        )
        bed.status = "OCCUPIED"
        db.add(allocation)
        db.commit()
        db.refresh(allocation)
        return allocation

    def release_student_allocation(
        self,
        db: Session,
        school_id: uuid.UUID,
        allocation_id: uuid.UUID,
        released_at: date,
        reason: str | None = None,
    ) -> HostelAllocation:
        allocation = db.execute(
            select(HostelAllocation).where(
                HostelAllocation.id == allocation_id,
                HostelAllocation.school_id == school_id,
                HostelAllocation.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not allocation:
            raise NotFoundException("Hostel allocation not found.")

        if allocation.status != "ACTIVE":
            raise BadRequestException("Allocation is already released or transferred.")

        allocation.status = "RELEASED"
        allocation.released_at = released_at
        if reason:
            allocation.reason = reason

        # Free bed
        bed = db.execute(
            select(HostelBed).where(HostelBed.id == allocation.bed_id)
        ).scalar_one_or_none()
        if bed:
            bed.status = "AVAILABLE"

        db.commit()
        db.refresh(allocation)
        return allocation

    def get_allocations(
        self,
        db: Session,
        school_id: uuid.UUID,
        student_id: uuid.UUID | None = None,
        status: str | None = "ACTIVE",
    ) -> Sequence[HostelAllocation]:
        query = select(HostelAllocation).where(
            HostelAllocation.school_id == school_id,
            HostelAllocation.is_deleted.is_(False),
        )
        if student_id:
            query = query.where(HostelAllocation.student_id == student_id)
        if status:
            query = query.where(HostelAllocation.status == status)
        return db.execute(query.order_by(HostelAllocation.allocated_at.desc())).scalars().all()

    # DASHBOARD METRICS
    def get_dashboard_metrics(self, db: Session, school_id: uuid.UUID) -> dict:
        total_hostels = db.execute(
            select(func.count(HostelBuilding.id)).where(
                HostelBuilding.school_id == school_id,
                HostelBuilding.is_deleted.is_(False),
            )
        ).scalar() or 0

        total_rooms = db.execute(
            select(func.count(HostelRoom.id)).where(
                HostelRoom.school_id == school_id,
                HostelRoom.is_deleted.is_(False),
            )
        ).scalar() or 0

        total_beds = db.execute(
            select(func.count(HostelBed.id)).where(
                HostelBed.school_id == school_id,
                HostelBed.is_deleted.is_(False),
            )
        ).scalar() or 0

        occupied_beds = db.execute(
            select(func.count(HostelBed.id)).where(
                HostelBed.school_id == school_id,
                HostelBed.status == "OCCUPIED",
                HostelBed.is_deleted.is_(False),
            )
        ).scalar() or 0

        available_beds = db.execute(
            select(func.count(HostelBed.id)).where(
                HostelBed.school_id == school_id,
                HostelBed.status == "AVAILABLE",
                HostelBed.is_deleted.is_(False),
            )
        ).scalar() or 0

        occupancy_pct = (occupied_beds / total_beds * 100.0) if total_beds > 0 else 0.0

        today = date.today()
        today_present = db.execute(
            select(func.count(HostelAttendance.id)).where(
                HostelAttendance.school_id == school_id,
                HostelAttendance.attendance_date == today,
                HostelAttendance.status == "PRESENT",
                HostelAttendance.is_deleted.is_(False),
            )
        ).scalar() or 0

        pending_outpasses = db.execute(
            select(func.count(HostelOutpass.id)).where(
                HostelOutpass.school_id == school_id,
                HostelOutpass.status == "PENDING",
                HostelOutpass.is_deleted.is_(False),
            )
        ).scalar() or 0

        checked_out_students = db.execute(
            select(func.count(HostelOutpass.id)).where(
                HostelOutpass.school_id == school_id,
                HostelOutpass.status == "CHECKED_OUT",
                HostelOutpass.is_deleted.is_(False),
            )
        ).scalar() or 0

        return {
            "total_hostels": total_hostels,
            "total_rooms": total_rooms,
            "total_beds": total_beds,
            "occupied_beds": occupied_beds,
            "available_beds": available_beds,
            "occupancy_percentage": round(occupancy_pct, 2),
            "today_present_count": today_present,
            "pending_outpasses": pending_outpasses,
            "checked_out_students": checked_out_students,
        }


hostel_service = HostelService()
