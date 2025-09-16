#!/usr/bin/env python3
"""
创建告警表的脚本
"""

import asyncio
import aiomysql
from sqlalchemy import text
import os
import sys

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(__file__))

from app.services.database_service import database_service


async def create_alerts_table():
    """创建告警表和测试数据"""
    try:
        # 读取SQL脚本
        with open('sql/create_alerts_table.sql', 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # 分割SQL语句（按分号分割，忽略空行和注释）
        sql_statements = []
        for statement in sql_content.split(';'):
            statement = statement.strip()
            if statement and not statement.startswith('--'):
                sql_statements.append(statement)
        
        print("🔄 正在连接数据库...")
        async with database_service.get_session() as session:
            print("✅ 数据库连接成功")
            
            # 执行每个SQL语句
            for i, sql_statement in enumerate(sql_statements):
                if sql_statement.strip():
                    try:
                        print(f"🔄 执行SQL语句 {i+1}/{len(sql_statements)}...")
                        await session.execute(text(sql_statement))
                        print(f"✅ SQL语句 {i+1} 执行成功")
                    except Exception as e:
                        # 如果是表已存在错误，跳过
                        if "Table 'alerts' already exists" in str(e):
                            print(f"⚠️ SQL语句 {i+1}: 表已存在，跳过创建")
                        else:
                            print(f"❌ SQL语句 {i+1} 执行失败: {e}")
                            raise
            
            # 提交事务
            await session.commit()
            print("✅ 所有SQL语句执行完成，事务已提交")
        
        # 验证表是否创建成功
        print("🔄 验证表创建...")
        async with database_service.get_session() as session:
            result = await session.execute(text("SHOW TABLES LIKE 'alerts'"))
            tables = result.fetchall()
            
            if tables:
                print("✅ 告警表创建成功!")
                
                # 查询测试数据
                result = await session.execute(text("SELECT COUNT(*) as count FROM alerts"))
                count = result.fetchone()
                print(f"📊 表中已有 {count[0]} 条测试数据")
                
                # 显示表结构
                result = await session.execute(text("DESCRIBE alerts"))
                columns = result.fetchall()
                print("📋 表结构:")
                for column in columns:
                    print(f"  - {column[0]} ({column[1]}) {'NOT NULL' if column[2] == 'NO' else 'NULL'}")
            else:
                print("❌ 告警表创建失败!")
                
    except Exception as e:
        print(f"❌ 创建告警表过程中发生错误: {e}")
        raise


if __name__ == "__main__":
    print("🚀 开始创建告警表...")
    asyncio.run(create_alerts_table())
    print("🎉 告警表创建完成!")