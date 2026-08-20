from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import (
    bootstrap_or_require_permission,
    get_identity_user_service,
)
from app.identity.dependencies.require_permission import require_permission
from app.identity.models.user import IdentityUser
from app.identity.schemas.user import (
    UserCreate,
    UserFilter,
    UserListResponse,
    UserResponse,
    UserStatusUpdate,
    UserUpdate,
)
from app.identity.services.user_service import IdentityUserService

router = APIRouter(
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
)
def create_user(
    user: UserCreate,
    current_user: IdentityUser = Depends(bootstrap_or_require_permission("user.create")),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(get_identity_user_service),
):
    """Create a new user with tenant scoping."""
    return service.create_user(
        db,
        user,
        current_user=current_user,
    )


@router.get(
    "",
    response_model=UserListResponse,
    summary="List Users",
)
def get_users(
    school_id: UUID | None = Query(None),
    email: str | None = Query(None),
    username: str | None = Query(None),
    first_name: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    current_user: IdentityUser = Depends(require_permission("user.view")),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(get_identity_user_service),
):
    """List users with tenant scoping and filters."""
    filters = UserFilter(
        school_id=school_id,
        email=email,
        username=username,
        first_name=first_name,
        is_active=is_active,
        page=page,
        page_size=page_size,
    )

    return service.get_users(
        db,
        filters,
        current_user=current_user,
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User",
)
def get_user(
    user_id: UUID,
    current_user: IdentityUser = Depends(require_permission("user.view")),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(get_identity_user_service),
):
    """Retrieve a user by ID with tenant verification."""
    return service.get_user(
        db,
        user_id,
        current_user=current_user,
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
)
def update_user(
    user_id: UUID,
    user: UserUpdate,
    current_user: IdentityUser = Depends(require_permission("user.update")),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(get_identity_user_service),
):
    """Update a user with tenant verification."""
    return service.update_user(
        db,
        user_id,
        user,
        current_user=current_user,
    )


@router.put(
    "/{user_id}/status",
    response_model=UserResponse,
    summary="Update User Status (Suspend/Reactivate)",
)
def update_user_status(
    user_id: UUID,
    status_data: UserStatusUpdate,
    current_user: IdentityUser = Depends(require_permission("user.update")),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(get_identity_user_service),
):
    """
    Suspend or reactivate a user account.
    School Admin can manage users within their school (except Super Admins & self).
    """
    return service.update_user_status(
        db,
        user_id,
        status_data,
        current_user=current_user,
    )



@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
)
def delete_user(
    user_id: UUID,
    current_user: IdentityUser = Depends(require_permission("user.delete")),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(get_identity_user_service),
):
    """Delete a user with tenant verification."""
    service.delete_user(
        db,
        user_id,
        current_user=current_user,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )