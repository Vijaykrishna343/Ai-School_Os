from __future__ import annotations

import uuid
from datetime import date
from typing import Sequence
from sqlalchemy.orm import Session
from sqlalchemy import select, and_

from app.models.hostel.hostel_attendance import HostelAttendance
from app.models.hostel.hostel_allocation import HostelAllocation
from app.common.exceptions import BadRequestException, NotFoundException


class HostelAttendanceService:
    """
    Service for Hostel Night Roll Call Attendance.
    Strictly tenant-scoped by school_id.
    """

    def record_attendance(
        self,
        db: Session,
        school_id: uuid.UUID,
        attendance_date: date,
        building_id: uuid.UUID,
        room_id: uuid.UUID,
        student_id: uuid.UUID,
        status: str,
        recorded_by_id: uuid.UUID | None = None,
        remarks: str | None = None,
    ) -> HostelAttendance:
        # Check duplicate
        existing = db.execute(
            select(HostelAttendance).where(
                HostelAttendance.school_id == school_id,
                HostelAttendance.student_id == student_id,
                HostelAttendance.attendance_date == attendance_date,
                HostelAttendance.is_deleted.is_(False),
            )
        ).scalar_one_or_none()

        if existing:
            existing.status = status
            existing.remarks = remarks
            existing.recorded_by_id = recorded_by_id
            db.commit()
            db.refresh(existing)
            return existing

        attendance = HostelAttendance(
            school_id=school_id,
            attendance_date=attendance_date,
            building_id=building_id,
            room_id=room_id,
            student_id=student_id,
            status=status,
            recorded_by_id=recorded_by_id,
            remarks=remarks,
        )
        db.add(attendance)
        db.commit()
        db.refresh(attendance)
        return attendance

    def bulk_record_attendance(
        self,
        db: Session,
        school_id: uuid.UUID,
        attendance_date: date,
        building_id: uuid.UUID,
        room_id: uuid.UUID,
        records: list[dict],
        recorded_by_id: uuid.UUID | None = None,
    ) -> list[HostelAttendance]:
        results = []
        for item in records:
            att = self.record_attendance(
                db=db,
                school_id=school_id,
                attendance_date=attendance_date,
                building_id=building_id,
                room_id=room_id,
                student_id=item["student_id"],
                status=item["status"],
                recorded_by_id=recorded_by_id,
                remarks=item.get("remarks"),
            )
            results.append(att)
        return results

    def get_attendance(
        self,
        db: Session,
        school_id: uuid.UUID,
        attendance_date: date | None = None,
        building_id: uuid.UUID | None = None,
        student_id: uuid.UUID | None = None,
    ) -> Sequence[HostelAttendance]:
        query = select(HostelAttendance).where(
            HostelAttendance.school_id == school_id,
            HostelAttendance.is_deleted.is_(False),
        )
        if attendance_date:
            query = query.where(HostelAttendance.attendance_date == attendance_date)
        if building_id:
            query = query.where(HostelAttendance.building_id == building_id)
        if student_id:
            query = query.where(HostelAttendance.student_id == student_id)
        return db.execute(query.order_by(HostelAttendance.attendance_date.desc())).scalars().all()


hostel_attendance_service = HostelAttendanceService()
