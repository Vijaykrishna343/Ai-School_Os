from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_db, get_subject_service
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
)
def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
):
    return service.create_subject(
        db=db,
        subject_data=subject,
    )


@router.get(
    "",
    response_model=SubjectListResponse,
)
def get_subjects(
    school_id: UUID | None = Query(default=None),
    subject_code: str | None = Query(default=None),
    subject_name: str | None = Query(default=None),
    status: str | None = Query(default=None),
    is_optional: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
):
    filters = SubjectFilter(
        school_id=school_id,
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
)
def get_subject(
    subject_id: UUID,
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
):
    return service.get_subject(
        db=db,
        subject_id=subject_id,
    )


@router.put(
    "/{subject_id}",
    response_model=SubjectResponse,
)
def update_subject(
    subject_id: UUID,
    subject: SubjectUpdate,
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
):
    return service.update_subject(
        db=db,
        subject_id=subject_id,
        subject_data=subject,
    )


@router.delete(
    "/{subject_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_subject(
    subject_id: UUID,
    db: Session = Depends(get_db),
    service: SubjectService = Depends(get_subject_service),
):
    service.delete_subject(
        db=db,
        subject_id=subject_id,
    )