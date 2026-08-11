from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.academic_term.academic_term import AcademicTerm
from app.repositories.base import BaseRepository
from app.schemas.academic_term.academic_term import AcademicTermFilter


class AcademicTermRepository(BaseRepository[AcademicTerm]):
    """
    Repository responsible for AcademicTerm database operations.
    """

    def __init__(self) -> None:
        super().__init__(AcademicTerm)

    def get_by_id_and_school(
        self,
        db: Session,
        term_id: UUID,
        school_id: UUID,
    ) -> AcademicTerm | None:
        """
        Retrieve an active AcademicTerm by ID and school ID.
        """
        return db.scalar(
            select(AcademicTerm).where(
                AcademicTerm.id == term_id,
                AcademicTerm.school_id == school_id,
                AcademicTerm.is_deleted.is_(False),
            )
        )

    def exists_by_name(
        self,
        db: Session,
        academic_year_id: UUID,
        name: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active AcademicTerm with the specified name exists for an academic year.
        """
        query = select(AcademicTerm).where(
            AcademicTerm.academic_year_id == academic_year_id,
            func.lower(AcademicTerm.name) == name.strip().lower(),
            AcademicTerm.is_deleted.is_(False),
        )
        if exclude_id:
            query = query.where(AcademicTerm.id != exclude_id)

        result = db.scalar(query)
        return result is not None

    def exists_by_code(
        self,
        db: Session,
        academic_year_id: UUID,
        code: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active AcademicTerm with the specified code exists for an academic year.
        """
        query = select(AcademicTerm).where(
            AcademicTerm.academic_year_id == academic_year_id,
            func.upper(AcademicTerm.code) == code.strip().upper(),
            AcademicTerm.is_deleted.is_(False),
        )
        if exclude_id:
            query = query.where(AcademicTerm.id != exclude_id)

        result = db.scalar(query)
        return result is not None

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: AcademicTermFilter,
    ) -> tuple[list[AcademicTerm], int]:
        """
        List active AcademicTerms matching filters for a tenant school.
        """
        query = select(AcademicTerm).where(
            AcademicTerm.school_id == school_id,
            AcademicTerm.is_deleted.is_(False),
        )

        if filters.academic_year_id:
            query = query.where(
                AcademicTerm.academic_year_id == filters.academic_year_id
            )

        if filters.is_active is not None:
            query = query.where(AcademicTerm.is_active == filters.is_active)

        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(
                (AcademicTerm.name.ilike(search_pattern))
                | (AcademicTerm.code.ilike(search_pattern))
            )

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(AcademicTerm.display_order.asc(), AcademicTerm.start_date.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


academic_term_repository = AcademicTermRepository()
