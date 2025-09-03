"""Writer配置API接口"""
from typing import Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from loguru import logger

from app.services.database_service import get_db_session
from app.models.writer_db_config import WriterDbConfig

router = APIRouter(prefix="", tags=["Writer配置"])


class SaveIngestionConfigRequest(BaseModel):
    """保存数据摄取配置请求模型"""
    component_id: int = Field(..., description="组件ID", ge=1)
    module_content: Dict[str, Any] = Field(..., description="模块内容JSON")


class SaveIngestionConfigResponse(BaseModel):
    """保存数据摄取配置响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作消息")
    data: Dict[str, Any] = Field(default_factory=dict, description="返回数据")


class GetComponentConfigResponse(BaseModel):
    """获取组件配置响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="操作消息")
    data: Dict[str, Any] = Field(default_factory=dict, description="模块内容")


@router.post("/save-ingestion-config", response_model=SaveIngestionConfigResponse, summary="保存数据摄取配置")
async def save_ingestion_config(
    request: SaveIngestionConfigRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    保存数据摄取配置
    
    支持新增和更新操作：
    - 如果component_id不存在，则新增记录
    - 如果component_id已存在，则更新记录
    
    Args:
        request: 请求参数，包含component_id和module_content
        session: 数据库会话
    
    Returns:
        SaveIngestionConfigResponse: 操作结果
    """
    try:
        logger.info(f"保存数据摄取配置: component_id={request.component_id}")
        
        # 查询是否已存在记录
        existing_result = await session.execute(
            select(WriterDbConfig).where(WriterDbConfig.component_id == request.component_id)
        )
        existing_config = existing_result.scalar_one_or_none()
        
        current_time = datetime.now()
        
        if existing_config:
            # 更新现有记录
            existing_config.module_content = request.module_content
            existing_config.update_time = current_time
            
            await session.commit()
            await session.refresh(existing_config)
            
            logger.info(f"更新数据摄取配置成功: component_id={request.component_id}")
            
            return SaveIngestionConfigResponse(
                success=True,
                message="配置更新成功",
                data={
                    "component_id": existing_config.component_id,
                    "operation": "update",
                    "update_time": existing_config.update_time.isoformat()
                }
            )
        else:
            # 创建新记录
            new_config = WriterDbConfig(
                component_id=request.component_id,
                module_content=request.module_content,
                create_time=current_time,
                update_time=current_time
            )
            
            session.add(new_config)
            await session.commit()
            await session.refresh(new_config)
            
            logger.info(f"新增数据摄取配置成功: component_id={request.component_id}")
            
            return SaveIngestionConfigResponse(
                success=True,
                message="配置保存成功",
                data={
                    "component_id": new_config.component_id,
                    "operation": "create",
                    "create_time": new_config.create_time.isoformat()
                }
            )
        
    except Exception as e:
        logger.error(f"保存数据摄取配置失败: component_id={request.component_id}, error={str(e)}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"保存配置失败: {str(e)}"
        )


@router.get("/component/{component_id}/config", response_model=GetComponentConfigResponse, summary="获取组件配置")
async def get_component_config(
    component_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    根据组件ID获取配置信息
    
    Args:
        component_id: 组件ID
        session: 数据库会话
    
    Returns:
        GetComponentConfigResponse: 包含module_content的配置信息
    """
    try:
        logger.info(f"获取组件配置: component_id={component_id}")
        
        # 查询配置记录
        result = await session.execute(
            select(WriterDbConfig).where(WriterDbConfig.component_id == component_id)
        )
        config = result.scalar_one_or_none()
        
        if not config:
            logger.warning(f"组件配置不存在: component_id={component_id}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"组件ID {component_id} 的配置不存在"
            )
        
        logger.info(f"获取组件配置成功: component_id={component_id}")
        
        return GetComponentConfigResponse(
            success=True,
            message="获取配置成功",
            data=config.module_content or {}
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"获取组件配置失败: component_id={component_id}, error={str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        ) 