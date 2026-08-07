from uuid import UUID

from sqlalchemy.orm import Session

from app.common.exceptions import (
    AlreadyExistsException,
    NotFoundException,
)
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


class SubjectService(BaseService[SubjectRepository]):
    """
    Business logic for Subject.
    """

    def __init__(
        self,
        repository: SubjectRepository,
        school_repository: SchoolRepository,
    ):
        super().__init__(repository)

        self.school_repository = school_repository

    def create_subject(
        self,
        db: Session,
        subject_data: SubjectCreate,
    ) -> Subject:

        school = self.school_repository.get(
            db,
            subject_data.school_id,
        )

        if school is None:
            raise NotFoundException("School")

        if self.repository.get_by_subject_code(
            db,
            subject_data.school_id,
            subject_data.subject_code,
        ):
            raise AlreadyExistsException(
                "Subject code"
            )

        if self.repository.get_by_subject_name(
            db,
            subject_data.school_id,
            subject_data.subject_name,
        ):
            raise AlreadyExistsException(
                "Subject name"
            )

        return self.repository.create(
            db,
            subject_data,
        )

    def get_subject(
        self,
        db: Session,
        subject_id: UUID,
    ) -> Subject:

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

    def update_subject(
        self,
        db: Session,
        subject_id: UUID,
        subject_data: SubjectUpdate,
    ) -> Subject:

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
                raise AlreadyExistsException(
                    "Subject code"
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
                raise AlreadyExistsException(
                    "Subject name"
                )

        return self.repository.update(
            db,
            db_subject,
            subject_data,
        )

    def delete_subject(
        self,
        db: Session,
        subject_id: UUID,
    ) -> None:

        db_subject = self.get_subject(
            db,
            subject_id,
        )

        self.repository.soft_delete(
            db,
            db_subject,
        )


subject_service = SubjectService(
    repository=subject_repository,
    school_repository=school_repository,
)