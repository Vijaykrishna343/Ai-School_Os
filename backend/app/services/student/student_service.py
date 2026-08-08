from __future__ import annotations

from math import ceil
from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
    ValidationException,
)
from app.common.logger.logger import get_logger
from app.models.student import Student
from app.repositories.academic_year import (
    AcademicYearRepository,
    academic_year_repository,
)
from app.repositories.parent import (
    ParentRepository,
    parent_repository,
)
from app.repositories.school_class import (
    SchoolClassRepository,
    school_class_repository,
)
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.repositories.section import (
    SectionRepository,
    section_repository,
)
from app.repositories.student import (
    StudentRepository,
    student_repository,
)
from app.schemas.student.student_schema import (
    StudentCreate,
    StudentFilter,
    StudentListResponse,
    StudentResponse,
    StudentUpdate,
)
from app.services.base_service import BaseService
from app.utils.admission_number import (
    AdmissionNumberGenerator,
)
from app.utils.roll_number import (
    RollNumberGenerator,
)

logger = get_logger(__name__)


class StudentService(
    BaseService[StudentRepository],
):
    """
    Service responsible for all Student
    business logic.

    Responsibilities
    ----------------
    • Student CRUD
    • Duplicate validation
    • School validation
    • Parent validation
    • Academic Year validation
    • Class validation
    • Section validation
    • Admission Number generation
    • Roll Number generation
    • Search
    • Pagination
    """

    def __init__(
        self,
        repository: StudentRepository,
        school_repository: SchoolRepository,
        parent_repository: ParentRepository,
        academic_year_repository: AcademicYearRepository,
        school_class_repository: SchoolClassRepository,
        section_repository: SectionRepository,
    ) -> None:
        super().__init__(repository)

        self.school_repository = school_repository
        self.parent_repository = parent_repository
        self.academic_year_repository = academic_year_repository
        self.school_class_repository = school_class_repository
        self.section_repository = section_repository

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
            logger.warning("Validation failure: School ID '%s' not found for student", school_id)
            raise NotFoundException(
                "School",
                str(school_id),
            )

        return school

    def _validate_parent(
        self,
        db: Session,
        parent_id: UUID,
    ):
        """
        Validate parent existence.
        """

        parent = self.parent_repository.get(
            db,
            parent_id,
        )

        if parent is None:
            logger.warning("Validation failure: Parent ID '%s' not found for student", parent_id)
            raise NotFoundException(
                "Parent",
                str(parent_id),
            )

        return parent

    def _validate_academic_year(
        self,
        db: Session,
        academic_year_id: UUID,
    ):
        """
        Validate academic year existence.
        """

        academic_year = (
            self.academic_year_repository.get(
                db,
                academic_year_id,
            )
        )

        if academic_year is None:
            logger.warning("Validation failure: Academic Year ID '%s' not found for student", academic_year_id)
            raise NotFoundException(
                "Academic Year",
                str(academic_year_id),
            )

        return academic_year

    def _validate_school_class(
        self,
        db: Session,
        school_class_id: UUID,
    ):
        """
        Validate class existence.
        """

        school_class = (
            self.school_class_repository.get(
                db,
                school_class_id,
            )
        )

        if school_class is None:
            logger.warning("Validation failure: School Class ID '%s' not found for student", school_class_id)
            raise NotFoundException(
                "School Class",
                str(school_class_id),
            )

        return school_class

    def _validate_section(
        self,
        db: Session,
        section_id: UUID,
    ):
        """
        Validate section existence.
        """

        section = (
            self.section_repository.get(
                db,
                section_id,
            )
        )

        if section is None:
            logger.warning("Validation failure: Section ID '%s' not found for student", section_id)
            raise NotFoundException(
                "Section",
                str(section_id),
            )

        return section

    def _get_student_or_raise(
            self,
            db: Session,
            student_id:UUID,
    ) -> Student:
        """
        Get a student by ID or raise NotFoundException.
        """

        student = self.repository.get(
            db,
            student_id,
        )

        if student is None:
            logger.warning("Validation failure: Student ID '%s' not found", student_id)
            raise NotFoundException(
                "Student",
                str(student_id),
            )

        return student

    # ==========================================================
    # Duplicate Validation
    # ==========================================================

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
            logger.warning("Validation failure: Student email '%s' already exists", email)
            raise AlreadyExistsException(
                "Student Email",
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
            logger.warning("Validation failure: Student phone '%s' already exists", phone)
            raise AlreadyExistsException(
                "Student Phone",
                phone,
            )

    def _validate_roll_number(
        self,
        db: Session,
        academic_year_id: UUID,
        school_class_id: UUID,
        section_id: UUID,
        roll_number: str,
        exclude_id: UUID | None = None,
    ):
        """
        Validate roll number uniqueness.
        """

        if self.repository.exists_by_roll_number(
            db=db,
            academic_year_id=academic_year_id,
            school_class_id=school_class_id,
            section_id=section_id,
            roll_number=roll_number,
            exclude_id=exclude_id,
        ):
            logger.warning("Validation failure: Roll number '%s' already exists", roll_number)
            raise AlreadyExistsException(
                "Roll Number",
                roll_number,
            )
    def _validate_admission_number(
        self,
        db: Session,
        admission_number: str,
        exclude_id: UUID | None = None,
    ):
        """
        Validate admission number uniqueness.
        """

        if self.repository.exists_by_admission_number(
            db,
            admission_number,
            exclude_id,
        ):
            logger.warning("Validation failure: Admission number '%s' already exists", admission_number)
            raise AlreadyExistsException(
                "Admission Number",
                admission_number,
            )

    # ==========================================================
    # Number Generation
    # ==========================================================

    def _generate_admission_number(
        self,
        db: Session,
    ) -> str:
        """
        Generate the next admission number.
        """

        last_student = (
            self.repository.get_last_admission_number(
                db,
            )
        )

        admission_number = (
            AdmissionNumberGenerator.generate(
                last_student,
            )
        )

        self._validate_admission_number(
            db,
            admission_number,
        )

        return admission_number

    def _generate_roll_number(
        self,
        db: Session,
        academic_year_id: UUID,
        school_class_id: UUID,
        section_id: UUID,
    ) -> str:
        """
        Generate the next roll number.
        """

        last_student = (
            self.repository.get_last_roll_number(
                db=db,
                academic_year_id=academic_year_id,
                school_class_id=school_class_id,
                section_id=section_id,
            )
        )

        roll_number = (
            RollNumberGenerator.generate(
                last_student,
            )
        )

        self._validate_roll_number(
            db=db,
            academic_year_id=academic_year_id,
            school_class_id=school_class_id,
            section_id=section_id,
            roll_number=roll_number,
        )

        return roll_number

    # ==========================================================
    # Create Student
    # ==========================================================

    def create_student(
        self,
        db: Session,
        student_data: StudentCreate,
    ) -> StudentResponse:
        """
        Create a new student.
        """
        logger.info(
            "Creating student '%s %s' for school ID: %s",
            student_data.first_name,
            student_data.last_name,
            student_data.school_id,
        )

        # ------------------------------------------------------
        # Validate Foreign Keys
        # ------------------------------------------------------

        school = self._validate_school(
            db,
            student_data.school_id,
        )

        parent = self._validate_parent(
            db,
            student_data.parent_id,
        )

        academic_year = (
            self._validate_academic_year(
                db,
                student_data.academic_year_id,
            )
        )

        school_class = (
            self._validate_school_class(
                db,
                student_data.school_class_id,
            )
        )

        section = self._validate_section(
            db,
            student_data.section_id,
        )

        # ------------------------------------------------------
        # Relationship Validation
        # ------------------------------------------------------

        if academic_year.school_id != school.id:
            logger.warning("Validation failure: Academic Year school mismatch")
            raise ValidationException(
                "Academic Year does not belong to the selected School."
            )

        if school_class.school_id != school.id:
            logger.warning("Validation failure: School Class school mismatch")
            raise ValidationException(
                "School Class does not belong to the selected School."
            )

        if (
            section.school_class_id
            != school_class.id
        ):
            logger.warning("Validation failure: Section class mismatch")
            raise ValidationException(
                "Section does not belong to the selected School Class."
            )

        # ------------------------------------------------------
        # Duplicate Validation
        # ------------------------------------------------------

        self._validate_email(
            db,
            student_data.email,
        )

        self._validate_phone(
            db,
            student_data.phone,
        )

        # ------------------------------------------------------
        # Generate Numbers
        # ------------------------------------------------------

        admission_number = (
            self._generate_admission_number(
                db,
            )
        )

        roll_number = (
            self._generate_roll_number(
                db=db,
                academic_year_id=student_data.academic_year_id,
                school_class_id=student_data.school_class_id,
                section_id=student_data.section_id,
            )
        )

        # ------------------------------------------------------
        # Create Entity
        # ------------------------------------------------------

        student = Student(
            school_id=student_data.school_id,
            parent_id=student_data.parent_id,
            academic_year_id=student_data.academic_year_id,
            school_class_id=student_data.school_class_id,
            section_id=student_data.section_id,
            admission_number=admission_number,
            roll_number=roll_number,
            first_name=student_data.first_name,
            middle_name=student_data.middle_name,
            last_name=student_data.last_name,
            gender=student_data.gender,
            blood_group=student_data.blood_group,
            date_of_birth=student_data.date_of_birth,
            admission_date=student_data.admission_date,
            phone=student_data.phone,
            email=student_data.email,
            emergency_contact=student_data.emergency_contact,
            profile_photo_url=student_data.profile_photo_url,
            address_line1=student_data.address_line1,
            address_line2=student_data.address_line2,
            city=student_data.city,
            district=student_data.district,
            state=student_data.state,
            country=student_data.country,
            postal_code=student_data.postal_code,
            remarks=student_data.remarks,
            status=student_data.status,
        )

        created_student = (
            self.repository.create(
                db,
                student,
            )
        )

        logger.info(
            "Student '%s %s' created successfully with ID: %s (Admission No: %s)",
            created_student.first_name,
            created_student.last_name,
            created_student.id,
            created_student.admission_number,
        )

        return StudentResponse.model_validate(
            created_student,
        )

    # ==========================================================
    # Get Student
    # ==========================================================

    def get_student(
        self,
        db: Session,
        student_id: UUID,
    ) -> StudentResponse:
        """
        Get a student by ID.

        Raises:
            NotFoundException:
                If the student does not exist.
        """

        student = self._get_student_or_raise(
           db,
           student_id,
)

        return StudentResponse.model_validate(
            student,
        )

    # ==========================================================
    # Get Students
    # ==========================================================

    def get_students(
        self,
        db: Session,
        filters: StudentFilter,
    ) -> StudentListResponse:
        """
        Get paginated students with filters.
        """

        students, total = self.repository.get_students(
        db=db,
        school_id=filters.school_id,
        parent_id=filters.parent_id,
        academic_year_id=filters.academic_year_id,
        school_class_id=filters.school_class_id,
        section_id=filters.section_id,
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

        return StudentListResponse(
            items=[
                StudentResponse.model_validate(
                    student,
                )
                for student in students
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
            total_pages=total_pages,
        )

    # ==========================================================
    # Search Students
    # ==========================================================

    def search_students(
        self,
        db: Session,
        keyword: str,
    ) -> list[StudentResponse]:
        """
        Search students using multiple fields.

        Search is performed against:

        • Admission Number
        • Roll Number
        • First Name
        • Middle Name
        • Last Name
        • Email
        • Phone
        """

        keyword = keyword.strip()

        if not keyword:
            return []

        students = (
            self.repository.search_students(
                db,
                keyword,
            )
        )

        return [
            StudentResponse.model_validate(
                student,
            )
            for student in students
        ]
    # ==========================================================
    # Update Student
    # ==========================================================

    def update_student(
        self,
        db: Session,
        student_id: UUID,
        student_data: StudentUpdate,
    ) -> StudentResponse:
        """
        Update an existing student.
        """
        logger.info("Updating student ID: %s", student_id)

        student = self._get_student_or_raise(
            db,
            student_id,
        )

        update_data = (
            student_data.model_dump(
                exclude_unset=True,
            )
        )

        if not update_data:
            return StudentResponse.model_validate(
                student,
            )

        # ------------------------------------------------------
        # Validate Parent
        # ------------------------------------------------------

        if "parent_id" in update_data:
            self._validate_parent(
                db,
                update_data["parent_id"],
            )

        # ------------------------------------------------------
        # Validate Class
        # ------------------------------------------------------

        if "school_class_id" in update_data:
            school_class = (
                self._validate_school_class(
                    db,
                    update_data["school_class_id"],
                )
            )

            if school_class.school_id != student.school_id:
                logger.warning("Validation failure: Class school mismatch during student update")
                raise ValidationException(
                    "School Class does not belong to the student's school."
                )

        # ------------------------------------------------------
        # Validate Section
        # ------------------------------------------------------

        if "section_id" in update_data:
            section = self._validate_section(
                db,
                update_data["section_id"],
            )

            class_id = update_data.get(
                "school_class_id",
                student.school_class_id,
            )

            if section.school_class_id != class_id:
                logger.warning("Validation failure: Section class mismatch during student update")
                raise ValidationException(
                    "Section does not belong to the selected School Class."
                )

        # ------------------------------------------------------
        # Email Validation
        # ------------------------------------------------------

        if "email" in update_data:
            self._validate_email(
                db=db,
                email=update_data["email"],
                exclude_id=student.id,
            )

        # ------------------------------------------------------
        # Phone Validation
        # ------------------------------------------------------

        if "phone" in update_data:
            self._validate_phone(
                db=db,
                phone=update_data["phone"],
                exclude_id=student.id,
            )

        # ------------------------------------------------------
        # Roll Number Regeneration
        # ------------------------------------------------------

        regenerate_roll = (
            "school_class_id" in update_data
            or "section_id" in update_data
        )

        if regenerate_roll:

            class_id = update_data.get(
                "school_class_id",
                student.school_class_id,
            )

            section_id = update_data.get(
                "section_id",
                student.section_id,
            )

            new_roll_number = (
                self._generate_roll_number(
                    db=db,
                    academic_year_id=student.academic_year_id,
                    school_class_id=class_id,
                    section_id=section_id,
                )
            )

            student.roll_number = new_roll_number

        # ------------------------------------------------------
        # Update Fields
        # ------------------------------------------------------

        for field, value in update_data.items():
            setattr(
                student,
                field,
                value,
            )

        updated_student = (
            self.repository.update(
                db,
                student,
            )
        )

        logger.info("Student ID: %s updated successfully", student_id)

        return StudentResponse.model_validate(
            updated_student,
        )

    # ==========================================================
    # Delete Student
    # ==========================================================

    def delete_student(
        self,
        db: Session,
        student_id: UUID,
    ) -> None:
        """
        Soft delete a student.

        Raises:
            NotFoundException:
                If the student does not exist.
        """
        logger.info("Soft deleting student ID: %s", student_id)

        student = self._get_student_or_raise(
            db,
            student_id,
        )

        self.repository.delete(
            db,
            student,
        )
        logger.info("Student ID: %s soft deleted successfully", student_id)

    # ==========================================================
    # Exists
    # ==========================================================

    def student_exists(
        self,
        db: Session,
        student_id: UUID,
    ) -> bool:
        """
        Check whether a student exists.
        """

        return self.repository.exists(
            db,
            student_id,
        )

# ==========================================================
# Singleton Instance
# ==========================================================

student_service = StudentService(
    repository=student_repository,
    school_repository=school_repository,
    parent_repository=parent_repository,
    academic_year_repository=academic_year_repository,
    school_class_repository=school_class_repository,
    section_repository=section_repository,
)