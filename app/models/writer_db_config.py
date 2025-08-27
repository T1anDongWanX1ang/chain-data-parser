"""Writer DB配置模型"""
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy import BigInteger, JSON, DateTime, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WriterDbConfig(Base):
    """Writer DB配置模型"""
    __tablename__ = 'writer_db_config'
    
    component_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        comment="组件ID"
    )
    
    module_content: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=True,
        comment="模块内容JSON"
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
    
    # 定义索引
    __table_args__ = (
        Index('i_component_id', 'component_id'),
    )
    
    def __repr__(self) -> str:
        return f"<WriterDbConfig(component_id={self.component_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'component_id': self.component_id,
            'module_content': self.module_content,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        } 