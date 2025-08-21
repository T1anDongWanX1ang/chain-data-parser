"""任务监控服务"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from loguru import logger

from app.models.pipeline_task import PipelineTask


class TaskMonitorService:
    """任务监控服务"""
    
    @classmethod
    async def reset_running_tasks_on_startup(cls, session: AsyncSession):
        """应用启动时重置所有正在运行的任务状态"""
        try:
            # 查询所有正在运行的任务
            result = await session.execute(
                select(PipelineTask).where(PipelineTask.status == 0)
            )
            running_tasks = result.scalars().all()
            
            if running_tasks:
                logger.warning(f"发现 {len(running_tasks)} 个异常中断的任务，将标记为失败")
                
                # 将所有正在运行的任务标记为失败
                for task in running_tasks:
                    task.status = 2  # 失败
                    logger.info(f"任务 {task.id} (pipeline_id: {task.pipeline_id}) 标记为失败 - 程序重启导致")
                
                await session.commit()
                logger.info(f"已重置 {len(running_tasks)} 个异常任务状态")
            else:
                logger.info("未发现异常中断的任务")
                
        except Exception as e:
            logger.error(f"重置任务状态失败: {e}")
            await session.rollback()
    
    @classmethod
    async def check_timeout_tasks(cls, session: AsyncSession, timeout_minutes: int = 60):
        """检查超时任务并标记为失败"""
        try:
            timeout_time = datetime.now() - timedelta(minutes=timeout_minutes)
            
            # 查询超时的正在运行任务
            result = await session.execute(
                select(PipelineTask).where(
                    PipelineTask.status == 0,
                    PipelineTask.create_time < timeout_time
                )
            )
            timeout_tasks = result.scalars().all()
            
            if timeout_tasks:
                logger.warning(f"发现 {len(timeout_tasks)} 个超时任务")
                
                for task in timeout_tasks:
                    task.status = 2  # 失败
                    logger.info(f"任务 {task.id} 超时失败 - 运行时间超过 {timeout_minutes} 分钟")
                
                await session.commit()
                logger.info(f"已标记 {len(timeout_tasks)} 个超时任务为失败")
            
        except Exception as e:
            logger.error(f"检查超时任务失败: {e}")
            await session.rollback()
    
    @classmethod
    async def get_task_statistics(cls, session: AsyncSession) -> Dict[str, Any]:
        """获取任务统计信息"""
        try:
            # 查询各状态任务数量
            running_count = await session.scalar(
                select(PipelineTask).where(PipelineTask.status == 0).count()
            )
            success_count = await session.scalar(
                select(PipelineTask).where(PipelineTask.status == 1).count()
            )
            failed_count = await session.scalar(
                select(PipelineTask).where(PipelineTask.status == 2).count()
            )
            
            # 查询最近24小时的任务
            recent_time = datetime.now() - timedelta(hours=24)
            recent_tasks = await session.execute(
                select(PipelineTask).where(PipelineTask.create_time >= recent_time)
            )
            recent_count = len(recent_tasks.scalars().all())
            
            return {
                "total_tasks": running_count + success_count + failed_count,
                "running_tasks": running_count,
                "success_tasks": success_count,
                "failed_tasks": failed_count,
                "recent_24h_tasks": recent_count,
                "last_check_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取任务统计失败: {e}")
            return {"error": str(e)}


class TaskMonitorDaemon:
    """任务监控守护进程"""
    
    def __init__(self, check_interval: int = 300, timeout_minutes: int = 60):
        """
        初始化监控守护进程
        
        Args:
            check_interval: 检查间隔（秒），默认5分钟
            timeout_minutes: 任务超时时间（分钟），默认60分钟
        """
        self.check_interval = check_interval
        self.timeout_minutes = timeout_minutes
        self.running = False
        self._task = None
    
    async def start_monitoring(self):
        """启动监控"""
        if self.running:
            logger.warning("任务监控守护进程已在运行")
            return
            
        self.running = True
        logger.info(f"任务监控守护进程启动 - 检查间隔: {self.check_interval}秒, 超时时间: {self.timeout_minutes}分钟")
        
        self._task = asyncio.create_task(self._monitor_loop())
    
    async def _monitor_loop(self):
        """监控循环"""
        while self.running:
            try:
                from app.services.database_service import database_service
                
                async with database_service.get_session() as session:
                    await TaskMonitorService.check_timeout_tasks(session, self.timeout_minutes)
                
                # 等待下次检查
                await asyncio.sleep(self.check_interval)
                
            except asyncio.CancelledError:
                logger.info("任务监控守护进程被取消")
                break
            except Exception as e:
                logger.error(f"任务监控守护进程错误: {e}")
                await asyncio.sleep(60)  # 出错后等待1分钟再继续
    
    async def stop_monitoring(self):
        """停止监控"""
        if not self.running:
            return
            
        self.running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("任务监控守护进程已停止")
    
    def is_running(self) -> bool:
        """检查是否正在运行"""
        return self.running and self._task and not self._task.done()


# 全局监控守护进程实例
task_monitor_daemon = TaskMonitorDaemon()


# 应用启动时调用的函数
async def initialize_task_monitoring():
    """初始化任务监控"""
    try:
        from app.services.database_service import database_service
        
        # 重置异常任务状态
        async with database_service.get_session() as session:
            await TaskMonitorService.reset_running_tasks_on_startup(session)
        
        # 启动监控守护进程
        await task_monitor_daemon.start_monitoring()
        
        logger.info("任务监控系统初始化完成")
        
    except Exception as e:
        logger.error(f"任务监控系统初始化失败: {e}")


# 应用关闭时调用的函数
async def shutdown_task_monitoring():
    """关闭任务监控"""
    try:
        await task_monitor_daemon.stop_monitoring()
        logger.info("任务监控系统已关闭")
    except Exception as e:
        logger.error(f"任务监控系统关闭失败: {e}")
