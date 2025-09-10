"""合约相关工具函数"""
import json
import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from pathlib import Path
from loguru import logger
from web3 import Web3


def load_abi_from_file(file_path: str) -> List[Dict[str, Any]]:
    """从文件加载ABI"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            abi = json.load(f)
        return abi
    except Exception as e:
        raise ValueError(f"加载ABI文件失败: {e}")


def load_abi_from_string(abi_string: str) -> List[Dict[str, Any]]:
    """从字符串加载ABI"""
    try:
        abi = json.loads(abi_string)
        return abi
    except Exception as e:
        raise ValueError(f"解析ABI字符串失败: {e}")


def get_standard_erc20_abi() -> List[Dict[str, Any]]:
    """获取标准ERC20 ABI"""
    return [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "from", "type": "address"},
                {"indexed": True, "name": "to", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
            ],
            "name": "Transfer",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "owner", "type": "address"},
                {"indexed": True, "name": "spender", "type": "address"},
                {"indexed": False, "name": "value", "type": "uint256"}
            ],
            "name": "Approval",
            "type": "event"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "name",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "symbol",
            "outputs": [{"name": "", "type": "string"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "decimals",
            "outputs": [{"name": "", "type": "uint8"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        },
        {
            "constant": True,
            "inputs": [{"name": "account", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "", "type": "uint256"}],
            "type": "function"
        }
    ]


def get_uniswap_v2_pair_abi() -> List[Dict[str, Any]]:
    """获取Uniswap V2 Pair ABI（主要事件）"""
    return [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "sender", "type": "address"},
                {"indexed": False, "name": "amount0In", "type": "uint256"},
                {"indexed": False, "name": "amount1In", "type": "uint256"},
                {"indexed": False, "name": "amount0Out", "type": "uint256"},
                {"indexed": False, "name": "amount1Out", "type": "uint256"},
                {"indexed": True, "name": "to", "type": "address"}
            ],
            "name": "Swap",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "sender", "type": "address"},
                {"indexed": False, "name": "amount0", "type": "uint256"},
                {"indexed": False, "name": "amount1", "type": "uint256"}
            ],
            "name": "Mint",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "sender", "type": "address"},
                {"indexed": False, "name": "amount0", "type": "uint256"},
                {"indexed": False, "name": "amount1", "type": "uint256"},
                {"indexed": True, "name": "to", "type": "address"}
            ],
            "name": "Burn",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": False, "name": "reserve0", "type": "uint112"},
                {"indexed": False, "name": "reserve1", "type": "uint112"}
            ],
            "name": "Sync",
            "type": "event"
        }
    ]


def get_uniswap_v3_pool_abi() -> List[Dict[str, Any]]:
    """获取Uniswap V3 Pool ABI（主要事件）"""
    return [
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "sender", "type": "address"},
                {"indexed": True, "name": "recipient", "type": "address"},
                {"indexed": False, "name": "amount0", "type": "int256"},
                {"indexed": False, "name": "amount1", "type": "int256"},
                {"indexed": False, "name": "sqrtPriceX96", "type": "uint160"},
                {"indexed": False, "name": "liquidity", "type": "uint128"},
                {"indexed": False, "name": "tick", "type": "int24"}
            ],
            "name": "Swap",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": False, "name": "sender", "type": "address"},
                {"indexed": True, "name": "owner", "type": "address"},
                {"indexed": True, "name": "tickLower", "type": "int24"},
                {"indexed": True, "name": "tickUpper", "type": "int24"},
                {"indexed": False, "name": "amount", "type": "uint128"},
                {"indexed": False, "name": "amount0", "type": "uint256"},
                {"indexed": False, "name": "amount1", "type": "uint256"}
            ],
            "name": "Mint",
            "type": "event"
        },
        {
            "anonymous": False,
            "inputs": [
                {"indexed": True, "name": "owner", "type": "address"},
                {"indexed": True, "name": "tickLower", "type": "int24"},
                {"indexed": True, "name": "tickUpper", "type": "int24"},
                {"indexed": False, "name": "amount", "type": "uint128"},
                {"indexed": False, "name": "amount0", "type": "uint256"},
                {"indexed": False, "name": "amount1", "type": "uint256"}
            ],
            "name": "Burn",
            "type": "event"
        }
    ]


def validate_abi(abi: List[Dict[str, Any]]) -> bool:
    """验证ABI格式是否正确"""
    if not isinstance(abi, list):
        return False
    
    for item in abi:
        if not isinstance(item, dict):
            return False
        
        # 检查必要字段
        if 'type' not in item:
            return False
        
        # 根据类型检查特定字段
        if item['type'] == 'event':
            if 'name' not in item or 'inputs' not in item:
                return False
        elif item['type'] == 'function':
            if 'name' not in item:
                return False
    
    return True


def extract_events_from_abi(abi: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """从ABI中提取所有事件定义"""
    events = []
    for item in abi:
        if item.get('type') == 'event':
            events.append(item)
    return events


def get_event_names_from_abi(abi: List[Dict[str, Any]]) -> List[str]:
    """从ABI中获取所有事件名称"""
    event_names = []
    for item in abi:
        if item.get('type') == 'event' and 'name' in item:
            event_names.append(item['name'])
    return event_names


def save_abi_to_file(abi: List[Dict[str, Any]], file_path: str):
    """保存ABI到文件"""
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(abi, f, indent=2, ensure_ascii=False)
    except Exception as e:
        raise ValueError(f"保存ABI文件失败: {e}")


# 常用合约地址
class WellKnownContracts:
    """知名合约地址"""
    
    # 以太坊主网
    ETHEREUM = {
        "USDT": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
        "USDC": "0xA0b86a33E6417C66cF4CEf23fE4c7DCdF6e81C93",
        "WETH": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "UNI": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
        "UNISWAP_V2_FACTORY": "0x5C69bEe701ef814a2B6a3EDD4B1652CB9cc5aA6f",
        "UNISWAP_V3_FACTORY": "0x1F98431c8aD98523631AE4a59f267346ea31F984"
    }
    
    # BSC主网
    BSC = {
        "USDT": "0x55d398326f99059fF775485246999027B3197955",
        "USDC": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
        "WBNB": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "BUSD": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
        "PANCAKE_FACTORY": "0xcA143Ce32Fe78f1f7019d7d551a6402fC5350c73"
    }
    
    # Polygon主网
    POLYGON = {
        "USDT": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
        "USDC": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        "WMATIC": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "QUICK": "0x831753DD7087CaC61aB5644b308642cc1c33Dc13"
    }


class ProxyContractDetector:
    """代理合约检测器"""
    
    # 常见的代理合约模式storage slots
    PROXY_STORAGE_SLOTS = {
        # EIP-1967 标准代理合约
        "EIP1967_IMPLEMENTATION": "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc",
        "EIP1967_ADMIN": "0xb53127684a568b3173ae13b9f8a6016e243e63b6e8ee1178d6a717850b5d6103",
        "EIP1967_BEACON": "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50",
        
        # OpenZeppelin Proxy patterns
        "OZ_IMPLEMENTATION": "0x5f016c73cf85c6ce1e2f27e78e54b6fbf0d9d1df7e4db66a3b4b0c4b9b3b4a5c",
        
        # Compound/Delegate proxy pattern
        "COMPOUND_IMPLEMENTATION": "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7",
        
        # Diamond proxy pattern (EIP-2535)
        "DIAMOND_STORAGE": "0xc8fcad8db84d3cc18b4c41d551ea0ee66dd599cde068d998e57d5e09332c131c",
        
        # 其他常见模式
        "PROXY_IMPLEMENTATION": "0x0000000000000000000000000000000000000000000000000000000000000001",
        "MASTER_COPY": "0x0000000000000000000000000000000000000000000000000000000000000002"
    }
    
    @staticmethod
    def get_proxy_detection_bytecode() -> str:
        """获取代理合约检测bytecode - 检查delegatecall模式"""
        # 查找delegatecall指令 (0xf4)
        return "f4"
    
    @staticmethod
    async def detect_proxy_contract(
        contract_address: str, 
        rpc_url: str, 
        timeout: int = 15
    ) -> Dict[str, Any]:
        """
        检测是否为代理合约并获取实现地址
        
        Args:
            contract_address: 合约地址
            rpc_url: RPC节点URL
            timeout: 请求超时时间
            
        Returns:
            检测结果包含：
            - is_proxy: 是否为代理合约
            - proxy_type: 代理类型
            - implementation_address: 实现合约地址
            - detection_method: 检测方法
        """
        result = {
            "is_proxy": False,
            "proxy_type": None,
            "implementation_address": None,
            "detection_method": None,
            "error": None
        }
        
        try:
            # 1. 检查EIP-1967标准代理
            impl_addr = await ProxyContractDetector._check_eip1967_proxy(
                contract_address, rpc_url, timeout
            )
            if impl_addr:
                result.update({
                    "is_proxy": True,
                    "proxy_type": "EIP-1967",
                    "implementation_address": impl_addr,
                    "detection_method": "storage_slot"
                })
                return result
            
            # 2. 检查OpenZeppelin代理
            impl_addr = await ProxyContractDetector._check_openzeppelin_proxy(
                contract_address, rpc_url, timeout
            )
            if impl_addr:
                result.update({
                    "is_proxy": True,
                    "proxy_type": "OpenZeppelin",
                    "implementation_address": impl_addr,
                    "detection_method": "storage_slot"
                })
                return result
            
            # 3. 检查bytecode是否包含delegatecall
            has_delegatecall = await ProxyContractDetector._check_delegatecall_pattern(
                contract_address, rpc_url, timeout
            )
            if has_delegatecall:
                # 尝试通过常见方法调用获取实现地址
                impl_addr = await ProxyContractDetector._get_implementation_by_method_call(
                    contract_address, rpc_url, timeout
                )
                if impl_addr:
                    result.update({
                        "is_proxy": True,
                        "proxy_type": "Custom",
                        "implementation_address": impl_addr,
                        "detection_method": "method_call"
                    })
                else:
                    result.update({
                        "is_proxy": True,
                        "proxy_type": "Unknown",
                        "implementation_address": None,
                        "detection_method": "bytecode_analysis"
                    })
                return result
            
            logger.info(f"合约 {contract_address} 不是代理合约")
            return result
            
        except Exception as e:
            logger.error(f"检测代理合约时发生错误: {e}")
            result["error"] = str(e)
            return result
    
    @staticmethod
    async def _check_eip1967_proxy(
        contract_address: str, 
        rpc_url: str, 
        timeout: int
    ) -> Optional[str]:
        """检查EIP-1967标准代理合约"""
        try:
            slot = ProxyContractDetector.PROXY_STORAGE_SLOTS["EIP1967_IMPLEMENTATION"]
            impl_addr = await ProxyContractDetector._read_storage_slot(
                contract_address, slot, rpc_url, timeout
            )
            
            if impl_addr and impl_addr != "0x" + "0" * 64:
                # 提取地址（后20字节）
                address = "0x" + impl_addr[-40:]
                if address != "0x" + "0" * 40:
                    logger.info(f"检测到EIP-1967代理合约，实现地址: {address}")
                    return address
            
        except Exception as e:
            logger.debug(f"EIP-1967检测失败: {e}")
        
        return None
    
    @staticmethod
    async def _check_openzeppelin_proxy(
        contract_address: str, 
        rpc_url: str, 
        timeout: int
    ) -> Optional[str]:
        """检查OpenZeppelin代理合约"""
        try:
            slot = ProxyContractDetector.PROXY_STORAGE_SLOTS["OZ_IMPLEMENTATION"]
            impl_addr = await ProxyContractDetector._read_storage_slot(
                contract_address, slot, rpc_url, timeout
            )
            
            if impl_addr and impl_addr != "0x" + "0" * 64:
                address = "0x" + impl_addr[-40:]
                if address != "0x" + "0" * 40:
                    logger.info(f"检测到OpenZeppelin代理合约，实现地址: {address}")
                    return address
            
        except Exception as e:
            logger.debug(f"OpenZeppelin代理检测失败: {e}")
        
        return None
    
    @staticmethod
    async def _check_delegatecall_pattern(
        contract_address: str, 
        rpc_url: str, 
        timeout: int
    ) -> bool:
        """检查合约bytecode是否包含delegatecall指令"""
        try:
            bytecode = await ProxyContractDetector._get_contract_bytecode(
                contract_address, rpc_url, timeout
            )
            
            if bytecode and len(bytecode) > 2:
                # 移除0x前缀
                code = bytecode[2:] if bytecode.startswith("0x") else bytecode
                # 检查是否包含delegatecall指令 (0xf4)
                if "f4" in code.lower():
                    logger.info(f"在合约 {contract_address} 中发现delegatecall指令")
                    return True
            
        except Exception as e:
            logger.debug(f"bytecode分析失败: {e}")
        
        return False
    
    @staticmethod
    async def _get_implementation_by_method_call(
        contract_address: str, 
        rpc_url: str, 
        timeout: int
    ) -> Optional[str]:
        """通过常见方法调用获取实现地址"""
        # 常见的获取实现地址的方法签名
        method_signatures = [
            "0x5c60da1b",  # implementation()
            "0x39bc9af7",  # implementation() - 另一种签名
            "0x4555d5c9",  # getImplementation()
            "0x0e61e117"   # getImplementationAddress()
        ]
        
        for signature in method_signatures:
            try:
                result = await ProxyContractDetector._call_contract_method(
                    contract_address, signature, rpc_url, timeout
                )
                
                if result and result != "0x" and len(result) >= 42:
                    # 提取地址（最后20字节）
                    address = "0x" + result[-40:]
                    if address != "0x" + "0" * 40:
                        logger.info(f"通过方法调用获取实现地址: {address}")
                        return address
                        
            except Exception as e:
                logger.debug(f"方法调用 {signature} 失败: {e}")
                continue
        
        return None
    
    @staticmethod
    async def _read_storage_slot(
        contract_address: str, 
        slot: str, 
        rpc_url: str, 
        timeout: int
    ) -> Optional[str]:
        """读取合约存储槽"""
        from app.config import settings
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getStorageAt",
            "params": [contract_address, slot, "latest"],
            "id": 1
        }
        
        # 使用更短的超时和连接配置
        timeout_config = aiohttp.ClientTimeout(total=timeout, connect=5, sock_read=timeout//2)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        
        # 获取代理配置
        proxy_url = settings.blockchain.https_proxy or settings.blockchain.http_proxy
        
        async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
            async with session.post(rpc_url, json=payload, proxy=proxy_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result")
        
        return None
    
    @staticmethod
    async def _get_contract_bytecode(
        contract_address: str, 
        rpc_url: str, 
        timeout: int
    ) -> Optional[str]:
        """获取合约bytecode"""
        from app.config import settings
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getCode",
            "params": [contract_address, "latest"],
            "id": 1
        }
        
        # 使用更短的超时和连接配置
        timeout_config = aiohttp.ClientTimeout(total=timeout, connect=5, sock_read=timeout//2)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        
        # 获取代理配置
        proxy_url = settings.blockchain.https_proxy or settings.blockchain.http_proxy
        
        async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
            async with session.post(rpc_url, json=payload, proxy=proxy_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result")
        
        return None
    
    @staticmethod
    async def _call_contract_method(
        contract_address: str, 
        method_signature: str, 
        rpc_url: str, 
        timeout: int
    ) -> Optional[str]:
        """调用合约方法"""
        from app.config import settings
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_call",
            "params": [{
                "to": contract_address,
                "data": method_signature
            }, "latest"],
            "id": 1
        }
        
        # 使用更短的超时和连接配置
        timeout_config = aiohttp.ClientTimeout(total=timeout, connect=5, sock_read=timeout//2)
        connector = aiohttp.TCPConnector(limit=10, limit_per_host=5)
        
        # 获取代理配置
        proxy_url = settings.blockchain.https_proxy or settings.blockchain.http_proxy
        
        async with aiohttp.ClientSession(timeout=timeout_config, connector=connector) as session:
            async with session.post(rpc_url, json=payload, proxy=proxy_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("result")
        
        return None


async def get_contract_implementation_address(
    contract_address: str,
    rpc_url: str,
    timeout: int = 30
) -> Optional[str]:
    """
    获取合约的真实实现地址（如果是代理合约）
    
    Args:
        contract_address: 合约地址
        rpc_url: RPC节点URL
        timeout: 请求超时时间
        
    Returns:
        实现合约地址，如果不是代理合约则返回原地址
    """
    result = await ProxyContractDetector.detect_proxy_contract(
        contract_address, rpc_url, timeout
    )
    
    if result["is_proxy"] and result["implementation_address"]:
        logger.info(f"代理合约 {contract_address} -> 实现合约 {result['implementation_address']}")
        return result["implementation_address"]
    
    return contract_address