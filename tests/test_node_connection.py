#!/usr/bin/env python3
"""
简化版Web3节点连接测试脚本
快速判断节点是否连接成功
"""

import sys
import time
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware


def test_node_connection(rpc_url: str) -> bool:
    """
    测试节点连接
    
    Args:
        rpc_url: RPC节点URL
        
    Returns:
        bool: 连接是否成功
    """
    print(f"🔗 测试节点连接: {rpc_url}")
    
    # # 1. 测试HTTP连接
    # try:
    #     response = requests.post(
    #         rpc_url,
    #         json={
    #             "jsonrpc": "2.0",
    #             "method": "web3_clientVersion",
    #             "params": [],
    #             "id": 1
    #         },
    #         timeout=10
    #     )
    #
    #     if response.status_code != 200:
    #         print(f"❌ HTTP连接失败: {response.status_code}")
    #         return False
    #
    #     data = response.json()
    #     if 'error' in data:
    #         print(f"❌ RPC错误: {data['error']}")
    #         return False
    #
    #     print(f"✅ HTTP连接成功")
    #     if 'result' in data:
    #         print(f"   客户端: {data['result']}")
    #
    # except requests.exceptions.ConnectTimeout:
    #     print(f"❌ 连接超时")
    #     return False
    # except requests.exceptions.ConnectionError:
    #     print(f"❌ 连接错误")
    #     return False
    # except Exception as e:
    #     print(f"❌ HTTP测试失败: {e}")
    #     return False
    
    # 2. 测试Web3连接
    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if w3.is_connected():
            print(f"✅ Web3连接成功")
        else:
            # 尝试POA中间件
            print(f"   尝试POA中间件...")
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if w3.is_connected():
                print(f"✅ Web3连接成功 (使用POA中间件)")
            else:
                print(f"❌ Web3连接失败")
                return False
        
        # 获取基本信息
        try:
            chain_id = w3.eth.chain_id
            block_number = w3.eth.block_number
            print(f"   链ID: {chain_id}")
            print(f"   最新区块: {block_number}")
            
            # 检查同步状态
            syncing = w3.eth.syncing
            if syncing:
                print(f"   ⚠️  节点正在同步")
            else:
                print(f"   ✅ 节点已同步")
                
        except Exception as e:
            print(f"   ⚠️  获取节点信息失败: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Web3连接失败: {e}")
        return False


def quick_test():
    """快速测试函数"""
    print("🚀 Web3节点连接快速测试")
    print("=" * 40)
    
    # 获取用户输入
    rpc_url = input("请输入RPC URL: ").strip()
    
    if not rpc_url:
        print("❌ 未提供RPC URL")
        return
    
    # 执行测试
    start_time = time.time()
    success = test_node_connection(rpc_url)
    test_time = time.time() - start_time
    
    # 显示结果
    print("\n" + "=" * 40)
    if success:
        print(f"🎉 节点连接成功! (耗时: {test_time:.2f}s)")
    else:
        print(f"💥 节点连接失败! (耗时: {test_time:.2f}s)")
        print("\n💡 常见解决方案:")
        print("• 检查节点是否运行")
        print("• 确认RPC接口已启用")
        print("• 检查防火墙设置")
        print("• 验证URL格式正确")


def batch_test():
    """批量测试多个节点"""
    print("🚀 Web3节点批量连接测试")
    print("=" * 40)
    
    # 预定义节点列表
    nodes = [
        ("以太坊主网", "https://mainnet.infura.io/v3/c3fbac6d01a74109b3c5088d657f528e"),
        ("BSC主网", "https://bsc-dataseed.binance.org/"),
        ("本地节点", "http://localhost:8545"),
    ]
    
    results = []
    
    for name, url in nodes:
        print(f"\n📍 测试 {name}")
        print("-" * 30)
        
        start_time = time.time()
        success = test_node_connection(url)
        test_time = time.time() - start_time
        
        results.append({
            "name": name,
            "url": url,
            "success": success,
            "time": test_time
        })
    
    # 显示汇总结果
    print("\n" + "=" * 50)
    print("📊 批量测试结果汇总")
    print("=" * 50)
    
    for result in results:
        status = "✅ 成功" if result["success"] else "❌ 失败"
        print(f"{result['name']:<15} {status} ({result['time']:.2f}s)")
    
    success_count = sum(1 for r in results if r["success"])
    print(f"\n总计: {success_count}/{len(results)} 个节点连接成功")


def main():
    """主函数"""
    print("选择测试模式:")
    print("1. 单个节点测试")
    print("2. 批量节点测试")
    
    choice = input("请选择 (1/2): ").strip()
    
    if choice == "1":
        quick_test()
    elif choice == "2":
        batch_test()
    else:
        print("❌ 无效选择")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
