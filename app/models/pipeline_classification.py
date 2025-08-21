"""管道分类模型"""
from datetime import datetime
from sqlalchemy import BigInteger, String, DateTime
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
    
    parent_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
        comment="父级ID"
    )
    
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=True,
        comment="分类名称"
    )
    
    create_time: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=True,
        comment="创建时间"
    )
    
    def __repr__(self) -> str:
        return f"<PipelineClassification(id={self.id}, name='{self.name}', parent_id={self.parent_id})>"
