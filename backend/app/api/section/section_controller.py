from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.section.section_dependency import (
    get_section_service,
)
from app.common.responses.api_response import ApiResponse
from app.dependencies.database import get_db
from app.schemas.section.section import (
    SectionCreate,
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
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
):
    created_section = service.create_section(db, section)

    return ApiResponse.success(
        message="Section created successfully.",
        data=SectionResponse.model_validate(
            created_section
        ).model_dump(mode="json"),
    )


@router.get(
    "/{section_id}",
    response_model=dict,
    summary="Get Section",
)
def get_section(
    section_id: UUID,
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
):
    section = service.get_section(
        db,
        section_id,
    )

    return ApiResponse.success(
        message="Section fetched successfully.",
        data=SectionResponse.model_validate(
            section
        ).model_dump(mode="json"),
    )


@router.get(
    "/class/{school_class_id}",
    response_model=dict,
    summary="Get Sections By Class",
)
def get_sections(
    school_class_id: UUID,
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
):
    sections = service.get_sections(
        db,
        school_class_id,
    )

    return ApiResponse.success(
        message="Sections fetched successfully.",
        data=[
            SectionResponse.model_validate(
                section
            ).model_dump(mode="json")
            for section in sections
        ],
    )


@router.put(
    "/{section_id}",
    response_model=dict,
    summary="Update Section",
)
def update_section(
    section_id: UUID,
    section: SectionUpdate,
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
):
    updated_section = service.update_section(
        db,
        section_id,
        section,
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
    db: Session = Depends(get_db),
    service: SectionService = Depends(get_section_service),
):
    service.delete_section(
        db,
        section_id,
    )

    return ApiResponse.success(
        message="Section deleted successfully.",
    )