from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    Response,
    status,
)
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import (
    get_role_permission_service,
)
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.security.current_user import (
    get_current_user,
)
from app.identity.services.role_permission_service import (
    IdentityRolePermissionService,
)

router = APIRouter(
    prefix="/roles",
    tags=["Role Permissions"],
)


@router.post(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign Permission to Role",
    dependencies=[
        Depends(require_permission("role_permission.assign")),
    ],
)
def assign_permission(
    role_id: UUID,
    permission_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityRolePermissionService = Depends(
        get_role_permission_service,
    ),
):
    """
    Assign a permission to a role.
    """

    return service.assign_permission(
        db,
        role_id,
        permission_id,
    )


@router.get(
    "/{role_id}/permissions",
    summary="Get Role Permissions",
    dependencies=[Depends(get_current_user)],
)
def get_permissions(
    role_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityRolePermissionService = Depends(
        get_role_permission_service,
    ),
):
    """
    Get all permissions assigned to a role.
    """

    return service.get_permissions(
        db,
        role_id,
    )


@router.delete(
    "/{role_id}/permissions/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove Role Permission",
    dependencies=[
        Depends(require_permission("role_permission.remove")),
    ],
)
def remove_permission(
    role_id: UUID,
    permission_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityRolePermissionService = Depends(
        get_role_permission_service,
    ),
):
    """
    Remove a permission from a role.
    """

    service.remove_permission(
        db,
        role_id,
        permission_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )
