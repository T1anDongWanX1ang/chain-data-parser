"""应用启动和关闭事件处理"""
from loguru import logger
from app.services.task_monitor_service import initialize_task_monitoring, shutdown_task_monitoring


async def startup_event():
    """应用启动事件"""
    try:
        logger.info("应用启动中...")
        
        # 初始化任务监控系统
        await initialize_task_monitoring()
        
        logger.info("应用启动完成")
        
    except Exception as e:
        logger.error(f"应用启动失败: {e}")
        raise


async def shutdown_event():
    """应用关闭事件"""
    try:
        logger.info("应用关闭中...")
        
        # 关闭任务监控系统
        await shutdown_task_monitoring()
        
        logger.info("应用关闭完成")
        
    except Exception as e:
        logger.error(f"应用关闭失败: {e}")
