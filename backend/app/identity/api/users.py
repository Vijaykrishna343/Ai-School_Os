from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.dependencies.database import get_db
from app.identity.dependencies import (
    bootstrap_or_require_permission,
    get_identity_user_service,
)
from app.identity.dependencies.require_permission import (
    require_permission,
)
from app.identity.schemas.user import (
    UserCreate,
    UserFilter,
    UserListResponse,
    UserResponse,
    UserUpdate,
)
from app.identity.security.current_user import (
    get_current_user,
)
from app.identity.services.user_service import (
    IdentityUserService,
)

router = APIRouter(
    tags=["Users"],
)


@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create User",
    dependencies=[
        Depends(bootstrap_or_require_permission("user.create")),
    ],
)
def create_user(
    user: UserCreate,
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(
        get_identity_user_service,
    ),
):
    """Create a new user."""
    return service.create_user(
        db,
        user,
    )


@router.get(
    "",
    response_model=UserListResponse,
    summary="List Users",
    dependencies=[Depends(get_current_user)],
)
def get_users(
    school_id: UUID | None = Query(None),
    email: str | None = Query(None),
    username: str | None = Query(None),
    first_name: str | None = Query(None),
    is_active: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(
        get_identity_user_service,
    ),
):
    """List users with pagination and filters."""
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
    )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User",
    dependencies=[Depends(get_current_user)],
)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(
        get_identity_user_service,
    ),
):
    """Retrieve a user by ID."""
    return service.get_user(
        db,
        user_id,
    )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    dependencies=[
        Depends(require_permission("user.update")),
    ],
)
def update_user(
    user_id: UUID,
    user: UserUpdate,
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(
        get_identity_user_service,
    ),
):
    """Update a user."""
    return service.update_user(
        db,
        user_id,
        user,
    )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete User",
    dependencies=[
        Depends(require_permission("user.delete")),
    ],
)
def delete_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    service: IdentityUserService = Depends(
        get_identity_user_service,
    ),
):
    """Delete a user."""
    service.delete_user(
        db,
        user_id,
    )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )