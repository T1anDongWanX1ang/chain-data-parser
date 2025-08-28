#!/usr/bin/env python3
"""
Web3节点连接测试脚本
测试各种RPC节点的连接状态和基本功能
"""

import sys
import time
import requests
import json
from typing import Optional, Dict, Any
from web3 import Web3
from web3.middleware import geth_poa_middleware


class Web3NodeTester:
    """Web3节点连接测试器"""
    
    def __init__(self):
        self.test_results = {}
        
    def test_http_connectivity(self, rpc_url: str) -> Dict[str, Any]:
        """测试HTTP连接性"""
        print(f"\n🔗 测试HTTP连接: {rpc_url}")
        result = {
            "url": rpc_url,
            "http_connected": False,
            "client_version": None,
            "response_time": None,
            "error": None
        }
        
        try:
            start_time = time.time()
            response = requests.post(
                rpc_url,
                json={
                    "jsonrpc": "2.0",
                    "method": "web3_clientVersion",
                    "params": [],
                    "id": 1
                },
                timeout=10,
                headers={'Content-Type': 'application/json'}
            )
            response_time = time.time() - start_time
            result["response_time"] = response_time
            
            if response.status_code == 200:
                data = response.json()
                if 'result' in data:
                    result["http_connected"] = True
                    result["client_version"] = data['result']
                    print(f"✅ HTTP连接成功 ({response_time:.2f}s)")
                    print(f"   客户端版本: {data['result']}")
                elif 'error' in data:
                    result["error"] = data['error']
                    print(f"❌ RPC错误: {data['error']}")
                else:
                    result["error"] = "未知响应格式"
                    print(f"❌ 未知响应格式")
            else:
                result["error"] = f"HTTP {response.status_code}: {response.text}"
                print(f"❌ HTTP错误: {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            result["error"] = "连接超时"
            print(f"❌ 连接超时")
            print(f"   检查项:")
            print(f"   • 节点是否正在运行")
            print(f"   • 防火墙设置")
            print(f"   • RPC端口是否开放")
        except requests.exceptions.ConnectionError as e:
            result["error"] = f"连接错误: {str(e)}"
            print(f"❌ 连接错误: {e}")
            print(f"   可能原因:")
            print(f"   • 节点未启动")
            print(f"   • RPC接口未启用")
            print(f"   • 网络不可达")
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ 其他错误: {e}")
            
        return result
    
    def test_web3_connection(self, rpc_url: str, enable_poa: bool = False) -> Dict[str, Any]:
        """测试Web3连接"""
        print(f"\n🌐 测试Web3连接")
        if enable_poa:
            print(f"   启用POA中间件")
            
        result = {
            "url": rpc_url,
            "web3_connected": False,
            "poa_enabled": enable_poa,
            "chain_id": None,
            "block_number": None,
            "gas_price": None,
            "syncing": None,
            "peer_count": None,
            "error": None
        }
        
        try:
            # 创建Web3实例
            provider = Web3.HTTPProvider(
                rpc_url,
                request_kwargs={
                    'timeout': 30,
                    'headers': {'Content-Type': 'application/json'}
                }
            )
            w3 = Web3(provider)
            
            # 如果启用POA，添加中间件
            if enable_poa:
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            # 测试连接
            if w3.is_connected():
                result["web3_connected"] = True
                print(f"✅ Web3连接成功")
                
                # 获取链ID
                try:
                    chain_id = w3.eth.chain_id
                    result["chain_id"] = chain_id
                    print(f"   链ID: {chain_id}")
                except Exception as e:
                    print(f"   ⚠️  获取链ID失败: {e}")
                
                # 获取最新区块号
                try:
                    block_number = w3.eth.block_number
                    result["block_number"] = block_number
                    print(f"   最新区块: {block_number}")
                except Exception as e:
                    print(f"   ⚠️  获取区块号失败: {e}")
                
                # 获取Gas价格
                try:
                    gas_price = w3.eth.gas_price
                    result["gas_price"] = gas_price
                    gas_price_gwei = Web3.from_wei(gas_price, 'gwei')
                    print(f"   Gas价格: {gas_price} wei ({gas_price_gwei} gwei)")
                except Exception as e:
                    print(f"   ⚠️  获取Gas价格失败: {e}")
                
                # 检查同步状态
                try:
                    syncing = w3.eth.syncing
                    result["syncing"] = syncing
                    if syncing:
                        if isinstance(syncing, dict):
                            current = syncing.get('currentBlock', 0)
                            highest = syncing.get('highestBlock', 0)
                            print(f"   ⚠️  节点正在同步: {current}/{highest}")
                        else:
                            print(f"   ⚠️  节点正在同步")
                    else:
                        print(f"   ✅ 节点已同步")
                except Exception as e:
                    print(f"   ⚠️  获取同步状态失败: {e}")
                
                # 获取节点连接数
                try:
                    peer_count = w3.net.peer_count
                    result["peer_count"] = peer_count
                    print(f"   连接节点数: {peer_count}")
                except Exception as e:
                    print(f"   ⚠️  获取节点连接数失败: {e}")
                    
            else:
                result["error"] = "Web3连接失败"
                print(f"❌ Web3连接失败")
                
                # 如果没有启用POA，尝试启用POA再测试
                if not enable_poa:
                    print(f"   尝试启用POA中间件...")
                    return self.test_web3_connection(rpc_url, enable_poa=True)
                    
        except Exception as e:
            result["error"] = str(e)
            print(f"❌ Web3连接异常: {e}")
            
        return result
    
    def test_rpc_methods(self, rpc_url: str) -> Dict[str, Any]:
        """测试常用RPC方法"""
        print(f"\n🔧 测试RPC方法")
        
        methods_to_test = [
            ("web3_clientVersion", [], "客户端版本"),
            ("eth_chainId", [], "链ID"),
            ("eth_blockNumber", [], "区块号"),
            ("eth_gasPrice", [], "Gas价格"),
            ("net_version", [], "网络版本"),
            ("eth_syncing", [], "同步状态"),
            ("net_peerCount", [], "节点连接数"),
            ("eth_accounts", [], "账户列表"),
            ("eth_coinbase", [], "Coinbase地址")
        ]
        
        results = {}
        success_count = 0
        
        for method, params, description in methods_to_test:
            try:
                response = requests.post(
                    rpc_url,
                    json={
                        "jsonrpc": "2.0",
                        "method": method,
                        "params": params,
                        "id": 1
                    },
                    timeout=5
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'result' in data:
                        results[method] = data['result']
                        success_count += 1
                        # 格式化显示结果
                        result_str = str(data['result'])
                        if len(result_str) > 50:
                            result_str = result_str[:50] + "..."
                        print(f"   ✅ {description}: {result_str}")
                    elif 'error' in data:
                        results[method] = f"错误: {data['error']}"
                        print(f"   ❌ {description}: {data['error']}")
                    else:
                        results[method] = "未知响应"
                        print(f"   ❓ {description}: 未知响应格式")
                else:
                    results[method] = f"HTTP {response.status_code}"
                    print(f"   ❌ {description}: HTTP {response.status_code}")
                    
            except Exception as e:
                results[method] = f"异常: {str(e)}"
                print(f"   ❌ {description}: {e}")
        
        print(f"\n   📊 RPC方法测试结果: {success_count}/{len(methods_to_test)} 成功")
        return results
    
    def test_block_operations(self, rpc_url: str) -> Dict[str, Any]:
        """测试区块操作"""
        print(f"\n📦 测试区块操作")
        
        result = {
            "latest_block": None,
            "block_details": None,
            "transaction_count": None,
            "error": None
        }
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # 如果连接失败，尝试POA
            if not w3.is_connected():
                w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if w3.is_connected():
                # 获取最新区块
                try:
                    latest_block = w3.eth.get_block('latest')
                    result["latest_block"] = latest_block.number
                    result["transaction_count"] = len(latest_block.transactions)
                    
                    print(f"   ✅ 最新区块号: {latest_block.number}")
                    print(f"   ✅ 区块哈希: {latest_block.hash.hex()}")
                    print(f"   ✅ 交易数量: {len(latest_block.transactions)}")
                    print(f"   ✅ 区块时间: {latest_block.timestamp}")
                    print(f"   ✅ Gas使用: {latest_block.gasUsed}/{latest_block.gasLimit}")
                    
                    result["block_details"] = {
                        "number": latest_block.number,
                        "hash": latest_block.hash.hex(),
                        "timestamp": latest_block.timestamp,
                        "gas_used": latest_block.gasUsed,
                        "gas_limit": latest_block.gasLimit,
                        "transaction_count": len(latest_block.transactions)
                    }
                    
                except Exception as e:
                    result["error"] = str(e)
                    print(f"   ❌ 获取区块信息失败: {e}")
                    
            else:
                result["error"] = "Web3连接失败"
                print(f"   ❌ Web3连接失败，无法测试区块操作")
                
        except Exception as e:
            result["error"] = str(e)
            print(f"   ❌ 区块操作测试失败: {e}")
            
        return result
    
    def diagnose_connection_issues(self, rpc_url: str):
        """诊断连接问题"""
        print(f"\n🔍 连接问题诊断")
        
        # 解析URL
        if rpc_url.startswith('http://'):
            protocol = 'HTTP'
            host_port = rpc_url[7:]
        elif rpc_url.startswith('https://'):
            protocol = 'HTTPS'
            host_port = rpc_url[8:]
        else:
            print(f"❌ 无效的RPC URL格式: {rpc_url}")
            return
        
        if ':' in host_port and not host_port.startswith('['):  # 排除IPv6
            host, port = host_port.split(':', 1)
            port = port.split('/')[0]  # 移除路径部分
        else:
            host = host_port.split('/')[0]
            port = '80' if protocol == 'HTTP' else '443'
        
        print(f"   协议: {protocol}")
        print(f"   主机: {host}")
        print(f"   端口: {port}")
        
        # 测试端口连通性
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect_ex((host, int(port)))
            sock.close()
            
            if result == 0:
                print(f"   ✅ 端口 {port} 可达")
            else:
                print(f"   ❌ 端口 {port} 不可达")
                print(f"   可能原因:")
                print(f"   • 节点未启动")
                print(f"   • 防火墙阻止连接")
                print(f"   • 端口配置错误")
        except Exception as e:
            print(f"   ❌ 端口测试失败: {e}")
    
    def run_comprehensive_test(self, rpc_url: str) -> Dict[str, Any]:
        """运行综合测试"""
        print(f"\n{'='*60}")
        print(f"🚀 Web3节点连接综合测试")
        print(f"{'='*60}")
        print(f"RPC URL: {rpc_url}")
        print(f"测试时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 1. HTTP连接测试
        http_result = self.test_http_connectivity(rpc_url)
        
        # 2. Web3连接测试
        web3_result = self.test_web3_connection(rpc_url)
        
        # 3. RPC方法测试
        rpc_methods_result = self.test_rpc_methods(rpc_url)
        
        # 4. 区块操作测试
        block_result = self.test_block_operations(rpc_url)
        
        # 5. 如果连接失败，进行诊断
        if not http_result.get("http_connected", False):
            self.diagnose_connection_issues(rpc_url)
        
        # 汇总结果
        comprehensive_result = {
            "rpc_url": rpc_url,
            "test_time": time.strftime('%Y-%m-%d %H:%M:%S'),
            "timestamp": time.time(),
            "http_test": http_result,
            "web3_test": web3_result,
            "rpc_methods": rpc_methods_result,
            "block_test": block_result,
            "overall_success": (
                http_result.get("http_connected", False) and
                web3_result.get("web3_connected", False)
            )
        }
        
        # 打印总结
        print(f"\n{'='*60}")
        print(f"📊 测试结果总结")
        print(f"{'='*60}")
        
        if comprehensive_result["overall_success"]:
            print(f"✅ 总体状态: 节点连接成功")
        else:
            print(f"❌ 总体状态: 节点连接失败")
        
        print(f"   HTTP连接: {'✅' if http_result.get('http_connected') else '❌'}")
        print(f"   Web3连接: {'✅' if web3_result.get('web3_connected') else '❌'}")
        print(f"   区块操作: {'✅' if block_result.get('latest_block') else '❌'}")
        
        if http_result.get("response_time"):
            print(f"   响应时间: {http_result['response_time']:.2f}s")
        if http_result.get("client_version"):
            print(f"   客户端: {http_result['client_version']}")
        if web3_result.get("chain_id"):
            print(f"   链ID: {web3_result['chain_id']}")
        if web3_result.get("block_number"):
            print(f"   最新区块: {web3_result['block_number']}")
        if web3_result.get("peer_count") is not None:
            print(f"   连接节点: {web3_result['peer_count']}")
        
        return comprehensive_result


def main():
    """主函数"""
    tester = Web3NodeTester()
    
    # 预定义的测试URL
    test_urls = {
        "1": ("以太坊主网 (Infura)", "https://mainnet.infura.io/v3/c3fbac6d01a74109b3c5088d657f528e"),
        "2": ("BSC主网", "https://bsc-dataseed.binance.org/"),
        "3": ("Polygon主网", "https://polygon-rpc.com/"),
        "4": ("本地节点", "http://localhost:8545"),
        "5": ("自定义URL", "")
    }
    
    print("🌐 Web3节点连接测试工具")
    print("=" * 50)
    
    # 显示选项
    print("请选择要测试的节点:")
    for key, (name, url) in test_urls.items():
        if url:
            print(f"{key}. {name} - {url}")
        else:
            print(f"{key}. {name}")
    
    # 用户选择
    choice = input("\n请输入选项 (1-5): ").strip()
    
    if choice in test_urls:
        name, url = test_urls[choice]
        if not url:  # 自定义URL
            url = input("请输入自定义RPC URL: ").strip()
            if not url:
                print("❌ 未提供RPC URL")
                return
        
        print(f"\n选择的节点: {name}")
        
        # 运行测试
        result = tester.run_comprehensive_test(url)
        
        # 保存结果到文件
        timestamp = int(time.time())
        filename = f"web3_test_result_{timestamp}.json"
        try:
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False, default=str)
            print(f"\n💾 详细结果已保存到: {filename}")
        except Exception as e:
            print(f"\n⚠️  保存结果文件失败: {e}")
        
        # 提供建议
        if not result["overall_success"]:
            print(f"\n💡 连接失败的常见解决方案:")
            print(f"1. 检查节点是否正在运行")
            print(f"2. 确认RPC接口已启用 (--http --http-addr 0.0.0.0)")
            print(f"3. 检查防火墙和端口设置")
            print(f"4. 如果是私有链，可能需要POA中间件")
            print(f"5. 确认节点已完全同步")
    
    else:
        print("❌ 无效的选项")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
