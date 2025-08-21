#!/usr/bin/env python3
"""
区块链数据管道演示脚本

这个脚本演示了如何使用JSON配置文件和组件生成可执行的数据处理管道
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.component.pipeline_executor import BlockchainDataPipeline


def create_demo_config():
    """创建演示配置"""
    demo_config = {
        "pipeline_name": "演示数据管道",
        "version": "1.0.0",
        "description": "演示如何通过JSON配置生成可执行管道",
        "components": {
            "step1_event_monitor": {
                "name": "步骤1: 事件监控",
                "enabled": True,
                "type": "event_monitor",
                "config": {
                    "chain_name": "ethereum",
                    "contract_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                    "abi_path": "../abis/erc20.json",
                    "events_to_monitor": ["Transfer"],
                    "mode": "realtime",
                    "poll_interval": 1.0,
                    "output_format": "detailed"
                }
            },
            "step2_get_token_name": {
                "name": "步骤2: 获取代币名称",
                "enabled": True,
                "type": "contract_caller",
                "config": {
                    "chain_name": "ethereum",
                    "contract_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                    "abi_path": "../abis/erc20.json",
                    "method_name": "name",
                    "method_params": []
                }
            },
            "step3_get_balance": {
                "name": "步骤3: 获取接收者余额",
                "enabled": True,
                "type": "contract_caller",
                "config": {
                    "chain_name": "ethereum",
                    "contract_address": "0x742d35Cc6634C0532925a3b8D4C9db96C4b4d8b6",
                    "abi_path": "../abis/erc20.json",
                    "method_name": "balanceOf",
                    "method_params": ["event_args.to"]
                }
            },
            "step4_data_transform": {
                "name": "步骤4: 数据转换",
                "enabled": True,
                "type": "dict_mapper",
                "config": {
                    "mapping_rules": [
                        {
                            "source_key": "event_name",
                            "target_key": "交易类型",
                            "transformer": "to_string"
                        },
                        {
                            "source_key": "event_args.from",
                            "target_key": "发送地址",
                            "transformer": "to_lowercase"
                        },
                        {
                            "source_key": "event_args.to",
                            "target_key": "接收地址",
                            "transformer": "to_lowercase"
                        },
                        {
                            "source_key": "event_args.value",
                            "target_key": "转账金额",
                            "transformer": "to_string"
                        },
                        {
                            "source_key": "name",
                            "target_key": "代币名称",
                            "transformer": "to_string"
                        },
                        {
                            "source_key": "balanceOf",
                            "target_key": "接收者余额",
                            "transformer": "to_string"
                        }
                    ]
                }
            },
            "step5_send_to_kafka": {
                "name": "步骤5: 发送到Kafka",
                "enabled": True,
                "type": "kafka_producer",
                "config": {
                    "bootstrap_servers": "localhost:9092",
                    "topic": "demo-blockchain-events",
                    "acks": 1,
                    "retries": 3
                }
            }
        },
        "error_handling": {
            "retry_policy": {
                "max_retries": 2,
                "retry_delay": 1.0,
                "backoff_multiplier": 2.0
            }
        },
        "performance": {
            "caching": {
                "enabled": True,
                "cache_ttl": 300
            }
        }
    }
    
    return demo_config


def explain_pipeline_flow():
    """解释管道流程"""
    print("\n" + "=" * 80)
    print("📋 管道流程说明")
    print("=" * 80)
    print("这个演示管道将按以下步骤执行:")
    print("")
    print("1️⃣  事件监控器 → 监听区块链上的Transfer事件")
    print("   ↓ 输出: 事件数据(from, to, value等)")
    print("")
    print("2️⃣  合约调用器 → 调用name()方法获取代币名称")
    print("   ↓ 输出: 代币名称")
    print("")
    print("3️⃣  合约调用器 → 调用balanceOf()方法获取接收者余额")
    print("   ↓ 输入: 使用步骤1的'to'地址")
    print("   ↓ 输出: 接收者余额")
    print("")
    print("4️⃣  数据映射器 → 转换和重命名数据字段")
    print("   ↓ 输入: 前面所有步骤的数据")
    print("   ↓ 输出: 格式化的数据结构")
    print("")
    print("5️⃣  Kafka生产者 → 发送最终数据到消息队列")
    print("   ↓ 输入: 映射后的数据")
    print("   ↓ 输出: 发送确认")
    print("")
    print("🔄 数据流向: 事件 → 查询 → 映射 → 发送")
    print("=" * 80)


async def run_demo():
    """运行演示"""
    print("🚀 区块链数据管道演示")
    print("=" * 50)
    print("本演示展示如何通过JSON配置生成可执行的数据处理管道")
    
    # 解释流程
    explain_pipeline_flow()
    
    input("\n按Enter键开始演示...")
    
    # 创建演示配置
    print("\n📝 1. 创建JSON配置文件...")
    demo_config = create_demo_config()
    
    # 保存配置到临时文件
    config_file = Path("demo_config.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(demo_config, f, indent=2, ensure_ascii=False)
    
    print(f"   ✅ 配置文件已创建: {config_file}")
    print(f"   📊 配置了 {len(demo_config['components'])} 个组件")
    
    # 显示配置概要
    print("\n📋 2. 配置概要:")
    for name, comp in demo_config['components'].items():
        status = "🟢 启用" if comp['enabled'] else "🔴 禁用"
        print(f"   {status} {comp['name']} ({comp['type']})")
    
    input("\n按Enter键开始执行管道...")
    
    try:
        # 创建并执行管道
        print("\n⚙️  3. 初始化管道执行器...")
        pipeline = BlockchainDataPipeline(str(config_file))
        
        print("\n🔄 4. 执行数据处理管道...")
        result = await pipeline.execute_pipeline()
        
        # 显示结果
        print("\n📊 5. 执行结果分析:")
        pipeline.print_execution_summary(result)
        
        # 显示最终数据
        print("\n📦 6. 最终处理数据:")
        final_data = result.get('pipeline_data', {})
        
        print("   🔍 数据字段:")
        for key, value in final_data.items():
            if isinstance(value, dict):
                print(f"     {key}: (对象包含 {len(value)} 个字段)")
            else:
                value_str = str(value)[:50] + "..." if len(str(value)) > 50 else str(value)
                print(f"     {key}: {value_str}")
        
        # 保存演示结果
        output_file = Path("demo_result.json")
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 详细结果已保存到: {output_file}")
        
        print("\n🎉 演示完成！")
        print("\n" + "=" * 80)
        print("总结:")
        print("✅ 通过JSON配置文件定义了完整的数据处理流程")
        print("✅ 管道执行器自动解析配置并创建组件实例")
        print("✅ 组件按顺序执行，数据在组件间自动传递")
        print("✅ 生成了详细的执行报告和处理结果")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ 演示执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理临时文件
        if config_file.exists():
            config_file.unlink()
            print(f"\n🧹 已清理临时文件: {config_file}")


def show_file_structure():
    """显示文件结构"""
    print("\n📁 项目文件结构:")
    print("├── configs/")
    print("│   ├── pipeline_config.json      # 实际的JSON配置文件")
    print("│   └── component_pipeline_config.json  # 原始Python脚本")
    print("├── app/component/")
    print("│   ├── pipeline_executor.py      # 管道执行器")
    print("│   ├── event_monitor.py          # 事件监控组件")
    print("│   ├── contract_caller.py        # 合约调用组件")
    print("│   ├── dict_mapper.py            # 数据映射组件")
    print("│   └── kafka_client.py           # Kafka客户端组件")
    print("├── run_pipeline.py               # 启动脚本")
    print("├── demo_pipeline.py              # 本演示脚本")
    print("└── README_PIPELINE_USAGE.md      # 使用说明")


def main():
    """主函数"""
    print("🎯 区块链数据管道系统演示")
    print("展示JSON配置与组件结合生成可执行程序的完整流程")
    
    show_file_structure()
    
    print("\n选择操作:")
    print("1. 运行交互式演示")
    print("2. 直接运行演示管道")
    print("3. 显示配置文件示例")
    print("4. 退出")
    
    choice = input("\n请选择 (1-4): ").strip()
    
    if choice == "1":
        asyncio.run(run_demo())
    elif choice == "2":
        # 直接运行，不等待用户输入
        config = create_demo_config()
        config_file = Path("demo_config.json")
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        async def quick_run():
            pipeline = BlockchainDataPipeline(str(config_file))
            result = await pipeline.execute_pipeline()
            pipeline.print_execution_summary(result)
            config_file.unlink()
        
        asyncio.run(quick_run())
    elif choice == "3":
        config = create_demo_config()
        print("\n📝 配置文件示例:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
    elif choice == "4":
        print("👋 再见！")
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    main()