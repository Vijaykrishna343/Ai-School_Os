from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.models.school import School
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.school.school import (
    SchoolCreate,
    SchoolUpdate,
)
from app.services.base_service import BaseService


class SchoolService(BaseService[SchoolRepository]):
    """
    Business logic for School operations.
    """

    def __init__(
        self,
        repository: SchoolRepository,
    ):
        super().__init__(repository)

    def create_school(
        self,
        db: Session,
        school_data: SchoolCreate,
    ) -> School:
        """
        Create a new school.
        """

        if self.repository.exists_by_code(
            db,
            school_data.code,
        ):
            raise AlreadyExistsException(
                "School",
                school_data.code,
            )

        school = School(
            **school_data.model_dump()
        )

        return self.repository.create(
            db,
            school,
        )

    def get_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> School:
        """
        Get a school by ID.
        """

        school = self.repository.get(
            db,
            school_id,
        )

        if school is None:
            raise NotFoundException(
                "School",
                str(school_id),
            )

        return school

    def get_all_schools(
        self,
        db: Session,
    ) -> list[School]:
        """
        Get all active schools.
        """

        return self.repository.get_all(db)

    def update_school(
        self,
        db: Session,
        school_id: UUID,
        school_data: SchoolUpdate,
    ) -> School:
        """
        Update an existing school.
        """

        school = self.get_school(
            db,
            school_id,
        )

        update_data = school_data.model_dump(
            exclude_unset=True
        )

        for key, value in update_data.items():
            setattr(
                school,
                key,
                value,
            )

        return self.repository.update(
            db,
            school,
        )

    def delete_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> None:
        """
        Soft delete a school.
        """

        school = self.get_school(
            db,
            school_id,
        )

        self.repository.delete(
            db,
            school,
        )


school_service = SchoolService(repository=school_repository)