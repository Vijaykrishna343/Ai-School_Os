from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import get_role_service
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.schemas.role import (
    RoleCreate,
    RoleFilter,
    RoleResponse,
    RoleUpdate,
)
from app.identity.security.current_user import (
    get_current_user,
)
from app.identity.services.role_service import IdentityRoleService

router = APIRouter(
    prefix="/roles",
    tags=["Roles"],
)


@router.post(
    "",
    response_model=RoleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Role",
    dependencies=[
        Depends(require_permission("role.create")),
    ],
)
def create_role(
    role: RoleCreate,
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
) -> RoleResponse:
    """Create a new role."""
    return service.create_role(db, role)


@router.get(
    "",
    summary="List Roles",
    dependencies=[Depends(get_current_user)],
)
def list_roles(
    filters: RoleFilter = Depends(),
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
):
    """List roles for a school."""
    return service.list_school_roles(
        db,
        filters.school_id,
    )


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get Role",
    dependencies=[Depends(get_current_user)],
)
def get_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
) -> RoleResponse:
    """Retrieve a role by ID."""
    return service.get_role(db, role_id)


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update Role",
    dependencies=[
        Depends(require_permission("role.update")),
    ],
)
def update_role(
    role_id: UUID,
    role: RoleUpdate,
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
) -> RoleResponse:
    """Update a role."""
    return service.update_role(
        db,
        role_id,
        role,
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Role",
    dependencies=[
        Depends(require_permission("role.delete")),
    ],
)
def delete_role(
    role_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
):
    """Delete a role."""
    service.delete_role(
        db,
        role_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )