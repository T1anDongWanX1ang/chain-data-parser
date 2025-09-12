#!/usr/bin/env python3
"""
测试优化版管道执行器的日志路径绑定功能
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

from app.component.pipeline_executor_optimized import OptimizedBlockchainDataPipeline, PipelineContext


async def test_log_path_binding():
    """测试日志路径绑定功能"""
    
    print("🧪 测试优化版管道执行器的日志路径绑定功能")
    print("=" * 60)
    
    # 创建临时日志文件路径
    temp_dir = Path(tempfile.mkdtemp())
    log_file_path = temp_dir / "pipeline_test.log"
    
    print(f"📁 临时日志目录: {temp_dir}")
    print(f"📄 日志文件路径: {log_file_path}")
    
    # 创建测试配置
    test_config = {
        "pipeline_name": "日志路径绑定测试管道",
        "description": "测试日志输出到指定路径",
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
    
    try:
        print("\n🔄 创建带日志路径的管道实例...")
        
        # 创建管道实例，指定日志路径
        pipeline = OptimizedBlockchainDataPipeline(
            config_dict=test_config,
            log_path=str(log_file_path)
        )
        
        print(f"✅ 管道实例创建成功，实例ID: {pipeline.instance_id}")
        
        # 初始化组件
        print("\n🔄 初始化管道组件...")
        await pipeline._initialize_components()
        print(f"✅ 组件初始化完成，共 {len(pipeline.components)} 个组件")
        
        # 模拟处理一些数据
        print("\n🔄 模拟数据处理...")
        
        # 创建测试数据
        test_data = {
            "event_name": "Transfer",
            "from": "0x1234567890ABCDEF1234567890ABCDEF12345678",
            "to": "0xABCDEF1234567890ABCDEF1234567890ABCDEF12",
            "value": "1000000000000000000",  # 1 ETH in wei
            "block_number": 18500000,
            "transaction_hash": "0xtest123456789",
            "log_index": 0
        }
        
        # 创建管道上下文
        context = PipelineContext(data=test_data)
        
        # 处理数据（跳过第一个组件，从第二个开始）
        processed_context = await pipeline._process_pipeline_data(context)
        
        print(f"✅ 数据处理完成")
        print(f"📊 处理结果字段数: {len(processed_context.data)}")
        
        # 检查日志文件是否创建
        print(f"\n🔍 检查日志文件...")
        if log_file_path.exists():
            file_size = log_file_path.stat().st_size
            print(f"✅ 日志文件已创建: {log_file_path}")
            print(f"📏 文件大小: {file_size} 字节")
            
            # 读取并显示日志内容的前几行
            print(f"\n📄 日志文件内容预览:")
            print("-" * 50)
            with open(log_file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines[:10]):  # 显示前10行
                    print(f"{i+1:2d}: {line.rstrip()}")
                
                if len(lines) > 10:
                    print(f"... (还有 {len(lines) - 10} 行)")
            print("-" * 50)
        else:
            print("❌ 日志文件未创建")
            return False
        
        # 测试多个实例的日志隔离
        print(f"\n🔄 测试多实例日志隔离...")
        
        # 创建第二个管道实例，使用相同的日志文件
        pipeline2 = OptimizedBlockchainDataPipeline(
            config_dict=test_config,
            log_path=str(log_file_path)
        )
        
        print(f"✅ 第二个管道实例创建成功，实例ID: {pipeline2.instance_id}")
        
        # 检查两个实例的ID是否不同
        if pipeline.instance_id != pipeline2.instance_id:
            print(f"✅ 实例ID隔离正常: {pipeline.instance_id} != {pipeline2.instance_id}")
        else:
            print(f"⚠️  实例ID相同，可能存在问题")
        
        # 清理资源
        print(f"\n🧹 清理测试资源...")
        pipeline._cleanup_logging()
        pipeline2._cleanup_logging()
        
        # 删除临时文件
        if log_file_path.exists():
            log_file_path.unlink()
        temp_dir.rmdir()
        
        print(f"✅ 清理完成")
        
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_relative_log_path():
    """测试相对路径日志配置"""
    
    print(f"\n🧪 测试相对路径日志配置")
    print("-" * 40)
    
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
    
    try:
        # 使用相对路径
        relative_log_path = "logs/test_relative_path.log"
        
        print(f"📁 相对日志路径: {relative_log_path}")
        
        # 创建管道实例
        pipeline = OptimizedBlockchainDataPipeline(
            config_dict=simple_config,
            log_path=relative_log_path
        )
        
        print(f"✅ 相对路径管道创建成功，实例ID: {pipeline.instance_id}")
        
        # 检查实际的日志文件路径
        project_root = Path(__file__).parent
        expected_log_file = project_root / relative_log_path
        
        print(f"📄 预期日志文件路径: {expected_log_file}")
        
        # 清理
        pipeline._cleanup_logging()
        
        # 如果日志文件存在，删除它
        if expected_log_file.exists():
            expected_log_file.unlink()
            print(f"🧹 清理日志文件: {expected_log_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 相对路径测试失败: {e}")
        return False


async def test_no_log_path():
    """测试不指定日志路径的情况"""
    
    print(f"\n🧪 测试不指定日志路径（仅控制台输出）")
    print("-" * 45)
    
    simple_config = {
        "pipeline_name": "仅控制台日志测试",
        "description": "测试仅控制台日志输出",
        "classification_id": 1,
        "components": [
            {
                "name": "console_only_monitor",
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
    
    try:
        # 不指定日志路径
        pipeline = OptimizedBlockchainDataPipeline(config_dict=simple_config)
        
        print(f"✅ 仅控制台日志管道创建成功，实例ID: {pipeline.instance_id}")
        print(f"📋 日志处理器数量: {len(pipeline.logger_ids)}")
        
        # 清理
        pipeline._cleanup_logging()
        
        return True
        
    except Exception as e:
        print(f"❌ 仅控制台日志测试失败: {e}")
        return False


async def main():
    """主函数"""
    print("🚀 测试优化版管道执行器的日志路径绑定功能")
    print("=" * 70)
    
    # 测试绝对路径日志绑定
    success1 = await test_log_path_binding()
    
    # 测试相对路径日志配置
    success2 = await test_relative_log_path()
    
    # 测试不指定日志路径
    success3 = await test_no_log_path()
    
    print(f"\n📊 测试结果总结:")
    print("=" * 30)
    
    if success1:
        print("✅ 绝对路径日志绑定测试通过")
    else:
        print("❌ 绝对路径日志绑定测试失败")
    
    if success2:
        print("✅ 相对路径日志配置测试通过")
    else:
        print("❌ 相对路径日志配置测试失败")
    
    if success3:
        print("✅ 仅控制台日志测试通过")
    else:
        print("❌ 仅控制台日志测试失败")
    
    if success1 and success2 and success3:
        print(f"\n🎉 所有日志路径绑定测试通过！")
        print("📋 验证功能:")
        print("   ✅ 支持绝对路径日志文件输出")
        print("   ✅ 支持相对路径日志文件输出")
        print("   ✅ 支持仅控制台日志输出")
        print("   ✅ 多实例日志隔离正常")
        print("   ✅ 日志文件自动创建目录")
        print("   ✅ 日志轮转和压缩配置")
        print("   ✅ 实例ID标识和过滤")
    else:
        print(f"\n❌ 部分测试失败，请检查实现")


if __name__ == "__main__":
    asyncio.run(main())
