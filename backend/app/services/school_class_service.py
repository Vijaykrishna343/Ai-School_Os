from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.models.school_class import SchoolClass
from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.schemas.school_class import (
    SchoolClassCreate,
    SchoolClassUpdate,
)


class SchoolClassService:
    """
    Business logic for School Class operations.
    """

    def __init__(
        self,
        repository: SchoolClassRepository,
        school_repository: SchoolRepository,
    ):
        self.repository = repository
        self.school_repository = school_repository

    def create_school_class(
        self,
        db: Session,
        school_class_data: SchoolClassCreate,
    ) -> SchoolClass:
        """
        Create a new school class.
        """

        school = self.school_repository.get(
            db,
            school_class_data.school_id,
        )

        if school is None:
            raise NotFoundException(
                "School",
                str(school_class_data.school_id),
            )

        if self.repository.exists_by_name(
            db,
            school_class_data.school_id,
            school_class_data.name,
        ):
            raise AlreadyExistsException(
                "School Class",
                school_class_data.name,
            )

        if school_class_data.display_order <= 0:
            raise ValidationException(
                "Display order must be greater than zero."
            )

        school_class = SchoolClass(
            **school_class_data.model_dump()
        )

        return self.repository.create(
            db,
            school_class,
        )

    def get_school_class(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> SchoolClass:
        """
        Get school class by ID.
        """

        school_class = self.repository.get(
            db,
            school_class_id,
        )

        if school_class is None:
            raise NotFoundException(
                "School Class",
                str(school_class_id),
            )

        return school_class

    def get_all_school_classes(
        self,
        db: Session,
    ) -> list[SchoolClass]:
        """
        Get all school classes.
        """

        return self.repository.get_all(db)

    def get_school_classes_by_school(
        self,
        db: Session,
        school_id: UUID,
    ) -> list[SchoolClass]:
        """
        Get all classes of a school.
        """

        school = self.school_repository.get(
            db,
            school_id,
        )

        if school is None:
            raise NotFoundException(
                "School",
                str(school_id),
            )

        return self.repository.get_by_school(
            db,
            school_id,
        )

    def update_school_class(
        self,
        db: Session,
        school_class_id: UUID,
        school_class_data: SchoolClassUpdate,
    ) -> SchoolClass:
        """
        Update school class.
        """

        school_class = self.get_school_class(
            db,
            school_class_id,
        )

        update_data = school_class_data.model_dump(
            exclude_unset=True,
        )

        if (
            "name" in update_data
            and update_data["name"] != school_class.name
        ):
            if self.repository.exists_by_name(
                db,
                school_class.school_id,
                update_data["name"],
            ):
                raise AlreadyExistsException(
                    "School Class",
                    update_data["name"],
                )

        if (
            "display_order" in update_data
            and update_data["display_order"] <= 0
        ):
            raise ValidationException(
                "Display order must be greater than zero."
            )

        for key, value in update_data.items():
            setattr(
                school_class,
                key,
                value,
            )

        return self.repository.update(
            db,
            school_class,
        )

    def delete_school_class(
        self,
        db: Session,
        school_class_id: UUID,
    ) -> None:
        """
        Soft delete school class.
        """

        school_class = self.get_school_class(
            db,
            school_class_id,
        )

        self.repository.delete(
            db,
            school_class,
        )


school_class_service = SchoolClassService(
    repository=school_class_repository,
    school_repository=school_repository,
)