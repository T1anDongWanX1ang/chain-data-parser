"""管道配置API接口"""
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from loguru import logger

from app.services.database_service import get_db_session
from app.services.pipeline_config_service import PipelineConfigService
from app.services.task_monitor_service import TaskMonitorService
from app.models.pipeline import Pipeline
from app.models.pipeline_task import PipelineTask
from app.models.pipeline_classification import PipelineClassification

router = APIRouter(prefix="/pipeline", tags=["管道配置"])


class PipelineConfigRequest(BaseModel):
    """管道配置请求模型"""
    pipeline_id: int  = Field(None, description="管道ID")
    pipeline_info: str = Field(..., description="管道配置信息JSON字符串")


class PipelineConfigResponse(BaseModel):
    """管道配置响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    pipeline_id: int = Field(None, description="管道ID")
    components_created: int = Field(0, description="创建的组件数量")


class PipelineItem(BaseModel):
    """管道项模型"""
    id: int = Field(..., description="管道ID")
    classification_id: int = Field(..., description="分类ID")
    name: Optional[str] = Field(None, description="管道名称")
    description: Optional[str] = Field(None, description="管道描述")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")


class PipelineListResponse(BaseModel):
    """管道列表响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[PipelineItem] = Field(..., description="管道列表数据")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class PipelineStartRequest(BaseModel):
    """管道启动请求模型"""
    pipeline_id: int = Field(..., description="管道ID")
    log_path: Optional[str] = Field(None, description="日志文件路径（可选）")


class PipelineStartResponse(BaseModel):
    """管道启动响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: Optional[int] = Field(None, description="任务ID")
    pipeline_id: int = Field(..., description="管道ID")


class TaskStatusResponse(BaseModel):
    """任务状态响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: int = Field(..., description="任务ID")
    pipeline_id: int = Field(..., description="管道ID")
    status: int = Field(..., description="任务状态")
    status_text: str = Field(..., description="状态描述")
    create_time: Optional[str] = Field(None, description="创建时间")
    log_path: Optional[str] = Field(None, description="日志路径")


class RunningTasksResponse(BaseModel):
    """正在运行任务响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[Dict[str, Any]] = Field(..., description="任务列表")
    count: int = Field(..., description="任务数量")


class TaskItem(BaseModel):
    """任务项模型"""
    task_id: int = Field(..., description="任务ID")
    pipeline_id: int = Field(..., description="管道ID")
    pipeline_name: Optional[str] = Field(None, description="管道名称")
    pipeline_description: Optional[str] = Field(None, description="管道描述")
    status: int = Field(..., description="任务状态")
    status_text: str = Field(..., description="状态描述")
    create_time: Optional[str] = Field(None, description="创建时间")
    log_path: Optional[str] = Field(None, description="日志路径")


class TaskListResponse(BaseModel):
    """任务列表响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[TaskItem] = Field(..., description="任务列表数据")
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页大小")
    total_pages: int = Field(..., description="总页数")


class TaskLogResponse(BaseModel):
    """任务日志响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    task_id: int = Field(..., description="任务ID")
    log_path: Optional[str] = Field(None, description="日志文件路径")
    log_content: str = Field(..., description="日志内容")
    total_lines: int = Field(..., description="日志总行数")
    returned_lines: int = Field(..., description="返回的行数")


class LatestTaskResponse(BaseModel):
    """最新任务响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    pipeline_id: int = Field(..., description="管道ID")
    task: Optional[TaskItem] = Field(None, description="最新任务信息，如果没有任务则为null")


# Pipeline新增相关模型
class PipelineCreateRequest(BaseModel):
    """Pipeline新增请求模型"""
    classification_id: int = Field(..., description="分类ID")
    name: Optional[str] = Field(None, description="管道名称", max_length=255)
    description: Optional[str] = Field(None, description="管道描述", max_length=255)


class PipelineCreateResponse(BaseModel):
    """Pipeline新增响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[PipelineItem] = Field(None, description="管道数据")


class PipelineUpdateResponse(BaseModel):
    """Pipeline更新响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[PipelineItem] = Field(None, description="管道数据")


