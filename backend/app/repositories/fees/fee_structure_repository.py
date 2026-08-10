from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.enums.fees import FeeStructureStatus
from app.models.fees.fee_structure import FeeStructure
from app.repositories.base import BaseRepository


class FeeStructureRepository(BaseRepository[FeeStructure]):
    """
    Repository for FeeStructure database operations.
    """

    def __init__(self) -> None:
        super().__init__(FeeStructure)

    def get_by_id_and_school(
        self,
        db: Session,
        structure_id: UUID,
        school_id: UUID,
    ) -> FeeStructure | None:
        """
        Retrieve an active FeeStructure by ID and school_id.
        """
        return db.scalar(
            select(FeeStructure).where(
                FeeStructure.id == structure_id,
                FeeStructure.school_id == school_id,
                FeeStructure.is_deleted.is_(False),
            )
        )

    def exists_by_name(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID,
        name: str,
        school_class_id: UUID | None = None,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active fee structure with the given name exists for the school and academic year.
        """
        stmt = select(FeeStructure).where(
            FeeStructure.school_id == school_id,
            FeeStructure.academic_year_id == academic_year_id,
            FeeStructure.name == name,
            FeeStructure.is_deleted.is_(False),
        )
        if school_class_id is not None:
            stmt = stmt.where(FeeStructure.school_class_id == school_class_id)
        else:
            stmt = stmt.where(FeeStructure.school_class_id.is_(None))

        if exclude_id is not None:
            stmt = stmt.where(FeeStructure.id != exclude_id)

        return db.scalar(stmt) is not None

    def list_structures(
        self,
        db: Session,
        school_id: UUID,
        academic_year_id: UUID | None = None,
        school_class_id: UUID | None = None,
        status: FeeStructureStatus | None = None,
        search: str | None = None,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[FeeStructure], int]:
        """
        List active fee structures for a school matching filters.
        """
        query = select(FeeStructure).where(
            FeeStructure.school_id == school_id,
            FeeStructure.is_deleted.is_(False),
        )

        if academic_year_id is not None:
            query = query.where(FeeStructure.academic_year_id == academic_year_id)

        if school_class_id is not None:
            query = query.where(FeeStructure.school_class_id == school_class_id)

        if status is not None:
            query = query.where(FeeStructure.status == status)

        if search:
            query = query.where(FeeStructure.name.ilike(f"%{search}%"))

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(FeeStructure.name)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        return list(db.scalars(query)), total


fee_structure_repository = FeeStructureRepository()
