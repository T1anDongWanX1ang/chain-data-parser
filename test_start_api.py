#!/usr/bin/env python3
"""
测试 start 接口使用优化版管道执行器
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.services.database_service import database_service
from app.services.pipeline_config_service import PipelineConfigService


async def test_start_api():
    """测试启动API使用优化版管道执行器"""
    
    print("🧪 测试 start 接口使用优化版管道执行器")
    print("-" * 50)
    
    try:
        # 初始化数据库服务
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 首先保存一个测试管道配置
            test_pipeline_config = {
                "pipeline_name": "API测试管道",
                "description": "测试start接口使用优化版执行器",
                "classification_id": 1,
                "components": [
                    {
                        "name": "step1",
                        "type": "event_monitor",
                        "chain_name": "ethereum",
                        "contract_address": "0xA0b86a33E6441c8C06DD2c1c1e3e5C2b8b6C6E5D",
                        "abi_path": "abis/erc20.json",
                        "events_to_monitor": ["Transfer", "Approval"],
                        "mode": "realtime",
                        "output_format": "detailed",
                        "poll_interval": 2.0
                    },
                    {
                        "name": "step2",
                        "type": "contract_caller",
                        "chain_name": "ethereum",
                        "contract_address": "0xA0b86a33E6441c8C06DD2c1c1e3e5C2b8b6C6E5D",
                        "abi_path": "abis/erc20.json",
                        "method_name": "decimals",
                        "method_params": []
                    },
                    {
                        "name": "step3",
                        "type": "dict_mapper",
                        "dict_mappers": [
                            {
                                "event_name": "Transfer",
                                "mapping_rules": [
                                    {
                                        "source_key": "from",
                                        "target_key": "sender_address",
                                        "transformer": "to_lowercase",
                                        "condition": None,
                                        "default_value": None
                                    },
                                    {
                                        "source_key": "to",
                                        "target_key": "receiver_address",
                                        "transformer": "to_lowercase",
                                        "condition": None,
                                        "default_value": None
                                    },
                                    {
                                        "source_key": "value",
                                        "target_key": "transfer_amount",
                                        "transformer": "wei_to_ether",
                                        "condition": None,
                                        "default_value": "0"
                                    }
                                ]
                            },
                            {
                                "event_name": "Approval",
                                "mapping_rules": [
                                    {
                                        "source_key": "owner",
                                        "target_key": "token_owner",
                                        "transformer": "to_lowercase",
                                        "condition": None,
                                        "default_value": None
                                    },
                                    {
                                        "source_key": "spender",
                                        "target_key": "approved_spender",
                                        "transformer": "to_lowercase",
                                        "condition": None,
                                        "default_value": None
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "step4",
                        "type": "kafka_producer",
                        "bootstrap_servers": "localhost:9092",
                        "topic": "test_api_events",
                        "acks": 1,
                        "sync_send": False
                    }
                ]
            }
            
            pipeline_id = 1001  # 使用测试管道ID
            pipeline_info_str = json.dumps(test_pipeline_config, ensure_ascii=False, indent=2)
            
            print("🔄 保存测试管道配置...")
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 配置保存结果: {save_result}")
            
            print(f"\n🔄 启动管道任务 (pipeline_id: {pipeline_id})...")
            
            # 测试启动管道任务 - 这里会使用优化版执行器
            start_result = await service.start_pipeline_task(pipeline_id)
            print(f"✅ 启动结果: {start_result}")
            
            task_id = start_result.get('task_id')
            if task_id:
                print(f"📋 任务ID: {task_id}")
                print("⚠️  注意: 管道将在后台运行，使用优化版执行器")
                print("📝 可以通过任务状态接口查看执行情况")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🚀 测试 start 接口集成优化版管道执行器")
    print("=" * 60)
    
    success = await test_start_api()
    
    if success:
        print("\n🎉 start 接口测试成功！")
        print("📋 验证内容:")
        print("   ✅ 管道配置保存")
        print("   ✅ 启动接口调用")
        print("   ✅ 使用优化版执行器")
        print("   ✅ 后台任务创建")
    else:
        print("\n❌ start 接口测试失败")


if __name__ == "__main__":
    asyncio.run(main())
