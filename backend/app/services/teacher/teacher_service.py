from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.models.teacher import Teacher
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.repositories.teacher import (
    TeacherRepository,
    teacher_repository,
)
from app.schemas.teacher import (
    TeacherCreate,
    TeacherFilter,
    TeacherListResponse,
    TeacherResponse,
    TeacherUpdate,
)
from app.services.base_service import BaseService
from app.utils.employee_id import (
    EmployeeIdGenerator,
)


class TeacherService(
    BaseService[TeacherRepository],
):
    """
    Service responsible for all Teacher
    business logic.

    Responsibilities
    ----------------
    • Teacher CRUD
    • School validation
    • Employee ID generation
    • Duplicate validation
    • Search
    • Pagination
    """

    def __init__(
        self,
        repository: TeacherRepository,
        school_repository: SchoolRepository,
    ) -> None:
        super().__init__(repository)
        self.school_repository = school_repository
    # ==========================================================
    # Private Validation Helpers
    # ==========================================================

    def _validate_school(
        self,
        db: Session,
        school_id: UUID,
    ):
        """
        Validate school existence.
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

        return school

    def _get_teacher_or_raise(
        self,
        db: Session,
        teacher_id: UUID,
    ) -> Teacher:
        """
        Get a teacher by ID or raise NotFoundException.
        """

        teacher = self.repository.get(
            db,
            teacher_id,
        )

        if teacher is None:
            raise NotFoundException(
                "Teacher",
                str(teacher_id),
            )

        return teacher

    # ==========================================================
    # Duplicate Validation
    # ==========================================================

    def _validate_employee_id(
        self,
        db: Session,
        employee_id: str,
        exclude_id: UUID | None = None,
    ):
        """
        Validate employee ID uniqueness.
        """

        if self.repository.exists_by_employee_id(
            db,
            employee_id,
            exclude_id,
        ):
            raise AlreadyExistsException(
                "Employee ID",
                employee_id,
            )

    def _validate_email(
        self,
        db: Session,
        email: str | None,
        exclude_id: UUID | None = None,
    ):
        """
        Validate email uniqueness.
        """

        if not email:
            return

        if self.repository.exists_by_email(
            db,
            email,
            exclude_id,
        ):
            raise AlreadyExistsException(
                "Teacher Email",
                email,
            )

    def _validate_phone(
        self,
        db: Session,
        phone: str | None,
        exclude_id: UUID | None = None,
    ):
        """
        Validate phone uniqueness.
        """

        if not phone:
            return

        if self.repository.exists_by_phone(
            db,
            phone,
            exclude_id,
        ):
            raise AlreadyExistsException(
                "Teacher Phone",
                phone,
            )

    # ==========================================================
    # Employee ID Generation
    # ==========================================================

    def _generate_employee_id(
        self,
        db: Session,
    ) -> str:
        """
        Generate the next employee ID.
        """

        last_teacher = (
            self.repository.get_last_employee(
                db,
            )
        )

        employee_id = (
            EmployeeIdGenerator.generate(
                last_teacher,
            )
        )

        self._validate_employee_id(
            db,
            employee_id,
        )

        return employee_id
    # ==========================================================
    # Create Teacher
    # ==========================================================

    def create_teacher(
        self,
        db: Session,
        teacher_data: TeacherCreate,
    ) -> TeacherResponse:
        """
        Create a new teacher.

        Business Rules
        --------------
        • School must exist
        • Employee ID is auto-generated
        • Email must be unique
        • Phone must be unique
        """

    # ------------------------------------------------------
    # Validate School
    # ------------------------------------------------------

        self._validate_school(
            db,
            teacher_data.school_id,
        )

        # ------------------------------------------------------
        # Duplicate Validation
        # ------------------------------------------------------

        self._validate_email(
            db,
            teacher_data.email,
        )

        self._validate_phone(
            db,
            teacher_data.phone,
        )

        # ------------------------------------------------------
        # Generate Employee ID
        # ------------------------------------------------------

        employee_id = self._generate_employee_id(
            db,
        )

        # ------------------------------------------------------
        # Create Entity
        # ------------------------------------------------------

        teacher = Teacher(
            school_id=teacher_data.school_id,
            employee_id=employee_id,

            first_name=teacher_data.first_name,
            middle_name=teacher_data.middle_name,
            last_name=teacher_data.last_name,

            gender=teacher_data.gender,
            blood_group=teacher_data.blood_group,

            date_of_birth=teacher_data.date_of_birth,
            joining_date=teacher_data.joining_date,

            qualification=teacher_data.qualification,
            specialization=teacher_data.specialization,
            experience_years=teacher_data.experience_years,

            phone=teacher_data.phone,
            email=teacher_data.email,
            emergency_contact=teacher_data.emergency_contact,

            profile_photo_url=teacher_data.profile_photo_url,

            address_line1=teacher_data.address_line1,
            address_line2=teacher_data.address_line2,
            city=teacher_data.city,
            district=teacher_data.district,
            state=teacher_data.state,
            country=teacher_data.country,
            postal_code=teacher_data.postal_code,

            salary=teacher_data.salary,
            remarks=teacher_data.remarks,
            status=teacher_data.status,
        )

        created_teacher = self.repository.create(
            db,
            teacher,
        )

        return TeacherResponse.model_validate(
            created_teacher,
        )
    # ==========================================================
    # Get Teacher
    # ==========================================================

    def get_teacher(
        self,
        db: Session,
        teacher_id: UUID,
    ) -> TeacherResponse:
        """
        Get a teacher by ID.

        Raises:
            NotFoundException:
                If the teacher does not exist.
        """

        teacher = self._get_teacher_or_raise(
            db,
            teacher_id,
        )

        return TeacherResponse.model_validate(
            teacher,
        )
    # ==========================================================
    # Get Teachers
    # ==========================================================

    def get_teachers(
        self,
        db: Session,
        filters: TeacherFilter,
    ) -> TeacherListResponse:
        """
        Get paginated teachers with filters.
        """

        teachers, total = self.repository.get_teachers(
            db=db,
            school_id=filters.school_id,
            gender=filters.gender,
            status=filters.status,
            page=filters.page,
            page_size=filters.page_size,
        )

        total_pages = (
            ceil(total / filters.page_size)
            if total > 0
            else 0
        )

        return TeacherListResponse(
            items=[
                TeacherResponse.model_validate(
                    teacher,
                )
                for teacher in teachers
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )
    # ==========================================================
    # Search Teachers
    # ==========================================================

    def search_teachers(
        self,
        db: Session,
        keyword: str,
    ) -> list[TeacherResponse]:
        """
        Search teachers using multiple fields.
        """

        keyword = keyword.strip()

        if not keyword:
            return []

        teachers = self.repository.search_teachers(
            db,
            keyword,
        )

        return [
            TeacherResponse.model_validate(
                teacher,
            )
            for teacher in teachers
        ]
    # ==========================================================
    # Update Teacher
    # ==========================================================

    def update_teacher(
        self,
        db: Session,
        teacher_id: UUID,
        teacher_data: TeacherUpdate,
    ) -> TeacherResponse:
        """
        Update an existing teacher.
        """

        teacher = self._get_teacher_or_raise(
            db,
            teacher_id,
        )


        self._validate_email(
            db,
            teacher_data.email,
            teacher.id,
        )

        self._validate_phone(
            db,
            teacher_data.phone,
            teacher.id,
        )

        update_data = (
            teacher_data.model_dump(exclude_unset=True)
        )

        # Apply update fields to the entity before persisting
        for key, value in update_data.items():
            setattr(teacher, key, value)

        updated_teacher = self.repository.update(
            db,
            teacher,
        )

        return TeacherResponse.model_validate(
            updated_teacher,
        )
    # ==========================================================
    # Delete Teacher
    # ==========================================================

    def delete_teacher(
        self,
        db: Session,
        teacher_id: UUID,
    ) -> bool:
        """
        Soft delete a teacher.
        """

        teacher = self._get_teacher_or_raise(
            db,
            teacher_id,
        )

        self.repository.delete(
            db,
            teacher,
        )

        return True
    # ==========================================================
    # Exists
    # ==========================================================

    def teacher_exists(
        self,
        db: Session,
        teacher_id: UUID,
    ) -> bool:
        """
        Check whether a teacher exists.
        """

        return (
            self.repository.get(
                db,
                teacher_id,
            )
            is not None
        )


teacher_service = TeacherService(
    repository=teacher_repository,
    school_repository=school_repository,
)