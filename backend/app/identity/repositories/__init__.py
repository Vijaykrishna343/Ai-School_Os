from .user_repository import (
    IdentityUserRepository,
    identity_user_repository,
)

from .role_repository import (
    IdentityRoleRepository,
    role_repository,
)

from .permission_repository import (
    IdentityPermissionRepository,
    permission_repository,
)

from .user_role_repository import (
    IdentityUserRoleRepository,
    user_role_repository,
)

from .role_permission_repository import (
    IdentityRolePermissionRepository,
    role_permission_repository,
)

__all__ = [
    # User
    "IdentityUserRepository",
    "identity_user_repository",

    # Role
    "IdentityRoleRepository",
    "role_repository",

    # Permission
    "IdentityPermissionRepository",
    "permission_repository",

    # User Role
    "IdentityUserRoleRepository",
    "user_role_repository",

    # Role Permission
    "IdentityRolePermissionRepository",
    "role_permission_repository",
]