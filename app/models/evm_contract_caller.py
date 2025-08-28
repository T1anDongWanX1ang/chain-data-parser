"""EVM合约调用器模型"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class EvmContractCaller(Base):
    """EVM合约调用器模型"""
    __tablename__ = 'evm_contract_caller'
    
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
    
    chain_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="链名称"
    )
    
    abi_path: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="ABI文件路径"
    )
    
    contract_address: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="合约地址"
    )
    
    method_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        comment="方法名称"
    )
    
    method_params: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="方法参数"
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
        back_populates="evm_contract_caller"
    )
    
    def __repr__(self) -> str:
        return f"<EvmContractCaller(id={self.id}, event_name='{self.event_name}', chain_name='{self.chain_name}', contract_address='{self.contract_address}', method_name='{self.method_name}', component_id={self.component_id})>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'component_id': self.component_id,
            'event_name': self.event_name,
            'chain_name': self.chain_name,
            'abi_path': self.abi_path,
            'contract_address': self.contract_address,
            'method_name': self.method_name,
            'method_params': self.method_params,
            'create_time': self.create_time.isoformat() if self.create_time else None,
            'update_time': self.update_time.isoformat() if self.update_time else None
        }
