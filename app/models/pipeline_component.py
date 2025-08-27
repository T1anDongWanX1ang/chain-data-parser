"""管道组件模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PipelineComponent(Base):
    """管道组件模型"""
    __tablename__ = 'pipeline_component'
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    pipeline_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('pipeline.id'),
        nullable=False,
        comment="管道ID"
    )
    
    pre_component_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        nullable=True,
        comment="上一个组件ID"
    )
    
    name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="组件名称"
    )
    
    type: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="组件类型"
    )
    
    create_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="创建时间"
    )
    
    # 定义索引
    __table_args__ = (
        Index('i_pipeline_id', 'pipeline_id'),
    )
    
    # 关系定义 (使用字符串引用避免循环导入)
    pipeline = relationship(
        "Pipeline",
        back_populates="components"
    )
    
    evm_event_monitor = relationship(
        "EvmEventMonitor",
        back_populates="component",
        uselist=False
    )
    
    kafka_producer = relationship(
        "KafkaProducer",
        back_populates="component",
        uselist=False
    )
    
    evm_contract_caller = relationship(
        "EvmContractCaller",
        back_populates="component",
        uselist=False
    )
    
    dict_mappers = relationship(
        "DictMapper",
        back_populates="component",
        uselist=True
    )
    
    def __repr__(self) -> str:
        return f"<PipelineComponent(id={self.id}, name='{self.name}', type='{self.type}', pipeline_id={self.pipeline_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'pipeline_id': self.pipeline_id,
            'pre_component_id': self.pre_component_id,
            'name': self.name,
            'type': self.type,
            'create_time': self.create_time.isoformat() if self.create_time else None
        }
