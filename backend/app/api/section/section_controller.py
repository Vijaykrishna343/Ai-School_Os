"""
Section Management Controller Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting Section entities.
"""

from math import ceil
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.section.section_dependency import (
    get_section_service,
)
from app.common.responses.api_response import ApiResponse
from app.dependencies.database import get_db
from app.identity.dependencies.require_permission import require_permission
from app.identity.models import IdentityUser
from app.schemas.section.section import (
    SectionCreate,
    SectionListResponse,
    SectionResponse,
    SectionUpdate,
)
from app.services.section_service import SectionService

router = APIRouter()


@router.post(
    "",
    response_model=dict,
    summary="Create Section",
)
def create_section(
    section: SectionCreate,
    current_user: IdentityUser = Depends(require_permission("section.create")),
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
) -> dict[str, object]:
    """
    Create a new section.
    """
    created_section = service.create_section(
        db,
        section,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Section created successfully.",
        data=SectionResponse.model_validate(
            created_section
        ).model_dump(mode="json"),
    )


@router.get(
    "/class/{school_class_id}",
    response_model=dict,
    summary="Get Sections By Class",
)
def get_sections(
    school_class_id: UUID,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("section.view")),
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
) -> dict[str, object]:
    """
    Get paginated list of active sections for a specific school class.
    """
    sections = service.get_sections(
        db,
        school_class_id,
        current_school_id=current_user.school_id,
    )
    total = len(sections)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = sections[start:end]
    total_pages = ceil(total / page_size) if total > 0 else 0

    list_response = SectionListResponse(
        items=[
            SectionResponse.model_validate(sec)
            for sec in paginated_items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="Sections fetched successfully.",
        data=list_response.model_dump(mode="json"),
    )


@router.get(
    "/{section_id}",
    response_model=dict,
    summary="Get Section",
)
def get_section(
    section_id: UUID,
    current_user: IdentityUser = Depends(require_permission("section.view")),
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
) -> dict[str, object]:
    """
    Retrieve a section by ID.
    """
    section = service.get_section(
        db,
        section_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Section fetched successfully.",
        data=SectionResponse.model_validate(
            section
        ).model_dump(mode="json"),
    )


@router.put(
    "/{section_id}",
    response_model=dict,
    summary="Update Section",
)
def update_section(
    section_id: UUID,
    section: SectionUpdate,
    current_user: IdentityUser = Depends(require_permission("section.update")),
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
) -> dict[str, object]:
    """
    Update an existing section.
    """
    updated_section = service.update_section(
        db,
        section_id,
        section,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Section updated successfully.",
        data=SectionResponse.model_validate(
            updated_section
        ).model_dump(mode="json"),
    )


@router.delete(
    "/{section_id}",
    response_model=dict,
    summary="Delete Section",
)
def delete_section(
    section_id: UUID,
    current_user: IdentityUser = Depends(require_permission("section.delete")),
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
) -> dict[str, object]:
    """
    Soft delete a section.
    """
    service.delete_section(
        db,
        section_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Section deleted successfully.",
    )