#!/usr/bin/env python3
"""
服务类测试脚本

测试 PipelineConfigService 和 FileUploadService 的功能
"""

import asyncio
import tempfile
import json
from pathlib import Path
from loguru import logger

# 模拟测试 FileUploadService
def test_file_upload_service():
    """测试文件上传服务"""
    print("=" * 50)
    print("测试 FileUploadService")
    print("=" * 50)
    
    from app.services.file_upload_service import FileUploadService
    
    # 创建服务实例
    service = FileUploadService(upload_dir="test_uploads")
    
    # 测试获取配置信息
    print("1. 获取配置信息:")
    config = service.get_upload_info()
    print(json.dumps(config, indent=2, ensure_ascii=False))
    
    # 测试生成唯一文件名
    print("\n2. 生成唯一文件名:")
    unique_name = service._generate_unique_filename("test_config.json")
    print(f"原文件名: test_config.json")
    print(f"唯一文件名: {unique_name}")
    
    # 测试文件验证
    print("\n3. 文件类型验证:")
    class MockFile:
        def __init__(self, filename, size=1024):
            self.filename = filename
            self.size = size
    
    try:
        service._validate_file(MockFile("test.json", 1024))
        print("✅ JSON文件验证通过")
    except Exception as e:
        print(f"❌ JSON文件验证失败: {e}")
    
    try:
        service._validate_file(MockFile("test.exe", 1024))
        print("✅ EXE文件验证通过")
    except Exception as e:
        print(f"❌ EXE文件验证失败: {e}")
    
    # 测试列出文件
    print("\n4. 列出文件:")
    try:
        files = service.list_files()
        print(f"找到 {len(files)} 个文件")
        for file_info in files[:3]:  # 只显示前3个
            print(f"  - {file_info['file_name']} ({file_info['file_size']} bytes)")
    except Exception as e:
        print(f"列出文件失败: {e}")
    
    print("\n✅ FileUploadService 测试完成")


def test_pipeline_config_service_structure():
    """测试管道配置服务结构"""
    print("\n" + "=" * 50)
    print("测试 PipelineConfigService 结构")
    print("=" * 50)
    
    from app.services.pipeline_config_service import PipelineConfigService
    
    # 检查类方法
    methods = [method for method in dir(PipelineConfigService) if not method.startswith('_')]
    print("公共方法:")
    for method in methods:
        print(f"  - {method}")
    
    # 检查私有方法
    private_methods = [method for method in dir(PipelineConfigService) if method.startswith('_') and not method.startswith('__')]
    print("\n私有方法:")
    for method in private_methods:
        print(f"  - {method}")
    
    print("\n✅ PipelineConfigService 结构检查完成")


def create_test_pipeline_config():
    """创建测试管道配置"""
    return {
        "pipeline_name": "test_pipeline",
        "description": "测试管道配置",
        "components": [
            {
                "name": "测试事件监控器",
                "type": "event_monitor",
                "chain_name": "ethereum",
                "contract_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                "abi_path": "abis/erc20.json",
                "events_to_monitor": ["Transfer"]
            },
            {
                "name": "测试合约调用器",
                "type": "contract_caller",
                "chain_name": "ethereum",
                "abi_path": "abis/erc20.json",
                "contract_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                "method_name": "symbol",
                "method_params": []
            },
            {
                "name": "测试字典映射器",
                "type": "dict_mapper",
                "mapping_rules": [
                    {
                        "source_key": "event_name",
                        "target_key": "event_type",
                        "transformer": "to_string"
                    }
                ]
            },
            {
                "name": "测试Kafka生产者",
                "type": "kafka_producer",
                "bootstrap_servers": "localhost:9092",
                "topic": "test-topic"
            }
        ]
    }


def test_json_parsing():
    """测试JSON解析"""
    print("\n" + "=" * 50)
    print("测试 JSON 解析")
    print("=" * 50)
    
    # 创建测试配置
    config = create_test_pipeline_config()
    
    # 转换为JSON字符串
    json_str = json.dumps(config, ensure_ascii=False)
    print(f"JSON字符串长度: {len(json_str)} 字符")
    
    # 解析JSON
    try:
        parsed_config = json.loads(json_str)
        print("✅ JSON解析成功")
        print(f"管道名称: {parsed_config['pipeline_name']}")
        print(f"组件数量: {len(parsed_config['components'])}")
        
        # 显示组件信息
        for i, component in enumerate(parsed_config['components'], 1):
            print(f"  组件 {i}: {component['name']} ({component['type']})")
        
    except Exception as e:
        print(f"❌ JSON解析失败: {e}")
    
    print("\n✅ JSON解析测试完成")


def test_file_operations():
    """测试文件操作"""
    print("\n" + "=" * 50)
    print("测试文件操作")
    print("=" * 50)
    
    from app.services.file_upload_service import FileUploadService
    
    # 创建临时目录
    with tempfile.TemporaryDirectory() as temp_dir:
        service = FileUploadService(upload_dir=temp_dir)
        
        # 创建测试文件
        test_file = Path(temp_dir) / "test.json"
        test_data = {"test": "data", "timestamp": "2024-01-15"}
        
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)
        
        print(f"创建测试文件: {test_file}")
        
        # 测试获取文件信息
        try:
            file_info = service.get_file_info(str(test_file))
            print("✅ 获取文件信息成功:")
            print(f"  文件名: {file_info['file_name']}")
            print(f"  文件大小: {file_info['file_size']} bytes")
            print(f"  文件扩展名: {file_info['file_extension']}")
        except Exception as e:
            print(f"❌ 获取文件信息失败: {e}")
        
        # 测试列出文件
        try:
            files = service.list_files(temp_dir)
            print(f"✅ 列出文件成功，找到 {len(files)} 个文件")
        except Exception as e:
            print(f"❌ 列出文件失败: {e}")
    
    print("\n✅ 文件操作测试完成")


def main():
    """主函数"""
    print("服务类功能测试")
    print("测试 PipelineConfigService 和 FileUploadService")
    
    try:
        # 测试文件上传服务
        test_file_upload_service()
        
        # 测试管道配置服务结构
        test_pipeline_config_service_structure()
        
        # 测试JSON解析
        test_json_parsing()
        
        # 测试文件操作
        test_file_operations()
        
        print("\n" + "=" * 50)
        print("🎉 所有测试完成！")
        print("=" * 50)
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    main()