# 树形结构相关模型
class TreeClassificationNode(BaseModel):
    """树形结构节点模型"""
    id: int = Field(..., description="节点ID")
    parent_id: Optional[int] = Field(None, description="父级ID")
    name: Optional[str] = Field(None, description="节点名称")
    description: Optional[str] = Field(None, description="节点描述")
    create_time: Optional[str] = Field(None, description="创建时间")
    update_time: Optional[str] = Field(None, description="更新时间")
    type: str = Field(..., description="节点类型：classification(分类) 或 pipeline(管道)")
    children: List['TreeClassificationNode'] = Field(default_factory=list, description="子节点列表")


class TreeStructureResponse(BaseModel):
    """树形结构响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: List[TreeClassificationNode] = Field(..., description="树形结构数据")


# 为了支持递归引用，需要更新模型
TreeClassificationNode.model_rebuild()


# 管道分类相关模型
class PipelineClassificationRequest(BaseModel):
    """管道分类请求模型"""
    parent_id: int = Field(..., description="父级ID")
    name: Optional[str] = Field(None, description="分类名称", max_length=255)


class PipelineUpdateRequest(BaseModel):
    """管道更新请求模型"""
    name: Optional[str] = Field(None, description="管道名称", max_length=255)
    description: Optional[str] = Field(None, description="管道描述", max_length=255)


class PipelineClassificationUpdateRequest(BaseModel):
    """管道分类更新请求模型"""
    parent_id: Optional[int] = Field(None, description="父级ID")
    name: Optional[str] = Field(None, description="分类名称", max_length=255)


class PipelineClassificationItem(BaseModel):
    """管道分类项模型"""
    id: int = Field(..., description="分类ID")
    parent_id: int = Field(..., description="父级ID")
    name: Optional[str] = Field(None, description="分类名称")
    create_time: Optional[str] = Field(None, description="创建时间")


class PipelineClassificationResponse(BaseModel):
    """管道分类响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[PipelineClassificationItem] = Field(None, description="分类数据")





# 依赖注入已移至 database_service.py


@router.post("/config", response_model=PipelineConfigResponse, summary="保存管道配置")
async def save_pipeline_config(
    request: PipelineConfigRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    保存管道配置
    
    解析pipeline_info JSON字符串，将数据保存到对应的数据库表中：
    - pipeline: 管道基本信息
    - pipeline_component: 管道组件信息
    - evm_event_monitor: EVM事件监控器配置
    - evm_contract_caller: EVM合约调用器配置
    - dict_mapper: 字典映射器配置
    - kafka_producer: Kafka生产者配置
    
    Args:
        request: 包含pipeline_id和pipeline_info的请求体
        session: 数据库会话
    
    Returns:
        PipelineConfigResponse: 保存结果
    """
    service = PipelineConfigService(session)
    result = await service.parse_and_save_pipeline(
        request.pipeline_id, 
        request.pipeline_info
    )


    
    return PipelineConfigResponse(**result)


@router.get("/config/{pipeline_id}", summary="获取管道配置")
async def get_pipeline_config(
    pipeline_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取管道配置
    
    Args:
        pipeline_id: 管道ID
        session: 数据库会话
    
    Returns:
        管道配置信息
    """
    try:
        service = PipelineConfigService(session)
        return await service.get_pipeline_config(pipeline_id)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取管道配置失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取配置失败: {str(e)}"
        )


@router.get("/list", response_model=PipelineListResponse, summary="分页查询管道列表")
async def get_pipelines_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小，最大100"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    分页查询管道列表
    
    返回所有管道的基本信息，包括所有字段：
    - id: 管道ID
    - name: 管道名称
    - description: 管道描述
    - create_time: 创建时间
    - update_time: 更新时间
    
    Args:
        page: 页码，从1开始，默认为1
        page_size: 每页大小，默认为10，最大100
        session: 数据库会话
    
    Returns:
        PipelineListResponse: 分页查询结果
    """
    try:
        service = PipelineConfigService(session)
        pipelines, total = await service.get_pipelines_paginated(page, page_size)
        
        # 转换为响应格式
        pipeline_items = []
        for pipeline in pipelines:
            pipeline_items.append(PipelineItem(
                id=pipeline.id,
                classification_id=pipeline.classification_id,
                name=pipeline.name,
                description=pipeline.description,
                create_time=pipeline.create_time.isoformat() if pipeline.create_time else None,
                update_time=pipeline.update_time.isoformat() if pipeline.update_time else None
            ))
        
        # 计算总页数
        import math
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return PipelineListResponse(
            success=True,
            message="查询成功",
            data=pipeline_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分页查询管道列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.post("/start", response_model=PipelineStartResponse, summary="启动管道任务")
async def start_pipeline(
    request: PipelineStartRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    启动管道任务
    
    根据 pipeline_id 查询管道配置信息，创建任务记录并启动管道执行器。
    任务状态会保存到 pipeline_task 表中：
    - 0: 正在运行
    - 1: 成功或结束
    - 2: 失败
    
    Args:
        request: 包含 pipeline_id 的请求体
        session: 数据库会话
    
    Returns:
        PipelineStartResponse: 启动结果，包含任务ID
    """
    try:
        service = PipelineConfigService(session)
        result = await service.start_pipeline_task(request.pipeline_id, request.log_path)
        
        return PipelineStartResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动管道任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"启动失败: {str(e)}"
        )


