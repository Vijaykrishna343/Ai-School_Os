from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import get_role_permission_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.services.role_permission_service import IdentityRolePermissionService

router = APIRouter(
    prefix="/roles",
    tags=["Role Permissions"],
)


@router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign Permission to Role",
)
def assign_permission(
    role_id: UUID,
    permission_id: UUID,
    current_user: IdentityUser = Depends(require_permission("role_permission.assign")),
    db: Session = Depends(get_db),
    service: IdentityRolePermissionService = Depends(get_role_permission_service),
):
    """
    Assign a permission to a role (system role and tenant guarded).
    """
    return service.assign_permission(
        db,
        role_id,
        permission_id,
        current_user=current_user,
    )


@router.get(
    "/{role_id}/permissions",
    summary="Get Role Permissions",
)
def get_permissions(
    role_id: UUID,
    current_user: IdentityUser = Depends(require_permission("role_permission.view")),
    db: Session = Depends(get_db),
    service: IdentityRolePermissionService = Depends(get_role_permission_service),
):
    """
    Get all permissions assigned to a role.
    """
    return service.get_permissions(
        db,
        role_id,
        current_user=current_user,
    )


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Role Permission",
)
def remove_permission(
    role_id: UUID,
    permission_id: UUID,
    current_user: IdentityUser = Depends(require_permission("role_permission.remove")),
    db: Session = Depends(get_db),
    service: IdentityRolePermissionService = Depends(get_role_permission_service),
):
    """
    Remove a permission from a role (system role and tenant guarded).
    """
    service.remove_permission(
        db,
        role_id,
        permission_id,
        current_user=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )

