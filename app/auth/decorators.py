"""Authentication decorator module"""
from functools import wraps
from typing import Callable, List, Optional, Union
from fastapi import HTTPException, status, Depends
from inspect import signature

from app.models import User
from .dependencies import (
    get_current_user,
    get_current_active_user,
    get_admin_user,
    RoleChecker,
    PermissionChecker
)


def require_auth(func: Callable) -> Callable:
    """
    Decorator that requires authentication

    Args:
        func: Function to be decorated

    Returns:
        Decorated function
    """
    sig = signature(func)
    params = list(sig.parameters.values())

    # If current_user is not in function parameters, add it
    if not any(param.name == "current_user" for param in params):
        # Add current_user parameter
        new_params = params + [
            sig.parameters.get('current_user') or
            type('Parameter', (), {
                'name': 'current_user',
                'annotation': User,
                'default': Depends(get_current_user)
            })()
        ]
        func.__signature__ = sig.replace(parameters=new_params)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # If current_user is not in kwargs, dependency injection failed
        if 'current_user' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User authentication required"
            )
        return await func(*args, **kwargs)

    return wrapper


def require_active_user(func: Callable) -> Callable:
    """
    Decorator that requires active user

    Args:
        func: Function to be decorated

    Returns:
        Decorated function
    """
    sig = signature(func)
    params = list(sig.parameters.values())

    # If current_user is not in function parameters, add it
    if not any(param.name == "current_user" for param in params):
        new_params = params + [
            type('Parameter', (), {
                'name': 'current_user',
                'annotation': User,
                'default': Depends(get_current_active_user)
            })()
        ]
        func.__signature__ = sig.replace(parameters=new_params)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if 'current_user' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Active user authentication required"
            )
        return await func(*args, **kwargs)

    return wrapper


def require_admin(func: Callable) -> Callable:
    """
    Decorator that requires admin privileges

    Args:
        func: Function to be decorated

    Returns:
        Decorated function
    """
    sig = signature(func)
    params = list(sig.parameters.values())

    # If current_user is not in function parameters, add it
    if not any(param.name == "current_user" for param in params):
        new_params = params + [
            type('Parameter', (), {
                'name': 'current_user',
                'annotation': User,
                'default': Depends(get_admin_user)
            })()
        ]
        func.__signature__ = sig.replace(parameters=new_params)

    @wraps(func)
    async def wrapper(*args, **kwargs):
        if 'current_user' not in kwargs:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin privileges required"
            )
        return await func(*args, **kwargs)

    return wrapper


def require_roles(allowed_roles: Union[str, List[str]]) -> Callable:
    """
    Decorator that requires specific roles

    Args:
        allowed_roles: List of allowed roles or single role

    Returns:
        Decorator function
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(func: Callable) -> Callable:
        sig = signature(func)
        params = list(sig.parameters.values())

        # If current_user is not in function parameters, add it
        if not any(param.name == "current_user" for param in params):
            role_checker = RoleChecker(allowed_roles)
            new_params = params + [
                type('Parameter', (), {
                    'name': 'current_user',
                    'annotation': User,
                    'default': Depends(role_checker)
                })()
            ]
            func.__signature__ = sig.replace(parameters=new_params)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if 'current_user' not in kwargs:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of the following roles required: {', '.join(allowed_roles)}"
                )
            return await func(*args, **kwargs)

        return wrapper
    return decorator


def require_permission(permission: str) -> Callable:
    """
    Decorator that requires specific permission

    Args:
        permission: Required permission

    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        sig = signature(func)
        params = list(sig.parameters.values())

        # If current_user is not in function parameters, add it
        if not any(param.name == "current_user" for param in params):
            permission_checker = PermissionChecker(permission)
            new_params = params + [
                type('Parameter', (), {
                    'name': 'current_user',
                    'annotation': User,
                    'default': Depends(permission_checker)
                })()
            ]
            func.__signature__ = sig.replace(parameters=new_params)

        @wraps(func)
        async def wrapper(*args, **kwargs):
            if 'current_user' not in kwargs:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission required: {permission}"
                )
            return await func(*args, **kwargs)

        return wrapper
    return decorator


class Protected:
    """Protected endpoint class decorator"""

    @staticmethod
    def auth_required(func: Callable) -> Callable:
        """Requires authentication"""
        return require_auth(func)

    @staticmethod
    def active_user_required(func: Callable) -> Callable:
        """Requires active user"""
        return require_active_user(func)

    @staticmethod
    def admin_required(func: Callable) -> Callable:
        """Requires admin privileges"""
        return require_admin(func)

    @staticmethod
    def roles_required(roles: Union[str, List[str]]) -> Callable:
        """Requires specific roles"""
        return require_roles(roles)

    @staticmethod
    def permission_required(permission: str) -> Callable:
        """Requires specific permission"""
        return require_permission(permission)


# Common decorator aliases
auth_required = Protected.auth_required
active_user_required = Protected.active_user_required
admin_required = Protected.admin_required
roles_required = Protected.roles_required
permission_required = Protected.permission_required