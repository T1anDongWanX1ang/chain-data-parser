#!/usr/bin/env python3
"""
测试contract_caller组件数据保存功能
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


async def test_database_save():
    """测试直接数据库保存功能"""
    logger.info("开始测试数据库保存功能...")
    
    try:
        # 初始化数据库
        await database_service.init_db()
        
        # 测试数据
        test_record = EvmContractCaller(
            component_id=12345,
            event_name="test_event",
            chain_name="ethereum",
            abi_path="/path/to/test.abi",
            contract_address="0x1234567890123456789012345678901234567890",
            method_name="test_method",
            method_params='["param1", "param2"]',
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        
        async with database_service.get_session() as session:
            session.add(test_record)
            await session.commit()
            
            # 查询验证
            from sqlalchemy import select
            result = await session.execute(
                select(EvmContractCaller).where(EvmContractCaller.component_id == 12345)
            )
            saved_record = result.scalar_one_or_none()
            
            if saved_record:
                logger.info(f"✅ 数据保存成功: {saved_record}")
                logger.info(f"   记录ID: {saved_record.id}")
                logger.info(f"   组件ID: {saved_record.component_id}")
                logger.info(f"   事件名称: {saved_record.event_name}")
                logger.info(f"   合约地址: {saved_record.contract_address}")
                logger.info(f"   方法名称: {saved_record.method_name}")
                return True
            else:
                logger.error("❌ 数据保存失败: 未找到保存的记录")
                return False
                
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
        return False


async def test_pipeline_with_mock_config():
    """测试pipeline中的数据保存功能"""
    logger.info("开始测试pipeline数据保存功能...")
    
    # 创建模拟配置
    mock_config = {
        "pipeline_name": "test_contract_caller_save",
        "components": [
            {
                "name": "event_monitor",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0xA0b86a33E6441ad15d1b5b64E7c3c5b8B1d5C38D",
                "abi_path": "abis/test.json",
                "events_to_monitor": ["Transfer"],
                "mode": "realtime"
            },
            {
                "name": "balance_checker",
                "type": "contract_caller",
                "chain_name": "ethereum",
                "contract_address": "0xA0b86a33E6441ad15d1b5b64E7c3c5b8B1d5C38D",
                "abi_path": "abis/test.json",
                "method_name": "balanceOf",
                "method_params": ["args.to"]
            }
        ]
    }
    
    try:
        # 初始化数据库
        await database_service.init_db()
        
        # 创建pipeline
        pipeline = BlockchainDataPipeline(config_dict=mock_config)
        
        # 模拟处理数据（不需要真实的区块链数据）
        mock_event_data = {
            "event": "Transfer",
            "args": {
                "from": "0x1234567890123456789012345678901234567890",
                "to": "0x9876543210987654321098765432109876543210",
                "value": "1000000000000000000"
            },
            "blockNumber": 18500000,
            "transactionHash": "0xabcdef1234567890"
        }
        
        # 测试_process_data方法（这会保存contract_caller数据）
        logger.info("处理模拟事件数据...")
        processed_data = await pipeline._process_data(mock_event_data)
        
        logger.info(f"处理完成，结果: {processed_data}")
        
        # 验证数据是否保存到数据库
        component_id = hash("balance_checker") % (10**8)
        async with database_service.get_session() as session:
            from sqlalchemy import select
            result = await session.execute(
                select(EvmContractCaller).where(EvmContractCaller.component_id == component_id)
            )
            saved_records = result.scalars().all()
            
            if saved_records:
                logger.info(f"✅ Pipeline数据保存成功，共找到 {len(saved_records)} 条记录")
                for record in saved_records:
                    logger.info(f"   记录: 组件ID={record.component_id}, 事件={record.event_name}, 方法={record.method_name}")
                return True
            else:
                logger.warning("⚠️ 未找到pipeline保存的记录（可能是正常的，如果contract_caller执行失败）")
                return False
                
    except Exception as e:
        logger.error(f"❌ Pipeline测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("开始测试contract_caller数据保存功能")
    logger.info("=" * 60)
    
    # 测试1: 直接数据库保存
    logger.info("\n🔵 测试1: 直接数据库保存")
    test1_result = await test_database_save()
    
    # 测试2: Pipeline中的数据保存
    logger.info("\n🔵 测试2: Pipeline中的数据保存")
    test2_result = await test_pipeline_with_mock_config()
    
    # 汇总结果
    logger.info("\n" + "=" * 60)
    logger.info("测试结果汇总:")
    logger.info(f"  直接数据库保存: {'✅ 通过' if test1_result else '❌ 失败'}")
    logger.info(f"  Pipeline数据保存: {'✅ 通过' if test2_result else '❌ 失败'}")
    
    if test1_result and test2_result:
        logger.info("🎉 所有测试通过！数据保存功能正常工作")
    else:
        logger.error("💥 部分测试失败，请检查实现")
    
    # 清理
    await database_service.close()


if __name__ == "__main__":
    asyncio.run(main())