@router.get("/task/{task_id}", response_model=TaskStatusResponse, summary="查询任务状态")
async def get_task_status(
    task_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    查询任务状态
    
    根据任务ID查询任务的详细状态信息，包括：
    - 任务状态：0(正在运行)、1(成功或结束)、2(失败)
    - 创建时间
    - 日志路径
    
    Args:
        task_id: 任务ID
        session: 数据库会话
    
    Returns:
        TaskStatusResponse: 任务状态信息
    """
    try:
        task = await session.get(PipelineTask, task_id)
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"任务不存在: {task_id}"
            )
        
        return TaskStatusResponse(
            success=True,
            message="查询成功",
            task_id=task.id,
            pipeline_id=task.pipeline_id,
            status=task.status,
            status_text=task.status_text,
            create_time=task.create_time.isoformat() if task.create_time else None,
            log_path=task.log_path
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/tasks/running", response_model=RunningTasksResponse, summary="获取正在运行的任务")
async def get_running_tasks(
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取所有正在运行的任务
    
    返回当前系统中所有状态为"正在运行"(status=0)的任务列表。
    可用于监控系统中的活跃任务。
    
    Args:
        session: 数据库会话
    
    Returns:
        RunningTasksResponse: 正在运行的任务列表
    """
    try:
        from sqlalchemy import select
        
        result = await session.execute(
            select(PipelineTask).where(PipelineTask.status == 0)
            .order_by(PipelineTask.create_time.desc())
        )
        running_tasks = result.scalars().all()
        
        return RunningTasksResponse(
            success=True,
            message="查询成功",
            data=[
                {
                    "task_id": task.id,
                    "pipeline_id": task.pipeline_id,
                    "create_time": task.create_time.isoformat() if task.create_time else None,
                    "log_path": task.log_path,
                    "status_text": task.status_text
                }
                for task in running_tasks
            ],
            count=len(running_tasks)
        )
        
    except Exception as e:
        logger.error(f"查询正在运行任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/tasks/statistics", summary="获取任务统计信息")
async def get_task_statistics(
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取任务统计信息
    
    返回系统中任务的统计数据，包括：
    - 总任务数
    - 各状态任务数量
    - 最近24小时任务数
    
    Args:
        session: 数据库会话
    
    Returns:
        Dict: 任务统计信息
    """
    try:
        statistics = await TaskMonitorService.get_task_statistics(session)
        
        return {
            "success": True,
            "message": "查询成功",
            "data": statistics
        }
        
    except Exception as e:
        logger.error(f"获取任务统计失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.post("/tasks/reset-running", summary="重置正在运行的任务")
async def reset_running_tasks(
    session: AsyncSession = Depends(get_db_session)
):
    """
    手动重置所有正在运行的任务状态
    
    将所有状态为"正在运行"(status=0)的任务标记为失败(status=2)。
    通常用于系统维护或异常恢复。
    
    Args:
        session: 数据库会话
    
    Returns:
        Dict: 重置结果
    """
    try:
        await TaskMonitorService.reset_running_tasks_on_startup(session)
        
        return {
            "success": True,
            "message": "重置完成"
        }
        
    except Exception as e:
        logger.error(f"重置任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"重置失败: {str(e)}"
        )


@router.get("/tasks", response_model=TaskListResponse, summary="分页查询任务列表")
async def get_tasks_list(
    page: int = Query(1, ge=1, description="页码，从1开始"),
    page_size: int = Query(10, ge=1, le=100, description="每页大小，最大100"),
    status: Optional[int] = Query(None, ge=0, le=2, description="状态过滤：0(运行中)、1(成功)、2(失败)"),
    pipeline_name: Optional[str] = Query(None, description="管道名称关键字搜索"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    分页查询任务列表并关联管道信息
    
    返回任务列表，包含关联的管道信息：
    - 任务基本信息：ID、状态、创建时间、日志路径
    - 关联管道信息：管道ID、名称、描述
    - 支持按状态过滤
    - 支持按管道名称关键字搜索（模糊匹配）
    - 按创建时间降序排列（最新的在前面）
    
    Args:
        page: 页码，从1开始，默认为1
        page_size: 每页大小，默认为10，最大100
        status: 状态过滤，可选值：0(运行中)、1(成功)、2(失败)
        pipeline_name: 管道名称关键字，支持模糊搜索
        session: 数据库会话
    
    Returns:
        TaskListResponse: 分页查询结果
    """
    try:
        service = PipelineConfigService(session)
        tasks, total = await service.get_tasks_paginated(page, page_size, status, pipeline_name)
        
        # 转换为响应格式
        task_items = []
        for task_data in tasks:
            task_items.append(TaskItem(**task_data))
        
        # 计算总页数
        import math
        total_pages = math.ceil(total / page_size) if total > 0 else 0
        
        return TaskListResponse(
            success=True,
            message="查询成功",
            data=task_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"分页查询任务列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/pipeline/{pipeline_id}/latest-task", response_model=LatestTaskResponse, summary="查询管道最新任务")
async def get_pipeline_latest_task(
    pipeline_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    根据管道ID查询最新的任务信息
    
    Args:
        pipeline_id: 管道ID
        session: 数据库会话
    
    Returns:
        LatestTaskResponse: 最新任务信息
    """
    try:
        # 验证管道是否存在
        from sqlalchemy import select
        pipeline_query = select(Pipeline).where(Pipeline.id == pipeline_id)
        pipeline_result = await session.execute(pipeline_query)
        pipeline = pipeline_result.scalar_one_or_none()
        
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"管道 ID {pipeline_id} 不存在"
            )
        
        # 查询该管道的最新任务（按创建时间倒序）
        task_query = select(PipelineTask).where(
            PipelineTask.pipeline_id == pipeline_id
        ).order_by(PipelineTask.create_time.desc()).limit(1)
        
        task_result = await session.execute(task_query)
        latest_task = task_result.scalar_one_or_none()
        
        if not latest_task:
            return LatestTaskResponse(
                success=True,
                message=f"管道 ID {pipeline_id} 暂无任务记录",
                pipeline_id=pipeline_id,
                task=None
            )
        
        # 构建任务信息
        task_item = TaskItem(
            task_id=latest_task.id,
            pipeline_id=latest_task.pipeline_id,
            pipeline_name=pipeline.name,
            pipeline_description=pipeline.description,
            status=latest_task.status or 0,
            status_text=latest_task.status_text,
            create_time=latest_task.create_time.isoformat() if latest_task.create_time else None,
            log_path=latest_task.log_path
        )
        
        return LatestTaskResponse(
            success=True,
            message=f"成功获取管道 ID {pipeline_id} 的最新任务信息",
            pipeline_id=pipeline_id,
            task=task_item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询管道最新任务失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询失败: {str(e)}"
        )


@router.get("/task/{task_id}/log", response_model=TaskLogResponse, summary="获取任务日志")
async def get_task_log(
    task_id: int,
    lines: int = Query(900, ge=1, le=5000, description="读取的行数，默认900行，最大5000行"),
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取任务日志内容
    
    根据任务ID获取对应的日志文件内容，返回日志文件的最后N行。
    支持多种编码格式的日志文件读取。
    
    Args:
        task_id: 任务ID
        lines: 读取的行数，默认900行，最大5000行
        session: 数据库会话
    
    Returns:
        TaskLogResponse: 日志内容和相关信息
    """
    try:
        service = PipelineConfigService(session)
        log_data = await service.get_task_log(task_id, lines)
        
        return TaskLogResponse(
            success=True,
            message="获取日志成功",
            **log_data
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务日志失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取日志失败: {str(e)}"
        )


# Pipeline新增接口
@router.post("/create", response_model=PipelineCreateResponse, summary="新增管道")
async def create_pipeline(
    request: PipelineCreateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    新增管道
    
    创建一个新的管道记录。
    
    Args:
        request: 包含classification_id、name和description的请求体
        session: 数据库会话
    
    Returns:
        PipelineCreateResponse: 创建结果
    """
    try:
        from datetime import datetime
        
        # 创建新的管道记录
        pipeline = Pipeline(
            classification_id=request.classification_id,
            name=request.name,
            description=request.description,
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        session.add(pipeline)
        await session.flush()  # 获取生成的ID
        await session.commit()
        
        # 构建响应数据
        pipeline_item = PipelineItem(
            id=pipeline.id,
            classification_id=pipeline.classification_id,
            name=pipeline.name,
            description=pipeline.description,
            create_time=pipeline.create_time.isoformat() if pipeline.create_time else None,
            update_time=pipeline.update_time.isoformat() if pipeline.update_time else None
        )
        
        logger.info(f"新增管道成功: id={pipeline.id}, name={pipeline.name}, classification_id={pipeline.classification_id}")
        
        return PipelineCreateResponse(
            success=True,
            message="新增管道成功",
            data=pipeline_item
        )
        
    except Exception as e:
        logger.error(f"新增管道失败: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增失败: {str(e)}"
        )


@router.get("/tree", response_model=TreeStructureResponse, summary="获取管道分类树形结构")
async def get_pipeline_tree(
    session: AsyncSession = Depends(get_db_session)
):
    """
    获取管道分类树形结构
    
    查询所有管道分类和管道数据，以树形结构返回。
    树形结构包括：
    - 分类层级关系（父子关系）
    - 每个分类下的管道列表
    - 完整的分类和管道信息
    
    Args:
        session: 数据库会话
    
    Returns:
        TreeStructureResponse: 树形结构数据
    """
    try:
        from sqlalchemy import select
        
        # 查询所有分类（排除已删除的）
        classifications_result = await session.execute(
            select(PipelineClassification)
            .where(PipelineClassification.disabled == False)
            .order_by(PipelineClassification.id)
        )
        all_classifications = classifications_result.scalars().all()
        
        # 查询所有管道（排除已删除的）
        pipelines_result = await session.execute(
            select(Pipeline)
            .where(Pipeline.disabled == False)
            .order_by(Pipeline.id)
        )
        all_pipelines = pipelines_result.scalars().all()
        
        # 构建节点字典，包含分类和管道
        node_dict = {}
        
        # 添加分类节点
        for classification in all_classifications:
            node_dict[f"classification_{classification.id}"] = {
                'node': TreeClassificationNode(
                    id=classification.id,
                    parent_id=classification.parent_id,
                    name=classification.name,
                    description=None,  # 分类没有description字段
                    create_time=classification.create_time.isoformat() if classification.create_time else None,
                    update_time=None,  # 分类没有update_time字段
                    type="classification",
                    children=[]
                ),
                'parent_id': classification.parent_id,
                'type': 'classification'
            }
        
        # 添加管道节点
        for pipeline in all_pipelines:
            node_dict[f"pipeline_{pipeline.id}"] = {
                'node': TreeClassificationNode(
                    id=pipeline.id,
                    parent_id=pipeline.classification_id,
                    name=pipeline.name,
                    description=pipeline.description,
                    create_time=pipeline.create_time.isoformat() if pipeline.create_time else None,
                    update_time=pipeline.update_time.isoformat() if pipeline.update_time else None,
                    type="pipeline",
                    children=[]
                ),
                'parent_id': pipeline.classification_id,
                'type': 'pipeline'
            }
        
        # 构建树形结构
        root_nodes = []
        
        # 找到所有根节点和子节点
        for node_key, node_data in node_dict.items():
            parent_id = node_data['parent_id']
            current_node = node_data['node']
            node_type = node_data['type']
            
            # 查找父节点
            parent_found = False
            if parent_id is not None:
                # 对于管道节点，父节点是分类
                if node_type == 'pipeline':
                    parent_key = f"classification_{parent_id}"
                    if parent_key in node_dict:
                        node_dict[parent_key]['node'].children.append(current_node)
                        parent_found = True
                # 对于分类节点，父节点也是分类
                elif node_type == 'classification':
                    parent_key = f"classification_{parent_id}"
                    if parent_key in node_dict:
                        node_dict[parent_key]['node'].children.append(current_node)
                        parent_found = True
            
            # 如果没有找到父节点，且是分类节点，则为根节点
            if not parent_found and node_type == 'classification':
                root_nodes.append(current_node)
        
        # 递归排序子节点
        def sort_children(node: TreeClassificationNode):
            # 按类型和ID排序：分类在前，管道在后，同类型按ID排序
            node.children.sort(key=lambda x: (x.type == "pipeline", x.id))
            for child in node.children:
                sort_children(child)
        
        # 对根节点排序并递归排序所有子节点
        root_nodes.sort(key=lambda x: x.id)
        for root_node in root_nodes:
            sort_children(root_node)
        
        logger.info(f"获取管道分类树形结构成功: 分类数={len(all_classifications)}, 管道数={len(all_pipelines)}, 根节点数={len(root_nodes)}")
        
        return TreeStructureResponse(
            success=True,
            message="获取树形结构成功",
            data=root_nodes
        )
        
    except Exception as e:
        logger.error(f"获取管道分类树形结构失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取树形结构失败: {str(e)}"
        )


# 管道分类接口
@router.post("/classification", response_model=PipelineClassificationResponse, summary="新增管道分类")
async def create_pipeline_classification(
    request: PipelineClassificationRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    新增管道分类
    
    创建一个新的管道分类记录。
    
    Args:
        request: 包含parent_id和name的请求体
        session: 数据库会话
    
    Returns:
        PipelineClassificationResponse: 创建结果
    """
    try:
        from datetime import datetime
        
        # 创建新的分类记录
        classification = PipelineClassification(
            parent_id=request.parent_id,
            name=request.name,
            create_time=datetime.now()
        )
        
        session.add(classification)
        await session.flush()  # 获取生成的ID
        await session.commit()
        
        # 构建响应数据
        classification_item = PipelineClassificationItem(
            id=classification.id,
            parent_id=classification.parent_id,
            name=classification.name,
            create_time=classification.create_time.isoformat() if classification.create_time else None
        )
        
        logger.info(f"新增管道分类成功: id={classification.id}, name={classification.name}")
        
        return PipelineClassificationResponse(
            success=True,
            message="新增分类成功",
            data=classification_item
        )
        
    except Exception as e:
        logger.error(f"新增管道分类失败: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"新增失败: {str(e)}"
        )


@router.put("/classification/{classification_id}", response_model=PipelineClassificationResponse, summary="修改管道分类")
async def update_pipeline_classification(
    classification_id: int,
    request: PipelineClassificationUpdateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    修改管道分类
    
    根据分类ID更新管道分类信息。
    
    Args:
        classification_id: 分类ID
        request: 包含要更新字段的请求体
        session: 数据库会话
    
    Returns:
        PipelineClassificationResponse: 更新结果
    """
    try:
        # 查找现有分类
        classification = await session.get(PipelineClassification, classification_id)
        if not classification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分类不存在: {classification_id}"
            )
        
        # 检查分类是否已被删除
        if classification.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分类已被删除，无法修改"
            )
        
        # 更新字段
        updated = False
        if request.parent_id is not None:
            classification.parent_id = request.parent_id
            updated = True
        if request.name is not None and request.name.strip():
            classification.name = request.name.strip()
            updated = True
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的字段"
            )
        
        await session.commit()
        
        # 构建响应数据
        classification_item = PipelineClassificationItem(
            id=classification.id,
            parent_id=classification.parent_id,
            name=classification.name,
            create_time=classification.create_time.isoformat() if classification.create_time else None
        )
        
        logger.info(f"修改管道分类成功: id={classification.id}, name={classification.name}")
        
        return PipelineClassificationResponse(
            success=True,
            message="修改分类成功",
            data=classification_item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改管道分类失败: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改失败: {str(e)}"
        )


@router.delete("/classification/{classification_id}", summary="删除管道分类")
async def delete_pipeline_classification(
    classification_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    删除管道分类（逻辑删除）
    
    根据分类ID逻辑删除管道分类记录。
    会检查是否有子分类，如果有子分类则不能删除。
    
    Args:
        classification_id: 分类ID
        session: 数据库会话
    
    Returns:
        Dict: 删除结果
    """
    try:
        from sqlalchemy import select
        from datetime import datetime
        
        # 查找现有分类
        classification = await session.get(PipelineClassification, classification_id)
        if not classification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"分类不存在: {classification_id}"
            )
        
        # 检查分类是否已被删除
        if classification.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="分类已被删除"
            )
        
        # 检查是否有子分类
        child_result = await session.execute(
            select(PipelineClassification).where(
                PipelineClassification.parent_id == classification_id,
                PipelineClassification.disabled == False
            )
        )
        child_classifications = child_result.scalars().all()
        
        if child_classifications:
            child_names = [child.name for child in child_classifications]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该分类下还有子分类，不能删除。子分类: {', '.join(child_names)}"
            )
        
        # 检查是否有关联的管道
        pipeline_result = await session.execute(
            select(Pipeline).where(
                Pipeline.classification_id == classification_id,
                Pipeline.disabled == False
            )
        )
        pipelines = pipeline_result.scalars().all()
        
        if pipelines:
            pipeline_names = [pipeline.name for pipeline in pipelines]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该分类下还有管道，不能删除。管道: {', '.join(pipeline_names)}"
            )
        
        # 逻辑删除分类
        classification.disabled = True
        await session.commit()
        
        logger.info(f"逻辑删除管道分类成功: id={classification_id}, name={classification.name}")
        
        return {
            "success": True,
            "message": "删除分类成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除管道分类失败: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )


@router.put("/{pipeline_id}", response_model=PipelineUpdateResponse, summary="修改管道")
async def update_pipeline(
    pipeline_id: int,
    request: PipelineUpdateRequest,
    session: AsyncSession = Depends(get_db_session)
):
    """
    修改管道
    
    根据管道ID更新管道信息，支持修改名称和描述。
    
    Args:
        pipeline_id: 管道ID
        request: 包含要更新字段的请求体
        session: 数据库会话
    
    Returns:
        PipelineUpdateResponse: 更新结果
    """
    try:
        from datetime import datetime
        
        # 查找现有管道
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"管道不存在: {pipeline_id}"
            )
        
        # 检查管道是否已被删除
        if pipeline.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管道已被删除，无法修改"
            )
        
        # 更新字段
        updated = False
        if request.name is not None and request.name.strip():
            pipeline.name = request.name.strip()
            updated = True
        if request.description is not None:
            pipeline.description = request.description.strip() if request.description.strip() else None
            updated = True
        
        if not updated:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="没有提供要更新的字段"
            )
        
        # 更新修改时间
        pipeline.update_time = datetime.now()
        await session.commit()
        
        # 构建响应数据
        pipeline_item = PipelineItem(
            id=pipeline.id,
            classification_id=pipeline.classification_id,
            name=pipeline.name,
            description=pipeline.description,
            create_time=pipeline.create_time.isoformat() if pipeline.create_time else None,
            update_time=pipeline.update_time.isoformat() if pipeline.update_time else None
        )
        
        logger.info(f"修改管道成功: id={pipeline.id}, name={pipeline.name}")
        
        return PipelineUpdateResponse(
            success=True,
            message="修改管道成功",
            data=pipeline_item
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"修改管道失败: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"修改失败: {str(e)}"
        )


