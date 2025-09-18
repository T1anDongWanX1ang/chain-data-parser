"""告警模块API路由"""
from typing import Optional
from datetime import datetime, date as DateType
from fastapi import APIRouter, Depends, HTTPException, Query, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select, update, and_
from sqlalchemy.exc import IntegrityError

from app.models.alert import Alert, AlertResponse, AlertCountResponse, AlertListResponse, BatchAlertCreate, BatchAlertResponse, AlertCreate
from app.services.database_service import get_db_session
from app.config import settings
from loguru import logger

router = APIRouter(prefix="/alerts", tags=["alerts"])

def verify_api_key(x_api_key: str = Header(None)):
    """
    验证API Key
    
    Args:
        x_api_key: 请求头中的API key
        
    Raises:
        HTTPException: 当API key无效时
    """
    if not x_api_key or x_api_key not in settings.alert.valid_api_keys:
        raise HTTPException(
            status_code=401, 
            detail="无效的API Key"
        )
    return x_api_key

@router.get("/count", response_model=AlertCountResponse)
async def get_alert_count(db: AsyncSession = Depends(get_db_session)):
    """
    获取告警数量统计
    
    Returns:
        AlertCountResponse: 包含总数和按严重程度分类的统计
    """
    try:
        # 获取未清除告警总数
        total_result = await db.execute(select(func.count(Alert.id)).filter(Alert.is_cleared == False))
        total_count = total_result.scalar()
        
        # 按严重程度统计
        severity_stats = {}
        severity_query = await db.execute(
            select(Alert.severity, func.count(Alert.id).label('count'))
            .filter(Alert.is_cleared == False)
            .group_by(Alert.severity)
        )
        
        for severity, count in severity_query.fetchall():
            severity_stats[severity] = count
            
        logger.info(f"获取告警数量: 总数={total_count}, 详情={severity_stats}")
        
        return AlertCountResponse(
            count=total_count,
            severity_stats=severity_stats
        )
        
    except Exception as e:
        logger.error(f"获取告警数量失败: {e}")
        raise HTTPException(status_code=500, detail="获取告警数量失败")

