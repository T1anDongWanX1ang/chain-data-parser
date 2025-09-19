"""用户模型"""
from typing import Optional
from datetime import datetime
from sqlalchemy import BigInteger, String, Boolean, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class User(Base, TimestampMixin):
    """用户模型"""
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )

    wallet_address: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        comment="钱包地址（唯一标识）"
    )

    role: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default='user',
        comment="用户角色（admin: 管理员, user: 普通用户）"
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default='active',
        comment="用户状态（active: 活跃, disabled: 禁用）"
    )

    display_name: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
        comment="显示名称（可选）"
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="最后登录时间"
    )

    # 索引定义
    __table_args__ = (
        Index('idx_users_wallet_address', 'wallet_address', unique=True),
        Index('idx_users_role_status', 'role', 'status'),
        Index('idx_users_created_at', 'created_at'),
        Index('idx_users_last_login_at', 'last_login_at'),
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, wallet_address='{self.wallet_address}', role='{self.role}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'wallet_address': self.wallet_address,
            'role': self.role,
            'status': self.status,
            'display_name': self.display_name,
            'last_login_at': self.last_login_at.isoformat() if self.last_login_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def is_admin(self) -> bool:
        """是否为管理员"""
        return self.role == 'admin'

    @property
    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self.status == 'active'


class UserSession(Base, TimestampMixin):
    """用户会话模型"""
    __tablename__ = 'user_sessions'

    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )

    user_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="用户ID"
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        unique=True,
        comment="JWT令牌哈希值"
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        comment="过期时间"
    )

    is_revoked: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否已撤销"
    )

    device_info: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="设备信息（User-Agent等）"
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(45),
        nullable=True,
        comment="IP地址（支持IPv6）"
    )

    # 索引定义
    __table_args__ = (
        Index('idx_user_sessions_user_id', 'user_id'),
        Index('idx_user_sessions_token_hash', 'token_hash', unique=True),
        Index('idx_user_sessions_expires_at', 'expires_at'),
        Index('idx_user_sessions_user_expires', 'user_id', 'expires_at'),
        Index('idx_user_sessions_revoked', 'is_revoked'),
    )

    def __repr__(self) -> str:
        return f"<UserSession(id={self.id}, user_id={self.user_id}, expires_at='{self.expires_at}')>"

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token_hash': self.token_hash,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_revoked': self.is_revoked,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @property
    def is_expired(self) -> bool:
        """是否已过期"""
        from datetime import datetime
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self) -> bool:
        """是否有效（未撤销且未过期）"""
        return not self.is_revoked and not self.is_expired