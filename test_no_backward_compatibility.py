#!/usr/bin/env python3
"""
测试新增管道配置接口，验证不再支持旧的 mapping_rules 格式
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


async def test_new_format_only():
    """测试只支持新的 dict_mappers 格式"""
    
    print("🧪 测试新格式支持 - 只支持 dict_mappers")
    print("-" * 50)
    
    try:
        # 初始化数据库服务
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试新格式配置
            new_format_config = {
                "pipeline_name": "新格式测试管道",
                "description": "测试只支持新的dict_mappers格式",
                "classification_id": 1,
                "components": [
                    {
                        "name": "new_mapper_step",
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
                                    }
                                ]
                            }
                        ]
                    }
                ]
            }
            
            pipeline_id = 3001  # 使用新的测试管道ID
            pipeline_info_str = json.dumps(new_format_config, ensure_ascii=False, indent=2)
            
            print("🔄 测试新格式配置保存...")
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 新格式保存成功: {save_result}")
            
            # 验证保存的配置
            saved_config = await service.get_pipeline_config(pipeline_id)
            dict_mapper_component = None
            for component in saved_config.get('components', []):
                if component.get('type') == 'dict_mapper':
                    dict_mapper_component = component
                    break
            
            if dict_mapper_component:
                dict_mappers = dict_mapper_component.get('dict_mappers', [])
                print(f"📊 dict_mappers 数量: {len(dict_mappers)}")
                
                if len(dict_mappers) == 2:
                    print("🎉 新格式验证通过")
                    return True
                else:
                    print("⚠️  新格式验证失败")
                    return False
            
            return False
            
    except Exception as e:
        print(f"❌ 新格式测试失败: {e}")
        return False


async def test_old_format_rejection():
    """测试旧格式被拒绝"""
    
    print("\n🧪 测试旧格式拒绝 - 应该抛出错误")
    print("-" * 45)
    
    try:
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试旧格式配置（应该被拒绝）
            old_format_config = {
                "pipeline_name": "旧格式测试管道",
                "description": "测试旧格式应该被拒绝",
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
                            }
                        ]
                    }
                ]
            }
            
            pipeline_id = 3002  # 使用另一个测试管道ID
            pipeline_info_str = json.dumps(old_format_config, ensure_ascii=False, indent=2)
            
            print("🔄 测试旧格式配置保存（应该失败）...")
            
            try:
                save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
                print(f"⚠️  意外成功: {save_result}")
                print("❌ 旧格式应该被拒绝，但却成功了")
                return False
                
            except Exception as e:
                error_message = str(e)
                # 处理 HTTPException 的情况
                if hasattr(e, 'detail'):
                    error_message = e.detail
                
                print(f"🔍 捕获到错误: {error_message}")
                
                if "dict_mapper 组件必须包含 dict_mappers 配置" in error_message:
                    print(f"✅ 正确拒绝旧格式: {error_message}")
                    print("🎉 旧格式拒绝验证通过")
                    return True
                else:
                    print(f"⚠️  错误类型不匹配: {error_message}")
                    return False
            
    except Exception as e:
        print(f"❌ 旧格式拒绝测试失败: {e}")
        return False


async def test_empty_dict_mappers_rejection():
    """测试空的 dict_mappers 被拒绝"""
    
    print("\n🧪 测试空 dict_mappers 拒绝")
    print("-" * 35)
    
    try:
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试空的 dict_mappers 配置
            empty_config = {
                "pipeline_name": "空配置测试管道",
                "description": "测试空dict_mappers应该被拒绝",
                "classification_id": 1,
                "components": [
                    {
                        "name": "empty_mapper_step",
                        "type": "dict_mapper",
                        "dict_mappers": []  # 空数组
                    }
                ]
            }
            
            pipeline_id = 3003
            pipeline_info_str = json.dumps(empty_config, ensure_ascii=False, indent=2)
            
            print("🔄 测试空 dict_mappers 配置（应该失败）...")
            
            try:
                save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
                print(f"⚠️  意外成功: {save_result}")
                print("❌ 空 dict_mappers 应该被拒绝")
                return False
                
            except Exception as e:
                error_message = str(e)
                # 处理 HTTPException 的情况
                if hasattr(e, 'detail'):
                    error_message = e.detail
                
                print(f"🔍 捕获到错误: {error_message}")
                
                if "dict_mapper 组件必须包含 dict_mappers 配置" in error_message:
                    print(f"✅ 正确拒绝空配置: {error_message}")
                    print("🎉 空配置拒绝验证通过")
                    return True
                else:
                    print(f"⚠️  错误类型不匹配: {error_message}")
                    return False
                    
    except Exception as e:
        print(f"❌ 空配置拒绝测试失败: {e}")
        return False


async def test_empty_mapping_rules_rejection():
    """测试空的 mapping_rules 被拒绝"""
    
    print("\n🧪 测试空 mapping_rules 拒绝")
    print("-" * 35)
    
    try:
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 测试空的 mapping_rules 配置
            empty_rules_config = {
                "pipeline_name": "空规则测试管道",
                "description": "测试空mapping_rules应该被拒绝",
                "classification_id": 1,
                "components": [
                    {
                        "name": "empty_rules_step",
                        "type": "dict_mapper",
                        "dict_mappers": [
                            {
                                "event_name": "Transfer",
                                "mapping_rules": []  # 空的映射规则
                            }
                        ]
                    }
                ]
            }
            
            pipeline_id = 3004
            pipeline_info_str = json.dumps(empty_rules_config, ensure_ascii=False, indent=2)
            
            print("🔄 测试空 mapping_rules 配置（应该失败）...")
            
            try:
                save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
                print(f"⚠️  意外成功: {save_result}")
                print("❌ 空 mapping_rules 应该被拒绝")
                return False
                
            except Exception as e:
                error_message = str(e)
                # 处理 HTTPException 的情况
                if hasattr(e, 'detail'):
                    error_message = e.detail
                
                print(f"🔍 捕获到错误: {error_message}")
                
                if "dict_mapper 配置必须包含 mapping_rules" in error_message:
                    print(f"✅ 正确拒绝空规则: {error_message}")
                    print("🎉 空规则拒绝验证通过")
                    return True
                else:
                    print(f"⚠️  错误类型不匹配: {error_message}")
                    return False
                    
    except Exception as e:
        print(f"❌ 空规则拒绝测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 测试移除向后兼容性 - 只支持新的 dict_mappers 格式")
    print("=" * 70)
    
    # 测试新格式支持
    success1 = await test_new_format_only()
    
    # 测试旧格式拒绝
    success2 = await test_old_format_rejection()
    
    # 测试空配置拒绝
    success3 = await test_empty_dict_mappers_rejection()
    
    # 测试空规则拒绝
    success4 = await test_empty_mapping_rules_rejection()
    
    if success1 and success2 and success3 and success4:
        print("\n🎉 所有测试通过！")
        print("📋 验证内容:")
        print("   ✅ 新的 dict_mappers 格式正常工作")
        print("   ✅ 旧的 mapping_rules 格式被正确拒绝")
        print("   ✅ 空的 dict_mappers 配置被拒绝")
        print("   ✅ 空的 mapping_rules 被拒绝")
        print("   ✅ 完全移除了向后兼容性")
    else:
        print("\n❌ 部分测试失败")
        if not success1:
            print("   ❌ 新格式支持测试失败")
        if not success2:
            print("   ❌ 旧格式拒绝测试失败")
        if not success3:
            print("   ❌ 空配置拒绝测试失败")
        if not success4:
            print("   ❌ 空规则拒绝测试失败")


if __name__ == "__main__":
    asyncio.run(main())
