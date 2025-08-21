#!/usr/bin/env python3
"""
优化后的数据库服务测试脚本

测试 DatabaseService 的各项功能
"""

import asyncio
import sys
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from app.services.database_service import database_service


async def test_database_service():
    """测试数据库服务"""
    print("=" * 60)
    print("测试优化后的 DatabaseService")
    print("=" * 60)
    
    try:
        # 1. 测试连接信息
        print("\n1. 获取连接信息:")
        print("-" * 30)
        connection_info = database_service.get_connection_info()
        print(f"状态: {connection_info.get('status', 'unknown')}")
        if connection_info.get('status') != 'not_initialized':
            print(f"数据库驱动: {connection_info.get('driver', 'unknown')}")
            print(f"连接URL: {connection_info.get('url', 'unknown')}")
            print(f"已初始化: {connection_info.get('initialized', False)}")
        
        # 2. 测试数据库初始化
        print("\n2. 初始化数据库:")
        print("-" * 30)
        await database_service.init_db()
        print("✅ 数据库初始化成功")
        
        # 3. 测试健康检查
        print("\n3. 数据库健康检查:")
        print("-" * 30)
        health_result = await database_service.health_check()
        print(f"状态: {health_result['status']}")
        print(f"数据库: {health_result['database']}")
        print(f"已初始化: {health_result['initialized']}")
        
        if health_result['status'] == 'unhealthy':
            print(f"错误: {health_result.get('error', 'unknown')}")
        
        # 4. 测试会话获取
        print("\n4. 测试数据库会话:")
        print("-" * 30)
        try:
            async with database_service.get_session() as session:
                result = await session.execute("SELECT 1 as test_value")
                row = result.fetchone()
                print(f"✅ 会话测试成功，查询结果: {row[0] if row else 'None'}")
        except Exception as e:
            print(f"❌ 会话测试失败: {e}")
        
        # 5. 测试依赖注入会话
        print("\n5. 测试依赖注入会话:")
        print("-" * 30)
        try:
            async for session in database_service.get_session_dependency():
                result = await session.execute("SELECT 'dependency_test' as test_value")
                row = result.fetchone()
                print(f"✅ 依赖注入会话测试成功，查询结果: {row[0] if row else 'None'}")
                break  # 只测试一次
        except Exception as e:
            print(f"❌ 依赖注入会话测试失败: {e}")
        
        # 6. 测试原生SQL执行
        print("\n6. 测试原生SQL执行:")
        print("-" * 30)
        try:
            result = await database_service.execute_raw_sql("SELECT 'raw_sql_test' as test_value")
            row = result.fetchone()
            print(f"✅ 原生SQL执行成功，查询结果: {row[0] if row else 'None'}")
        except Exception as e:
            print(f"❌ 原生SQL执行失败: {e}")
        
        # 7. 更新后的连接信息
        print("\n7. 更新后的连接信息:")
        print("-" * 30)
        updated_info = database_service.get_connection_info()
        print(f"数据库驱动: {updated_info.get('driver', 'unknown')}")
        print(f"连接URL: {updated_info.get('url', 'unknown')}")
        print(f"连接池大小: {updated_info.get('pool_size', 'N/A')}")
        print(f"已签出连接: {updated_info.get('checked_out', 'N/A')}")
        print(f"溢出连接: {updated_info.get('overflow', 'N/A')}")
        print(f"已初始化: {updated_info.get('initialized', False)}")
        
        print("\n" + "=" * 60)
        print("🎉 数据库服务测试完成！")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"数据库服务测试失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        await database_service.close()
        print("\n🧹 数据库连接已关闭")


def test_service_structure():
    """测试服务结构"""
    print("\n" + "=" * 60)
    print("测试 DatabaseService 结构")
    print("=" * 60)
    
    # 检查公共方法
    public_methods = [method for method in dir(database_service) if not method.startswith('_')]
    print("\n公共方法:")
    for method in sorted(public_methods):
        print(f"  - {method}")
    
    # 检查私有方法
    private_methods = [method for method in dir(database_service) if method.startswith('_') and not method.startswith('__')]
    print("\n私有方法:")
    for method in sorted(private_methods):
        print(f"  - {method}")
    
    # 检查属性
    properties = []
    for attr_name in dir(type(database_service)):
        attr = getattr(type(database_service), attr_name)
        if isinstance(attr, property):
            properties.append(attr_name)
    
    if properties:
        print("\n属性:")
        for prop in sorted(properties):
            print(f"  - {prop}")
    
    print("\n✅ DatabaseService 结构检查完成")


async def main():
    """主函数"""
    print("优化后的数据库服务测试")
    print("测试各项功能和性能改进")
    
    # 测试服务结构
    test_service_structure()
    
    # 测试服务功能
    await test_database_service()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行测试
    asyncio.run(main())
