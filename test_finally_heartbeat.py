#!/usr/bin/env python3
"""
测试finally块的心跳停止功能
验证任务成功、失败、异常时心跳守护线程都能正确停止
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.services.database_service import database_service
from app.services.task_monitor_service import HeartbeatManager
from app.models.pipeline_task import PipelineTask
from app.models.pipeline import Pipeline
from sqlalchemy import select
from loguru import logger


async def test_finally_heartbeat_success():
    """测试任务成功时的心跳停止"""
    logger.info("开始测试任务成功时的心跳停止...")
    
    try:
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            # 创建测试任务
            test_pipeline = Pipeline(
                name="成功任务测试管道",
                description="用于测试任务成功时心跳停止的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            test_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_success_heartbeat.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"测试任务已创建: task_id={test_task.id}")
            
            # 模拟任务执行过程
            heartbeat_started = False
            manager = HeartbeatManager()
            
            try:
                # 启动心跳守护线程
                await manager.start_heartbeat(test_task.id, interval=2)
                heartbeat_started = True
                logger.info("心跳守护线程已启动")
                
                # 模拟任务执行
                logger.info("模拟任务执行...")
                await asyncio.sleep(5)  # 模拟任务运行5秒
                
                # 模拟任务成功完成
                test_task.status = 1  # 成功
                await session.commit()
                logger.info("任务执行成功")
                
            except Exception as e:
                logger.error(f"任务执行异常: {e}")
                test_task.status = 2  # 失败
                await session.commit()
                
            finally:
                # 确保心跳守护线程总是被停止
                if heartbeat_started:
                    try:
                        await manager.stop_heartbeat(test_task.id)
                        logger.info("心跳守护线程已停止")
                    except Exception as heartbeat_error:
                        logger.error(f"停止心跳守护线程失败: {heartbeat_error}")
            
            # 验证心跳守护线程已停止
            status = manager.get_heartbeat_status(test_task.id)
            assert status is None, "心跳守护线程应该已停止"
            
            logger.info("✅ 任务成功时心跳停止测试通过")
            
            # 清理测试数据
            await session.delete(test_task)
            await session.delete(test_pipeline)
            await session.commit()
            
    except Exception as e:
        logger.error(f"❌ 任务成功时心跳停止测试失败: {e}")
        raise
    finally:
        await database_service.close()


async def test_finally_heartbeat_failure():
    """测试任务失败时的心跳停止"""
    logger.info("开始测试任务失败时的心跳停止...")
    
    try:
        async with database_service.get_session() as session:
            # 创建测试任务
            test_pipeline = Pipeline(
                name="失败任务测试管道",
                description="用于测试任务失败时心跳停止的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            test_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_failure_heartbeat.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"测试任务已创建: task_id={test_task.id}")
            
            # 模拟任务执行过程
            heartbeat_started = False
            manager = HeartbeatManager()
            
            try:
                # 启动心跳守护线程
                await manager.start_heartbeat(test_task.id, interval=2)
                heartbeat_started = True
                logger.info("心跳守护线程已启动")
                
                # 模拟任务执行
                logger.info("模拟任务执行...")
                await asyncio.sleep(3)  # 模拟任务运行3秒
                
                # 模拟任务失败
                raise Exception("模拟任务失败")
                
            except Exception as e:
                logger.error(f"任务执行失败: {e}")
                test_task.status = 2  # 失败
                await session.commit()
                
            finally:
                # 确保心跳守护线程总是被停止
                if heartbeat_started:
                    try:
                        await manager.stop_heartbeat(test_task.id)
                        logger.info("心跳守护线程已停止")
                    except Exception as heartbeat_error:
                        logger.error(f"停止心跳守护线程失败: {heartbeat_error}")
            
            # 验证心跳守护线程已停止
            status = manager.get_heartbeat_status(test_task.id)
            assert status is None, "心跳守护线程应该已停止"
            
            logger.info("✅ 任务失败时心跳停止测试通过")
            
            # 清理测试数据
            await session.delete(test_task)
            await session.delete(test_pipeline)
            await session.commit()
            
    except Exception as e:
        logger.error(f"❌ 任务失败时心跳停止测试失败: {e}")
        raise


async def test_finally_heartbeat_exception():
    """测试任务异常时的心跳停止"""
    logger.info("开始测试任务异常时的心跳停止...")
    
    try:
        async with database_service.get_session() as session:
            # 创建测试任务
            test_pipeline = Pipeline(
                name="异常任务测试管道",
                description="用于测试任务异常时心跳停止的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            test_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_exception_heartbeat.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"测试任务已创建: task_id={test_task.id}")
            
            # 模拟任务执行过程
            heartbeat_started = False
            manager = HeartbeatManager()
            
            try:
                # 启动心跳守护线程
                await manager.start_heartbeat(test_task.id, interval=2)
                heartbeat_started = True
                logger.info("心跳守护线程已启动")
                
                # 模拟任务执行
                logger.info("模拟任务执行...")
                await asyncio.sleep(2)  # 模拟任务运行2秒
                
                # 模拟严重异常
                raise RuntimeError("模拟严重异常")
                
            except Exception as e:
                logger.error(f"任务执行异常: {e}")
                test_task.status = 2  # 失败
                await session.commit()
                
            finally:
                # 确保心跳守护线程总是被停止
                if heartbeat_started:
                    try:
                        await manager.stop_heartbeat(test_task.id)
                        logger.info("心跳守护线程已停止")
                    except Exception as heartbeat_error:
                        logger.error(f"停止心跳守护线程失败: {heartbeat_error}")
            
            # 验证心跳守护线程已停止
            status = manager.get_heartbeat_status(test_task.id)
            assert status is None, "心跳守护线程应该已停止"
            
            logger.info("✅ 任务异常时心跳停止测试通过")
            
            # 清理测试数据
            await session.delete(test_task)
            await session.delete(test_pipeline)
            await session.commit()
            
    except Exception as e:
        logger.error(f"❌ 任务异常时心跳停止测试失败: {e}")
        raise


async def test_multiple_tasks_finally():
    """测试多个任务的心跳停止"""
    logger.info("开始测试多个任务的心跳停止...")
    
    try:
        async with database_service.get_session() as session:
            # 创建测试管道
            test_pipeline = Pipeline(
                name="多任务测试管道",
                description="用于测试多个任务心跳停止的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            # 创建多个测试任务
            task_ids = []
            for i in range(3):
                test_task = PipelineTask(
                    pipeline_id=test_pipeline.id,
                    create_time=datetime.now(),
                    status=0,  # 正在运行
                    log_path=f"/tmp/test_multi_heartbeat_{i}.log"
                )
                session.add(test_task)
                task_ids.append(test_task.id)
            
            await session.commit()
            logger.info(f"创建了 {len(task_ids)} 个测试任务: {task_ids}")
            
            # 模拟多个任务执行
            manager = HeartbeatManager()
            started_tasks = []
            
            try:
                # 启动多个心跳守护线程
                for task_id in task_ids:
                    await manager.start_heartbeat(task_id, interval=1)
                    started_tasks.append(task_id)
                    logger.info(f"任务 {task_id} 的心跳守护线程已启动")
                
                # 模拟任务执行
                logger.info("模拟多个任务执行...")
                await asyncio.sleep(3)  # 模拟任务运行3秒
                
                # 模拟部分任务成功，部分失败
                for i, task_id in enumerate(task_ids):
                    task = await session.get(PipelineTask, task_id)
                    if task:
                        task.status = 1 if i % 2 == 0 else 2  # 交替成功/失败
                        await session.commit()
                
                logger.info("多个任务执行完成")
                
            except Exception as e:
                logger.error(f"多个任务执行异常: {e}")
                # 标记所有任务为失败
                for task_id in task_ids:
                    task = await session.get(PipelineTask, task_id)
                    if task:
                        task.status = 2
                        await session.commit()
                
            finally:
                # 确保所有心跳守护线程都被停止
                for task_id in started_tasks:
                    try:
                        await manager.stop_heartbeat(task_id)
                        logger.info(f"任务 {task_id} 的心跳守护线程已停止")
                    except Exception as heartbeat_error:
                        logger.error(f"停止任务 {task_id} 的心跳守护线程失败: {heartbeat_error}")
            
            # 验证所有心跳守护线程都已停止
            for task_id in task_ids:
                status = manager.get_heartbeat_status(task_id)
                assert status is None, f"任务 {task_id} 的心跳守护线程应该已停止"
            
            logger.info("✅ 多个任务心跳停止测试通过")
            
            # 清理测试数据
            for task_id in task_ids:
                task = await session.get(PipelineTask, task_id)
                if task:
                    await session.delete(task)
            await session.delete(test_pipeline)
            await session.commit()
            
    except Exception as e:
        logger.error(f"❌ 多个任务心跳停止测试失败: {e}")
        raise


async def main():
    """主函数"""
    logger.info("🚀 开始finally块心跳停止综合测试")
    
    try:
        # 测试任务成功时的心跳停止
        await test_finally_heartbeat_success()
        
        # 测试任务失败时的心跳停止
        await test_finally_heartbeat_failure()
        
        # 测试任务异常时的心跳停止
        await test_finally_heartbeat_exception()
        
        # 测试多个任务的心跳停止
        await test_multiple_tasks_finally()
        
        logger.info("🎉 所有finally块心跳停止测试通过！")
        
    except Exception as e:
        logger.error(f"💥 测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
