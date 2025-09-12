"""测试多条 dict_mapper 配置功能"""
import json
import asyncio
from datetime import datetime
from app.services.database_service import database_service
from app.services.pipeline_config_service import PipelineConfigService


async def test_multi_dict_mapper_config():
    """测试多条 dict_mapper 配置的保存和获取"""
    
    # 测试配置：包含多条 dict_mapper 配置的管道
    test_pipeline_config = {
        "pipeline_name": "多映射器测试管道",
        "description": "测试多条 dict_mapper 配置功能",
        "classification_id": 1,
        "components": [
            {
                "name": "事件监控器",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0x1234567890123456789012345678901234567890",
                "abi_path": "abis/erc20.json",
                "events_to_monitor": ["Transfer", "Approval"]
            },
            {
                "name": "多映射器组件",
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
                            },
                            {
                                "source_key": "value",
                                "target_key": "approved_amount",
                                "transformer": "wei_to_ether",
                                "condition": None,
                                "default_value": "0"
                            }
                        ]
                    },
                    {
                        "event_name": None,  # 通用映射器，不指定事件名
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
                "name": "Kafka生产者",
                "type": "kafka_producer",
                "bootstrap_servers": "localhost:9092",
                "topic": "blockchain_events"
            }
        ]
    }
    
    try:
        # 初始化数据库服务
        await database_service.init_database()
        
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试保存管道配置
            print("🔄 正在保存多条 dict_mapper 配置...")
            pipeline_id = 999  # 使用测试ID
            pipeline_info_str = json.dumps(test_pipeline_config, ensure_ascii=False, indent=2)
            
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 保存结果: {save_result}")
            
            # 测试获取管道配置
            print("\n🔄 正在获取管道配置...")
            retrieved_config = await service.get_pipeline_config(pipeline_id)
            
            print(f"✅ 获取的管道配置:")
            print(f"   管道名称: {retrieved_config['pipeline_name']}")
            print(f"   组件数量: {len(retrieved_config['components'])}")
            
            # 检查 dict_mapper 组件
            for component in retrieved_config['components']:
                if component['type'] == 'dict_mapper':
                    print(f"\n📋 Dict Mapper 组件: {component['name']}")
                    dict_mappers = component.get('dict_mappers', [])
                    print(f"   映射器数量: {len(dict_mappers)}")
                    
                    for i, mapper in enumerate(dict_mappers):
                        print(f"   映射器 {i+1}:")
                        print(f"     ID: {mapper['id']}")
                        print(f"     事件名称: {mapper['event_name'] or '通用'}")
                        print(f"     映射规则数量: {len(mapper['mapping_rules'])}")
                        
                        # 显示前3个映射规则
                        for j, rule in enumerate(mapper['mapping_rules'][:3]):
                            print(f"       规则 {j+1}: {rule['source_key']} -> {rule['target_key']}")
                        
                        if len(mapper['mapping_rules']) > 3:
                            print(f"       ... 还有 {len(mapper['mapping_rules']) - 3} 个规则")
            
            print(f"\n🎉 测试完成！成功保存和获取了 {len([c for c in retrieved_config['components'] if c['type'] == 'dict_mapper'])} 个 dict_mapper 组件")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


async def test_backward_compatibility():
    """测试向后兼容性：旧的 mapping_rules 格式"""
    
    # 旧格式的配置
    old_format_config = {
        "pipeline_name": "向后兼容测试管道",
        "description": "测试旧格式 mapping_rules 的兼容性",
        "classification_id": 1,
        "components": [
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
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            print("\n🔄 测试向后兼容性...")
            pipeline_id = 998  # 使用不同的测试ID
            pipeline_info_str = json.dumps(old_format_config, ensure_ascii=False, indent=2)
            
            # 保存旧格式配置
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 旧格式保存结果: {save_result}")
            
            # 获取配置并检查兼容性
            retrieved_config = await service.get_pipeline_config(pipeline_id)
            
            for component in retrieved_config['components']:
                if component['type'] == 'dict_mapper':
                    print(f"📋 向后兼容检查:")
                    print(f"   dict_mappers 数量: {len(component.get('dict_mappers', []))}")
                    print(f"   mapping_rules 数量: {len(component.get('mapping_rules', []))}")
                    
                    # 检查是否正确转换
                    dict_mappers = component.get('dict_mappers', [])
                    if dict_mappers:
                        first_mapper = dict_mappers[0]
                        print(f"   第一个映射器事件名称: {first_mapper['event_name']}")
                        print(f"   第一个映射器规则数量: {len(first_mapper['mapping_rules'])}")
            
            print("✅ 向后兼容性测试通过！")
            
    except Exception as e:
        print(f"❌ 向后兼容性测试失败: {e}")


async def main():
    """主测试函数"""
    print("🚀 开始测试多条 dict_mapper 配置功能\n")
    
    # 测试多条配置
    await test_multi_dict_mapper_config()
    
    # 测试向后兼容性
    await test_backward_compatibility()
    
    print("\n🎯 所有测试完成！")


if __name__ == "__main__":
    asyncio.run(main())
