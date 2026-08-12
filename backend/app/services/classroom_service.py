from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    ForbiddenException,
    NotFoundException,
    ValidationException,
)
from app.models.timetable.classroom import Classroom
from app.repositories.timetable.classroom_repository import (
    ClassroomRepository,
    classroom_repository,
)
from app.repositories.school.school_repository import (
    SchoolRepository,
    school_repository,
)
from app.schemas.timetable.classroom import (
    ClassroomCreate,
    ClassroomFilter,
    ClassroomListResponse,
    ClassroomResponse,
    ClassroomUpdate,
)


class ClassroomService:
    """
    Business logic service for Classroom operations.
    """

    def __init__(
        self,
        repository: ClassroomRepository = classroom_repository,
        school_repo: SchoolRepository = school_repository,
    ) -> None:
        self.repository = repository
        self.school_repository = school_repo

    def create_classroom(
        self,
        db: Session,
        classroom_data: ClassroomCreate,
        current_school_id: UUID | None = None,
    ) -> Classroom:
        """
        Create a new Classroom for a school.
        """
        if current_school_id is not None and classroom_data.school_id != current_school_id:
            raise ForbiddenException("Cannot create classroom for another school.")

        school = self.school_repository.get(db, classroom_data.school_id)
        if school is None or school.is_deleted:
            raise NotFoundException("School", str(classroom_data.school_id))

        if self.repository.exists_by_room_number(
            db, classroom_data.school_id, classroom_data.room_number
        ):
            raise AlreadyExistsException(
                "Classroom room_number", classroom_data.room_number
            )

        classroom = Classroom(
            school_id=classroom_data.school_id,
            room_number=classroom_data.room_number,
            building_name=classroom_data.building_name,
            capacity=classroom_data.capacity,
            room_type=classroom_data.room_type,
        )

        return self.repository.create(db, classroom)

    def get_classroom(
        self,
        db: Session,
        classroom_id: UUID,
        current_school_id: UUID | None = None,
    ) -> Classroom:
        """
        Retrieve a Classroom by ID within the tenant scope.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        classroom = self.repository.get_by_id_and_school(
            db, classroom_id, current_school_id
        )
        if classroom is None:
            raise NotFoundException("Classroom", str(classroom_id))

        return classroom

    def list_classrooms(
        self,
        db: Session,
        filters: ClassroomFilter,
        current_school_id: UUID | None = None,
    ) -> ClassroomListResponse:
        """
        List paginated Classrooms for a tenant school.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        items, total = self.repository.list_by_school(db, current_school_id, filters)
        total_pages = ceil(total / filters.page_size) if total > 0 else 0

        return ClassroomListResponse(
            items=[ClassroomResponse.model_validate(item) for item in items],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    def update_classroom(
        self,
        db: Session,
        classroom_id: UUID,
        classroom_data: ClassroomUpdate,
        current_school_id: UUID | None = None,
    ) -> Classroom:
        """
        Update an existing Classroom.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        classroom = self.repository.get_by_id_and_school(
            db, classroom_id, current_school_id
        )
        if classroom is None:
            raise NotFoundException("Classroom", str(classroom_id))

        if classroom_data.room_number is not None:
            if classroom_data.room_number.strip().upper() != classroom.room_number.strip().upper():
                if self.repository.exists_by_room_number(
                    db, current_school_id, classroom_data.room_number, exclude_id=classroom_id
                ):
                    raise AlreadyExistsException(
                        "Classroom room_number", classroom_data.room_number
                    )
            classroom.room_number = classroom_data.room_number

        if classroom_data.building_name is not None:
            classroom.building_name = classroom_data.building_name

        if classroom_data.capacity is not None:
            classroom.capacity = classroom_data.capacity

        if classroom_data.room_type is not None:
            classroom.room_type = classroom_data.room_type

        return self.repository.update(db, classroom)

    def delete_classroom(
        self,
        db: Session,
        classroom_id: UUID,
        current_school_id: UUID | None = None,
        current_user_id: UUID | None = None,
    ) -> None:
        """
        Soft delete a Classroom.
        """
        if current_school_id is None:
            raise ValidationException("School context is required.")

        classroom = self.repository.get_by_id_and_school(
            db, classroom_id, current_school_id
        )
        if classroom is None:
            raise NotFoundException("Classroom", str(classroom_id))

        self.repository.delete(db, classroom)


classroom_service = ClassroomService()
