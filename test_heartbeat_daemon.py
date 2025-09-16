#!/usr/bin/env python3
"""
心跳守护线程测试脚本
测试心跳守护线程的启动、运行和停止功能
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
from app.services.task_monitor_service import HeartbeatDaemon, HeartbeatManager, TaskMonitorService
from app.models.pipeline_task import PipelineTask
from app.models.pipeline import Pipeline
from sqlalchemy import select
from loguru import logger


async def test_heartbeat_daemon():
    """测试心跳守护线程"""
    logger.info("开始测试心跳守护线程...")
    
    try:
        # 初始化数据库
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            # 1. 创建测试任务
            logger.info("1. 创建测试任务...")
            
            # 先创建一个测试管道
            test_pipeline = Pipeline(
                name="心跳守护线程测试管道",
                description="用于测试心跳守护线程的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            # 创建测试任务
            test_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_heartbeat_daemon.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"测试任务已创建: task_id={test_task.id}")
            
            # 2. 测试心跳守护线程
            logger.info("2. 测试心跳守护线程...")
            
            # 创建心跳守护线程（使用较短的间隔进行测试）
            daemon = HeartbeatDaemon(task_id=test_task.id, interval=5)  # 5秒间隔
            
            # 启动守护线程
            await daemon.start()
            logger.info("心跳守护线程已启动")
            
            # 等待一段时间，观察心跳更新
            logger.info("等待心跳更新...")
            await asyncio.sleep(15)  # 等待15秒，应该会有3次心跳更新
            
            # 检查心跳状态
            status = daemon.get_status()
            logger.info(f"心跳状态: {status}")
            
            assert status['is_running'], "心跳守护线程应该正在运行"
            assert status['heartbeat_count'] >= 2, f"应该有至少2次心跳更新，实际: {status['heartbeat_count']}"
            
            # 检查数据库中的心跳时间
            await session.refresh(test_task)
            assert test_task.last_heartbeat is not None, "数据库中的心跳时间应该已更新"
            
            logger.info(f"数据库心跳时间: {test_task.last_heartbeat}")
            
            # 停止守护线程
            await daemon.stop()
            logger.info("心跳守护线程已停止")
            
            # 验证停止状态
            status = daemon.get_status()
            assert not status['is_running'], "心跳守护线程应该已停止"
            
            logger.info("心跳守护线程测试通过")
            
            # 3. 测试心跳管理器
            logger.info("3. 测试心跳管理器...")
            
            manager = HeartbeatManager()
            
            # 启动多个任务的心跳
            task_ids = [test_task.id, test_task.id + 1, test_task.id + 2]
            for task_id in task_ids:
                await manager.start_heartbeat(task_id, interval=3)
            
            # 等待一段时间
            await asyncio.sleep(10)
            
            # 检查所有心跳状态
            for task_id in task_ids:
                status = manager.get_heartbeat_status(task_id)
                if status:
                    logger.info(f"任务 {task_id} 心跳状态: {status}")
                    assert status['is_running'], f"任务 {task_id} 的心跳应该正在运行"
            
            # 停止所有心跳
            await manager.stop_all_heartbeats()
            logger.info("所有心跳守护线程已停止")
            
            # 验证所有心跳都已停止
            for task_id in task_ids:
                status = manager.get_heartbeat_status(task_id)
                assert status is None, f"任务 {task_id} 的心跳应该已停止"
            
            logger.info("心跳管理器测试通过")
            
            # 4. 测试超时检测
            logger.info("4. 测试超时检测...")
            
            # 创建一个无心跳的任务（模拟超时）
            timeout_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_timeout.log"
            )
            session.add(timeout_task)
            await session.commit()
            
            # 使用很短的超时时间测试
            await TaskMonitorService.check_timeout_tasks(session, timeout_minutes=0.01)  # 0.6秒
            
            # 检查任务状态
            await session.refresh(timeout_task)
            assert timeout_task.status == 2, "无心跳的任务应该被标记为失败"
            
            logger.info("超时检测测试通过")
            
            # 清理测试数据
            logger.info("5. 清理测试数据...")
            
            await session.delete(test_task)
            await session.delete(timeout_task)
            await session.delete(test_pipeline)
            await session.commit()
            
            logger.info("测试数据已清理")
            
        logger.info("✅ 心跳守护线程测试完成，所有测试通过！")
        
    except Exception as e:
        logger.error(f"❌ 心跳守护线程测试失败: {e}")
        raise
    finally:
        await database_service.close()


async def test_heartbeat_with_long_running_task():
    """测试长期运行任务的心跳守护线程"""
    logger.info("开始测试长期运行任务的心跳守护线程...")
    
    try:
        async with database_service.get_session() as session:
            # 创建测试管道和任务
            test_pipeline = Pipeline(
                name="长期运行心跳测试管道",
                description="用于测试长期运行任务心跳守护线程的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            test_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_long_running_heartbeat.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"长期运行测试任务已创建: task_id={test_task.id}")
            
            # 启动心跳守护线程
            manager = HeartbeatManager()
            await manager.start_heartbeat(test_task.id, interval=5)  # 5秒间隔
            
            # 模拟长期运行任务
            logger.info("模拟长期运行任务...")
            for i in range(6):  # 运行30秒
                logger.info(f"任务运行中... {i+1}/6")
                await asyncio.sleep(5)
                
                # 检查心跳状态
                status = manager.get_heartbeat_status(test_task.id)
                if status:
                    logger.info(f"心跳状态: 运行中={status['is_running']}, 心跳次数={status['heartbeat_count']}")
            
            # 停止心跳守护线程
            await manager.stop_heartbeat(test_task.id)
            
            # 检查最终状态
            final_status = manager.get_heartbeat_status(test_task.id)
            assert final_status is None, "心跳守护线程应该已停止"
            
            # 检查数据库中的心跳时间
            await session.refresh(test_task)
            assert test_task.last_heartbeat is not None, "应该有最后心跳时间"
            
            logger.info(f"长期运行任务心跳正常: 最后心跳时间={test_task.last_heartbeat}")
            
            # 清理测试数据
            await session.delete(test_task)
            await session.delete(test_pipeline)
            await session.commit()
            
        logger.info("✅ 长期运行任务心跳守护线程测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 长期运行任务心跳守护线程测试失败: {e}")
        raise


async def main():
    """主函数"""
    logger.info("🚀 开始心跳守护线程综合测试")
    
    try:
        # 测试基本心跳守护线程功能
        await test_heartbeat_daemon()
        
        # 测试长期运行任务的心跳守护线程
        await test_heartbeat_with_long_running_task()
        
        logger.info("🎉 所有心跳守护线程测试通过！")
        
    except Exception as e:
        logger.error(f"💥 测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
