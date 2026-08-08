from __future__ import annotations

from datetime import date
from math import ceil
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums import AttendanceStatus
from app.models.attendance import Attendance
from app.repositories.base import BaseRepository


class AttendanceRepository(BaseRepository[Attendance]):
    """
    Repository responsible for Attendance database operations.
    """

    def __init__(self) -> None:
        """
        Initialize AttendanceRepository with Attendance model.
        """
        super().__init__(Attendance)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_id_and_school(
        self,
        db: Session,
        attendance_id: UUID,
        school_id: UUID,
    ) -> Attendance | None:
        """
        Retrieve an active attendance record by ID and school ID.
        """
        return db.scalar(
            select(Attendance).where(
                Attendance.id == attendance_id,
                Attendance.school_id == school_id,
                Attendance.is_deleted.is_(False),
            )
        )

    def get_existing_record(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        section_id: UUID,
        student_id: UUID,
        attendance_date: date,
    ) -> Attendance | None:
        """
        Retrieve an active attendance record for a specific student, section, and date.
        """
        return db.scalar(
            select(Attendance).where(
                Attendance.school_id == school_id,
                Attendance.academic_year_id == academic_year_id,
                Attendance.section_id == section_id,
                Attendance.student_id == student_id,
                Attendance.attendance_date == attendance_date,
                Attendance.is_deleted.is_(False),
            )
        )

    def get_existing_for_students_and_date(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID,
        student_ids: list[UUID],
        attendance_date: date,
    ) -> list[Attendance]:
        """
        Retrieve existing active attendance records for a list of student IDs on a given date.
        """
        if not student_ids:
            return []

        result = db.scalars(
            select(Attendance).where(
                Attendance.school_id == school_id,
                Attendance.section_id == section_id,
                Attendance.student_id.in_(student_ids),
                Attendance.attendance_date == attendance_date,
                Attendance.is_deleted.is_(False),
            )
        )
        return list(result)

    def get_paginated_by_school(
        self,
        db: Session,
        school_id: UUID,
        section_id: UUID | None = None,
        school_class_id: UUID | None = None,
        student_id: UUID | None = None,
        attendance_date: date | None = None,
        status: AttendanceStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Attendance], int, int]:
        """
        Retrieve paginated active attendance records filtered by school and optional criteria.

        Returns:
            (items, total_count, total_pages)
        """
        filters = [
            Attendance.school_id == school_id,
            Attendance.is_deleted.is_(False),
        ]

        if section_id is not None:
            filters.append(Attendance.section_id == section_id)
        if school_class_id is not None:
            filters.append(Attendance.school_class_id == school_class_id)
        if student_id is not None:
            filters.append(Attendance.student_id == student_id)
        if attendance_date is not None:
            filters.append(Attendance.attendance_date == attendance_date)
        if status is not None:
            filters.append(Attendance.status == status)

        count_stmt = (
            select(func.count())
            .select_from(Attendance)
            .where(*filters)
        )
        total = db.scalar(count_stmt) or 0

        offset = (page - 1) * page_size
        items_stmt = (
            select(Attendance)
            .where(*filters)
            .order_by(Attendance.attendance_date.desc(), Attendance.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(db.scalars(items_stmt))
        total_pages = ceil(total / page_size) if total > 0 else 0

        return items, total, total_pages

    # ------------------------------------------------------------------
    # Bulk Operations
    # ------------------------------------------------------------------

    def create_bulk(
        self,
        db: Session,
        attendance_records: list[Attendance],
    ) -> list[Attendance]:
        """
        Add and commit multiple attendance records in a single batch.
        """
        db.add_all(attendance_records)
        db.commit()
        for record in attendance_records:
            db.refresh(record)
        return attendance_records


attendance_repository = AttendanceRepository()
