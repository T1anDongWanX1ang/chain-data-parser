"""Kafka生产者模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class KafkaProducer(Base):
    """Kafka生产者模型"""
    __tablename__ = 'kafka_producer'
    
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
    
    bootstrap_servers: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Kafka服务器地址"
    )
    
    topic: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="Kafka主题"
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
        back_populates="kafka_producer"
    )
    
    def __repr__(self) -> str:
        return f"<KafkaProducer(id={self.id}, topic='{self.topic}', bootstrap_servers='{self.bootstrap_servers}', component_id={self.component_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'component_id': self.component_id,
            'bootstrap_servers': self.bootstrap_servers,
            'topic': self.topic,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }
