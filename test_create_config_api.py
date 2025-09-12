#!/usr/bin/env python3
"""
测试新增管道配置接口，验证 dict_mapper 类型支持多个 mapping_rules 配置
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


async def test_create_config_api():
    """测试新增管道配置接口支持多个 dict_mapper 配置"""
    
    print("🧪 测试新增管道配置接口 - dict_mapper 支持多个 mapping_rules")
    print("-" * 65)
    
    try:
        # 初始化数据库服务
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试配置：包含多个 dict_mapper 配置的管道
            test_pipeline_config = {
                "pipeline_name": "多映射器测试管道",
                "description": "测试新增接口支持多个dict_mapper配置",
                "classification_id": 1,
                "components": [
                    {
                        "name": "event_step",
                        "type": "event_monitor",
                        "chain_name": "ethereum",
                        "contract_address": "0xA0b86a33E6441c8C06DD2c1c1e3e5C2b8b6C6E5D",
                        "abi_path": "abis/erc20.json",
                        "events_to_monitor": ["Transfer", "Approval", "Mint"],
                        "mode": "realtime",
                        "output_format": "detailed",
                        "poll_interval": 2.0
                    },
                    {
                        "name": "multi_mapper_step",
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
                                    },
                                    {
                                        "source_key": "blockNumber",
                                        "target_key": "block_number",
                                        "transformer": "to_int",
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
                                    },
                                    {
                                        "source_key": "value",
                                        "target_key": "approval_amount",
                                        "transformer": "wei_to_ether",
                                        "condition": None,
                                        "default_value": "0"
                                    }
                                ]
                            },
                            {
                                "event_name": "Mint",
                                "mapping_rules": [
                                    {
                                        "source_key": "to",
                                        "target_key": "mint_recipient",
                                        "transformer": "to_lowercase",
                                        "condition": None,
                                        "default_value": None
                                    },
                                    {
                                        "source_key": "amount",
                                        "target_key": "mint_amount",
                                        "transformer": "wei_to_ether",
                                        "condition": None,
                                        "default_value": "0"
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "kafka_step",
                        "type": "kafka_producer",
                        "bootstrap_servers": "localhost:9092",
                        "topic": "multi_mapper_events",
                        "acks": 1,
                        "sync_send": False
                    }
                ]
            }
            
            pipeline_id = 2001  # 使用新的测试管道ID
            pipeline_info_str = json.dumps(test_pipeline_config, ensure_ascii=False, indent=2)
            
            print("🔄 测试新增管道配置...")
            print(f"📋 管道ID: {pipeline_id}")
            print(f"📝 组件数量: {len(test_pipeline_config['components'])}")
            print(f"🎯 dict_mapper 配置数量: {len(test_pipeline_config['components'][1]['dict_mappers'])}")
            
            # 保存配置
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 保存结果: {save_result}")
            
            # 验证保存的配置
            print(f"\n🔍 验证保存的配置...")
            saved_config = await service.get_pipeline_config(pipeline_id)
            
            # 查找 dict_mapper 组件
            dict_mapper_component = None
            for component in saved_config.get('components', []):
                if component.get('type') == 'dict_mapper':
                    dict_mapper_component = component
                    break
            
            if dict_mapper_component:
                print("✅ 找到 dict_mapper 组件")
                
                # 验证 dict_mappers 配置
                dict_mappers = dict_mapper_component.get('dict_mappers', [])
                print(f"📊 dict_mappers 数量: {len(dict_mappers)}")
                
                # 验证是否没有顶级 mapping_rules 字段
                has_top_level_mapping_rules = 'mapping_rules' in dict_mapper_component
                print(f"❌ 包含顶级 mapping_rules: {has_top_level_mapping_rules}")
                
                # 验证每个 dict_mapper 配置
                expected_events = ["Transfer", "Approval", "Mint"]
                for i, mapper in enumerate(dict_mappers):
                    event_name = mapper.get('event_name')
                    mapping_rules = mapper.get('mapping_rules', [])
                    print(f"   {i+1}. event_name: {event_name}, mapping_rules: {len(mapping_rules)} 条")
                    
                    if event_name in expected_events:
                        expected_events.remove(event_name)
                
                # 验证结果
                if len(dict_mappers) == 3 and len(expected_events) == 0 and not has_top_level_mapping_rules:
                    print("🎉 验证通过: 新增接口正确支持多个 dict_mapper 配置")
                    
                    # 显示详细配置
                    print(f"\n📄 dict_mapper 组件详细配置:")
                    for mapper in dict_mappers:
                        print(f"   🎯 {mapper.get('event_name')}: {len(mapper.get('mapping_rules', []))} 条规则")
                        for rule in mapper.get('mapping_rules', []):
                            print(f"      - {rule.get('source_key')} → {rule.get('target_key')} ({rule.get('transformer')})")
                    
                    return True
                else:
                    print("⚠️  验证失败: dict_mapper 配置不符合预期")
                    return False
            else:
                print("❌ 未找到 dict_mapper 组件")
                return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_backward_compatibility():
    """测试向后兼容性：旧的 mapping_rules 格式"""
    
    print("\n🧪 测试向后兼容性 - 旧的 mapping_rules 格式")
    print("-" * 50)
    
    try:
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试旧格式配置
            old_format_config = {
                "pipeline_name": "向后兼容测试管道",
                "description": "测试旧的mapping_rules格式兼容性",
                "classification_id": 1,
                "components": [
                    {
                        "name": "old_mapper_step",
                        "type": "dict_mapper",
                        "mapping_rules": [
                            {
                                "source_key": "from",
                                "target_key": "sender",
                                "transformer": "to_lowercase",
                                "condition": None,
                                "default_value": None
                            },
                            {
                                "source_key": "to",
                                "target_key": "receiver",
                                "transformer": "to_lowercase",
                                "condition": None,
                                "default_value": None
                            }
                        ]
                    }
                ]
            }
            
            pipeline_id = 2002  # 使用另一个测试管道ID
            pipeline_info_str = json.dumps(old_format_config, ensure_ascii=False, indent=2)
            
            print("🔄 测试旧格式配置保存...")
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 保存结果: {save_result}")
            
            # 验证保存的配置
            saved_config = await service.get_pipeline_config(pipeline_id)
            
            # 查找 dict_mapper 组件
            dict_mapper_component = None
            for component in saved_config.get('components', []):
                if component.get('type') == 'dict_mapper':
                    dict_mapper_component = component
                    break
            
            if dict_mapper_component:
                dict_mappers = dict_mapper_component.get('dict_mappers', [])
                print(f"📊 转换后的 dict_mappers 数量: {len(dict_mappers)}")
                
                if len(dict_mappers) == 1:
                    mapper = dict_mappers[0]
                    event_name = mapper.get('event_name')
                    mapping_rules = mapper.get('mapping_rules', [])
                    
                    print(f"   event_name: {event_name} (应为 null)")
                    print(f"   mapping_rules: {len(mapping_rules)} 条")
                    
                    if event_name is None and len(mapping_rules) == 2:
                        print("🎉 向后兼容性验证通过")
                        return True
                    else:
                        print("⚠️  向后兼容性验证失败")
                        return False
            
            return False
            
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 测试新增管道配置接口的 dict_mapper 支持")
    print("=" * 70)
    
    # 测试新格式
    success1 = await test_create_config_api()
    
    # 测试向后兼容性
    success2 = await test_backward_compatibility()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！")
        print("📋 验证内容:")
        print("   ✅ 新增接口支持多个 dict_mapper 配置")
        print("   ✅ 每个 dict_mapper 包含 event_name 和 mapping_rules")
        print("   ✅ 查询时不返回顶级 mapping_rules 字段")
        print("   ✅ 向后兼容旧的 mapping_rules 格式")
    else:
        print("\n❌ 部分测试失败")
        if not success1:
            print("   ❌ 新格式测试失败")
        if not success2:
            print("   ❌ 向后兼容性测试失败")


if __name__ == "__main__":
    asyncio.run(main())
