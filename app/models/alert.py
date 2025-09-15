"""告警模型定义"""
from typing import Optional
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum, Text
from sqlalchemy.ext.declarative import declarative_base
from pydantic import BaseModel

Base = declarative_base()

class Alert(Base):
    """告警数据模型"""
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True, comment="告警ID")
    message = Column(String(255), nullable=False, comment="告警消息")
    alert_type = Column(String(50), default='system', comment="告警类型")
    severity = Column(
        Enum('low', 'medium', 'high', 'critical', name='severity_enum'), 
        default='medium', 
        comment="严重程度"
    )
    source = Column(String(100), default='chain-parser', comment="告警来源")
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    is_cleared = Column(Boolean, default=False, comment="是否已清除")
    cleared_at = Column(DateTime, nullable=True, comment="清除时间")
    cleared_by = Column(String(100), nullable=True, comment="清除人")

class AlertCreate(BaseModel):
    """创建告警的数据模型"""
    message: str
    alert_type: str = 'system'
    severity: str = 'medium'
    source: str = 'chain-parser'

class AlertResponse(BaseModel):
    """告警响应数据模型"""
    id: int
    message: str
    alert_type: str
    severity: str
    source: str
    created_at: datetime
    is_cleared: bool
    cleared_at: Optional[datetime] = None
    cleared_by: Optional[str] = None
    
    class Config:
        from_attributes = True

class AlertCountResponse(BaseModel):
    """告警数量响应模型"""
    count: int
    severity_stats: dict = {}

class AlertListResponse(BaseModel):
    """告警列表响应模型"""
    alerts: list[AlertResponse]
    total: int
    page: int
    size: int