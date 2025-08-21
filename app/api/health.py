"""健康检查API接口"""
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict, Any

from app.services.database_service import database_service

router = APIRouter(prefix="/health", tags=["健康检查"])


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str = Field(..., description="整体状态")
    database: Dict[str, Any] = Field(..., description="数据库状态")
    services: Dict[str, Any] = Field(..., description="服务状态")


@router.get("/", response_model=HealthResponse, summary="系统健康检查")
async def health_check():
    """
    系统健康检查
    
    检查数据库连接、服务状态等
    
    Returns:
        HealthResponse: 健康检查结果
    """
    # 检查数据库
    db_health = await database_service.health_check()
    
    # 检查其他服务状态
    services_status = {
        "pipeline_config": "active",
        "file_upload": "active",
        "api": "active"
    }
    
    # 确定整体状态
    overall_status = "healthy" if db_health["status"] == "healthy" else "unhealthy"
    
    return HealthResponse(
        status=overall_status,
        database=db_health,
        services=services_status
    )


@router.get("/database", summary="数据库详细信息")
async def database_info():
    """
    获取数据库详细信息
    
    Returns:
        dict: 数据库连接信息
    """
    health_info = await database_service.health_check()
    connection_info = database_service.get_connection_info()
    
    return {
        "health": health_info,
        "connection": connection_info
    }
