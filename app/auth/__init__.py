"""Authentication module

Provides complete Web3 authentication and permission management features, including:
- JWT token management
- Web3 signature verification
- Authentication middleware
- Permission control
- Role management
"""

from .jwt_service import JWTService, TokenInfo
from .web3_service import Web3Service
from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    get_optional_current_user,
    RoleChecker,
    PermissionChecker,
    require_admin,
    require_admin_or_moderator,
    require_admin_permission
)
from .middleware import (
    AuthenticationMiddleware,
    RoleBasedAccessMiddleware,
    RequestLoggingMiddleware
)
from .decorators import (
    require_auth,
    require_active_user,
    require_admin,
    require_roles,
    require_permission,
    Protected,
    auth_required,
    active_user_required,
    admin_required,
    roles_required,
    permission_required
)
from .schemas import (
    ChallengeRequest,
    ChallengeResponse,
    VerifyRequest,
    TokenResponse,
    UserInfo,
    RefreshTokenRequest,
    AuthErrorResponse
)

__all__ = [
    # JWT services
    "JWTService",
    "TokenInfo",

    # Web3 services
    "Web3Service",

    # Dependency injection
    "get_current_user",
    "get_current_active_user",
    "get_admin_user",
    "get_optional_current_user",
    "RoleChecker",
    "PermissionChecker",
    "require_admin",
    "require_admin_or_moderator",
    "require_admin_permission",

    # Middleware
    "AuthenticationMiddleware",
    "RoleBasedAccessMiddleware",
    "RequestLoggingMiddleware",

    # Decorators
    "require_auth",
    "require_active_user",
    "require_admin",
    "require_roles",
    "require_permission",
    "Protected",
    "auth_required",
    "active_user_required",
    "admin_required",
    "roles_required",
    "permission_required",

    # Schemas
    "ChallengeRequest",
    "ChallengeResponse",
    "VerifyRequest",
    "TokenResponse",
    "UserInfo",
    "RefreshTokenRequest",
    "AuthErrorResponse"
]