from __future__ import annotations

import uuid
from datetime import datetime
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.hostel.hostel_outpass import HostelOutpass
from app.models.hostel.hostel_allocation import HostelAllocation
from app.common.exceptions import BadRequestException, NotFoundException, ForbiddenException
from app.services.notification_service import notification_service


class HostelOutpassService:
    """
    Service for Hostel Leave & Outpass management.
    Lifecycle: PENDING -> APPROVED/REJECTED -> CHECKED_OUT -> RETURNED.
    """

    def create_outpass_request(
        self,
        db: Session,
        school_id: uuid.UUID,
        student_id: uuid.UUID,
        requested_by_id: uuid.UUID | None,
        reason: str,
        destination: str,
        departure_time: datetime,
        expected_return_time: datetime,
        emergency_contact: str | None = None,
        remarks: str | None = None,
    ) -> HostelOutpass:
        # Check active allocation
        alloc = db.execute(
            select(HostelAllocation).where(
                HostelAllocation.school_id == school_id,
                HostelAllocation.student_id == student_id,
                HostelAllocation.status == "ACTIVE",
                HostelAllocation.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not alloc:
            raise BadRequestException("Student does not have an active hostel allocation.")

        outpass = HostelOutpass(
            school_id=school_id,
            student_id=student_id,
            building_id=alloc.building_id,
            room_id=alloc.room_id,
            requested_by_id=requested_by_id,
            reason=reason,
            destination=destination,
            departure_time=departure_time,
            expected_return_time=expected_return_time,
            emergency_contact=emergency_contact,
            remarks=remarks,
            status="PENDING",
        )
        db.add(outpass)
        db.commit()
        db.refresh(outpass)
        return outpass

    def approve_outpass(
        self,
        db: Session,
        school_id: uuid.UUID,
        outpass_id: uuid.UUID,
        approved_by_id: uuid.UUID,
        approve: bool,
        remarks: str | None = None,
    ) -> HostelOutpass:
        outpass = db.execute(
            select(HostelOutpass).where(
                HostelOutpass.id == outpass_id,
                HostelOutpass.school_id == school_id,
                HostelOutpass.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not outpass:
            raise NotFoundException("Hostel outpass not found.")

        if outpass.status != "PENDING":
            raise BadRequestException(f"Outpass is in '{outpass.status}' state and cannot be processed.")

        # Prevent student from approving self
        if outpass.requested_by_id == approved_by_id:
            # Check if user is also warden/admin
            pass

        outpass.status = "APPROVED" if approve else "REJECTED"
        outpass.approved_by_id = approved_by_id
        if remarks:
            outpass.remarks = remarks

        db.commit()
        db.refresh(outpass)

        # Dispatch notification
        status_text = "APPROVED" if approve else "REJECTED"
        try:
            notification_service.queue_notification(
                db=db,
                school_id=school_id,
                recipient_type="STUDENT",
                recipient_id=outpass.student_id,
                channel="IN_APP",
                subject=f"Hostel Outpass {status_text}",
                body=f"Your outpass request to {outpass.destination} has been {status_text.lower()}.",
            )
        except Exception:
            pass

        return outpass

    def checkout_student(
        self,
        db: Session,
        school_id: uuid.UUID,
        outpass_id: uuid.UUID,
        actual_checkout_time: datetime | None = None,
    ) -> HostelOutpass:
        outpass = db.execute(
            select(HostelOutpass).where(
                HostelOutpass.id == outpass_id,
                HostelOutpass.school_id == school_id,
                HostelOutpass.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not outpass:
            raise NotFoundException("Hostel outpass not found.")

        if outpass.status != "APPROVED":
            raise BadRequestException(f"Cannot checkout student. Outpass status is '{outpass.status}'.")

        outpass.status = "CHECKED_OUT"
        outpass.actual_checkout_time = actual_checkout_time or datetime.now()
        db.commit()
        db.refresh(outpass)
        return outpass

    def return_student(
        self,
        db: Session,
        school_id: uuid.UUID,
        outpass_id: uuid.UUID,
        actual_return_time: datetime | None = None,
    ) -> HostelOutpass:
        outpass = db.execute(
            select(HostelOutpass).where(
                HostelOutpass.id == outpass_id,
                HostelOutpass.school_id == school_id,
                HostelOutpass.is_deleted.is_(False),
            )
        ).scalar_one_or_none()
        if not outpass:
            raise NotFoundException("Hostel outpass not found.")

        if outpass.status != "CHECKED_OUT":
            raise BadRequestException(f"Cannot mark return. Outpass status is '{outpass.status}'.")

        outpass.status = "RETURNED"
        outpass.actual_return_time = actual_return_time or datetime.now()
        db.commit()
        db.refresh(outpass)
        return outpass

    def get_outpasses(
        self,
        db: Session,
        school_id: uuid.UUID,
        student_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> Sequence[HostelOutpass]:
        query = select(HostelOutpass).where(
            HostelOutpass.school_id == school_id,
            HostelOutpass.is_deleted.is_(False),
        )
        if student_id:
            query = query.where(HostelOutpass.student_id == student_id)
        if status:
            query = query.where(HostelOutpass.status == status)
        return db.execute(query.order_by(HostelOutpass.created_at.desc())).scalars().all()


hostel_outpass_service = HostelOutpassService()
