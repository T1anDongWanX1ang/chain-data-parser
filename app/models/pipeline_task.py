"""管道任务模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, SmallInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PipelineTask(Base):
    """管道任务模型"""
    __tablename__ = 'pipeline_task'
    
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
    
    create_time: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
        comment="创建时间"
    )
    
    status: Mapped[Optional[int]] = mapped_column(
        SmallInteger,
        nullable=True,
        default=0,
        comment="0:正在运行，1:成功或结束，2:失败"
    )
    
    log_path: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="日志路径"
    )
    
    # 定义索引
    __table_args__ = (
        Index('i_pipeline_id', 'pipeline_id'),
    )
    
    # 关系定义
    pipeline = relationship(
        "Pipeline",
        back_populates="tasks"
    )
    
    def __repr__(self) -> str:
        return f"<PipelineTask(id={self.id}, pipeline_id={self.pipeline_id}, status={self.status})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'pipeline_id': self.pipeline_id,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'status': self.status,
            'log_path': self.log_path
        }
    
    @property
    def status_text(self) -> str:
        """状态文本描述"""
        status_mapping = {
            0: "正在运行",
            1: "成功或结束", 
            2: "失败"
        }
        return status_mapping.get(self.status, "未知状态")
