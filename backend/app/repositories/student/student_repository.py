from __future__ import annotations

from uuid import UUID

from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.orm import Session

from app.common.enums import (
    Gender,
    StudentStatus,
)
from app.models.student import Student
from app.repositories.base import BaseRepository


class StudentRepository(BaseRepository[Student]):
    """
    Repository responsible for all Student database operations.

    Responsibilities:
    - Student lookup queries
    - Duplicate check queries
    - Admission/Roll number lookup
    - Multi-field search
    - Filtering and pagination queries
    """

    def __init__(self) -> None:
        """
        Initialize StudentRepository with Student model.
        """
        super().__init__(Student)

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_by_admission_number(
        self,
        db: Session,
        admission_number: str,
    ) -> Student | None:
        """
        Get active student by admission number.
        """
        stmt = (
            select(Student)
            .where(
                Student.admission_number == admission_number,
                Student.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_roll_number(
        self,
        db: Session,
        academic_year_id: UUID,
        school_class_id: UUID,
        roll_number: str,
        section_id: UUID | None = None,
    ) -> Student | None:
        """
        Get active student by roll number within academic year and class.
        (Scope matches database constraint uq_student_roll_number).
        """
        stmt = (
            select(Student)
            .where(
                Student.academic_year_id == academic_year_id,
                Student.school_class_id == school_class_id,
                Student.roll_number == roll_number,
                Student.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_email(
        self,
        db: Session,
        email: str,
    ) -> Student | None:
        """
        Get active student by email (case-insensitive).
        """
        stmt = (
            select(Student)
            .where(
                func.lower(Student.email) == email.lower(),
                Student.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_by_phone(
        self,
        db: Session,
        phone: str,
    ) -> Student | None:
        """
        Get active student by phone.
        """
        stmt = (
            select(Student)
            .where(
                Student.phone == phone,
                Student.is_deleted.is_(False),
            )
        )

        return db.scalar(stmt)

    def get_last_admission_number(
        self,
        db: Session,
    ) -> Student | None:
        """
        Get the latest active student record by admission number order.
        """
        stmt = (
            select(Student)
            .where(
                Student.is_deleted.is_(False),
            )
            .order_by(
                desc(Student.admission_number),
            )
            .limit(1)
        )

        return db.scalar(stmt)

    def get_last_roll_number(
        self,
        db: Session,
        academic_year_id: UUID,
        school_class_id: UUID,
        section_id: UUID | None = None,
    ) -> Student | None:
        """
        Get the latest active student record by roll number order within Academic Year + Class.
        (Scope matches database constraint uq_student_roll_number).
        """
        stmt = (
            select(Student)
            .where(
                Student.academic_year_id == academic_year_id,
                Student.school_class_id == school_class_id,
                Student.is_deleted.is_(False),
            )
            .order_by(
                desc(Student.roll_number),
            )
            .limit(1)
        )

        return db.scalar(stmt)

    def search_students(
        self,
        db: Session,
        keyword: str,
    ) -> list[Student]:
        """
        Search active students using multiple fields.
        """
        keyword = keyword.strip()

        stmt = (
            select(Student)
            .where(
                Student.is_deleted.is_(False),
                or_(
                    Student.admission_number.ilike(f"%{keyword}%"),
                    Student.roll_number.ilike(f"%{keyword}%"),
                    Student.first_name.ilike(f"%{keyword}%"),
                    Student.middle_name.ilike(f"%{keyword}%"),
                    Student.last_name.ilike(f"%{keyword}%"),
                    Student.email.ilike(f"%{keyword}%"),
                    Student.phone.ilike(f"%{keyword}%"),
                ),
            )
            .order_by(
                Student.created_at.desc(),
            )
        )

        return list(db.scalars(stmt))

    def get_all_active_by_school_and_year(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
    ) -> list[Student]:
        """
        Get all active, non-deleted students for a school and academic year without pagination cap.
        Used for full academic year transitions.
        """
        stmt = (
            select(Student)
            .where(
                Student.school_id == school_id,
                Student.academic_year_id == academic_year_id,
                Student.status == StudentStatus.ACTIVE,
                Student.is_deleted.is_(False),
            )
            .order_by(Student.created_at.asc())
        )
        return list(db.scalars(stmt))

    def get_students(
        self,
        db: Session,
        *,
        school_id: UUID | None = None,
        parent_id: UUID | None = None,
        academic_year_id: UUID | None = None,
        school_class_id: UUID | None = None,
        section_id: UUID | None = None,
        gender: Gender | None = None,
        status: StudentStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Student], int]:
        """
        Filter active students with pagination.
        """
        page = max(page, 1)
        page_size = max(page_size, 1)

        filters = [
            Student.is_deleted.is_(False),
        ]

        if school_id is not None:
            filters.append(
                Student.school_id == school_id,
            )

        if parent_id is not None:
            filters.append(
                Student.parent_id == parent_id,
            )

        if academic_year_id is not None:
            filters.append(
                Student.academic_year_id == academic_year_id,
            )

        if school_class_id is not None:
            filters.append(
                Student.school_class_id == school_class_id,
            )

        if section_id is not None:
            filters.append(
                Student.section_id == section_id,
            )

        if gender is not None:
            filters.append(
                Student.gender == gender,
            )

        if status is not None:
            filters.append(
                Student.status == status,
            )

        stmt = (
            select(Student)
            .where(and_(*filters))
            .order_by(
                Student.created_at.desc(),
            )
        )

        count_stmt = (
            select(func.count())
            .select_from(Student)
            .where(and_(*filters))
        )

        total = db.scalar(count_stmt) or 0

        students = list(
            db.scalars(
                stmt.offset(
                    (page - 1) * page_size,
                ).limit(
                    page_size,
                )
            )
        )

        return students, total

    # ------------------------------------------------------------------
    # Existence Methods
    # ------------------------------------------------------------------

    def exists_by_admission_number(
        self,
        db: Session,
        admission_number: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check whether an active student exists with the specified admission number.
        """
        stmt = (
            select(Student.id)
            .where(
                Student.admission_number == admission_number,
                Student.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Student.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None

    def exists_by_roll_number(
        self,
        db: Session,
        academic_year_id: UUID,
        school_class_id: UUID,
        roll_number: str,
        section_id: UUID | None = None,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check whether an active student exists with the specified roll number in the given class.
        (Scope matches database constraint uq_student_roll_number).
        """
        stmt = (
            select(Student.id)
            .where(
                Student.academic_year_id == academic_year_id,
                Student.school_class_id == school_class_id,
                Student.roll_number == roll_number,
                Student.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Student.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None

    def exists_by_email(
        self,
        db: Session,
        email: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check whether an active student exists with the specified email.
        """
        stmt = (
            select(Student.id)
            .where(
                func.lower(Student.email) == email.lower(),
                Student.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Student.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None

    def exists_by_phone(
        self,
        db: Session,
        phone: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check whether an active student exists with the specified phone.
        """
        stmt = (
            select(Student.id)
            .where(
                Student.phone == phone,
                Student.is_deleted.is_(False),
            )
        )

        if exclude_id:
            stmt = stmt.where(
                Student.id != exclude_id,
            )

        return db.scalar(stmt.limit(1)) is not None


student_repository = StudentRepository()