"""Authentication-related Pydantic schemas"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator


class ChallengeRequest(BaseModel):
    """Challenge request"""
    wallet_address: str = Field(..., description="Wallet address")

    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        """Validate wallet address format"""
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid wallet address format')
        return v.lower()


class ChallengeResponse(BaseModel):
    """Challenge response"""
    challenge: str = Field(..., description="Challenge message to be signed")
    expires_at: datetime = Field(..., description="Challenge expiration time")


class VerifyRequest(BaseModel):
    """Verification request"""
    wallet_address: str = Field(..., description="Wallet address")
    signature: str = Field(..., description="Wallet signature")
    challenge: str = Field(..., description="Challenge message")

    @validator('wallet_address')
    def validate_wallet_address(cls, v):
        """Validate wallet address format"""
        if not v.startswith('0x') or len(v) != 42:
            raise ValueError('Invalid wallet address format')
        return v.lower()

    @validator('signature')
    def validate_signature(cls, v):
        """Validate signature format"""
        if not v.startswith('0x') or len(v) != 132:
            raise ValueError('Invalid signature format')
        return v


class TokenResponse(BaseModel):
    """Token response"""
    access_token: str = Field(..., description="Access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Expiration time (seconds)")
    user_info: "UserInfo" = Field(..., description="User information")


class UserInfo(BaseModel):
    """User information"""
    id: int = Field(..., description="User ID")
    wallet_address: str = Field(..., description="Wallet address")
    role: str = Field(..., description="User role")
    status: str = Field(..., description="User status")
    display_name: Optional[str] = Field(None, description="Display name")
    last_login_at: Optional[datetime] = Field(None, description="Last login time")
    created_at: datetime = Field(..., description="Creation time")


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str = Field(..., description="Refresh token")


class AuthErrorResponse(BaseModel):
    """Authentication error response"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Detailed information")


class TokenInfo(BaseModel):
    """Token information"""
    user_id: int = Field(..., description="User ID")
    wallet_address: str = Field(..., description="Wallet address")
    role: str = Field(..., description="User role")
    exp: int = Field(..., description="Expiration timestamp")
    iat: int = Field(..., description="Issued at timestamp")


# Update forward references
TokenResponse.model_rebuild()