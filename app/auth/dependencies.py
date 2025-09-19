"""Authentication dependency module"""
from typing import Optional, Annotated
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models import User, UserSession
from app.services.database_service import get_db_session
from .jwt_service import JWTService, TokenInfo


# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: AsyncSession = Depends(get_db_session)
) -> User:
    """
    Get current authenticated user

    Args:
        credentials: HTTP Bearer authentication credentials
        db: Database session

    Returns:
        Current user object

    Raises:
        HTTPException: Raised when authentication fails
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        # Verify JWT token
        token_info: TokenInfo = JWTService.verify_token(credentials.credentials)

        # Check if session is valid
        token_hash = JWTService.get_token_hash(credentials.credentials)
        session_query = await db.execute(
            select(UserSession)
            .where(UserSession.token_hash == token_hash)
            .where(UserSession.is_revoked == False)
        )
        user_session = session_query.scalar_one_or_none()

        if not user_session:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token session invalid or revoked",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check if session is expired
        if user_session.is_expired:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Get user information
        user_query = await db.execute(
            select(User).where(User.id == token_info.user_id)
        )
        user = user_query.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User does not exist",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been disabled"
            )

        logger.debug(f"User authentication successful: {user.wallet_address}")
        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User authentication failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (status is active)

    Args:
        current_user: Current user

    Returns:
        Active user object

    Raises:
        HTTPException: Raised when user is not active
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account has been deactivated"
        )
    return current_user


async def get_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get admin user

    Args:
        current_user: Current active user

    Returns:
        Admin user object

    Raises:
        HTTPException: Raised when user is not admin
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user


# Optional authentication dependency, does not require authentication
async def get_optional_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Get optional current user (not required authentication)

    Args:
        credentials: HTTP Bearer authentication credentials
        db: Database session

    Returns:
        User object or None
    """
    if not credentials:
        return None

    try:
        return await get_current_user(credentials, db)
    except HTTPException:
        return None


class RoleChecker:
    """Role-based access control checker"""

    def __init__(self, allowed_roles: list[str]):
        """
        Initialize role checker

        Args:
            allowed_roles: List of allowed roles
        """
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check user role permissions

        Args:
            current_user: Current active user

        Returns:
            User object

        Raises:
            HTTPException: Raised when user role permissions are insufficient
        """
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"One of the following roles required: {', '.join(self.allowed_roles)}"
            )
        return current_user


class PermissionChecker:
    """Permission checker"""

    def __init__(self, required_permission: str):
        """
        Initialize permission checker

        Args:
            required_permission: Required permission
        """
        self.required_permission = required_permission

    def __call__(self, current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check user permissions

        Args:
            current_user: Current active user

        Returns:
            User object

        Raises:
            HTTPException: Raised when user permissions are insufficient
        """
        # Admin has all permissions
        if current_user.is_admin:
            return current_user

        # This can be extended to more complex permission checking logic
        # Currently simplified to role-based checking
        if self.required_permission == "admin" and not current_user.is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {self.required_permission}"
            )

        return current_user


# Common permission checker instances
require_admin = RoleChecker(["admin"])
require_admin_or_moderator = RoleChecker(["admin", "moderator"])
require_admin_permission = PermissionChecker("admin")


# CORS-friendly admin checker, allows OPTIONS requests to bypass authentication
async def get_admin_user_or_options(
    request: Request,
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(security)],
    db: AsyncSession = Depends(get_db_session)
) -> Optional[User]:
    """
    Get admin user, allows OPTIONS requests to bypass authentication

    Args:
        request: HTTP request object
        credentials: HTTP Bearer authentication credentials
        db: Database session

    Returns:
        Admin user object or None (for OPTIONS requests)

    Raises:
        HTTPException: Raised when user is not admin
    """
    # If it's an OPTIONS request, skip authentication
    if request.method == "OPTIONS":
        return None

    # For non-OPTIONS requests, perform normal admin authentication
    current_user = await get_current_user(credentials, db)

    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return current_user