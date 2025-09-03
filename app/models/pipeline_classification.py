"""管道分类模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class PipelineClassification(Base):
    """管道分类模型"""
    
    __tablename__ = "pipelin_classification"
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="主键ID"
    )
    
    parent_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="父级ID"
    )
    
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="分类名称"
    )
    
    create_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="创建时间"
    )
    
    disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否禁用(逻辑删除)"
    )
    
    def __repr__(self) -> str:
        return f"<PipelineClassification(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'parent_id': self.parent_id,
            'name': self.name,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'disabled': self.disabled
        }
