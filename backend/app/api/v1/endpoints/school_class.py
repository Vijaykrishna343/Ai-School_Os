from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_db,
    get_school_class_service,
)
from app.schemas.school_class import (
    SchoolClassCreate,
    SchoolClassResponse,
    SchoolClassUpdate,
)
from app.services.school_class_service import (
    SchoolClassService,
)

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create School Class",
)
def create_school_class(
    school_class: SchoolClassCreate,
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
):
    created = service.create_school_class(
        db,
        school_class,
    )

    return ApiResponse.success(
        message="School class created successfully.",
        data=SchoolClassResponse.model_validate(
            created
        ).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All School Classes",
)
def get_all_school_classes(
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
):
    classes = service.get_all_school_classes(db)

    return ApiResponse.success(
        message="School classes fetched successfully.",
        data=[
            SchoolClassResponse.model_validate(
                cls
            ).model_dump()
            for cls in classes
        ],
    )


@router.get(
    "/{school_class_id}",
    response_model=dict,
    summary="Get School Class",
)
def get_school_class(
    school_class_id: UUID,
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
):
    school_class = service.get_school_class(
        db,
        school_class_id,
    )

    return ApiResponse.success(
        message="School class fetched successfully.",
        data=SchoolClassResponse.model_validate(
            school_class
        ).model_dump(),
    )


@router.put(
    "/{school_class_id}",
    response_model=dict,
    summary="Update School Class",
)
def update_school_class(
    school_class_id: UUID,
    school_class: SchoolClassUpdate,
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
):
    updated = service.update_school_class(
        db,
        school_class_id,
        school_class,
    )

    return ApiResponse.success(
        message="School class updated successfully.",
        data=SchoolClassResponse.model_validate(
            updated
        ).model_dump(),
    )


@router.delete(
    "/{school_class_id}",
    response_model=dict,
    summary="Delete School Class",
)
def delete_school_class(
    school_class_id: UUID,
    db: Session = Depends(get_db),
    service: SchoolClassService = Depends(
        get_school_class_service,
    ),
):
    service.delete_school_class(
        db,
        school_class_id,
    )

    return ApiResponse.success(
        message="School class deleted successfully.",
    )