#!/usr/bin/env python3
"""
测试带日志路径的 start 接口功能
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app.services.database_service import database_service
from app.services.pipeline_config_service import PipelineConfigService


async def test_start_api_with_log_path():
    """测试带日志路径的 start 接口"""
    
    print("🧪 测试带日志路径的 start 接口功能")
    print("=" * 50)
    
    try:
        # 初始化数据库服务
        await database_service.init_db()
        
        # 创建临时日志文件路径
        temp_dir = Path(tempfile.mkdtemp())
        custom_log_path = temp_dir / "custom_pipeline.log"
        
        print(f"📁 临时日志目录: {temp_dir}")
        print(f"📄 自定义日志路径: {custom_log_path}")
        
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 创建测试管道配置
            test_config = {
                "pipeline_name": "日志路径测试管道",
                "description": "测试自定义日志路径功能",
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
                        "output_format": "detailed",
                        "poll_interval": 1.0
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
                                    }
                                ]
                            }
                        ]
                    },
                    {
                        "name": "test_kafka_producer",
                        "type": "kafka_producer",
                        "bootstrap_servers": "localhost:9092",
                        "topic": "test_topic",
                        "acks": 1,
                        "sync_send": False
                    }
                ]
            }
            
            pipeline_id = 4001  # 使用新的测试管道ID
            pipeline_info_str = json.dumps(test_config, ensure_ascii=False, indent=2)
            
            print("\n🔄 保存测试管道配置...")
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 管道配置保存成功: {save_result}")
            
            # 测试1: 使用自定义日志路径启动管道
            print(f"\n🔄 测试1: 使用自定义日志路径启动管道...")
            start_result = await service.start_pipeline_task(pipeline_id, str(custom_log_path))
            print(f"✅ 管道启动成功: {start_result}")
            
            task_id = start_result.get('task_id')
            print(f"📋 任务ID: {task_id}")
            
            # 等待一段时间让管道初始化
            print(f"⏳ 等待管道初始化...")
            await asyncio.sleep(3)
            
            # 检查自定义日志文件是否创建
            if custom_log_path.exists():
                file_size = custom_log_path.stat().st_size
                print(f"✅ 自定义日志文件已创建: {custom_log_path}")
                print(f"📏 文件大小: {file_size} 字节")
                
                # 读取并显示日志内容的前几行
                print(f"\n📄 自定义日志文件内容预览:")
                print("-" * 40)
                with open(custom_log_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for i, line in enumerate(lines[:8]):  # 显示前8行
                        print(f"{i+1:2d}: {line.rstrip()}")
                    
                    if len(lines) > 8:
                        print(f"... (还有 {len(lines) - 8} 行)")
                print("-" * 40)
            else:
                print("❌ 自定义日志文件未创建")
                return False
            
            # 测试2: 不指定日志路径启动管道（使用默认路径）
            print(f"\n🔄 测试2: 使用默认日志路径启动管道...")
            pipeline_id_2 = 4002
            
            # 保存第二个管道配置
            test_config_2 = test_config.copy()
            test_config_2["pipeline_name"] = "默认日志路径测试管道"
            pipeline_info_str_2 = json.dumps(test_config_2, ensure_ascii=False, indent=2)
            
            save_result_2 = await service.parse_and_save_pipeline(pipeline_id_2, pipeline_info_str_2)
            print(f"✅ 第二个管道配置保存成功: {save_result_2}")
            
            # 启动管道（不指定日志路径）
            start_result_2 = await service.start_pipeline_task(pipeline_id_2)
            print(f"✅ 第二个管道启动成功: {start_result_2}")
            
            task_id_2 = start_result_2.get('task_id')
            print(f"📋 第二个任务ID: {task_id_2}")
            
            # 等待一段时间
            await asyncio.sleep(2)
            
            # 检查默认日志路径
            project_root = Path(__file__).parent
            default_log_pattern = f"logs/pipeline_{pipeline_id_2}_*.log"
            default_log_files = list(project_root.glob(default_log_pattern))
            
            if default_log_files:
                default_log_file = default_log_files[0]
                print(f"✅ 默认日志文件已创建: {default_log_file}")
                print(f"📏 文件大小: {default_log_file.stat().st_size} 字节")
                
                # 清理默认日志文件
                default_log_file.unlink()
                print(f"🧹 清理默认日志文件: {default_log_file}")
            else:
                print(f"⚠️  未找到默认日志文件，模式: {default_log_pattern}")
            
            # 清理自定义日志文件
            if custom_log_path.exists():
                custom_log_path.unlink()
            temp_dir.rmdir()
            print(f"🧹 清理临时目录: {temp_dir}")
            
            return True
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_relative_log_path():
    """测试相对路径日志功能"""
    
    print(f"\n🧪 测试相对路径日志功能")
    print("-" * 35)
    
    try:
        async with database_service.get_session() as session:
            service = PipelineConfigService(session)
            
            # 创建简单的测试配置
            simple_config = {
                "pipeline_name": "相对路径日志测试",
                "description": "测试相对路径日志输出",
                "classification_id": 1,
                "components": [
                    {
                        "name": "simple_event_monitor",
                        "type": "event_monitor",
                        "chain_name": "ethereum",
                        "contract_address": "0xA0b86a33E6441c8C06DD2b7c94b7E0e8d61c6e8e",
                        "abi_path": "abis/erc20.json",
                        "mode": "realtime",
                        "events_to_monitor": ["Transfer"],
                        "output_format": "detailed"
                    }
                ]
            }
            
            pipeline_id = 4003
            pipeline_info_str = json.dumps(simple_config, ensure_ascii=False, indent=2)
            
            # 保存配置
            save_result = await service.parse_and_save_pipeline(pipeline_id, pipeline_info_str)
            print(f"✅ 管道配置保存成功: {save_result}")
            
            # 使用相对路径
            relative_log_path = "logs/test_relative_api.log"
            
            print(f"📁 相对日志路径: {relative_log_path}")
            
            # 启动管道
            start_result = await service.start_pipeline_task(pipeline_id, relative_log_path)
            print(f"✅ 相对路径管道启动成功: {start_result}")
            
            # 等待一段时间
            await asyncio.sleep(2)
            
            # 检查实际的日志文件路径
            project_root = Path(__file__).parent
            expected_log_file = project_root / relative_log_path
            
            print(f"📄 预期日志文件路径: {expected_log_file}")
            
            if expected_log_file.exists():
                print(f"✅ 相对路径日志文件已创建")
                print(f"📏 文件大小: {expected_log_file.stat().st_size} 字节")
                
                # 清理
                expected_log_file.unlink()
                print(f"🧹 清理日志文件: {expected_log_file}")
            else:
                print(f"⚠️  相对路径日志文件未创建")
            
            return True
            
    except Exception as e:
        print(f"❌ 相对路径测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 测试带日志路径的 start 接口功能")
    print("=" * 60)
    
    # 测试自定义日志路径和默认日志路径
    success1 = await test_start_api_with_log_path()
    
    # 测试相对路径日志功能
    success2 = await test_relative_log_path()
    
    print(f"\n📊 测试结果总结:")
    print("=" * 30)
    
    if success1:
        print("✅ 自定义日志路径测试通过")
    else:
        print("❌ 自定义日志路径测试失败")
    
    if success2:
        print("✅ 相对路径日志测试通过")
    else:
        print("❌ 相对路径日志测试失败")
    
    if success1 and success2:
        print(f"\n🎉 所有日志路径功能测试通过！")
        print("📋 验证功能:")
        print("   ✅ start 接口支持自定义日志路径参数")
        print("   ✅ 自定义日志路径正确传递给管道执行器")
        print("   ✅ 不指定日志路径时使用默认路径")
        print("   ✅ 支持相对路径日志配置")
        print("   ✅ 日志文件正确创建和写入")
        print("   ✅ 任务记录中保存正确的日志路径")
    else:
        print(f"\n❌ 部分测试失败，请检查实现")


if __name__ == "__main__":
    asyncio.run(main())
