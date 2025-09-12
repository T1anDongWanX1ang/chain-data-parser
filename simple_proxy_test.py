#!/usr/bin/env python3
"""
简单的代理合约测试
"""

import asyncio
import aiohttp
import json

async def test_simple_api():
    """测试API是否正常响应"""
    url = "http://localhost:8001/api/v1/abis/auto-fetch"
    
    # 测试一个真正的代理合约 - USDC (EIP-1967 代理)
    data = {
        "contract_address": "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93",
        "chain_name": "ethereum",
        "check_proxy": True
    }
    
    print(f"🔍 测试代理合约ABI获取API")
    print(f"合约地址: {data['contract_address']}")
    print(f"链: {data['chain_name']}")
    print(f"代理检测: {data['check_proxy']}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data, timeout=aiohttp.ClientTimeout(total=60)) as response:
                result = await response.json()
                
                print(f"\n状态码: {response.status}")
                print(f"响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
                
                if response.status == 201:
                    print("\n✅ 测试成功！代理合约ABI获取功能正常")
                else:
                    print(f"\n⚠️ API返回错误: {result.get('detail', 'Unknown error')}")
                    
    except asyncio.TimeoutError:
        print("❌ 请求超时")
    except Exception as e:
        print(f"❌ 请求失败: {e}")

async def main():
    await test_simple_api()

if __name__ == "__main__":
    asyncio.run(main())