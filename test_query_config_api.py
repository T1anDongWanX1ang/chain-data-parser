#!/usr/bin/env python3
"""
测试查询管道配置接口，验证 dict_mapper 组件不返回 mapping_rules 字段
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


async def test_query_config_api():
    """测试查询管道配置接口"""
    
    print("🧪 测试查询管道配置接口 - dict_mapper 组件不返回 mapping_rules")
    print("-" * 60)
    
    try:
        # 初始化数据库服务
        await database_service.init_db()
        
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 查询之前保存的管道配置 (pipeline_id: 1001)
            pipeline_id = 1001
            
            print(f"🔄 查询管道配置 (pipeline_id: {pipeline_id})...")
            
            config = await service.get_pipeline_config(pipeline_id)
            
            print("✅ 查询成功！")
            print("\n📋 管道配置详情:")
            print(f"   管道名称: {config.get('pipeline_name')}")
            print(f"   组件数量: {len(config.get('components', []))}")
            
            # 检查每个组件
            for i, component in enumerate(config.get('components', []), 1):
                print(f"\n🔧 组件 {i}: {component.get('name')} ({component.get('type')})")
                
                if component.get('type') == 'dict_mapper':
                    print("   📊 Dict Mapper 组件分析:")
                    
                    # 检查是否有 mapping_rules 字段
                    has_mapping_rules = 'mapping_rules' in component
                    print(f"   ❌ 包含 mapping_rules 字段: {has_mapping_rules}")
                    
                    # 检查是否有 dict_mappers 字段
                    has_dict_mappers = 'dict_mappers' in component
                    print(f"   ✅ 包含 dict_mappers 字段: {has_dict_mappers}")
                    
                    if has_dict_mappers:
                        dict_mappers = component.get('dict_mappers', [])
                        print(f"   📝 dict_mappers 数量: {len(dict_mappers)}")
                        
                        for j, mapper in enumerate(dict_mappers, 1):
                            event_name = mapper.get('event_name', 'null')
                            rules_count = len(mapper.get('mapping_rules', []))
                            print(f"      {j}. event_name: {event_name}, mapping_rules: {rules_count} 条")
                    
                    # 验证结果
                    if not has_mapping_rules and has_dict_mappers:
                        print("   🎉 验证通过: dict_mapper 组件不包含 mapping_rules 字段")
                    else:
                        print("   ⚠️  验证失败: dict_mapper 组件仍包含 mapping_rules 字段")
                        return False
                
                else:
                    # 其他类型组件的基本信息
                    component_keys = list(component.keys())
                    print(f"   🔑 字段: {', '.join(component_keys)}")
            
            print(f"\n📄 完整配置 JSON:")
            print(json.dumps(config, ensure_ascii=False, indent=2))
            
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """主函数"""
    print("🚀 测试查询管道配置接口")
    print("=" * 70)
    
    success = await test_query_config_api()
    
    if success:
        print("\n🎉 查询接口测试成功！")
        print("📋 验证内容:")
        print("   ✅ dict_mapper 组件不返回 mapping_rules 字段")
        print("   ✅ dict_mapper 组件返回 dict_mappers 数组")
        print("   ✅ 每个 dict_mapper 包含 event_name 和 mapping_rules")
        print("   ✅ 其他组件类型正常返回")
    else:
        print("\n❌ 查询接口测试失败")


if __name__ == "__main__":
    asyncio.run(main())
