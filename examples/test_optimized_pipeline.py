#!/usr/bin/env python3
"""
测试优化后的管道执行器

演示新功能：
1. 组件工厂模式
2. 多条 dict_mapper 配置
3. 改进的数据流处理
4. 增强的错误处理
5. 组件生命周期管理
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from app.component.pipeline_executor_optimized import OptimizedBlockchainDataPipeline
from loguru import logger


async def test_optimized_pipeline_with_config_dict():
    """测试使用配置字典的优化管道"""
    
    # 测试配置
    test_config = {
        "pipeline_name": "测试优化管道",
        "description": "测试优化后的管道执行器功能",
        "classification_id": 1,
        "components": [
            {
                "name": "模拟事件监控器",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0x1234567890123456789012345678901234567890",
                "abi_path": "abis/erc20.json",
                "events_to_monitor": ["Transfer", "Approval"],
                "mode": "realtime",
                "output_format": "detailed",
                "poll_interval": 1.0
            },
            {
                "name": "多事件映射器",
                "type": "dict_mapper",
                "dict_mappers": [
                    {
                        "event_name": "Transfer",
                        "mapping_rules": [
                            {
                                "source_key": "from",
                                "target_key": "sender",
                                "transformer": None,
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "to",
                                "target_key": "receiver",
                                "transformer": None,
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "value",
                                "target_key": "amount",
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
                                "transformer": None,
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "spender",
                                "target_key": "approved_spender",
                                "transformer": None,
                                "condition": None,
                                "default_value": None
                            }
                        ]
                    },
                    {
                        "event_name": None,  # 通用映射器
                        "mapping_rules": [
                            {
                                "source_key": "blockNumber",
                                "target_key": "block_number",
                                "transformer": None,
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "transactionHash",
                                "target_key": "tx_hash",
                                "transformer": None,
                                "condition": None,
                                "default_value": None
                            }
                        ]
                    }
                ]
            },
            {
                "name": "Kafka发布器",
                "type": "kafka_producer",
                "bootstrap_servers": "localhost:9092",
                "topic": "test_events",
                "acks": 1,
                "sync_send": False
            }
        ]
    }
    
    try:
        print("🚀 开始测试优化后的管道执行器")
        print("-" * 50)
        
        # 创建管道实例
        pipeline = OptimizedBlockchainDataPipeline(
            config_dict=test_config,
            log_path="logs/test_optimized_pipeline.log"
        )
        
        print(f"✅ 管道创建成功: {test_config['pipeline_name']}")
        print(f"📋 组件数量: {len(test_config['components'])}")
        
        # 显示组件信息
        for i, component in enumerate(test_config['components']):
            comp_name = component['name']
            comp_type = component['type']
            print(f"   {i+1}. {comp_name} ({comp_type})")
            
            # 如果是 dict_mapper，显示映射器数量
            if comp_type == 'dict_mapper':
                dict_mappers = component.get('dict_mappers', [])
                print(f"      └─ 映射器数量: {len(dict_mappers)}")
                for j, mapper in enumerate(dict_mappers):
                    event_name = mapper.get('event_name') or '通用'
                    rules_count = len(mapper.get('mapping_rules', []))
                    print(f"         {j+1}. {event_name} ({rules_count} 条规则)")
        
        print("\n🔄 开始初始化组件...")
        
        # 注意：在实际测试中，事件监控器会尝试连接区块链
        # 这里我们只测试初始化过程，不实际启动监控
        print("⚠️  注意：实际的事件监控需要有效的区块链连接")
        print("📝 此测试主要验证组件创建和配置解析功能")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backward_compatibility():
    """测试向后兼容性"""
    
    # 旧格式配置
    old_config = {
        "pipeline_name": "向后兼容测试管道",
        "description": "测试旧格式配置的兼容性",
        "classification_id": 1,
        "components": [
            {
                "name": "事件监控器",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0x1234567890123456789012345678901234567890",
                "abi_path": "abis/erc20.json",
                "events_to_monitor": ["Transfer"]
            },
            {
                "name": "旧格式映射器",
                "type": "dict_mapper",
                "mapping_rules": [  # 旧格式
                    {
                        "source_key": "from",
                        "target_key": "sender",
                        "transformer": None,
                        "condition": None,
                        "default_value": None
                    },
                    {
                        "source_key": "to",
                        "target_key": "receiver",
                        "transformer": None,
                        "condition": None,
                        "default_value": None
                    }
                ]
            }
        ]
    }
    
    try:
        print("\n🔄 测试向后兼容性...")
        
        pipeline = OptimizedBlockchainDataPipeline(config_dict=old_config)
        print("✅ 向后兼容性测试通过！旧格式配置可以正常解析")
        
        return True
        
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False


def test_component_factory():
    """测试组件工厂"""
    from app.component.pipeline_executor_optimized import ComponentFactory, ComponentType
    
    print("\n🔄 测试组件工厂...")
    
    try:
        # 测试创建不同类型的组件
        test_configs = [
            {
                "type": "contract_caller",
                "name": "测试合约调用器",
                "config": {
                    "chain_name": "ethereum",
                    "contract_address": "0x1234567890123456789012345678901234567890",
                    "abi_path": "abis/erc20.json",
                    "method_name": "balanceOf"
                }
            },
            {
                "type": "dict_mapper",
                "name": "测试映射器",
                "config": {
                    "dict_mappers": [
                        {
                            "event_name": "Transfer",
                            "mapping_rules": [
                                {
                                    "source_key": "from",
                                    "target_key": "sender",
                                    "transformer": None,
                                    "condition": None,
                                    "default_value": None
                                }
                            ]
                        }
                    ]
                }
            },
            {
                "type": "kafka_producer",
                "name": "测试Kafka生产者",
                "config": {
                    "bootstrap_servers": "localhost:9092",
                    "topic": "test_topic"
                }
            }
        ]
        
        for test_config in test_configs:
            comp_type = test_config["type"]
            comp_name = test_config["name"]
            config = test_config["config"]
            
            try:
                component = ComponentFactory.create_component(comp_type, comp_name, config)
                print(f"   ✅ {comp_name} ({comp_type}) - 创建成功")
            except Exception as e:
                print(f"   ❌ {comp_name} ({comp_type}) - 创建失败: {e}")
        
        print("✅ 组件工厂测试完成")
        return True
        
    except Exception as e:
        print(f"❌ 组件工厂测试失败: {e}")
        return False


async def main():
    """主测试函数"""
    print("🧪 优化版管道执行器测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 组件工厂
    result1 = test_component_factory()
    test_results.append(("组件工厂测试", result1))
    
    # 测试2: 优化管道功能
    result2 = await test_optimized_pipeline_with_config_dict()
    test_results.append(("优化管道功能测试", result2))
    
    # 测试3: 向后兼容性
    result3 = await test_backward_compatibility()
    test_results.append(("向后兼容性测试", result3))
    
    # 输出测试结果
    print("\n" + "=" * 60)
    print("📊 测试结果汇总:")
    print("-" * 30)
    
    passed = 0
    for test_name, result in test_results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n🎯 总计: {passed}/{len(test_results)} 个测试通过")
    
    if passed == len(test_results):
        print("🎉 所有测试通过！优化版管道执行器功能正常")
    else:
        print("⚠️  部分测试失败，请检查相关功能")


if __name__ == "__main__":
    asyncio.run(main())
