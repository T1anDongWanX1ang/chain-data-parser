"""字典映射器模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class DictMapper(Base):
    """字典映射器模型"""
    __tablename__ = 'dict_mapper'
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    component_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('pipeline_component.id'),
        nullable=False,
        comment="组件ID"
    )
    
    event_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="事件名称"
    )
    
    dict_mapper: Mapped[Optional[str]] = mapped_column(
        String(2048),
        nullable=True,
        comment="字典映射配置"
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
    
    # 关系定义 (使用字符串引用避免循环导入)
    component = relationship(
        "PipelineComponent",
        back_populates="dict_mappers"
    )
    
    def __repr__(self) -> str:
        return f"<DictMapper(id={self.id}, component_id={self.component_id}, event_name={self.event_name})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'component_id': self.component_id,
            'event_name': self.event_name,
            'dict_mapper': self.dict_mapper,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }
