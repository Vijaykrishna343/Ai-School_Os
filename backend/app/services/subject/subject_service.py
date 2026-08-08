from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
from app.common.logger.logger import get_logger
from app.models.subject.subject import Subject
from app.repositories.school import (
    SchoolRepository,
    school_repository,
)
from app.repositories.subject import (
    SubjectRepository,
    subject_repository,
)
from app.schemas.subject import (
    SubjectCreate,
    SubjectFilter,
    SubjectListResponse,
    SubjectResponse,
    SubjectUpdate,
)
from app.services.base_service import BaseService

logger = get_logger(__name__)


class SubjectService(BaseService[SubjectRepository]):
    """
    Business logic for Subject.
    """

    def __init__(
        self,
        repository: SubjectRepository,
        school_repository: SchoolRepository,
    ) -> None:
        """
        Initialize SubjectService with repositories.
        """
        super().__init__(repository)

        self.school_repository = school_repository

    # ------------------------------------------------------------------
    # Create Methods
    # ------------------------------------------------------------------

    def create_subject(
        self,
        db: Session,
        subject_data: SubjectCreate,
    ) -> Subject:
        """
        Create a new subject entity.
        """
        logger.info(
            "Creating subject '%s' (%s) for school ID: %s",
            subject_data.subject_name,
            subject_data.subject_code,
            subject_data.school_id,
        )

        school = self.school_repository.get(
            db,
            subject_data.school_id,
        )

        if school is None:
            logger.warning("Validation failure: School ID '%s' not found for subject creation", subject_data.school_id)
            raise NotFoundException("School", str(subject_data.school_id))

        if self.repository.get_by_subject_code(
            db,
            subject_data.school_id,
            subject_data.subject_code,
        ):
            logger.warning("Validation failure: Subject code '%s' already exists", subject_data.subject_code)
            raise AlreadyExistsException(
                "Subject code",
                subject_data.subject_code,
            )

        if self.repository.get_by_subject_name(
            db,
            subject_data.school_id,
            subject_data.subject_name,
        ):
            logger.warning("Validation failure: Subject name '%s' already exists", subject_data.subject_name)
            raise AlreadyExistsException(
                "Subject name",
                subject_data.subject_name,
            )

        subject = Subject(**subject_data.model_dump())
        created = self.repository.create(
            db,
            subject,
        )
        logger.info("Subject created successfully with ID: %s", created.id)
        return created

    # ------------------------------------------------------------------
    # Read / Query Methods
    # ------------------------------------------------------------------

    def get_subject(
        self,
        db: Session,
        subject_id: UUID,
    ) -> Subject:
        """
        Get a subject by ID or raise NotFoundException.
        """
        return self.get_by_id(
            db,
            subject_id,
            "Subject",
        )

    def get_subjects(
        self,
        db: Session,
        filters: SubjectFilter,
    ) -> SubjectListResponse:
        """
        List subjects with applied pagination and filters.
        """
        subjects, total = self.repository.list(
            db,
            filters,
        )

        return SubjectListResponse(
            items=[
                SubjectResponse.model_validate(
                    subject
                )
                for subject in subjects
            ],
            total=total,
            page=filters.page,
            page_size=filters.page_size,
        )

    # ------------------------------------------------------------------
    # Update Methods
    # ------------------------------------------------------------------

    def update_subject(
        self,
        db: Session,
        subject_id: UUID,
        subject_data: SubjectUpdate,
    ) -> Subject:
        """
        Update an existing subject.
        """
        logger.info("Updating subject ID: %s", subject_id)
        db_subject = self.get_subject(
            db,
            subject_id,
        )

        if (
            subject_data.subject_code
            and subject_data.subject_code
            != db_subject.subject_code
        ):
            existing = (
                self.repository.get_by_subject_code(
                    db,
                    db_subject.school_id,
                    subject_data.subject_code,
                )
            )

            if (
                existing
                and existing.id != db_subject.id
            ):
                logger.warning("Validation failure: Subject code '%s' already exists", subject_data.subject_code)
                raise AlreadyExistsException(
                    "Subject code",
                    subject_data.subject_code,
                )

        if (
            subject_data.subject_name
            and subject_data.subject_name
            != db_subject.subject_name
        ):
            existing = (
                self.repository.get_by_subject_name(
                    db,
                    db_subject.school_id,
                    subject_data.subject_name,
                )
            )

            if (
                existing
                and existing.id != db_subject.id
            ):
                logger.warning("Validation failure: Subject name '%s' already exists", subject_data.subject_name)
                raise AlreadyExistsException(
                    "Subject name",
                    subject_data.subject_name,
                )

        updated = self.repository.update(
            db,
            db_subject,
            subject_data,
        )
        logger.info("Subject ID: %s updated successfully", subject_id)
        return updated

    # ------------------------------------------------------------------
    # Delete Methods
    # ------------------------------------------------------------------

    def delete_subject(
        self,
        db: Session,
        subject_id: UUID,
    ) -> None:
        """
        Soft delete a subject entity.
        """
        logger.info("Soft deleting subject ID: %s", subject_id)
        db_subject = self.get_subject(
            db,
            subject_id,
        )

        self.repository.soft_delete(
            db,
            db_subject,
        )
        logger.info("Subject ID: %s soft deleted successfully", subject_id)


subject_service = SubjectService(
    repository=subject_repository,
    school_repository=school_repository,
)