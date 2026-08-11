from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.dependencies import get_academic_term_service, get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.academic_term.academic_term import (
    AcademicTermCreate,
    AcademicTermFilter,
    AcademicTermListResponse,
    AcademicTermResponse,
    AcademicTermUpdate,
)
from app.services.academic_term_service import AcademicTermService

router = APIRouter()


@router.post(
    "",
    response_model=AcademicTermResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_academic_term(
    term_data: AcademicTermCreate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("academic_term.create")),
    service: AcademicTermService = Depends(get_academic_term_service),
) -> AcademicTermResponse:
    """
    Create a new AcademicTerm under an AcademicYear for the tenant school.
    """
    created = service.create_academic_term(
        db,
        term_data=term_data,
        current_school_id=current_user.school_id,
    )
    return AcademicTermResponse.model_validate(created)


@router.get(
    "",
    response_model=AcademicTermListResponse,
)
def list_academic_terms(
    academic_year_id: UUID | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("academic_term.view")),
    service: AcademicTermService = Depends(get_academic_term_service),
) -> AcademicTermListResponse:
    """
    List paginated AcademicTerms for the current school.
    """
    filters = AcademicTermFilter(
        school_id=current_user.school_id,
        academic_year_id=academic_year_id,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )
    return service.list_academic_terms(
        db,
        filters=filters,
        current_school_id=current_user.school_id,
    )


@router.get(
    "/{term_id}",
    response_model=AcademicTermResponse,
)
def get_academic_term(
    term_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("academic_term.view")),
    service: AcademicTermService = Depends(get_academic_term_service),
) -> AcademicTermResponse:
    """
    Get a specific AcademicTerm by ID.
    """
    term = service.get_academic_term(
        db,
        term_id=term_id,
        current_school_id=current_user.school_id,
    )
    return AcademicTermResponse.model_validate(term)


@router.put(
    "/{term_id}",
    response_model=AcademicTermResponse,
)
def update_academic_term(
    term_id: UUID,
    term_data: AcademicTermUpdate,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("academic_term.update")),
    service: AcademicTermService = Depends(get_academic_term_service),
) -> AcademicTermResponse:
    """
    Update an existing AcademicTerm.
    """
    updated = service.update_academic_term(
        db,
        term_id=term_id,
        term_data=term_data,
        current_school_id=current_user.school_id,
    )
    return AcademicTermResponse.model_validate(updated)


@router.delete(
    "/{term_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_academic_term(
    term_id: UUID,
    db: Session = Depends(get_db),
    current_user: IdentityUser = Depends(require_permission("academic_term.delete")),
    service: AcademicTermService = Depends(get_academic_term_service),
) -> None:
    """
    Soft delete an AcademicTerm.
    """
    service.delete_academic_term(
        db,
        term_id=term_id,
        current_school_id=current_user.school_id,
        current_user_id=current_user.id,
    )
