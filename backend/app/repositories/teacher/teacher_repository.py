from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.common.enums import (
    Gender,
    TeacherStatus,
)
from app.models.teacher import Teacher
from app.repositories.base import BaseRepository


class TeacherRepository(BaseRepository[Teacher]):
    """
    Repository responsible for all Teacher database operations.

    Responsibilities:
    - Teacher lookup
    - Duplicate validation
    - Employee ID lookup
    - Search
    - Filtering
    - Pagination

    NOTE:
    Business validations belong in the Service layer.
    """

    def __init__(self):
        super().__init__(Teacher)

    # ==========================================================
    # Lookup Methods
    # ==========================================================

    def get_by_employee_id(
        self,
        db: Session,
        employee_id: str,
    ) -> Teacher | None:
        """
        Get teacher by employee ID.
        """

        stmt = (
            select(Teacher)
            .where(
                Teacher.employee_id == employee_id,
                Teacher.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> Teacher | None:
        """
        Get teacher by email.
        Email comparison is case-insensitive.
        """

        stmt = (
            select(Teacher)
            .where(
                func.lower(Teacher.email) == email.lower(),
                Teacher.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_phone(
        self,
        db: Session,
        phone: str,
    ) -> Teacher | None:
        """
        Get teacher by phone.
        """

        stmt = (
            select(Teacher)
            .where(
                Teacher.phone == phone,
                Teacher.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    # ==========================================================
    # Exists Methods
    # ==========================================================

    def exists_by_employee_id(
        self,
        db: Session,
        employee_id: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check employee ID uniqueness.
        """

        stmt = (
            select(Teacher.id)
            .where(
                Teacher.employee_id == employee_id,
                Teacher.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Teacher.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None

    def exists_by_email(
        self,
        db: Session,
        email: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check email uniqueness.
        """

        stmt = (
            select(Teacher.id)
            .where(
                func.lower(Teacher.email) == email.lower(),
                Teacher.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Teacher.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None

    def exists_by_phone(
        self,
        db: Session,
        phone: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check phone uniqueness.
        """

        stmt = (
            select(Teacher.id)
            .where(
                Teacher.phone == phone,
                Teacher.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Teacher.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None

    # ==========================================================
    # Employee ID Generation
    # ==========================================================

    def get_last_employee(
        self,
        db: Session,
    ) -> Teacher | None:
        """
        Get the latest employee.

        Used by Employee ID Generator.
        """

        stmt = (
            select(Teacher)
            .where(
                Teacher.is_deleted.is_(False),
            )
            .order_by(
                desc(Teacher.employee_id),
            )
            .limit(1)
        )

        return db.scalar(stmt)

    # ==========================================================
    # Search
    # ==========================================================

    def search_teachers(
        self,
        db: Session,
        keyword: str,
    ) -> list[Teacher]:
        """
        Search teachers using multiple fields.
        """

        keyword = keyword.strip()

        stmt = (
            select(Teacher)
            .where(
                Teacher.is_deleted.is_(False),
                or_(
                    Teacher.employee_id.ilike(f"%{keyword}%"),
                    Teacher.first_name.ilike(f"%{keyword}%"),
                    Teacher.middle_name.ilike(f"%{keyword}%"),
                    Teacher.last_name.ilike(f"%{keyword}%"),
                    Teacher.email.ilike(f"%{keyword}%"),
                    Teacher.phone.ilike(f"%{keyword}%"),
                ),
            )
            .order_by(
                Teacher.created_at.desc(),
            )
        )

        return list(
            db.scalars(stmt).all()
        )

    # ==========================================================
    # Filter + Pagination
    # ==========================================================

    def get_teachers(
        self,
        db: Session,
        *,
        school_id: UUID | None = None,
        gender: Gender | None = None,
        status: TeacherStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Teacher], int]:
        """
        Filter teachers with pagination.
        """

        page = max(page, 1)
        page_size = max(page_size, 1)

        filters = [
            Teacher.is_deleted.is_(False),
        ]

        if school_id is not None:
            filters.append(
                Teacher.school_id == school_id,
            )

        if gender is not None:
            filters.append(
                Teacher.gender == gender,
            )

        if status is not None:
            filters.append(
                Teacher.status == status,
            )

        stmt = (
            select(Teacher)
            .where(and_(*filters))
            .order_by(
                Teacher.created_at.desc(),
            )
        )

        count_stmt = (
            select(func.count())
            .select_from(Teacher)
            .where(and_(*filters))
        )

        total = db.scalar(count_stmt) or 0

        teachers = (
            db.scalars(
                stmt.offset(
                    (page - 1) * page_size,
                ).limit(
                    page_size,
                )
            )
            .all()
        )

        return teachers, total

teacher_repository = TeacherRepository()