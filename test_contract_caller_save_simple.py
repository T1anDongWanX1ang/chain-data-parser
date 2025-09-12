#!/usr/bin/env python3
"""
简化的contract_caller数据保存功能测试
主要测试数据库保存逻辑，不依赖真实的ABI和区块链调用
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
import sys

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.services.database_service import database_service
from app.models.evm_contract_caller import EvmContractCaller
from app.component.pipeline_executor import BlockchainDataPipeline
from loguru import logger


async def test_pipeline_save_logic():
    """测试pipeline中的数据保存逻辑（不执行真实的合约调用）"""
    logger.info("开始测试pipeline数据保存逻辑...")
    
    try:
        # 初始化数据库
        await database_service.init_db()
        
        # 创建pipeline实例
        mock_config = {
            "pipeline_name": "test_save_logic",
            "components": []
        }
        pipeline = BlockchainDataPipeline(config_dict=mock_config)
        
        # 模拟组件配置
        comp_config = {
            "name": "test_caller",
            "type": "contract_caller",
            "chain_name": "ethereum",
            "contract_address": "0x1234567890123456789012345678901234567890",
            "abi_path": "/test/path.json",
            "method_name": "testMethod",
            "event_name": "TestEvent"
        }
        
        # 模拟方法参数
        method_args = ["0xtest", 100, True]
        
        # 直接测试_save_contract_caller_record方法
        component_id = 99999
        logger.info(f"测试保存contract_caller记录...")
        await pipeline._save_contract_caller_record(component_id, comp_config, method_args)
        
        # 验证数据是否保存成功
        async with database_service.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(EvmContractCaller).where(EvmContractCaller.component_id == component_id)
            )
            saved_record = result.scalar_one_or_none()
            
            if saved_record:
                logger.info(f"✅ Pipeline数据保存成功!")
                logger.info(f"   记录ID: {saved_record.id}")
                logger.info(f"   组件ID: {saved_record.component_id}")
                logger.info(f"   事件名称: {saved_record.event_name}")
                logger.info(f"   链名称: {saved_record.chain_name}")
                logger.info(f"   合约地址: {saved_record.contract_address}")
                logger.info(f"   方法名称: {saved_record.method_name}")
                logger.info(f"   方法参数: {saved_record.method_params}")
                logger.info(f"   ABI路径: {saved_record.abi_path}")
                logger.info(f"   创建时间: {saved_record.create_time}")
                
                # 验证参数是否正确序列化
                if saved_record.method_params:
                    parsed_params = json.loads(saved_record.method_params)
                    logger.info(f"   解析后的参数: {parsed_params}")
                    if parsed_params == method_args:
                        logger.info("   ✅ 参数序列化/反序列化正确")
                    else:
                        logger.warning("   ⚠️ 参数序列化/反序列化不匹配")
                
                return True
            else:
                logger.error("❌ 数据保存失败: 未找到保存的记录")
                return False
                
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_records():
    """测试保存多条记录"""
    logger.info("开始测试保存多条记录...")
    
    try:
        # 初始化数据库
        await database_service.init_db()
        
        # 创建pipeline实例
        mock_config = {"pipeline_name": "test_multiple_records", "components": []}
        pipeline = BlockchainDataPipeline(config_dict=mock_config)
        
        # 保存多条记录
        test_configs = [
            {
                "name": "caller1",
                "chain_name": "ethereum",
                "contract_address": "0xAAA",
                "method_name": "method1",
                "abi_path": "/path1.json"
            },
            {
                "name": "caller2", 
                "chain_name": "bsc",
                "contract_address": "0xBBB",
                "method_name": "method2",
                "abi_path": "/path2.json"
            },
            {
                "name": "caller3",
                "chain_name": "polygon", 
                "contract_address": "0xCCC",
                "method_name": "method3",
                "abi_path": "/path3.json"
            }
        ]
        
        saved_component_ids = []
        for i, config in enumerate(test_configs):
            component_id = 88800 + i
            method_args = [f"arg{i}", i * 100]
            await pipeline._save_contract_caller_record(component_id, config, method_args)
            saved_component_ids.append(component_id)
        
        # 验证所有记录
        async with database_service.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(EvmContractCaller).where(
                    EvmContractCaller.component_id.in_(saved_component_ids)
                )
            )
            saved_records = result.scalars().all()
            
            if len(saved_records) == len(test_configs):
                logger.info(f"✅ 多条记录保存成功! 保存了{len(saved_records)}条记录")
                for record in saved_records:
                    logger.info(f"   记录: ID={record.id}, 组件ID={record.component_id}, 链={record.chain_name}, 方法={record.method_name}")
                return True
            else:
                logger.error(f"❌ 多条记录保存失败: 期望{len(test_configs)}条，实际{len(saved_records)}条")
                return False
                
    except Exception as e:
        logger.error(f"❌ 多条记录测试失败: {e}")
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("简化的contract_caller数据保存功能测试")
    logger.info("=" * 60)
    
    # 测试1: 基本保存逻辑
    logger.info("\n🔵 测试1: Pipeline保存逻辑")
    test1_result = await test_pipeline_save_logic()
    
    # 测试2: 多条记录保存
    logger.info("\n🔵 测试2: 多条记录保存")
    test2_result = await test_multiple_records()
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总:")
    logger.info(f"  Pipeline保存逻辑: {'✅ 通过' if test1_result else '❌ 失败'}")
    logger.info(f"  多条记录保存: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        logger.info("🎉 所有测试通过！Contract caller数据保存功能正常工作")
        logger.info("📝 step2的内部数据现在会自动保存到evm_contract_caller表中，可以保存多条记录")
    else:
        logger.error("💥 部分测试失败")
    
    # 清理
    await database_service.close()


if __name__ == "__main__":
    asyncio.run(main())