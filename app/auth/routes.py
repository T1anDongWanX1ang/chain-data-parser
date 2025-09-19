"""Authentication API routes"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from loguru import logger

from app.models import User, UserSession
from app.services.database_service import get_db_session
from app.config import settings
from .schemas import (
    ChallengeRequest, ChallengeResponse,
    VerifyRequest, TokenResponse, UserInfo,
    RefreshTokenRequest, AuthErrorResponse
)
from .jwt_service import JWTService
from .web3_service import Web3Service


router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/challenge", response_model=ChallengeResponse)
async def create_challenge(
    request: ChallengeRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Generate Web3 signature challenge

    Args:
        request: Challenge request
        db: Database session

    Returns:
        Challenge response
    """
    try:
        # Validate wallet address format
        if not Web3Service.validate_ethereum_address(request.wallet_address):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid wallet address format"
            )

        # Generate challenge message
        challenge, expires_at = Web3Service.generate_challenge(request.wallet_address)

        logger.info(f"Generated challenge for wallet address {request.wallet_address}")

        return ChallengeResponse(
            challenge=challenge,
            expires_at=expires_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to generate challenge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate challenge"
        )


@router.post("/verify", response_model=TokenResponse)
async def verify_signature(
    request: VerifyRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Verify Web3 signature and return JWT token

    Args:
        request: Verification request
        db: Database session

    Returns:
        Token response
    """
    try:
        # Check if challenge is expired
        if Web3Service.is_challenge_expired(request.challenge):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge has expired, please regenerate"
            )

        # Verify wallet address in challenge message matches request
        challenge_wallet = Web3Service.extract_wallet_from_challenge(request.challenge)
        if challenge_wallet != request.wallet_address.lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Challenge message does not match wallet address"
            )

        # Verify signature
        if not Web3Service.verify_signature(
            request.wallet_address,
            request.signature,
            request.challenge
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Signature verification failed"
            )

        # Find or create user
        user_query = await db.execute(
            select(User).where(User.wallet_address == request.wallet_address.lower())
        )
        user = user_query.scalar_one_or_none()

        if not user:
            # Create new user
            user = User(
                wallet_address=request.wallet_address.lower(),
                role="user",  # Default role
                status="active"
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Created new user: {user.wallet_address}")
        else:
            # Update last login time
            await db.execute(
                update(User)
                .where(User.id == user.id)
                .values(last_login_at=datetime.utcnow())
            )
            await db.commit()
            logger.info(f"User logged in: {user.wallet_address}")

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been disabled"
            )

        # Generate JWT tokens
        access_token = JWTService.create_access_token(user)
        refresh_token = JWTService.create_refresh_token(user)

        # Save session information
        token_hash = JWTService.get_token_hash(access_token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)

        user_session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(user_session)
        await db.commit()

        # Construct user information
        user_info = UserInfo(
            id=user.id,
            wallet_address=user.wallet_address,
            role=user.role,
            status=user.status,
            display_name=user.display_name,
            last_login_at=user.last_login_at,
            created_at=user.created_at
        )

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60,
            user_info=user_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Signature verification failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Signature verification failed"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    Refresh access token

    Args:
        request: Refresh token request
        db: Database session

    Returns:
        New token response
    """
    try:
        # Verify refresh token
        token_info = JWTService.verify_refresh_token(request.refresh_token)

        # Find user
        user_query = await db.execute(
            select(User).where(User.id == token_info.user_id)
        )
        user = user_query.scalar_one_or_none()

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User does not exist"
            )

        # Check user status
        if user.status != "active":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account has been disabled"
            )

        # Generate new access token
        access_token = JWTService.create_access_token(user)

        # Save new session information
        token_hash = JWTService.get_token_hash(access_token)
        expires_at = datetime.utcnow() + timedelta(minutes=settings.security.access_token_expire_minutes)

        user_session = UserSession(
            user_id=user.id,
            token_hash=token_hash,
            expires_at=expires_at,
            is_revoked=False
        )
        db.add(user_session)
        await db.commit()

        # Construct user information
        user_info = UserInfo(
            id=user.id,
            wallet_address=user.wallet_address,
            role=user.role,
            status=user.status,
            display_name=user.display_name,
            last_login_at=user.last_login_at,
            created_at=user.created_at
        )

        logger.info(f"Token refresh successful: {user.wallet_address}")

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.security.access_token_expire_minutes * 60,
            user_info=user_info
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )


@router.post("/logout")
async def logout(
    token: str,
    db: AsyncSession = Depends(get_db_session)
):
    """
    User logout

    Args:
        token: Access token
        db: Database session

    Returns:
        Success message
    """
    try:
        # Verify token
        token_info = JWTService.verify_token(token)

        # Revoke session
        token_hash = JWTService.get_token_hash(token)
        await db.execute(
            update(UserSession)
            .where(UserSession.token_hash == token_hash)
            .values(is_revoked=True)
        )
        await db.commit()

        logger.info(f"User logged out: {token_info.wallet_address}")

        return {"message": "Logout successful"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )