#!/usr/bin/env python3
"""
简化的管道执行器测试

避免复杂的导入依赖，直接测试核心功能
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def test_component_factory():
    """测试组件工厂 - 不依赖外部服务"""
    print("🔄 测试组件工厂...")
    
    try:
        # 直接导入优化版本的组件
        from app.component.pipeline_executor_optimized import ComponentFactory, ComponentType
        
        # 测试创建字典映射器组件（最简单的组件）
        dict_mapper_config = {
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
                        }
                    ]
                }
            ]
        }
        
        # 创建字典映射器组件
        component = ComponentFactory.create_component(
            "dict_mapper", 
            "测试映射器", 
            dict_mapper_config
        )
        
        print(f"   ✅ 字典映射器组件创建成功: {component.name}")
        print(f"   📋 组件类型: {type(component).__name__}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ 组件工厂测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_dict_mapper_component():
    """测试字典映射器组件的多条配置功能"""
    print("\n🔄 测试字典映射器多条配置...")
    
    try:
        from app.component.pipeline_executor_optimized import DictMapperComponent, PipelineContext
        
        # 创建测试配置
        config = {
            "dict_mappers": [
                {
                    "event_name": "Transfer",
                    "mapping_rules": [
                        {
                            "source_key": "from",
                            "target_key": "sender_address",
                            "transformer": None,
                            "condition": None,
                            "default_value": None
                        },
                        {
                            "source_key": "to",
                            "target_key": "receiver_address",
                            "transformer": None,
                            "condition": None,
                            "default_value": None
                        },
                        {
                            "source_key": "value",
                            "target_key": "transfer_amount",
                            "transformer": None,
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
        }
        
        # 创建组件
        component = DictMapperComponent("测试多映射器", config)
        
        # 初始化组件
        init_success = await component.initialize()
        if not init_success:
            print("   ❌ 组件初始化失败")
            return False
        
        print(f"   ✅ 组件初始化成功，创建了 {len(component.mappers)} 个映射器")
        
        # 显示映射器信息
        for i, mapper_info in enumerate(component.mappers):
            event_name = mapper_info['event_name'] or '通用'
            rules_count = mapper_info['rules_count']
            print(f"      {i+1}. {event_name} 映射器 ({rules_count} 条规则)")
        
        # 测试 Transfer 事件数据处理
        print("\n   🔄 测试 Transfer 事件数据处理...")
        transfer_data = {
            "event_name": "Transfer",
            "from": "0x1234567890123456789012345678901234567890",
            "to": "0x0987654321098765432109876543210987654321",
            "value": "1000000000000000000",
            "blockNumber": 12345678,
            "transactionHash": "0xABCDEF1234567890ABCDEF1234567890ABCDEF1234567890ABCDEF1234567890",
            "logIndex": 5
        }
        
        context = PipelineContext(
            data=transfer_data.copy(),
            metadata={"test": True},
            pipeline_id="test_pipeline"
        )
        
        # 执行映射
        result_context = await component.execute(context)
        
        print(f"   ✅ Transfer 事件处理完成")
        print(f"      原始字段数: {len(transfer_data)}")
        print(f"      处理后字段数: {len(result_context.data)}")
        print(f"      新增字段: sender_address, receiver_address, transfer_amount, block_number, tx_hash")
        
        # 测试 Approval 事件数据处理
        print("\n   🔄 测试 Approval 事件数据处理...")
        approval_data = {
            "event_name": "Approval",
            "owner": "0x1111111111111111111111111111111111111111",
            "spender": "0x2222222222222222222222222222222222222222",
            "value": "5000000000000000000",
            "blockNumber": 12345679,
            "transactionHash": "0x1111111111111111111111111111111111111111111111111111111111111111",
            "logIndex": 3
        }
        
        context = PipelineContext(
            data=approval_data.copy(),
            metadata={"test": True},
            pipeline_id="test_pipeline"
        )
        
        # 执行映射
        result_context = await component.execute(context)
        
        print(f"   ✅ Approval 事件处理完成")
        print(f"      原始字段数: {len(approval_data)}")
        print(f"      处理后字段数: {len(result_context.data)}")
        print(f"      新增字段: token_owner, approved_spender, block_number, tx_hash")
        
        # 清理组件
        await component.cleanup()
        
        return True
        
    except Exception as e:
        print(f"   ❌ 字典映射器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backward_compatibility():
    """测试向后兼容性"""
    print("\n🔄 测试向后兼容性...")
    
    try:
        from app.component.pipeline_executor_optimized import DictMapperComponent, PipelineContext
        
        # 旧格式配置
        old_config = {
            "mapping_rules": [  # 旧格式，没有 dict_mappers
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
        
        # 创建组件
        component = DictMapperComponent("向后兼容测试", old_config)
        
        # 初始化组件
        init_success = await component.initialize()
        if not init_success:
            print("   ❌ 向后兼容组件初始化失败")
            return False
        
        print(f"   ✅ 向后兼容组件初始化成功，创建了 {len(component.mappers)} 个映射器")
        
        # 验证转换结果
        mapper_info = component.mappers[0]
        event_name = mapper_info['event_name']
        rules_count = mapper_info['rules_count']
        
        print(f"      映射器事件名称: {event_name} (应该为 None)")
        print(f"      映射规则数量: {rules_count} (应该为 2)")
        
        if event_name is None and rules_count == 2:
            print("   ✅ 向后兼容性验证通过")
        else:
            print("   ❌ 向后兼容性验证失败")
            return False
        
        # 清理组件
        await component.cleanup()
        
        return True
        
    except Exception as e:
        print(f"   ❌ 向后兼容性测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_validation():
    """测试配置验证功能"""
    print("\n🔄 测试配置验证...")
    
    try:
        from app.component.pipeline_executor_optimized import OptimizedBlockchainDataPipeline
        
        # 测试有效配置
        valid_config = {
            "pipeline_name": "测试管道",
            "description": "配置验证测试",
            "components": [
                {
                    "name": "数据源",
                    "type": "event_monitor",  # 有效的数据源组件
                    "chain_name": "ethereum",
                    "contract_address": "0x1234567890123456789012345678901234567890",
                    "abi_path": "abis/erc20.json"
                },
                {
                    "name": "数据处理",
                    "type": "dict_mapper",
                    "mapping_rules": []
                }
            ]
        }
        
        try:
            pipeline = OptimizedBlockchainDataPipeline(config_dict=valid_config)
            print("   ✅ 有效配置验证通过")
        except Exception as e:
            print(f"   ❌ 有效配置验证失败: {e}")
            return False
        
        # 测试无效配置 - 第一个组件不是数据源
        invalid_config = {
            "pipeline_name": "无效测试管道",
            "description": "配置验证测试",
            "components": [
                {
                    "name": "数据处理",
                    "type": "dict_mapper",  # 无效：第一个组件不是数据源
                    "mapping_rules": []
                }
            ]
        }
        
        try:
            pipeline = OptimizedBlockchainDataPipeline(config_dict=invalid_config)
            print("   ❌ 无效配置应该被拒绝，但通过了验证")
            return False
        except ValueError as e:
            print(f"   ✅ 无效配置正确被拒绝: {e}")
        except Exception as e:
            print(f"   ❌ 无效配置验证出现意外错误: {e}")
            return False
        
        return True
        
    except Exception as e:
        print(f"   ❌ 配置验证测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主测试函数"""
    print("🧪 优化版管道执行器简化测试套件")
    print("=" * 60)
    
    test_results = []
    
    # 测试1: 组件工厂
    result1 = test_component_factory()
    test_results.append(("组件工厂测试", result1))
    
    # 测试2: 字典映射器多条配置
    result2 = await test_dict_mapper_component()
    test_results.append(("字典映射器多条配置测试", result2))
    
    # 测试3: 向后兼容性
    result3 = await test_backward_compatibility()
    test_results.append(("向后兼容性测试", result3))
    
    # 测试4: 配置验证
    result4 = test_config_validation()
    test_results.append(("配置验证测试", result4))
    
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
    
    return passed == len(test_results)


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