@router.get("", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    severity: Optional[str] = Query(None, description="按严重程度过滤"),
    alert_type: Optional[str] = Query(None, description="按告警类型过滤"),
    case_name: Optional[str] = Query(None, description="按案例名称过滤"),
    table: Optional[str] = Query(None, description="按表名过滤"),
    owner: Optional[str] = Query(None, description="按负责人过滤"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    获取告警列表
    
    Args:
        page: 页码，从1开始
        size: 每页数量，最大100
        severity: 严重程度过滤 (low/medium/high/critical)
        alert_type: 告警类型过滤
        case_name: 案例名称过滤
        table: 表名过滤
        owner: 负责人过滤
    
    Returns:
        AlertListResponse: 告警列表和分页信息
    """
    try:
        # 构建查询条件
        query = select(Alert).filter(Alert.is_cleared == False)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if case_name:
            query = query.filter(Alert.case_name == case_name)
        if table:
            query = query.filter(Alert.table == table)
        if owner:
            query = query.filter(Alert.owner == owner)
            
        # 获取总数
        total_query = select(func.count(Alert.id)).filter(Alert.is_cleared == False)
        if severity:
            total_query = total_query.filter(Alert.severity == severity)
        if alert_type:
            total_query = total_query.filter(Alert.alert_type == alert_type)
        if case_name:
            total_query = total_query.filter(Alert.case_name == case_name)
        if table:
            total_query = total_query.filter(Alert.table == table)
        if owner:
            total_query = total_query.filter(Alert.owner == owner)
        total_result = await db.execute(total_query)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * size
        alerts_result = await db.execute(
            query.order_by(Alert.created_at.desc()).offset(offset).limit(size)
        )
        alerts = alerts_result.scalars().all()
        
        logger.info(f"获取告警列表: 页码={page}, 数量={len(alerts)}, 总数={total}")
        
        return AlertListResponse(
            alerts=[AlertResponse.model_validate(alert) for alert in alerts],
            total=total,
            page=page,
            size=size
        )
        
    except Exception as e:
        logger.error(f"获取告警列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取告警列表失败")

@router.delete("/clear-all")
async def clear_all_alerts(db: AsyncSession = Depends(get_db_session)):
    """
    清除所有未处理的告警
    
    Returns:
        dict: 操作结果
    """
    try:
        # 获取所有未清除的告警数量
        count_result = await db.execute(select(func.count(Alert.id)).filter(Alert.is_cleared == False))
        count = count_result.scalar()
        
        if count == 0:
            return {"success": True, "message": "没有需要清除的告警"}
        
        # 批量更新
        await db.execute(
            update(Alert)
            .filter(Alert.is_cleared == False)
            .values(
                is_cleared=True,
                cleared_at=datetime.utcnow(),
                cleared_by="system"
            )
        )
        
        await db.commit()
        logger.info(f"批量清除告警: 数量={count}")
        
        return {"success": True, "message": f"已清除 {count} 条告警"}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"批量清除告警失败: {e}")
        raise HTTPException(status_code=500, detail="批量清除告警失败")

@router.delete("/{alert_id}")
async def clear_alert(alert_id: int, db: AsyncSession = Depends(get_db_session)):
    """
    清除单个告警
    
    Args:
        alert_id: 告警ID
    
    Returns:
        dict: 操作结果
    """
    try:
        # 查找告警
        result = await db.execute(select(Alert).filter(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
            
        # 标记为已清除
        alert.is_cleared = True
        alert.cleared_at = datetime.utcnow()
        alert.cleared_by = "system"  # 可以后续扩展为用户信息
        
        await db.commit()
        logger.info(f"告警已清除: ID={alert_id}")
        
        return {"success": True, "message": f"告警 {alert_id} 已清除"}
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"清除告警失败: {e}")
        raise HTTPException(status_code=500, detail="清除告警失败")

@router.post("/test")
async def create_test_alert(db: AsyncSession = Depends(get_db_session)):
    """
    创建测试告警（开发调试用）
    
    Returns:
        dict: 创建结果
    """
    try:
        test_alert = Alert(
            message=f"测试告警 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            alert_type="test",
            severity="medium",
            source="api-test"
        )
        
        db.add(test_alert)
        await db.commit()
        await db.refresh(test_alert)
        
        logger.info(f"创建测试告警: ID={test_alert.id}")
        
        return {"success": True, "message": "测试告警创建成功", "alert_id": test_alert.id}
        
    except Exception as e:
        await db.rollback()
        logger.error(f"创建测试告警失败: {e}")
        raise HTTPException(status_code=500, detail="创建测试告警失败")

@router.post("/batch", response_model=BatchAlertResponse)
async def create_batch_alerts(
    batch_request: BatchAlertCreate,
    db: AsyncSession = Depends(get_db_session),
    api_key: str = Depends(verify_api_key)
):
    """
    批量创建告警（需要API Key验证）
    
    如果message和date组合已存在，则更新alert_times、last_alert和is_cleared字段
    否则创建新的告警记录
    
    Args:
        batch_request: 批量告警创建请求
        api_key: API密钥（通过Header验证）
    
    Returns:
        BatchAlertResponse: 批量操作结果
    """
    created_count = 0
    updated_count = 0
    failed_count = 0
    details = []
    
    try:
        for alert_data in batch_request.alerts:
            try:
                # 检查是否存在相同的message和date组合
                existing_alert_query = select(Alert).filter(
                    and_(
                        Alert.message == alert_data.message,
                        Alert.date == alert_data.date
                    )
                )
                result = await db.execute(existing_alert_query)
                existing_alert = result.scalar_one_or_none()
                
                if existing_alert:
                    # 更新现有记录
                    existing_alert.alert_times = (existing_alert.alert_times or 0) + (alert_data.alert_times or 1)
                    existing_alert.last_alert = alert_data.last_alert or datetime.utcnow()
                    existing_alert.is_cleared = False  # 重新激活告警
                    
                    # 更新其他字段（如果提供了新值）
                    if alert_data.alert_type != 'system':
                        existing_alert.alert_type = alert_data.alert_type
                    if alert_data.severity != 'medium':
                        existing_alert.severity = alert_data.severity
                    if alert_data.source != 'chain-parser':
                        existing_alert.source = alert_data.source
                    if alert_data.case_name:
                        existing_alert.case_name = alert_data.case_name
                    if alert_data.column:
                        existing_alert.column = alert_data.column
                    if alert_data.table:
                        existing_alert.table = alert_data.table
                    if alert_data.owner:
                        existing_alert.owner = alert_data.owner
                    
                    updated_count += 1
                    details.append({
                        "action": "updated",
                        "message": alert_data.message,
                        "date": str(alert_data.date),
                        "alert_id": existing_alert.id,
                        "new_alert_times": existing_alert.alert_times
                    })
                    
                else:
                    # 创建新记录
                    new_alert = Alert(
                        message=alert_data.message,
                        alert_type=alert_data.alert_type,
                        severity=alert_data.severity,
                        source=alert_data.source,
                        case_name=alert_data.case_name,
                        column=alert_data.column,
                        table=alert_data.table,
                        owner=alert_data.owner,
                        alert_times=alert_data.alert_times,
                        last_alert=alert_data.last_alert,
                        date=alert_data.date,
                        created_at=datetime.utcnow(),
                        is_cleared=False
                    )
                    
                    db.add(new_alert)
                    await db.flush()  # 获取ID但不提交
                    
                    created_count += 1
                    details.append({
                        "action": "created",
                        "message": alert_data.message,
                        "date": str(alert_data.date),
                        "alert_id": new_alert.id
                    })
                    
            except Exception as e:
                failed_count += 1
                details.append({
                    "action": "failed",
                    "message": alert_data.message,
                    "date": str(alert_data.date) if alert_data.date else None,
                    "error": str(e)
                })
                logger.error(f"处理告警失败: {alert_data.message}, 错误: {e}")
        
        # 提交所有更改
        await db.commit()
        
        success = failed_count == 0
        message = f"批量操作完成: 创建 {created_count} 条, 更新 {updated_count} 条, 失败 {failed_count} 条"
        
        logger.info(f"批量告警操作完成: {message}, API Key: {api_key}")
        
        return BatchAlertResponse(
            success=success,
            message=message,
            created_count=created_count,
            updated_count=updated_count,
            failed_count=failed_count,
            details=details
        )
        
    except Exception as e:
        await db.rollback()
        logger.error(f"批量创建告警失败: {e}")
        raise HTTPException(status_code=500, detail=f"批量创建告警失败: {str(e)}")