@router.delete("/{pipeline_id}", summary="删除管道")
async def delete_pipeline(
    pipeline_id: int,
    session: AsyncSession = Depends(get_db_session)
):
    """
    删除管道（逻辑删除）
    
    根据管道ID逻辑删除管道记录。
    会检查是否有正在运行的任务，如果有正在运行的任务则不能删除。
    
    Args:
        pipeline_id: 管道ID
        session: 数据库会话
    
    Returns:
        Dict: 删除结果
    """
    try:
        from sqlalchemy import select
        from datetime import datetime
        
        # 查找现有管道
        pipeline = await session.get(Pipeline, pipeline_id)
        if not pipeline:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"管道不存在: {pipeline_id}"
            )
        
        # 检查管道是否已被删除
        if pipeline.disabled:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="管道已被删除"
            )
        
        # 检查是否有正在运行的任务
        running_tasks_result = await session.execute(
            select(PipelineTask).where(
                PipelineTask.pipeline_id == pipeline_id,
                PipelineTask.status == 0  # 0表示正在运行
            )
        )
        running_tasks = running_tasks_result.scalars().all()
        
        if running_tasks:
            task_ids = [str(task.id) for task in running_tasks]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"该管道还有正在运行的任务，不能删除。任务ID: {', '.join(task_ids)}"
            )
        
        # 逻辑删除管道
        pipeline.disabled = True
        pipeline.update_time = datetime.now()
        await session.commit()
        
        logger.info(f"逻辑删除管道成功: id={pipeline_id}, name={pipeline.name}")
        
        return {
            "success": True,
            "message": "删除管道成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除管道失败: {e}")
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )



