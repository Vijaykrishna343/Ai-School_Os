"""
Subject Management Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting Subject entities.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_subject_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.models.subject.subject import Subject
from app.schemas.subject import (
    SubjectCreate,
    SubjectFilter,
    SubjectListResponse,
    SubjectResponse,
    SubjectUpdate,
)
from app.services.subject.subject_service import SubjectService

router = APIRouter()


@router.post(
    "",
    response_model=SubjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Subject",
)
def create_subject(
    subject: SubjectCreate,
    current_user: IdentityUser = Depends(require_permission("subject.create")),
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
) -> Subject:
    """
    Create a new subject.
    """
    # Enforce authoritative tenant boundary
    subject.school_id = current_user.school_id

    return service.create_subject(
        db=db,
        subject_data=subject,
        current_school_id=current_user.school_id,
    )


@router.get(
    "",
    response_model=SubjectListResponse,
    summary="Get Subjects",
)
def get_subjects(
    subject_code: str | None = Query(default=None),
    subject_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    is_optional: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("subject.view")),
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
) -> SubjectListResponse:
    """
    Retrieve paginated subjects matching query parameters.
    """
    filters = SubjectFilter(
        school_id=current_user.school_id,
        subject_code=subject_code,
        subject_name=subject_name,
        status=status,
        is_optional=is_optional,
        page=page,
        page_size=page_size,
    )

    return service.get_subjects(
        db=db,
        filters=filters,
    )


@router.get(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Get Subject by ID",
)
def get_subject(
    subject_id: UUID,
    current_user: IdentityUser = Depends(require_permission("subject.view")),
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
) -> Subject:
    """
    Retrieve a subject by ID.
    """
    return service.get_subject(
        db=db,
        subject_id=subject_id,
        current_school_id=current_user.school_id,
    )


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
    summary="Update Subject",
)
def update_subject(
    subject_id: UUID,
    subject: SubjectUpdate,
    current_user: IdentityUser = Depends(require_permission("subject.update")),
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
) -> Subject:
    """
    Update an existing subject.
    """
    return service.update_subject(
        db=db,
        subject_id=subject_id,
        subject_data=subject,
        current_school_id=current_user.school_id,
    )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Subject",
)
def delete_subject(
    subject_id: UUID,
    current_user: IdentityUser = Depends(require_permission("subject.delete")),
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
) -> None:
    """
    Soft delete a subject.
    """
    service.delete_subject(
        db=db,
        subject_id=subject_id,
        current_school_id=current_user.school_id,
    )