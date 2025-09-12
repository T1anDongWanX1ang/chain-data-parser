#!/usr/bin/env python3
"""
测试 DictMapper 只保留有映射规则的字段功能
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.component.pipeline_executor_optimized import OptimizedBlockchainDataPipeline, PipelineContext


async def test_dict_mapper_field_filtering():
    """测试字典映射器只保留映射字段的功能"""
    
    print("🧪 测试 DictMapper 字段过滤功能")
    print("=" * 50)
    
    # 创建测试配置
    test_config = {
        "pipeline_name": "字段过滤测试管道",
        "description": "测试DictMapper只保留有映射规则的字段",
        "classification_id": 1,
        "components": [
            {
                "name": "test_event_monitor",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0xA0b86a33E6441c8C06DD2b7c94b7E0e8d61c6e8e",
                "abi_path": "abis/erc20.json",
                "mode": "realtime",
                "events_to_monitor": ["Transfer"],
                "output_format": "detailed"
            },
            {
                "name": "test_dict_mapper",
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
                                "target_key": "amount",
                                "transformer": None,
                                "condition": None,
                                "default_value": "0"
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    try:
        print("🔄 创建管道实例...")
        pipeline = OptimizedBlockchainDataPipeline(config_dict=test_config)
        
        print("🔄 初始化组件...")
        await pipeline._initialize_components()
        
        print(f"✅ 组件初始化完成，共 {len(pipeline.components)} 个组件")
        
        # 创建包含额外字段的测试数据
        original_data = {
            # 有映射规则的字段
            "from": "0x1234567890ABCDEF1234567890ABCDEF12345678",
            "to": "0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
            "value": "1000000000000000000",
            
            # 没有映射规则的字段（应该被过滤掉）
            "event_name": "Transfer",
            "block_number": 18500000,
            "transaction_hash": "0xtest123456789",
            "log_index": 0,
            "gas_used": 21000,
            "gas_price": "20000000000",
            "contract_address": "0xA0b86a33E6441c8C06DD2b7c94b7E0e8d61c6e8e",
            "extra_field_1": "should_be_filtered",
            "extra_field_2": 12345,
            "nested_data": {
                "inner_field": "also_should_be_filtered"
            }
        }
        
        print(f"\n📊 原始数据字段数: {len(original_data)}")
        print("📋 原始数据字段:")
        for key, value in original_data.items():
            print(f"   - {key}: {value}")
        
        # 创建管道上下文
        context = PipelineContext(
            data=original_data,
            metadata={},
            pipeline_id="test_filter"
        )
        
        print(f"\n🔄 执行字典映射...")
        
        # 只处理 dict_mapper 组件（跳过第一个 event_monitor）
        dict_mapper_component = pipeline.components[1]  # 第二个组件是 dict_mapper
        
        result_context = await dict_mapper_component.execute(context)
        
        print(f"\n📊 映射后数据字段数: {len(result_context.data)}")
        print("📋 映射后数据字段:")
        for key, value in result_context.data.items():
            print(f"   - {key}: {value}")
        
        # 验证结果
        expected_fields = {"sender_address", "receiver_address", "amount"}
        actual_fields = set(result_context.data.keys())
        
        print(f"\n🔍 验证结果:")
        print(f"   预期字段: {expected_fields}")
        print(f"   实际字段: {actual_fields}")
        
        # 检查是否只包含映射后的字段
        unexpected_fields = actual_fields - expected_fields
        missing_fields = expected_fields - actual_fields
        
        if not unexpected_fields and not missing_fields:
            print("✅ 字段过滤测试通过！")
            print("   ✅ 只保留了有映射规则的字段")
            print("   ✅ 所有映射字段都存在")
            print("   ✅ 没有额外的未映射字段")
            
            # 验证字段值的正确性
            print(f"\n🔍 验证字段值:")
            if result_context.data.get("sender_address") == original_data["from"].lower():
                print("   ✅ sender_address 映射和转换正确")
            else:
                print(f"   ❌ sender_address 映射错误: 期望 {original_data['from'].lower()}, 实际 {result_context.data.get('sender_address')}")
            
            if result_context.data.get("receiver_address") == original_data["to"].lower():
                print("   ✅ receiver_address 映射和转换正确")
            else:
                print(f"   ❌ receiver_address 映射错误: 期望 {original_data['to'].lower()}, 实际 {result_context.data.get('receiver_address')}")
            
            if result_context.data.get("amount") == original_data["value"]:
                print("   ✅ amount 映射正确")
            else:
                print(f"   ❌ amount 映射错误: 期望 {original_data['value']}, 实际 {result_context.data.get('amount')}")
            
            return True
        else:
            print("❌ 字段过滤测试失败！")
            if unexpected_fields:
                print(f"   ❌ 包含了不应该存在的字段: {unexpected_fields}")
            if missing_fields:
                print(f"   ❌ 缺少预期的字段: {missing_fields}")
            return False
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_multiple_mappers_filtering():
    """测试多个映射器的字段过滤功能"""
    
    print(f"\n🧪 测试多个映射器的字段过滤")
    print("-" * 40)
    
    # 创建包含多个映射器的配置
    multi_mapper_config = {
        "pipeline_name": "多映射器字段过滤测试",
        "description": "测试多个映射器的字段过滤功能",
        "classification_id": 1,
        "components": [
            {
                "name": "test_event_monitor",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0xA0b86a33E6441c8C06DD2b7c94b7E0e8d61c6e8e",
                "abi_path": "abis/erc20.json",
                "mode": "realtime",
                "events_to_monitor": ["Transfer", "Approval"],
                "output_format": "detailed"
            },
            {
                "name": "multi_dict_mapper",
                "type": "dict_mapper",
                "dict_mappers": [
                    {
                        "event_name": "Transfer",
                        "mapping_rules": [
                            {
                                "source_key": "from",
                                "target_key": "transfer_from",
                                "transformer": "to_lowercase",
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "to",
                                "target_key": "transfer_to",
                                "transformer": "to_lowercase",
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
                                "target_key": "approval_owner",
                                "transformer": "to_lowercase",
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "spender",
                                "target_key": "approval_spender",
                                "transformer": "to_lowercase",
                                "condition": None,
                                "default_value": None
                            }
                        ]
                    }
                ]
            }
        ]
    }
    
    try:
        pipeline = OptimizedBlockchainDataPipeline(config_dict=multi_mapper_config)
        await pipeline._initialize_components()
        
        # 测试 Transfer 事件
        transfer_data = {
            "event_name": "Transfer",
            "from": "0x1111111111111111111111111111111111111111",
            "to": "0x2222222222222222222222222222222222222222",
            "value": "500000000000000000",
            "block_number": 18500001,
            "extra_field": "should_be_removed"
        }
        
        print(f"🔄 测试 Transfer 事件映射...")
        context = PipelineContext(
            data=transfer_data,
            metadata={},
            pipeline_id="test_transfer"
        )
        
        dict_mapper_component = pipeline.components[1]
        result_context = await dict_mapper_component.execute(context)
        
        expected_transfer_fields = {"transfer_from", "transfer_to"}
        actual_transfer_fields = set(result_context.data.keys())
        
        print(f"   原始字段数: {len(transfer_data)}")
        print(f"   映射后字段数: {len(result_context.data)}")
        print(f"   映射后字段: {actual_transfer_fields}")
        
        if actual_transfer_fields == expected_transfer_fields:
            print("   ✅ Transfer 事件字段过滤正确")
            transfer_success = True
        else:
            print(f"   ❌ Transfer 事件字段过滤错误: 期望 {expected_transfer_fields}, 实际 {actual_transfer_fields}")
            transfer_success = False
        
        # 测试 Approval 事件
        approval_data = {
            "event_name": "Approval",
            "owner": "0x3333333333333333333333333333333333333333",
            "spender": "0x4444444444444444444444444444444444444444",
            "value": "1000000000000000000",
            "block_number": 18500002,
            "transaction_hash": "0xapproval123",
            "extra_field": "should_also_be_removed"
        }
        
        print(f"\n🔄 测试 Approval 事件映射...")
        context = PipelineContext(
            data=approval_data,
            metadata={},
            pipeline_id="test_approval"
        )
        
        result_context = await dict_mapper_component.execute(context)
        
        expected_approval_fields = {"approval_owner", "approval_spender"}
        actual_approval_fields = set(result_context.data.keys())
        
        print(f"   原始字段数: {len(approval_data)}")
        print(f"   映射后字段数: {len(result_context.data)}")
        print(f"   映射后字段: {actual_approval_fields}")
        
        if actual_approval_fields == expected_approval_fields:
            print("   ✅ Approval 事件字段过滤正确")
            approval_success = True
        else:
            print(f"   ❌ Approval 事件字段过滤错误: 期望 {expected_approval_fields}, 实际 {actual_approval_fields}")
            approval_success = False
        
        return transfer_success and approval_success
        
    except Exception as e:
        print(f"❌ 多映射器测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 测试 DictMapper 字段过滤功能")
    print("=" * 60)
    
    # 测试单个映射器的字段过滤
    success1 = await test_dict_mapper_field_filtering()
    
    # 测试多个映射器的字段过滤
    success2 = await test_multiple_mappers_filtering()
    
    print(f"\n📊 测试结果总结:")
    print("=" * 30)
    
    if success1:
        print("✅ 单映射器字段过滤测试通过")
    else:
        print("❌ 单映射器字段过滤测试失败")
    
    if success2:
        print("✅ 多映射器字段过滤测试通过")
    else:
        print("❌ 多映射器字段过滤测试失败")
    
    if success1 and success2:
        print(f"\n🎉 所有字段过滤测试通过！")
        print("📋 验证功能:")
        print("   ✅ 只保留有映射规则的字段")
        print("   ✅ 过滤掉所有未映射的字段")
        print("   ✅ 支持多个映射器的字段过滤")
        print("   ✅ 正确应用字段转换器")
        print("   ✅ 根据事件名称选择正确的映射器")
    else:
        print(f"\n❌ 部分测试失败，请检查实现")


if __name__ == "__main__":
    asyncio.run(main())
