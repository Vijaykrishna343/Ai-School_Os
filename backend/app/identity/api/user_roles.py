from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import get_user_role_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.services.user_role_service import IdentityUserRoleService

router = APIRouter(
    prefix="/users",
    tags=["User Roles"],
)


@router.post(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign Role to User",
)
def assign_role(
    user_id: UUID,
    role_id: UUID,
    current_user: IdentityUser = Depends(require_permission("user_role.assign")),
    db: Session = Depends(get_db),
    service: IdentityUserRoleService = Depends(get_user_role_service),
):
    """
    Assign a role to a user with tenant isolation and privilege escalation checks.
    """
    return service.assign_role(
        db,
        user_id,
        role_id,
        current_user=current_user,
    )


@router.get(
    "/{user_id}/roles",
    summary="Get User Roles",
)
def get_roles(
    user_id: UUID,
    current_user: IdentityUser = Depends(require_permission("user_role.view")),
    db: Session = Depends(get_db),
    service: IdentityUserRoleService = Depends(get_user_role_service),
):
    """
    Get all roles assigned to a user (tenant scoped).
    """
    return service.get_roles(
        db,
        user_id,
        current_user=current_user,
    )


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove User Role",
)
def remove_role(
    user_id: UUID,
    role_id: UUID,
    current_user: IdentityUser = Depends(require_permission("user_role.remove")),
    db: Session = Depends(get_db),
    service: IdentityUserRoleService = Depends(get_user_role_service),
):
    """
    Remove a role from a user.
    """
    service.remove_role(
        db,
        user_id,
        role_id,
        current_user=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )