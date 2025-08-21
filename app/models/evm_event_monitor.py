"""EVM事件监控器模型"""
from typing import Optional
from sqlalchemy import BigInteger, String, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class EvmEventMonitor(Base):
    """EVM事件监控器模型"""
    __tablename__ = 'evm_event_monitor'
    
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
    
    chain_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="链名称"
    )
    
    contract_address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="合约地址"
    )
    
    abi_path: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="ABI文件路径"
    )
    
    events_to_monitor: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="监控的事件列表"
    )
    
    # 定义索引
    __table_args__ = (
        Index('i_component_id', 'component_id'),
    )
    
    # 关系定义 (使用字符串引用避免循环导入)
    component = relationship(
        "PipelineComponent",
        back_populates="evm_event_monitor"
    )
    
    def __repr__(self) -> str:
        return f"<EvmEventMonitor(id={self.id}, chain_name='{self.chain_name}', contract_address='{self.contract_address}', component_id={self.component_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'component_id': self.component_id,
            'chain_name': self.chain_name,
            'contract_address': self.contract_address,
            'abi_path': self.abi_path,
            'events_to_monitor': self.events_to_monitor
        }
