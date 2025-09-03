#!/usr/bin/env python3
"""
测试项目中EVMParserService的Web3连接功能
"""

import sys
import os
import asyncio
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.evm_parser import evm_parser_service
from app.config import settings


def test_evm_parser_connections():
    """测试EVMParserService的连接功能"""
    print("🚀 测试EVMParserService Web3连接")
    print("=" * 50)
    
    # 测试支持的链
    chains_to_test = ['ethereum', 'bsc', 'polygon']
    
    results = {}
    
    for chain_name in chains_to_test:
        print(f"\n📍 测试 {chain_name.upper()} 链")
        print("-" * 30)
        
        try:
            # 获取Web3实例
            w3 = evm_parser_service.get_web3(chain_name)
            
            if w3:
                print(f"✅ {chain_name} Web3实例创建成功")
                
                # 测试连接状态
                if w3.is_connected():
                    print(f"✅ {chain_name} 连接成功")
                    
                    # 获取基本信息
                    try:
                        chain_id = w3.eth.chain_id
                        block_number = w3.eth.block_number
                        gas_price = w3.eth.gas_price
                        
                        print(f"   链ID: {chain_id}")
                        print(f"   最新区块: {block_number}")
                        print(f"   Gas价格: {gas_price} wei")
                        
                        # 测试链ID映射
                        expected_chain_id = evm_parser_service.get_chain_id(chain_name)
                        if expected_chain_id == chain_id:
                            print(f"   ✅ 链ID映射正确: {expected_chain_id}")
                        else:
                            print(f"   ⚠️  链ID映射不匹配: 期望{expected_chain_id}, 实际{chain_id}")
                        
                        results[chain_name] = {
                            "success": True,
                            "chain_id": chain_id,
                            "block_number": block_number,
                            "gas_price": gas_price
                        }
                        
                    except Exception as e:
                        print(f"   ⚠️  获取链信息失败: {e}")
                        results[chain_name] = {
                            "success": True,
                            "error": f"获取信息失败: {e}"
                        }
                else:
                    print(f"❌ {chain_name} 连接失败")
                    results[chain_name] = {
                        "success": False,
                        "error": "Web3连接失败"
                    }
            else:
                print(f"❌ {chain_name} Web3实例创建失败")
                results[chain_name] = {
                    "success": False,
                    "error": "Web3实例创建失败"
                }
                
        except Exception as e:
            print(f"❌ {chain_name} 测试异常: {e}")
            results[chain_name] = {
                "success": False,
                "error": str(e)
            }
    
    # 显示汇总结果
    print("\n" + "=" * 50)
    print("📊 EVMParserService连接测试结果")
    print("=" * 50)
    
    success_count = 0
    for chain_name, result in results.items():
        if result.get("success"):
            status = "✅ 成功"
            success_count += 1
            if "chain_id" in result:
                status += f" (链ID: {result['chain_id']}, 区块: {result['block_number']})"
        else:
            status = f"❌ 失败 - {result.get('error', '未知错误')}"
        
        print(f"{chain_name.upper():<10} {status}")
    
    print(f"\n总计: {success_count}/{len(chains_to_test)} 个链连接成功")
    
    return results


def test_custom_rpc_url():
    """测试自定义RPC URL"""
    print("\n🔧 测试自定义RPC URL")
    print("=" * 30)
    
    custom_url = input("请输入自定义RPC URL (回车跳过): ").strip()
    
    if not custom_url:
        print("跳过自定义URL测试")
        return
    
    try:
        from web3 import Web3
        from web3.middleware import geth_poa_middleware
        
        # 创建Web3实例
        w3 = Web3(Web3.HTTPProvider(custom_url))
        
        print(f"测试URL: {custom_url}")
        
        if w3.is_connected():
            print(f"✅ 连接成功")
        else:
            # 尝试POA中间件
            w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            if w3.is_connected():
                print(f"✅ 连接成功 (使用POA中间件)")
            else:
                print(f"❌ 连接失败")
                return
        
        # 获取信息
        try:
            chain_id = w3.eth.chain_id
            block_number = w3.eth.block_number
            print(f"   链ID: {chain_id}")
            print(f"   最新区块: {block_number}")
        except Exception as e:
            print(f"   ⚠️  获取信息失败: {e}")
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")


def test_configuration():
    """测试配置信息"""
    print("\n⚙️  当前配置信息")
    print("=" * 30)
    
    print(f"以太坊RPC: {settings.blockchain.eth_rpc_url}")
    print(f"BSC RPC: {settings.blockchain.bsc_rpc_url}")
    print(f"Polygon RPC: {settings.blockchain.polygon_rpc_url}")
    print(f"Solana RPC: {settings.blockchain.solana_rpc_url}")
    
    # 测试链ID映射
    print(f"\n🔗 链ID映射:")
    chains = ['ethereum', 'bsc', 'base', 'solana']
    for chain in chains:
        chain_id = evm_parser_service.get_chain_id(chain)
        print(f"   {chain}: {chain_id}")


def main():
    """主函数"""
    print("🌐 EVMParserService Web3连接测试工具")
    print("=" * 60)
    
    try:
        # 1. 测试配置
        test_configuration()
        
        # 2. 测试EVMParserService连接
        results = test_evm_parser_connections()
        
        # 3. 测试自定义URL
        test_custom_rpc_url()
        
        # 4. 提供建议
        failed_chains = [chain for chain, result in results.items() if not result.get("success")]
        if failed_chains:
            print(f"\n💡 连接失败的链: {', '.join(failed_chains)}")
            print(f"建议检查:")
            print(f"• RPC URL是否正确")
            print(f"• 网络连接是否正常")
            print(f"• RPC服务是否可用")
            print(f"• 是否需要API密钥")
        
        print(f"\n🎉 测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n⏹️  测试已取消")
    except Exception as e:
        print(f"\n❌ 程序异常: {e}")
        sys.exit(1)
