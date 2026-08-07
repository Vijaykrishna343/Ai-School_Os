from .auth import router as auth_router
from .permissions import router as permissions_router
from .role_permissions import router as role_permissions_router
from .roles import router as roles_router
from .seed import router as seed_router
from .user_roles import router as user_roles_router
from .users import router as users_router

__all__ = [
    "auth_router",
    "roles_router",
    "permissions_router",
    "role_permissions_router",
    "user_roles_router",
    "users_router",
    "seed_router",
]