from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.common.exceptions import ForbiddenException, NotFoundException
from app.dependencies.database import get_db
from app.identity.dependencies import get_role_service
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.schemas.role import (
    RoleCreate,
    RoleFilter,
    RoleResponse,
    RoleUpdate,
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
)
def create_role(
    role: RoleCreate,
    current_user: IdentityUser = Depends(require_permission("role.create")),
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
) -> RoleResponse:
    """
    Create a new custom school role.
    Derives school_id from current_user for non-Super Admin users.
    """
    if not current_user.is_super_admin:
        role.school_id = current_user.school_id

    return service.create_role(db, role)


@router.get(
    "",
    summary="List Roles",
)
def list_roles(
    filters: RoleFilter = Depends(),
    current_user: IdentityUser = Depends(require_permission("role.view")),
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
):
    """
    List roles for a school.
    Returns system roles + custom school roles belonging to current_user's school.
    """
    school_id = filters.school_id if current_user.is_super_admin and filters.school_id else current_user.school_id
    system_roles = service.list_system_roles(db)
    school_roles = service.list_school_roles(db, school_id)
    
    # Merge and deduplicate
    role_map = {r.id: r for r in system_roles + school_roles}
    return [RoleResponse.model_validate(r) for r in role_map.values()]


@router.get(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Get Role",
)
def get_role(
    role_id: UUID,
    current_user: IdentityUser = Depends(require_permission("role.view")),
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
) -> RoleResponse:
    """Retrieve a role by ID with tenant verification."""
    role = service.get_role(db, role_id)
    if not role.is_system and not current_user.is_super_admin and role.school_id != current_user.school_id:
        raise NotFoundException("Role", str(role_id))
    return role


@router.put(
    "/{role_id}",
    response_model=RoleResponse,
    summary="Update Role",
)
def update_role(
    role_id: UUID,
    role: RoleUpdate,
    current_user: IdentityUser = Depends(require_permission("role.update")),
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
) -> RoleResponse:
    """Update a role with system role and tenant verification."""
    existing_role = service.get_role(db, role_id)
    if existing_role.is_system and not current_user.is_super_admin:
        raise ForbiddenException("System roles cannot be modified by school administrators.")
    if not current_user.is_super_admin and existing_role.school_id != current_user.school_id:
        raise NotFoundException("Role", str(role_id))
        
    return service.update_role(
        db,
        role_id,
        role,
    )


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Role",
)
def delete_role(
    role_id: UUID,
    current_user: IdentityUser = Depends(require_permission("role.delete")),
    db: Session = Depends(get_db),
    service: IdentityRoleService = Depends(get_role_service),
):
    """Delete a role with system role and tenant verification."""
    existing_role = service.get_role(db, role_id)
    if existing_role.is_system and not current_user.is_super_admin:
        raise ForbiddenException("System roles cannot be deleted by school administrators.")
    if not current_user.is_super_admin and existing_role.school_id != current_user.school_id:
        raise NotFoundException("Role", str(role_id))

    service.delete_role(
        db,
        role_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )