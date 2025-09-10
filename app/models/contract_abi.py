"""合约ABI模型"""
from typing import Optional
from sqlalchemy import BigInteger, String, Text, Index
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class ContractAbi(Base, TimestampMixin):
    """合约ABI模型"""
    __tablename__ = 'contract_abis'
    
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
        autoincrement=True,
        comment="主键ID"
    )
    
    contract_address: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        comment="合约地址"
    )
    
    chain_name: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        comment="链名称（如：ethereum, bsc, polygon）"
    )
    
    abi_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        comment="ABI JSON内容"
    )
    
    file_path: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="ABI文件存储路径"
    )
    
    source_type: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default='manual',
        comment="来源类型（manual: 手动上传, auto: 自动获取）"
    )
    
    # 索引定义
    __table_args__ = (
        Index('idx_contract_address_chain', 'contract_address', 'chain_name', unique=True),
        Index('idx_chain_name', 'chain_name'),
        Index('idx_created_at', 'created_at'),
    )
    
    def __repr__(self) -> str:
        return f"<ContractAbi(id={self.id}, contract_address='{self.contract_address}', chain_name='{self.chain_name}')>"
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            'id': self.id,
            'contract_address': self.contract_address,
            'chain_name': self.chain_name,
            'abi_content': self.abi_content,
            'file_path': self.file_path,
            'source_type': self.source_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }