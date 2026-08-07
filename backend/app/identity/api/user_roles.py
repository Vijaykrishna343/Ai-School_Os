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
    get_user_role_service,
)
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.security.current_user import (
    get_current_user,
)
from app.identity.services.user_role_service import (
    IdentityUserRoleService,
)

router = APIRouter(
    prefix="/users",
    tags=["User Roles"],
)


@router.post(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign Role to User",
    dependencies=[
        Depends(require_permission("user_role.assign")),
    ],
)
def assign_role(
    user_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityUserRoleService = Depends(
        get_user_role_service,
    ),
):
    """
    Assign a role to a user.
    """

    return service.assign_role(
        db,
        user_id,
        role_id,
    )


@router.get(
    "/{user_id}/roles",
    summary="Get User Roles",
    dependencies=[Depends(get_current_user)],
)
def get_roles(
    user_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityUserRoleService = Depends(
        get_user_role_service,
    ),
):
    """
    Get all roles assigned to a user.
    """

    return service.get_roles(
        db,
        user_id,
    )


@router.delete(
    "/{user_id}/roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove User Role",
    dependencies=[
        Depends(require_permission("user_role.remove")),
    ],
)
def remove_role(
    user_id: UUID,
    role_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityUserRoleService = Depends(
        get_user_role_service,
    ),
):
    """
    Remove a role from a user.
    """

    service.remove_role(
        db,
        user_id,
        role_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )