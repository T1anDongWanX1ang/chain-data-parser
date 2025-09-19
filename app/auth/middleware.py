"""Authentication middleware module"""
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models import User, UserSession
from app.services.database_service import database_service
from .jwt_service import JWTService


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Authentication middleware"""

    def __init__(
        self,
        app,
        exclude_paths: Optional[list[str]] = None,
        exclude_prefixes: Optional[list[str]] = None
    ):
        """
        Initialize authentication middleware

        Args:
            app: FastAPI application instance
            exclude_paths: List of excluded paths (exact match)
            exclude_prefixes: List of excluded path prefixes
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or []
        self.exclude_prefixes = exclude_prefixes or []

        # Default excluded paths
        self.default_exclude_paths = [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/static",
            "/api/v1/auth/challenge",
            "/api/v1/auth/verify",
            "/api/v1/auth/refresh"
        ]

        # Default excluded prefixes
        self.default_exclude_prefixes = [
            "/static/",
            "/docs",
            "/redoc"
        ]

    def is_path_excluded(self, path: str) -> bool:
        """
        Check if path is excluded

        Args:
            path: Request path

        Returns:
            Whether excluded
        """
        # Check exact match
        all_exclude_paths = self.default_exclude_paths + self.exclude_paths
        if path in all_exclude_paths:
            return True

        # Check prefix match
        all_exclude_prefixes = self.default_exclude_prefixes + self.exclude_prefixes
        for prefix in all_exclude_prefixes:
            if path.startswith(prefix):
                return True

        return False

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Middleware request processing

        Args:
            request: HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Check if this path needs to be excluded
        if self.is_path_excluded(request.url.path):
            return await call_next(request)

        # OPTIONS requests skip authentication (for CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Extract Authorization header
        authorization = request.headers.get("Authorization")
        if not authorization:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication token required",
                    "detail": "Please provide Bearer token in Authorization header"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check Bearer format
        if not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Invalid token format",
                    "detail": "Authorization header must use Bearer format"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        token = authorization[7:]  # Remove "Bearer " prefix

        try:
            # Verify JWT token
            token_info = JWTService.verify_token(token)

            # Get database session
            async with database_service.get_session() as db:
                # Check if session is valid
                token_hash = JWTService.get_token_hash(token)
                session_query = await db.execute(
                    select(UserSession)
                    .where(UserSession.token_hash == token_hash)
                    .where(UserSession.is_revoked == False)
                )
                user_session = session_query.scalar_one_or_none()

                if not user_session:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Invalid token session",
                            "detail": "Token session has been revoked or does not exist"
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # Check if session is expired
                if user_session.is_expired:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "Token has expired",
                            "detail": "Please refresh token or log in again"
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # Get user information
                user_query = await db.execute(
                    select(User).where(User.id == token_info.user_id)
                )
                user = user_query.scalar_one_or_none()

                if not user:
                    return JSONResponse(
                        status_code=status.HTTP_401_UNAUTHORIZED,
                        content={
                            "error": "User does not exist",
                            "detail": "User corresponding to token does not exist"
                        },
                        headers={"WWW-Authenticate": "Bearer"}
                    )

                # Check user status
                if user.status != "active":
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "User account has been disabled",
                            "detail": "Please contact administrator to restore account"
                        }
                    )

                # Add user information to request state
                request.state.current_user = user
                request.state.token_info = token_info

                logger.debug(f"User authentication successful: {user.wallet_address}")

        except HTTPException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": e.detail,
                    "detail": "Authentication failed"
                },
                headers=getattr(e, 'headers', None) or {"WWW-Authenticate": "Bearer"}
            )
        except Exception as e:
            logger.error(f"Authentication middleware error: {str(e)}")
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication failed",
                    "detail": "Error occurred during token verification"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Continue processing request
        return await call_next(request)


class RoleBasedAccessMiddleware(BaseHTTPMiddleware):
    """Role-based access control middleware"""

    def __init__(
        self,
        app,
        role_mappings: Optional[dict[str, list[str]]] = None
    ):
        """
        Initialize role-based access control middleware

        Args:
            app: FastAPI application instance
            role_mappings: Path role mapping configuration
                Format: {"path_prefix": ["allowed_role1", "allowed_role2"]}
        """
        super().__init__(app)
        self.role_mappings = role_mappings or {}

        # Default role mappings
        self.default_role_mappings = {
            "/api/v1/users": ["admin"],  # User management accessible only to admin
            "/api/v1/admin": ["admin"],  # Admin functions accessible only to admin
            "/api/v1/system": ["admin", "moderator"],  # System functions accessible to admin and moderator
        }

    def get_required_roles(self, path: str) -> Optional[list[str]]:
        """
        Get required roles for path

        Args:
            path: Request path

        Returns:
            Required role list, None means no restrictions
        """
        # Special paths, allow normal users to access
        user_accessible_paths = [
            "/api/v1/users/me/profile",  # User personal profile
        ]

        # Check if it's a special path accessible to users
        if path in user_accessible_paths:
            return None

        # Merge default and custom role mappings
        all_mappings = {**self.default_role_mappings, **self.role_mappings}

        # Match by path prefix, prioritize longest match
        matched_roles = None
        max_length = 0

        for prefix, roles in all_mappings.items():
            if path.startswith(prefix) and len(prefix) > max_length:
                matched_roles = roles
                max_length = len(prefix)

        return matched_roles

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Middleware request processing

        Args:
            request: HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # OPTIONS requests skip role verification (for CORS preflight)
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if role verification is needed
        required_roles = self.get_required_roles(request.url.path)
        if not required_roles:
            return await call_next(request)

        # Check if user is authenticated
        current_user = getattr(request.state, 'current_user', None)
        if not current_user:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "error": "Authentication required",
                    "detail": "This resource requires user authentication"
                },
                headers={"WWW-Authenticate": "Bearer"}
            )

        # Check user role
        if current_user.role not in required_roles:
            logger.warning(f"User {current_user.wallet_address} attempted to access resource requiring {required_roles} roles, but user role is {current_user.role}")
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "error": "Insufficient permissions",
                    "detail": f"One of the following roles required: {', '.join(required_roles)}"
                }
            )

        logger.debug(f"User {current_user.wallet_address} passed role check: {current_user.role}")
        return await call_next(request)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Request logging middleware"""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Record request logs

        Args:
            request: HTTP request
            call_next: Next middleware or route handler

        Returns:
            HTTP response
        """
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")

        # Get current user (if authenticated)
        current_user = getattr(request.state, 'current_user', None)
        user_info = current_user.wallet_address if current_user else "anonymous"

        # Record request start
        logger.info(
            f"Request started - {request.method} {request.url.path} - "
            f"User: {user_info} - IP: {client_ip} - UA: {user_agent}"
        )

        # Process request
        response = await call_next(request)

        # Record request end
        logger.info(
            f"Request completed - {request.method} {request.url.path} - "
            f"Status: {response.status_code} - User: {user_info}"
        )

        return response