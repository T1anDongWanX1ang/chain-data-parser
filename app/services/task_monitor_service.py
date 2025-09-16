"""任务监控服务"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
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
            
            # 查询超时的正在运行任务 - 使用心跳时间判断
            result = await session.execute(
                select(PipelineTask).where(
                    PipelineTask.status == 0,
                    # 优先使用心跳时间，如果没有心跳时间则使用创建时间
                    or_(
                        and_(PipelineTask.last_heartbeat.isnot(None), 
                             PipelineTask.last_heartbeat < timeout_time),
                        and_(PipelineTask.last_heartbeat.is_(None), 
                             PipelineTask.create_time < timeout_time)
                    )
                )
            )
            timeout_tasks = result.scalars().all()
            
            if timeout_tasks:
                logger.warning(f"发现 {len(timeout_tasks)} 个超时任务")
                
                for task in timeout_tasks:
                    if task.status == 0:  # 只有正在运行的任务才能标记为失败
                        task.status = 2  # 失败
                        # 记录更详细的超时信息
                        if task.last_heartbeat:
                            last_heartbeat_str = task.last_heartbeat.strftime('%Y-%m-%d %H:%M:%S')
                            logger.info(f"任务 {task.id} 超时失败 - 最后心跳时间: {last_heartbeat_str}, 超过 {timeout_minutes} 分钟无心跳")
                        else:
                            create_time_str = task.create_time.strftime('%Y-%m-%d %H:%M:%S') if task.create_time else 'N/A'
                            logger.info(f"任务 {task.id} 超时失败 - 创建时间: {create_time_str}, 超过 {timeout_minutes} 分钟无心跳")
                    else:
                        logger.warning(f"任务 {task.id} 状态已改变，跳过超时处理: 当前状态={task.status}")
                
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
    
    @classmethod
    async def update_task_heartbeat(cls, session: AsyncSession, task_id: int) -> bool:
        """更新任务心跳时间"""
        try:
            task = await session.get(PipelineTask, task_id)
            if not task:
                logger.warning(f"任务不存在，无法更新心跳: task_id={task_id}")
                return False
            
            if task.status != 0:  # 只更新正在运行的任务
                logger.warning(f"任务状态不是运行中，无法更新心跳: task_id={task_id}, status={task.status}")
                return False
            
            task.last_heartbeat = datetime.now()
            await session.commit()
            logger.debug(f"任务心跳已更新: task_id={task_id}")
            return True
            
        except Exception as e:
            logger.error(f"更新任务心跳失败: task_id={task_id}, 错误: {e}")
            await session.rollback()
            return False


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


class HeartbeatDaemon:
    """心跳守护线程"""
    
    def __init__(self, task_id: int, interval: int = 30):
        """
        初始化心跳守护线程
        
        Args:
            task_id: 任务ID
            interval: 心跳间隔（秒）
        """
        self.task_id = task_id
        self.interval = interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_heartbeat_time = 0
        self.heartbeat_count = 0
        
    async def start(self):
        """启动心跳守护线程"""
        if self.is_running:
            logger.warning(f"心跳守护线程已在运行: task_id={self.task_id}")
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._heartbeat_loop())
        logger.info(f"心跳守护线程已启动: task_id={self.task_id}, 间隔={self.interval}秒")
    
    async def stop(self):
        """停止心跳守护线程"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self._task and not self._task.done():
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"心跳守护线程已停止: task_id={self.task_id}, 总心跳次数={self.heartbeat_count}")
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self.is_running:
            try:
                await self._update_heartbeat()
                self.heartbeat_count += 1
                self.last_heartbeat_time = time.time()
                
                # 等待下次心跳
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                logger.info(f"心跳守护线程被取消: task_id={self.task_id}")
                break
            except Exception as e:
                logger.error(f"心跳守护线程异常: task_id={self.task_id}, 错误: {e}")
                # 异常时等待较短时间后重试
                await asyncio.sleep(5)
    
    async def _update_heartbeat(self):
        """更新心跳到数据库"""
        try:
            from app.services.database_service import database_service
            
            async with database_service.get_session() as session:
                success = await TaskMonitorService.update_task_heartbeat(session, self.task_id)
                if success:
                    logger.debug(f"心跳更新成功: task_id={self.task_id}")
                else:
                    logger.warning(f"心跳更新失败: task_id={self.task_id}")
                    
        except Exception as e:
            logger.error(f"心跳更新异常: task_id={self.task_id}, 错误: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """获取心跳状态"""
        return {
            "task_id": self.task_id,
            "is_running": self.is_running,
            "interval": self.interval,
            "last_heartbeat_time": self.last_heartbeat_time,
            "heartbeat_count": self.heartbeat_count,
            "time_since_last_heartbeat": time.time() - self.last_heartbeat_time if self.last_heartbeat_time > 0 else None
        }


class HeartbeatManager:
    """心跳管理器 - 管理所有任务的心跳守护线程"""
    
    def __init__(self):
        self.daemons: Dict[int, HeartbeatDaemon] = {}
    
    async def start_heartbeat(self, task_id: int, interval: int = 30):
        """启动任务的心跳守护线程"""
        if task_id in self.daemons:
            logger.warning(f"任务 {task_id} 的心跳守护线程已存在")
            return
        
        daemon = HeartbeatDaemon(task_id, interval)
        await daemon.start()
        self.daemons[task_id] = daemon
        logger.info(f"已启动任务 {task_id} 的心跳守护线程")
    
    async def stop_heartbeat(self, task_id: int):
        """停止任务的心跳守护线程"""
        if task_id in self.daemons:
            await self.daemons[task_id].stop()
            del self.daemons[task_id]
            logger.info(f"已停止任务 {task_id} 的心跳守护线程")
    
    async def stop_all_heartbeats(self):
        """停止所有心跳守护线程"""
        for task_id in list(self.daemons.keys()):
            await self.stop_heartbeat(task_id)
    
    def get_heartbeat_status(self, task_id: int) -> Optional[Dict[str, Any]]:
        """获取任务的心跳状态"""
        if task_id in self.daemons:
            return self.daemons[task_id].get_status()
        return None


# 全局监控守护进程实例
task_monitor_daemon = TaskMonitorDaemon()

# 全局心跳管理器实例
heartbeat_manager = HeartbeatManager()


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
        # 停止所有心跳守护线程
        await heartbeat_manager.stop_all_heartbeats()
        
        # 停止任务监控守护进程
        await task_monitor_daemon.stop_monitoring()
        logger.info("任务监控系统已关闭")
    except Exception as e:
        logger.error(f"任务监控系统关闭失败: {e}")
