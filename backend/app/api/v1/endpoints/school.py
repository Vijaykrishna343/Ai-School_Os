from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_db, get_school_service
from app.schemas.school.school import (
    SchoolCreate,
    SchoolResponse,
    SchoolUpdate,
)
from app.services.school_service import SchoolService


router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create School",
)
def create_school(
    school: SchoolCreate,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
):
    created_school = service.create_school(db, school)

    return ApiResponse.success(
        message="School created successfully.",
        data=SchoolResponse.model_validate(created_school).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Schools",
)
def get_all_schools(
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
):
    schools = service.get_all_schools(db)

    return ApiResponse.success(
        message="Schools fetched successfully.",
        data=[
            SchoolResponse.model_validate(school).model_dump()
            for school in schools
        ],
    )


@router.get(
    "/{school_id}",
    response_model=dict,
    summary="Get School",
)
def get_school(
    school_id: UUID,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
):
    school = service.get_school(db, school_id)

    return ApiResponse.success(
        message="School fetched successfully.",
        data=SchoolResponse.model_validate(school).model_dump(),
    )


@router.put(
    "/{school_id}",
    response_model=dict,
    summary="Update School",
)
def update_school(
    school_id: UUID,
    school: SchoolUpdate,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
):
    updated_school = service.update_school(
        db,
        school_id,
        school,
    )

    return ApiResponse.success(
        message="School updated successfully.",
        data=SchoolResponse.model_validate(updated_school).model_dump(),
    )


@router.delete(
    "/{school_id}",
    response_model=dict,
    summary="Delete School",
)
def delete_school(
    school_id: UUID,
    db: Session = Depends(get_db),
    service: SchoolService = Depends(get_school_service),
):
    service.delete_school(
        db,
        school_id,
    )

    return ApiResponse.success(
        message="School deleted successfully.",
    )