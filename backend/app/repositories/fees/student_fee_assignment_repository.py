from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.fees import StudentFeeAssignmentStatus
from app.models.fees.student_fee_assignment import StudentFeeAssignment
from app.repositories.base import BaseRepository


class StudentFeeAssignmentRepository(BaseRepository[StudentFeeAssignment]):
    """
    Repository for StudentFeeAssignment database operations.
    """

    def __init__(self) -> None:
        super().__init__(StudentFeeAssignment)

    def get_by_id_and_school(
        self,
        db: Session,
        assignment_id: UUID,
        school_id: UUID,
    ) -> StudentFeeAssignment | None:
        """
        Retrieve an active StudentFeeAssignment by ID and school_id.
        """
        return db.scalar(
            select(StudentFeeAssignment).where(
                StudentFeeAssignment.id == assignment_id,
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted.is_(False),
            )
        )

    def get_by_id_and_school_for_update(
        self,
        db: Session,
        assignment_id: UUID,
        school_id: UUID,
    ) -> StudentFeeAssignment | None:
        """
        Retrieve an active StudentFeeAssignment by ID and school_id with a row lock (FOR UPDATE).
        """
        return db.scalar(
            select(StudentFeeAssignment)
            .where(
                StudentFeeAssignment.id == assignment_id,
                StudentFeeAssignment.school_id == school_id,
                StudentFeeAssignment.is_deleted.is_(False),
            )
            .with_for_update()
        )

    def exists_active_assignment(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        student_id: UUID,
        fee_structure_id: UUID,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active assignment for the student, academic year, and fee structure exists.
        """
        stmt = select(StudentFeeAssignment).where(
            StudentFeeAssignment.school_id == school_id,
            StudentFeeAssignment.academic_year_id == academic_year_id,
            StudentFeeAssignment.student_id == student_id,
            StudentFeeAssignment.fee_structure_id == fee_structure_id,
            StudentFeeAssignment.is_deleted.is_(False),
        )
        if exclude_id is not None:
            stmt = stmt.where(StudentFeeAssignment.id != exclude_id)

        return db.scalar(stmt) is not None

    def list_assignments(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID | None = None,
        student_id: UUID | None = None,
        fee_structure_id: UUID | None = None,
        status: StudentFeeAssignmentStatus | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[StudentFeeAssignment], int]:
        """
        List active student fee assignments matching filters.
        """
        query = select(StudentFeeAssignment).where(
            StudentFeeAssignment.school_id == school_id,
            StudentFeeAssignment.is_deleted.is_(False),
        )

        if academic_year_id is not None:
            query = query.where(StudentFeeAssignment.academic_year_id == academic_year_id)

        if student_id is not None:
            query = query.where(StudentFeeAssignment.student_id == student_id)

        if fee_structure_id is not None:
            query = query.where(StudentFeeAssignment.fee_structure_id == fee_structure_id)

        if status is not None:
            query = query.where(StudentFeeAssignment.status == status)

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(StudentFeeAssignment.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(db.scalars(query)), total


student_fee_assignment_repository = StudentFeeAssignmentRepository()
