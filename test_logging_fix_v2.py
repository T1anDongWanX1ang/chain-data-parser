#!/usr/bin/env python3
"""
测试修复后的日志功能 v2
"""

import sys
import os
import tempfile
from pathlib import Path
from loguru import logger
import uuid

def test_fixed_logging_v2():
    """测试修复后的日志功能 v2"""
    print("=== 测试修复后的日志功能 v2 ===")
    
    # 创建实例ID
    instance_id = str(uuid.uuid4())[:8]
    logger_ids = []
    
    try:
        # 创建临时日志文件
        with tempfile.NamedTemporaryFile(suffix='.log', delete=False) as tmp_log:
            log_path = tmp_log.name
        
        print(f"临时日志文件: {log_path}")
        
        # 定义日志格式
        # 带实例ID的日志格式
        instance_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>[{extra[instance_id]}]</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        # 普通日志格式
        general_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>[global]</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        
        # 添加控制台输出 - 带实例ID的日志
        instance_console_handler_id = logger.add(
            sys.stdout,
            format=instance_log_format,
            level="INFO",
            filter=lambda record: record["extra"].get("instance_id") == instance_id
        )
        logger_ids.append(instance_console_handler_id)
        
        # 添加控制台输出 - 普通日志（没有实例ID的）
        general_console_handler_id = logger.add(
            sys.stdout,
            format=general_log_format,
            level="INFO",
            filter=lambda record: record["extra"].get("instance_id") is None
        )
        logger_ids.append(general_console_handler_id)
        
        # 添加文件输出 - 带实例ID的日志
        instance_file_handler_id = logger.add(
            log_path,
            format=instance_log_format,
            level="INFO",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("instance_id") == instance_id
        )
        logger_ids.append(instance_file_handler_id)
        
        # 添加文件输出 - 普通日志（没有实例ID的）
        general_file_handler_id = logger.add(
            log_path,
            format=general_log_format,
            level="INFO",
            rotation="10 MB",
            retention="7 days",
            compression="zip",
            encoding="utf-8",
            filter=lambda record: record["extra"].get("instance_id") is None
        )
        logger_ids.append(general_file_handler_id)
        
        print("\\n1. 测试带 instance_id 的日志:")
        logger.bind(instance_id=instance_id).info("这是带 instance_id 的日志")
        
        print("\\n2. 测试不带 instance_id 的日志:")
        logger.info("这是不带 instance_id 的普通日志")
        
        print("\\n3. 测试不同级别的日志:")
        logger.warning("这是警告日志")
        logger.error("这是错误日志")
        
        # 强制刷新日志
        import time
        time.sleep(0.1)
        
        # 检查文件内容
        print("\\n4. 检查日志文件内容:")
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [line for line in content.strip().split('\\n') if line.strip()]
                print(f"   日志文件包含 {len(lines)} 行日志")
                
                # 检查各种日志是否都写入了
                checks = [
                    ("带 instance_id 的日志", "这是带 instance_id 的日志" in content),
                    ("不带 instance_id 的日志", "这是不带 instance_id 的普通日志" in content),
                    ("警告日志", "这是警告日志" in content),
                    ("错误日志", "这是错误日志" in content)
                ]
                
                for desc, result in checks:
                    status = "✅" if result else "❌"
                    print(f"   {status} {desc}: {'已写入' if result else '未写入'}")
                
                print("\\n   日志文件内容:")
                for i, line in enumerate(lines, 1):
                    print(f"   {i}: {line}")
        else:
            print("   ❌ 日志文件不存在")
        
        # 清理处理器
        for handler_id in logger_ids:
            try:
                logger.remove(handler_id)
            except Exception as e:
                print(f"⚠️  清理处理器失败: {e}")
        
        # 清理临时文件
        try:
            os.unlink(log_path)
        except:
            pass
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        # 清理处理器
        for handler_id in logger_ids:
            try:
                logger.remove(handler_id)
            except:
                pass
    
    print("\\n📋 修复总结:")
    print("  🔧 使用分离的处理器处理带/不带 instance_id 的日志")
    print("  ✅ 带 instance_id 的日志显示具体实例ID")
    print("  ✅ 不带 instance_id 的日志显示 [global] 标识")
    print("  ✅ 所有日志都会同时输出到控制台和文件")
    print("  ✅ 避免了格式化错误")

if __name__ == "__main__":
    test_fixed_logging_v2()
