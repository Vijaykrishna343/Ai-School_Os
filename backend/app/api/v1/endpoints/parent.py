from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_db,
    get_parent_service,
)
from app.schemas.parent import (
    ParentCreate,
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
)
def create_parent(
    parent: ParentCreate,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
):
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
)
def get_all_parents(
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
):
    parents = service.get_all_parents(db)

    return ApiResponse.success(
        message="Parents fetched successfully.",
        data=[
            ParentResponse.model_validate(parent).model_dump()
            for parent in parents
        ],
    )


@router.get(
    "/{parent_id}",
    response_model=dict,
    summary="Get Parent",
)
def get_parent(
    parent_id: UUID,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
):
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
)
def update_parent(
    parent_id: UUID,
    parent: ParentUpdate,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
):
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
)
def delete_parent(
    parent_id: UUID,
    db: Session = Depends(get_db),
    service: ParentService = Depends(get_parent_service),
):
    service.delete_parent(
        db,
        parent_id,
    )

    return ApiResponse.success(
        message="Parent deleted successfully.",
    )