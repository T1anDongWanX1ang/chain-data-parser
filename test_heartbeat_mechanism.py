#!/usr/bin/env python3
"""
心跳机制测试脚本
测试任务监控系统的心跳更新和超时检测功能
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.services.database_service import database_service
from app.services.task_monitor_service import TaskMonitorService
from app.models.pipeline_task import PipelineTask
from app.models.pipeline import Pipeline
from sqlalchemy import select
from loguru import logger


async def test_heartbeat_mechanism():
    """测试心跳机制"""
    logger.info("开始测试心跳机制...")
    
    try:
        # 初始化数据库
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            # 1. 创建一个测试任务
            logger.info("1. 创建测试任务...")
            
            # 先创建一个测试管道
            test_pipeline = Pipeline(
                name="心跳测试管道",
                description="用于测试心跳机制的管道",
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
                log_path="/tmp/test_heartbeat.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"测试任务已创建: task_id={test_task.id}")
            
            # 2. 测试心跳更新
            logger.info("2. 测试心跳更新...")
            
            # 初始心跳时间应该为None
            assert test_task.last_heartbeat is None, "初始心跳时间应该为None"
            
            # 更新心跳
            success = await TaskMonitorService.update_task_heartbeat(session, test_task.id)
            assert success, "心跳更新应该成功"
            
            # 重新查询任务
            await session.refresh(test_task)
            assert test_task.last_heartbeat is not None, "心跳时间应该已更新"
            
            logger.info(f"心跳更新成功: {test_task.last_heartbeat}")
            
            # 3. 测试超时检测（使用很短的超时时间）
            logger.info("3. 测试超时检测...")
            
            # 等待1秒
            await asyncio.sleep(1)
            
            # 使用1秒超时时间检测
            await TaskMonitorService.check_timeout_tasks(session, timeout_minutes=0.01)  # 0.6秒
            
            # 重新查询任务状态
            await session.refresh(test_task)
            assert test_task.status == 0, "任务状态应该仍然是运行中（有心跳）"
            
            logger.info("超时检测正确：有心跳的任务未被标记为超时")
            
            # 4. 测试无心跳任务的超时检测
            logger.info("4. 测试无心跳任务的超时检测...")
            
            # 创建另一个任务，不更新心跳
            test_task2 = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now() - timedelta(minutes=2),  # 2分钟前创建
                status=0,  # 正在运行
                log_path="/tmp/test_heartbeat2.log"
            )
            session.add(test_task2)
            await session.commit()
            
            logger.info(f"无心跳测试任务已创建: task_id={test_task2.id}")
            
            # 使用1分钟超时时间检测
            await TaskMonitorService.check_timeout_tasks(session, timeout_minutes=1)
            
            # 重新查询任务状态
            await session.refresh(test_task2)
            assert test_task2.status == 2, "无心跳的任务应该被标记为失败"
            
            logger.info("超时检测正确：无心跳的任务被标记为超时失败")
            
            # 5. 测试任务统计
            logger.info("5. 测试任务统计...")
            
            stats = await TaskMonitorService.get_task_statistics(session)
            logger.info(f"任务统计: {stats}")
            
            assert stats['running_tasks'] >= 1, "应该有正在运行的任务"
            assert stats['failed_tasks'] >= 1, "应该有失败的任务"
            
            logger.info("任务统计功能正常")
            
            # 清理测试数据
            logger.info("6. 清理测试数据...")
            
            await session.delete(test_task)
            await session.delete(test_task2)
            await session.delete(test_pipeline)
            await session.commit()
            
            logger.info("测试数据已清理")
            
        logger.info("✅ 心跳机制测试完成，所有测试通过！")
        
    except Exception as e:
        logger.error(f"❌ 心跳机制测试失败: {e}")
        raise
    finally:
        await database_service.close()


async def test_heartbeat_with_long_running_task():
    """测试长期运行任务的心跳机制"""
    logger.info("开始测试长期运行任务的心跳机制...")
    
    try:
        async with database_service.get_session() as session:
            # 创建测试管道和任务
            test_pipeline = Pipeline(
                name="长期运行测试管道",
                description="用于测试长期运行任务心跳机制的管道",
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            session.add(test_pipeline)
            await session.commit()
            
            test_task = PipelineTask(
                pipeline_id=test_pipeline.id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path="/tmp/test_long_running.log"
            )
            session.add(test_task)
            await session.commit()
            
            logger.info(f"长期运行测试任务已创建: task_id={test_task.id}")
            
            # 模拟长期运行任务的心跳更新
            for i in range(5):  # 模拟5次心跳更新
                logger.info(f"模拟心跳更新 {i+1}/5...")
                
                success = await TaskMonitorService.update_task_heartbeat(session, test_task.id)
                assert success, f"第{i+1}次心跳更新应该成功"
                
                # 等待一段时间
                await asyncio.sleep(2)
            
            # 检查任务状态
            await session.refresh(test_task)
            assert test_task.status == 0, "长期运行的任务应该仍然是运行状态"
            assert test_task.last_heartbeat is not None, "应该有最后心跳时间"
            
            logger.info(f"长期运行任务心跳正常: 最后心跳时间={test_task.last_heartbeat}")
            
            # 清理测试数据
            await session.delete(test_task)
            await session.delete(test_pipeline)
            await session.commit()
            
        logger.info("✅ 长期运行任务心跳机制测试完成！")
        
    except Exception as e:
        logger.error(f"❌ 长期运行任务心跳机制测试失败: {e}")
        raise


async def main():
    """主函数"""
    logger.info("🚀 开始心跳机制综合测试")
    
    try:
        # 测试基本心跳机制
        await test_heartbeat_mechanism()
        
        # 测试长期运行任务的心跳机制
        await test_heartbeat_with_long_running_task()
        
        logger.info("🎉 所有心跳机制测试通过！")
        
    except Exception as e:
        logger.error(f"💥 测试失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
