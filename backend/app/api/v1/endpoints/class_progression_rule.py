"""
Class Progression Matrix Endpoints.

Provides HTTP routes for managing class progression rules.
"""

from http import HTTPStatus
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.common.responses import ApiResponse
from app.dependencies import (
    get_class_progression_rule_service,
    get_db,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.schemas.academic_year.class_progression_rule_schema import (
    ClassProgressionRuleCreate,
    ClassProgressionRuleListResponse,
    ClassProgressionRuleResponse,
    ClassProgressionRuleUpdate,
)
from app.services.class_progression_rule_service import ClassProgressionRuleService

router = APIRouter()


@router.post(
    "/",
    response_model=dict,
    status_code=HTTPStatus.CREATED,
    summary="Create Class Progression Rule",
)
def create_class_progression_rule(
    rule_data: ClassProgressionRuleCreate,
    current_user: IdentityUser = Depends(
        require_permission("progression_matrix.manage")
    ),
    db: Session = Depends(get_db),
    service: ClassProgressionRuleService = Depends(
        get_class_progression_rule_service
    ),
) -> dict[str, object]:
    """
    Create a new class progression rule for the authenticated user's school.
    """
    created = service.create_rule(
        db,
        rule_data,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Class progression rule created successfully.",
        data=ClassProgressionRuleResponse.model_validate(created).model_dump(),
    )


@router.get(
    "/",
    response_model=dict,
    summary="Get All Class Progression Rules",
)
def get_all_class_progression_rules(
    source_class_id: UUID | None = Query(default=None),
    target_class_id: UUID | None = Query(default=None),
    is_terminal: bool | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_user: IdentityUser = Depends(
        require_permission("progression_matrix.view")
    ),
    db: Session = Depends(get_db),
    service: ClassProgressionRuleService = Depends(
        get_class_progression_rule_service
    ),
) -> dict[str, object]:
    """
    Get paginated list of class progression rules for the authenticated user's school.
    """
    items, total, total_pages = service.get_paginated_rules(
        db,
        current_school_id=current_user.school_id,
        source_class_id=source_class_id,
        target_class_id=target_class_id,
        is_terminal=is_terminal,
        page=page,
        page_size=page_size,
    )

    list_response = ClassProgressionRuleListResponse(
        items=[
            ClassProgressionRuleResponse.model_validate(rule) for rule in items
        ],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )

    return ApiResponse.success(
        message="Class progression rules fetched successfully.",
        data=list_response.model_dump(),
    )


@router.get(
    "/{rule_id}",
    response_model=dict,
    summary="Get Class Progression Rule",
)
def get_class_progression_rule(
    rule_id: UUID,
    current_user: IdentityUser = Depends(
        require_permission("progression_matrix.view")
    ),
    db: Session = Depends(get_db),
    service: ClassProgressionRuleService = Depends(
        get_class_progression_rule_service
    ),
) -> dict[str, object]:
    """
    Retrieve a class progression rule by ID for the authenticated user's school.
    """
    rule = service.get_rule(
        db,
        rule_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Class progression rule fetched successfully.",
        data=ClassProgressionRuleResponse.model_validate(rule).model_dump(),
    )


@router.put(
    "/{rule_id}",
    response_model=dict,
    summary="Update Class Progression Rule",
)
def update_class_progression_rule(
    rule_id: UUID,
    rule_data: ClassProgressionRuleUpdate,
    current_user: IdentityUser = Depends(
        require_permission("progression_matrix.manage")
    ),
    db: Session = Depends(get_db),
    service: ClassProgressionRuleService = Depends(
        get_class_progression_rule_service
    ),
) -> dict[str, object]:
    """
    Update an existing class progression rule for the authenticated user's school.
    """
    updated = service.update_rule(
        db,
        rule_id,
        rule_data,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Class progression rule updated successfully.",
        data=ClassProgressionRuleResponse.model_validate(updated).model_dump(),
    )


@router.delete(
    "/{rule_id}",
    response_model=dict,
    summary="Delete Class Progression Rule",
)
def delete_class_progression_rule(
    rule_id: UUID,
    current_user: IdentityUser = Depends(
        require_permission("progression_matrix.manage")
    ),
    db: Session = Depends(get_db),
    service: ClassProgressionRuleService = Depends(
        get_class_progression_rule_service
    ),
) -> dict[str, object]:
    """
    Soft delete a class progression rule for the authenticated user's school.
    """
    service.delete_rule(
        db,
        rule_id,
        current_school_id=current_user.school_id,
    )

    return ApiResponse.success(
        message="Class progression rule deleted successfully.",
    )
