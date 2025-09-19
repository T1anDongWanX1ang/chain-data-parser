"""JWT token service"""
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from fastapi import HTTPException, status

from app.config import settings
from app.models import User
from .schemas import TokenInfo


class JWTService:
    """JWT token service class"""

    @staticmethod
    def create_access_token(user: User, expires_delta: Optional[timedelta] = None) -> str:
        """
        Create access token

        Args:
            user: User object
            expires_delta: Expiration time interval

        Returns:
            JWT access token
        """
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)

        payload = {
            "sub": str(user.id),  # subject (User ID)
            "wallet_address": user.wallet_address,
            "role": user.role,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")
        return token

    @staticmethod
    def create_refresh_token(user: User) -> str:
        """
        Create refresh token

        Args:
            user: User object

        Returns:
            JWT refresh token
        """
        expire = datetime.utcnow() + timedelta(days=30)  # Refresh token 30-day validity period

        payload = {
            "sub": str(user.id),
            "wallet_address": user.wallet_address,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "refresh"
        }

        token = jwt.encode(payload, settings.security.secret_key, algorithm="HS256")
        return token

    @staticmethod
    def verify_token(token: str) -> TokenInfo:
        """
        Verify token

        Args:
            token: JWT token

        Returns:
            Token information

        Raises:
            HTTPException: When token is invalid
        """
        try:
            payload = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])

            # Check token type
            if payload.get("type") != "access":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token type"
                )

            # Extract token information
            token_info = TokenInfo(
                user_id=int(payload["sub"]),
                wallet_address=payload["wallet_address"],
                role=payload["role"],
                exp=payload["exp"],
                iat=payload["iat"]
            )

            return token_info

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )

    @staticmethod
    def verify_refresh_token(token: str) -> TokenInfo:
        """
        Verify refresh token

        Args:
            token: JWT refresh token

        Returns:
            Token information

        Raises:
            HTTPException: When token is invalid
        """
        try:
            payload = jwt.decode(token, settings.security.secret_key, algorithms=["HS256"])

            # Check token type
            if payload.get("type") != "refresh":
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid refresh token type"
                )

            # Extract token information
            token_info = TokenInfo(
                user_id=int(payload["sub"]),
                wallet_address=payload["wallet_address"],
                role="",  # Refresh token does not contain role information
                exp=payload["exp"],
                iat=payload["iat"]
            )

            return token_info

        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token has expired"
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )

    @staticmethod
    def get_token_hash(token: str) -> str:
        """
        Get token hash value

        Args:
            token: JWT token

        Returns:
            Token hash value
        """
        return hashlib.sha256(token.encode()).hexdigest()

    @staticmethod
    def decode_token_payload(token: str) -> Dict[str, Any]:
        """
        Decode token payload (without verification)

        Args:
            token: JWT token

        Returns:
            Token payload
        """
        try:
            return jwt.decode(token, options={"verify_signature": False})
        except jwt.JWTError:
            return {}