#!/usr/bin/env python3
"""
管道配置API使用示例

演示如何使用管道配置API保存和获取管道配置
"""

import json
import asyncio
import httpx
from loguru import logger

# 示例管道配置JSON
PIPELINE_CONFIG = {
    "pipeline_name": "usdc_transfer_monitor",
    "description": "USDC转账事件监控管道配置",
    "components": [
        {
            "name": "USDC转账事件监控器",
            "type": "event_monitor",
            "chain_name": "ethereum",
            "contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "abi_path": "../abis/erc20.json",
            "events_to_monitor": [
                "Transfer"
            ]
        },
        {
            "name": "USDC符号查询器",
            "type": "contract_caller",
            "chain_name": "ethereum",
            "abi_path": "../abis/erc20.json",
            "contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "method_name": "symbol",
            "method_params": []
        },
        {
            "name": "USDC精度查询器",
            "type": "contract_caller",
            "chain_name": "ethereum",
            "abi_path": "../abis/erc20.json",
            "contract_address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "method_name": "decimals",
            "method_params": []
        },
        {
            "name": "字段映射",
            "type": "dict_mapper",
            "mapping_rules": [
                {
                    "source_key": "event_name",
                    "target_key": "event_type",
                    "transformer": "to_string"
                },
                {
                    "source_key": "transaction_hash",
                    "target_key": "transaction_hash",
                    "transformer": "to_lowercase"
                },
                {
                    "source_key": "block_number",
                    "target_key": "block_number",
                    "transformer": "to_int"
                },
                {
                    "source_key": "args.from",
                    "target_key": "from_address",
                    "transformer": "to_lowercase"
                },
                {
                    "source_key": "args.to",
                    "target_key": "to_address",
                    "transformer": "to_lowercase"
                },
                {
                    "source_key": "args.value",
                    "target_key": "transfer_amount",
                    "transformer": "to_string"
                },
                {
                    "source_key": "symbol_result",
                    "target_key": "token_symbol"
                },
                {
                    "source_key": "decimals_result",
                    "target_key": "token_decimals",
                    "transformer": "to_int"
                }
            ]
        },
        {
            "name": "USDC转账Kafka生产者",
            "type": "kafka_producer",
            "bootstrap_servers": "localhost:9092",
            "topic": "usdc-transfers"
        }
    ]
}


class PipelineConfigAPIClient:
    """管道配置API客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.client = httpx.AsyncClient()
    
    async def save_pipeline_config(self, pipeline_id: int, pipeline_info: dict) -> dict:
        """保存管道配置"""
        url = f"{self.base_url}/pipeline/config"
        
        payload = {
            "pipeline_id": pipeline_id,
            "pipeline_info": json.dumps(pipeline_info, ensure_ascii=False)
        }
        
        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"保存管道配置失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    async def get_pipeline_config(self, pipeline_id: int) -> dict:
        """获取管道配置"""
        url = f"{self.base_url}/pipeline/config/{pipeline_id}"
        
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as e:
            logger.error(f"获取管道配置失败: {e}")
            if hasattr(e, 'response') and e.response:
                logger.error(f"响应内容: {e.response.text}")
            raise
    
    async def close(self):
        """关闭客户端"""
        await self.client.aclose()


async def main():
    """主函数"""
    print("管道配置API使用示例")
    print("=" * 50)
    
    # 创建API客户端
    client = PipelineConfigAPIClient()
    
    try:
        pipeline_id = 1001
        
        print(f"1. 保存管道配置 (ID: {pipeline_id})")
        print("-" * 30)
        
        # 保存管道配置
        save_result = await client.save_pipeline_config(pipeline_id, PIPELINE_CONFIG)
        print(f"保存结果: {json.dumps(save_result, indent=2, ensure_ascii=False)}")
        
        print(f"\n2. 获取管道配置 (ID: {pipeline_id})")
        print("-" * 30)
        
        # 获取管道配置
        config_result = await client.get_pipeline_config(pipeline_id)
        print(f"配置信息: {json.dumps(config_result, indent=2, ensure_ascii=False)}")
        
        print(f"\n3. 配置验证")
        print("-" * 30)
        
        # 验证保存的配置
        original_components = len(PIPELINE_CONFIG['components'])
        saved_components = len(config_result['components'])
        
        print(f"原始组件数量: {original_components}")
        print(f"保存组件数量: {saved_components}")
        print(f"配置验证: {'✅ 通过' if original_components == saved_components else '❌ 失败'}")
        
        # 显示组件详情
        print(f"\n4. 组件详情")
        print("-" * 30)
        for i, component in enumerate(config_result['components'], 1):
            print(f"组件 {i}: {component['name']} ({component['type']})")
            if component['type'] == 'event_monitor':
                print(f"  - 链: {component.get('chain_name')}")
                print(f"  - 合约: {component.get('contract_address')}")
                print(f"  - 事件: {component.get('events_to_monitor')}")
            elif component['type'] == 'contract_caller':
                print(f"  - 链: {component.get('chain_name')}")
                print(f"  - 合约: {component.get('contract_address')}")
                print(f"  - 方法: {component.get('method_name')}")
            elif component['type'] == 'dict_mapper':
                rules_count = len(component.get('mapping_rules', []))
                print(f"  - 映射规则数量: {rules_count}")
            elif component['type'] == 'kafka_producer':
                print(f"  - 服务器: {component.get('bootstrap_servers')}")
                print(f"  - 主题: {component.get('topic')}")
        
    except Exception as e:
        logger.error(f"示例执行失败: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        await client.close()


if __name__ == "__main__":
    # 配置日志
    logger.remove()
    logger.add(
        lambda msg: print(msg, end=""),
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 运行示例
    asyncio.run(main())
