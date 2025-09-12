#!/usr/bin/env python3
"""
测试代理合约 ABI 获取功能
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any

# 已知的代理合约地址用于测试
TEST_CONTRACTS = {
    "ethereum": {
        # USDC代理合约 (EIP-1967)
        "USDC_PROXY": "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93",
        
        # USDT代理合约
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        
        # 一个常见的 OpenZeppelin 代理合约
        "COMPOUND_USDC": "0x39aa39c021dfbae8fac545936693ac917d5e7563"
    }
}

async def test_api_request(contract_address: str, chain_name: str, check_proxy: bool = True) -> Dict[str, Any]:
    """测试API请求"""
    url = "http://localhost:8001/abis/auto-fetch"
    
    data = {
        "contract_address": contract_address,
        "chain_name": chain_name,
        "check_proxy": check_proxy
    }
    
    print(f"\n📡 测试API请求:")
    print(f"   地址: {contract_address}")
    print(f"   链: {chain_name}")
    print(f"   代理检测: {check_proxy}")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=data) as response:
                result = await response.json()
                
                print(f"   状态码: {response.status}")
                if response.status == 201:
                    print(f"   ✅ 成功获取ABI")
                    print(f"   ABI函数数量: {result.get('data', {}).get('abi_functions_count', 0)}")
                else:
                    print(f"   ❌ 获取失败: {result.get('detail', 'Unknown error')}")
                
                return result
                
    except Exception as e:
        print(f"   ❌ 请求异常: {e}")
        return {"error": str(e)}

async def test_direct_service():
    """直接测试服务功能"""
    print("🔍 直接测试代理合约检测服务...")
    
    try:
        from app.services.blockchain_explorer_service import BlockchainExplorerService, ChainType
        
        # 测试USDC代理合约
        usdc_proxy = "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93"
        
        async with BlockchainExplorerService(timeout=30) as explorer:
            print(f"\n📋 测试合约: {usdc_proxy}")
            
            # 不检测代理
            print("   不检测代理合约:")
            abi_without_proxy = await explorer.get_contract_abi(
                usdc_proxy, ChainType.ETHEREUM, check_proxy=False
            )
            if abi_without_proxy:
                print(f"     ✅ 获取到 {len(abi_without_proxy)} 个ABI项")
            else:
                print("     ❌ 未获取到ABI")
            
            # 检测代理
            print("   检测代理合约:")
            abi_with_proxy = await explorer.get_contract_abi(
                usdc_proxy, ChainType.ETHEREUM, check_proxy=True
            )
            if abi_with_proxy:
                print(f"     ✅ 获取到 {len(abi_with_proxy)} 个ABI项")
            else:
                print("     ❌ 未获取到ABI")
                
    except Exception as e:
        print(f"❌ 服务测试失败: {e}")

async def test_proxy_detection():
    """测试代理合约检测功能"""
    print("\n🕵️ 测试代理合约检测功能...")
    
    try:
        from app.utils.contract_utils import ProxyContractDetector
        from app.config import settings
        
        # 测试几个已知的代理合约
        test_addresses = [
            "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93",  # USDC
            "0xdAC17F958D2ee523a2206206994597C13D831ec7",  # USDT
        ]
        
        rpc_url = settings.blockchain.eth_rpc_url
        
        for address in test_addresses:
            print(f"\n🔎 检测合约: {address}")
            
            result = await ProxyContractDetector.detect_proxy_contract(
                address, rpc_url, timeout=30
            )
            
            if result["is_proxy"]:
                print(f"   ✅ 检测到代理合约")
                print(f"   类型: {result['proxy_type']}")
                print(f"   实现地址: {result['implementation_address']}")
                print(f"   检测方法: {result['detection_method']}")
            else:
                print(f"   ℹ️ 非代理合约")
                if result.get("error"):
                    print(f"   错误: {result['error']}")
                    
    except Exception as e:
        print(f"❌ 代理检测失败: {e}")

async def main():
    """主测试函数"""
    print("🚀 开始测试代理合约ABI获取功能")
    print("=" * 50)
    
    # 1. 测试代理合约检测
    await test_proxy_detection()
    
    # 2. 直接测试服务
    await test_direct_service()
    
    # 3. 测试API请求
    print("\n🌐 测试API接口...")
    
    # 测试USDC代理合约
    await test_api_request(
        "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93", 
        "ethereum", 
        check_proxy=True
    )
    
    # 测试同一合约但关闭代理检测
    await test_api_request(
        "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93", 
        "ethereum", 
        check_proxy=False
    )
    
    print("\n✅ 测试完成")

if __name__ == "__main__":
    asyncio.run(main())