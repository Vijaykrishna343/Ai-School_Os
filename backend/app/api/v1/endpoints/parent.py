"""
Parent Management Endpoints.

Provides HTTP routes for creating, retrieving, updating, and deleting Parent entities.
"""

from math import ceil
from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_db,
    get_parent_service,
)
from app.identity.dependencies.require_permission import require_permission
from app.schemas.parent import (
    ParentCreate,
    ParentListResponse,
    ParentResponse,
    ParentUpdate,
)
from app.services.parent_service import ParentService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create Parent",
    dependencies=[Depends(require_permission("parent.create"))],
)
def create_parent(
    parent: ParentCreate,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
) -> dict[str, object]:
    """
    Create a new parent record.
    """
    created_parent = service.create_parent(db, parent)

    return ApiResponse.success(
        message="Parent created successfully.",
        data=ParentResponse.model_validate(
            created_parent
        ).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Parents",
    dependencies=[Depends(require_permission("parent.view"))],
)
def get_all_parents(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
) -> dict[str, object]:
    """
    Get paginated list of active parents.
    """
    parents = service.get_all_parents(db)
    total = len(parents)

    start = (page - 1) * page_size
    end = start + page_size
    paginated_items = parents[start:end]
    total_pages = ceil(total / page_size) if total > 0 else 0

    list_response = ParentListResponse(
        items=[
            ParentResponse.model_validate(p)
            for p in paginated_items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="Parents fetched successfully.",
        data=list_response.model_dump(),
    )


@router.get(
    "/{parent_id}",
    response_model=dict,
    summary="Get Parent",
    dependencies=[Depends(require_permission("parent.view"))],
)
def get_parent(
    parent_id: UUID,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
) -> dict[str, object]:
    """
    Retrieve a parent by ID.
    """
    parent = service.get_parent(db, parent_id)

    return ApiResponse.success(
        message="Parent fetched successfully.",
        data=ParentResponse.model_validate(
            parent
        ).model_dump(),
    )


@router.put(
    "/{parent_id}",
    response_model=dict,
    summary="Update Parent",
    dependencies=[Depends(require_permission("parent.update"))],
)
def update_parent(
    parent_id: UUID,
    parent: ParentUpdate,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
) -> dict[str, object]:
    """
    Update an existing parent record.
    """
    updated_parent = service.update_parent(
        db,
        parent_id,
        parent,
    )

    return ApiResponse.success(
        message="Parent updated successfully.",
        data=ParentResponse.model_validate(
            updated_parent
        ).model_dump(),
    )


@router.delete(
    "/{parent_id}",
    response_model=dict,
    summary="Delete Parent",
    dependencies=[Depends(require_permission("parent.delete"))],
)
def delete_parent(
    parent_id: UUID,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
) -> dict[str, object]:
    """
    Soft delete a parent record.
    """
    service.delete_parent(
        db,
        parent_id,
    )

    return ApiResponse.success(
        message="Parent deleted successfully.",
    )