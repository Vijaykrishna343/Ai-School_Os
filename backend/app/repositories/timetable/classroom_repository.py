from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.timetable.classroom import Classroom
from app.repositories.base import BaseRepository
from app.schemas.timetable.classroom import ClassroomFilter


class ClassroomRepository(BaseRepository[Classroom]):
    """
    Repository responsible for Classroom database operations.
    """

    def __init__(self) -> None:
        super().__init__(Classroom)

    def get_by_id_and_school(
        self,
        db: Session,
        classroom_id: UUID,
        school_id: UUID,
    ) -> Classroom | None:
        """
        Retrieve an active Classroom by ID and school ID.
        """
        return db.scalar(
            select(Classroom).where(
                Classroom.id == classroom_id,
                Classroom.school_id == school_id,
                Classroom.is_deleted.is_(False),
            )
        )

    def exists_by_room_number(
        self,
        db: Session,
        school_id: UUID,
        room_number: str,
        exclude_id: UUID | None = None,
    ) -> bool:
        """
        Check if an active Classroom with the same room_number exists for a school.
        """
        query = select(Classroom).where(
            Classroom.school_id == school_id,
            func.upper(Classroom.room_number) == room_number.strip().upper(),
            Classroom.is_deleted.is_(False),
        )
        if exclude_id:
            query = query.where(Classroom.id != exclude_id)

        result = db.scalar(query)
        return result is not None

    def list_by_school(
        self,
        db: Session,
        school_id: UUID,
        filters: ClassroomFilter,
    ) -> tuple[list[Classroom], int]:
        """
        List active Classrooms matching filters for a tenant school.
        """
        query = select(Classroom).where(
            Classroom.school_id == school_id,
            Classroom.is_deleted.is_(False),
        )

        if filters.room_type is not None:
            query = query.where(Classroom.room_type == filters.room_type)

        if filters.search:
            search_pattern = f"%{filters.search}%"
            query = query.where(
                (Classroom.room_number.ilike(search_pattern))
                | (Classroom.building_name.ilike(search_pattern))
            )

        total = (
            db.scalar(select(func.count()).select_from(query.subquery()))
            or 0
        )

        query = (
            query.order_by(Classroom.room_number.asc())
            .offset((filters.page - 1) * filters.page_size)
            .limit(filters.page_size)
        )

        return list(db.scalars(query)), total


classroom_repository = ClassroomRepository()
