"""管道模型"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import BigInteger, String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Pipeline(Base):
    """管道模型"""
    __tablename__ = 'pipeline'
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    classification_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="分类ID"
    )
    
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="管道名称"
    )
    
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="管道描述"
    )
    
    create_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="创建时间"
    )
    
    update_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="更新时间"
    )
    
    disabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        comment="是否禁用(逻辑删除)"
    )
    
    # 关系定义 (使用字符串引用避免循环导入)
    components = relationship(
        "PipelineComponent",
        back_populates="pipeline",
        cascade="all, delete-orphan"
    )
    
    tasks = relationship(
        "PipelineTask",
        back_populates="pipeline",
        cascade="all, delete-orphan"
    )
    
    def __repr__(self) -> str:
        return f"<Pipeline(id={self.id}, classification_id={self.classification_id}, name='{self.name}', description='{self.description}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'classification_id': self.classification_id,
            'name': self.name,
            'description': self.description,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None,
            'disabled': self.disabled
        }
