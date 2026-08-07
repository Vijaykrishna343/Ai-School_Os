from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import get_academic_year_service, get_db
from app.schemas.academic_year import (
    AcademicYearCreate,
    AcademicYearResponse,
    AcademicYearUpdate,
)
from app.services.academic_year_service import AcademicYearService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create Academic Year",
)
def create_academic_year(
    academic_year: AcademicYearCreate,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
):
    created = service.create_academic_year(
        db,
        academic_year,
    )

    return ApiResponse.success(
        message="Academic year created successfully.",
        data=AcademicYearResponse.model_validate(
            created
        ).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Academic Years",
)
def get_all_academic_years(
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
):
    academic_years = service.get_all_academic_years(db)

    return ApiResponse.success(
        message="Academic years fetched successfully.",
        data=[
            AcademicYearResponse.model_validate(
                academic_year
            ).model_dump()
            for academic_year in academic_years
        ],
    )


@router.get(
    "/{academic_year_id}",
    response_model=dict,
    summary="Get Academic Year",
)
def get_academic_year(
    academic_year_id: UUID,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
):
    academic_year = service.get_academic_year(
        db,
        academic_year_id,
    )

    return ApiResponse.success(
        message="Academic year fetched successfully.",
        data=AcademicYearResponse.model_validate(
            academic_year
        ).model_dump(),
    )


@router.put(
    "/{academic_year_id}",
    response_model=dict,
    summary="Update Academic Year",
)
def update_academic_year(
    academic_year_id: UUID,
    academic_year: AcademicYearUpdate,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
):
    updated = service.update_academic_year(
        db,
        academic_year_id,
        academic_year,
    )

    return ApiResponse.success(
        message="Academic year updated successfully.",
        data=AcademicYearResponse.model_validate(
            updated
        ).model_dump(),
    )


@router.delete(
    "/{academic_year_id}",
    response_model=dict,
    summary="Delete Academic Year",
)
def delete_academic_year(
    academic_year_id: UUID,
    db: Session = Depends(get_db),
    service: AcademicYearService = Depends(get_academic_year_service),
):
    service.delete_academic_year(
        db,
        academic_year_id,
    )

    return ApiResponse.success(
        message="Academic year deleted successfully.",
    )