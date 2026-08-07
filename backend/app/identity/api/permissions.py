from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import get_permission_service
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.schemas.permission import (
    PermissionCreate,
    PermissionFilter,
    PermissionResponse,
    PermissionUpdate,
)
from app.identity.security.current_user import (
    get_current_user,
)
from app.identity.services.permission_service import (
    IdentityPermissionService,
)

router = APIRouter(
    prefix="/permissions",
    tags=["Permissions"],
)


@router.post(
    "",
    response_model=PermissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Permission",
    dependencies=[
        Depends(require_permission("permission.create")),
    ],
)
def create_permission(
    permission: PermissionCreate,
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(
        get_permission_service,
    ),
) -> PermissionResponse:
    """Create a new permission."""
    return service.create_permission(
        db,
        permission,
    )


@router.get(
    "",
    summary="List Permissions",
    dependencies=[Depends(get_current_user)],
)
def list_permissions(
    filters: PermissionFilter = Depends(),
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(
        get_permission_service,
    ),
):
    """List permissions."""
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
    dependencies=[Depends(get_current_user)],
)
def get_permission(
    permission_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(
        get_permission_service,
    ),
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
    dependencies=[
        Depends(require_permission("permission.update")),
    ],
)
def update_permission(
    permission_id: UUID,
    permission: PermissionUpdate,
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(
        get_permission_service,
    ),
) -> PermissionResponse:
    """Update a permission."""
    return service.update_permission(
        db,
        permission_id,
        permission,
    )


@router.delete(
    "/{permission_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete Permission",
    dependencies=[
        Depends(require_permission("permission.delete")),
    ],
)
def delete_permission(
    permission_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityPermissionService = Depends(
        get_permission_service,
    ),
):
    """Delete a permission."""
    service.delete_permission(
        db,
        permission_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )