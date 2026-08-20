from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException
from app.dependencies.database import get_db
from app.identity.dependencies import get_permission_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.schemas.permission import (
    PermissionCreate,
    PermissionFilter,
    PermissionResponse,
    PermissionUpdate,
)
from app.identity.services.permission_service import IdentityPermissionService

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Permission",
)
def create_permission(
    permission: PermissionCreate,
    current_user: IdentityUser = Depends(require_permission("permission.create")),
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(get_permission_service),
) -> PermissionResponse:
    """Create a new global permission (Super Admin only)."""
    if not current_user.is_super_admin:
        raise ForbiddenException("Global permission definitions are managed strictly by Super Admin.")
    return service.create_permission(
        db,
        permission,
    )


@router.get(
    "",
    summary="List Permissions",
)
def list_permissions(
    filters: PermissionFilter = Depends(),
    current_user: IdentityUser = Depends(require_permission("permission.view")),
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(get_permission_service),
):
    """List global permissions."""
    if filters.module:
        return service.list_by_module(
            db,
            filters.module,
        )

    return service.list_permissions(db)


@router.get(
    "/{permission_id}",
    response_model=PermissionResponse,
    summary="Get Permission",
)
def get_permission(
    permission_id: UUID,
    current_user: IdentityUser = Depends(require_permission("permission.view")),
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(get_permission_service),
) -> PermissionResponse:
    """Retrieve a permission by ID."""
    return service.get_permission(
        db,
        permission_id,
    )


@router.put(
    "/{permission_id}",
    response_model=PermissionResponse,
    summary="Update Permission",
)
def update_permission(
    permission_id: UUID,
    permission: PermissionUpdate,
    current_user: IdentityUser = Depends(require_permission("permission.update")),
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(get_permission_service),
) -> PermissionResponse:
    """Update a permission (Super Admin only)."""
    if not current_user.is_super_admin:
        raise ForbiddenException("Global permission definitions are managed strictly by Super Admin.")
    return service.update_permission(
        db,
        permission_id,
        permission,
    )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Permission",
)
def delete_permission(
    permission_id: UUID,
    current_user: IdentityUser = Depends(require_permission("permission.delete")),
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(get_permission_service),
):
    """Delete a permission (Super Admin only)."""
    if not current_user.is_super_admin:
        raise ForbiddenException("Global permission definitions are managed strictly by Super Admin.")
    service.delete_permission(
        db,
        permission_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )