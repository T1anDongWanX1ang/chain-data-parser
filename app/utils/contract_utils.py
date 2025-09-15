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
            "0x0e61e117",  # getImplementationAddress()
            "0x0ac7c44c",  # target() - 一些代理合约使用这个
            "0x65fb1017",  # proxy() - 另一种代理方法
            "0x6ba9f3d8"   # getTarget() - 目标地址获取
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
        
        # 尝试从存储槽读取更多可能的代理地址位置
        additional_slots = [
            "0x0000000000000000000000000000000000000000000000000000000000000000",  # slot 0
            "0x0000000000000000000000000000000000000000000000000000000000000001",  # slot 1
            "0x0000000000000000000000000000000000000000000000000000000000000002",  # slot 2
            "0xc5f16f0fcc639fa48a6947836d9850f504798523bf8c9a3a87d5876cf622bcf7",  # compound proxy
        ]
        
        for slot in additional_slots:
            try:
                result = await ProxyContractDetector._read_storage_slot(
                    contract_address, slot, rpc_url, timeout
                )
                
                if result and result != "0x" + "0" * 64:
                    address = "0x" + result[-40:]
                    if address != "0x" + "0" * 40:
                        logger.info(f"从存储槽 {slot} 获取实现地址: {address}")
                        return address
                        
            except Exception as e:
                logger.debug(f"读取存储槽 {slot} 失败: {e}")
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


class AdvancedProxyAnalyzer:
    """高级代理合约分析器"""
    
    @staticmethod
    async def advanced_proxy_analysis(
        contract_address: str,
        rpc_url: str,
        chain_name: str = "ethereum",
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        高级代理合约分析，使用多种技术获取实现地址
        
        Args:
            contract_address: 合约地址
            rpc_url: RPC节点URL
            chain_name: 链名称
            timeout: 请求超时时间
            
        Returns:
            分析结果包含所有可能的实现地址
        """
        result = {
            "contract_address": contract_address,
            "implementation_addresses": [],
            "creation_info": None,
            "bytecode_analysis": {},
            "transaction_analysis": {},
            "error": None
        }
        
        try:
            # 1. 历史交易分析
            logger.info(f"开始分析合约 {contract_address} 的历史交易")
            tx_analysis = await AdvancedProxyAnalyzer._analyze_creation_transaction(
                contract_address, rpc_url, chain_name, timeout
            )
            result["transaction_analysis"] = tx_analysis
            
            # 2. 深度字节码分析
            logger.info(f"开始深度分析合约 {contract_address} 的字节码")
            bytecode_analysis = await AdvancedProxyAnalyzer._deep_bytecode_analysis(
                contract_address, rpc_url, timeout
            )
            result["bytecode_analysis"] = bytecode_analysis
            
            # 3. 从多种来源收集实现地址
            addresses = set()
            
            # 从交易分析中获取
            if tx_analysis.get("proxy_factory_pattern"):
                factory_addr = tx_analysis["proxy_factory_pattern"].get("master_copy")
                if factory_addr:
                    addresses.add(factory_addr)
            
            if tx_analysis.get("constructor_args"):
                for arg in tx_analysis["constructor_args"]:
                    if AdvancedProxyAnalyzer._is_valid_address(arg):
                        addresses.add(arg)
            
            # 从字节码分析中获取
            if bytecode_analysis.get("hardcoded_addresses"):
                addresses.update(bytecode_analysis["hardcoded_addresses"])
            
            # 4. 事件日志分析
            logger.info(f"分析合约 {contract_address} 的升级事件")
            upgrade_events = await AdvancedProxyAnalyzer._analyze_upgrade_events(
                contract_address, rpc_url, timeout
            )
            
            for event in upgrade_events:
                if event.get("new_implementation"):
                    addresses.add(event["new_implementation"])
            
            # 5. 特殊模式检测 - 添加已知的代理合约模式
            special_addresses = await AdvancedProxyAnalyzer._check_special_proxy_patterns(
                contract_address, rpc_url, timeout
            )
            addresses.update(special_addresses)
            
            # 6. 验证和过滤地址
            valid_addresses = []
            for addr in addresses:
                if await AdvancedProxyAnalyzer._verify_implementation_address(
                    addr, rpc_url, timeout
                ):
                    valid_addresses.append(addr)
            
            result["implementation_addresses"] = valid_addresses
            
            logger.info(
                f"高级分析完成，为合约 {contract_address} 找到 {len(valid_addresses)} 个可能的实现地址"
            )
            
        except Exception as e:
            logger.error(f"高级代理分析失败: {e}")
            result["error"] = str(e)
        
        return result
    
    @staticmethod
    async def _analyze_creation_transaction(
        contract_address: str,
        rpc_url: str,
        chain_name: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        分析合约创建交易获取代理信息
        """
        result = {
            "creation_tx": None,
            "creator_address": None,
            "constructor_args": [],
            "proxy_factory_pattern": None
        }
        
        try:
            # 通过区块链浏览器API获取创建交易
            creation_info = await AdvancedProxyAnalyzer._get_contract_creation_info(
                contract_address, chain_name, timeout
            )
            
            if creation_info:
                result["creation_tx"] = creation_info.get("txhash")
                result["creator_address"] = creation_info.get("from")
                
                # 解析构造函数参数
                input_data = creation_info.get("input", "")
                if input_data and len(input_data) > 10:
                    constructor_args = AdvancedProxyAnalyzer._parse_constructor_args(input_data)
                    result["constructor_args"] = constructor_args
                
                # 检查是否为工厂模式代理
                factory_info = await AdvancedProxyAnalyzer._check_factory_pattern(
                    creation_info.get("from"), rpc_url, timeout
                )
                result["proxy_factory_pattern"] = factory_info
                
        except Exception as e:
            logger.debug(f"创建交易分析失败: {e}")
        
        return result
    
    @staticmethod
    async def _deep_bytecode_analysis(
        contract_address: str,
        rpc_url: str,
        timeout: int
    ) -> Dict[str, Any]:
        """
        深度分析合约字节码
        """
        result = {
            "bytecode_size": 0,
            "has_delegatecall": False,
            "has_callcode": False,
            "hardcoded_addresses": [],
            "assembly_patterns": []
        }
        
        try:
            bytecode = await ProxyContractDetector._get_contract_bytecode(
                contract_address, rpc_url, timeout
            )
            
            if not bytecode or bytecode == "0x":
                return result
            
            code = bytecode[2:] if bytecode.startswith("0x") else bytecode
            result["bytecode_size"] = len(code) // 2
            
            # 检查指令模式
            result["has_delegatecall"] = "f4" in code.lower()
            result["has_callcode"] = "f2" in code.lower()
            
            # 提取可能的地址
            addresses = AdvancedProxyAnalyzer._extract_addresses_from_bytecode(code)
            result["hardcoded_addresses"] = addresses
            
            # 分析汇编模式
            patterns = AdvancedProxyAnalyzer._analyze_assembly_patterns(code)
            result["assembly_patterns"] = patterns
            
        except Exception as e:
            logger.debug(f"字节码分析失败: {e}")
        
        return result
    
    @staticmethod
    async def _analyze_upgrade_events(
        contract_address: str,
        rpc_url: str,
        timeout: int
    ) -> List[Dict[str, Any]]:
        """
        分析代理合约的升级事件
        """
        events = []
        
        try:
            # 常见的升级事件签名
            upgrade_topics = [
                "0xbc7cd75a20ee27fd9adebab32041f755214dbc6bffa90cc0225b39da2e5c2d3b",  # Upgraded(address)
                "0x7e644d79422f17c01e4894b5f4f588d331ebfa28653d42ae832dc59e38c9798f",  # AdminChanged
                "0xa78a17b0bcf19b95d46d53ddf59df127b353fdf4b7bc34b9c5d04c8e12c06dc1",  # ImplementationUpdated
            ]
            
            for topic in upgrade_topics:
                try:
                    logs = await AdvancedProxyAnalyzer._get_event_logs(
                        contract_address, topic, rpc_url, timeout
                    )
                    
                    for log in logs:
                        event_data = AdvancedProxyAnalyzer._parse_upgrade_event(log)
                        if event_data:
                            events.append(event_data)
                            
                except Exception as e:
                    logger.debug(f"获取升级事件失败 {topic}: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"升级事件分析失败: {e}")
        
        return events
    
    @staticmethod
    def _extract_addresses_from_bytecode(bytecode: str) -> List[str]:
        """
        从字节码中提取可能的地址
        """
        addresses = []
        
        # 查找20字节的地址模式
        import re
        
        # 地址通常以0x开头，或者在字节码中以00000000000000000000...开头
        # 查找可能的地址模式（40个十六进制字符）
        address_pattern = r'([0-9a-fA-F]{40})'
        matches = re.findall(address_pattern, bytecode)
        
        for match in matches:
            # 过滤掉全0或明显不是地址的值
            if match != "0" * 40 and not match.startswith("ffffff"):
                address = "0x" + match.lower()
                if AdvancedProxyAnalyzer._is_valid_address(address):
                    addresses.append(address)
        
        # 更精细的模式匹配 - 查找特定的存储/加载模式
        # 查找PUSH20指令后的地址 (0x73 + 20字节地址)
        push20_pattern = r'73([0-9a-fA-F]{40})'
        push20_matches = re.findall(push20_pattern, bytecode, re.IGNORECASE)
        
        for match in push20_matches:
            if match != "0" * 40:
                address = "0x" + match.lower()
                if AdvancedProxyAnalyzer._is_valid_address(address):
                    addresses.append(address)
                    logger.info(f"从PUSH20指令中提取到地址: {address}")
        
        # 查找可能的存储槽模式 - 地址可能存储在特定位置
        # 查找常见的代理模式：EXTCODESIZE, DELEGATECALL等指令序列附近的地址
        delegatecall_pattern = r'f4.{0,100}73([0-9a-fA-F]{40})'
        delegatecall_matches = re.findall(delegatecall_pattern, bytecode, re.IGNORECASE)
        
        for match in delegatecall_matches:
            if match != "0" * 40:
                address = "0x" + match.lower()
                if AdvancedProxyAnalyzer._is_valid_address(address):
                    addresses.append(address)
                    logger.info(f"从DELEGATECALL附近提取到地址: {address}")
        
        return list(set(addresses))  # 去重
    
    @staticmethod
    def _analyze_assembly_patterns(bytecode: str) -> List[str]:
        """
        分析汇编模式
        """
        patterns = []
        
        # 检查常见的代理模式
        if "3d3d3d3d363d3d37363d73" in bytecode.lower():
            patterns.append("minimal_proxy_pattern")
        
        if "36600080376020600036600073" in bytecode.lower():
            patterns.append("openzeppelin_proxy_pattern")
        
        if "60806040526004361061" in bytecode.lower():
            patterns.append("standard_proxy_selector")
        
        return patterns
    
    @staticmethod
    async def _get_contract_creation_info(
        contract_address: str,
        chain_name: str,
        timeout: int
    ) -> Optional[Dict[str, Any]]:
        """
        获取合约创建信息
        """
        try:
            if chain_name.lower() == "ethereum":
                # 使用Etherscan API
                api_key = "YourEtherscanAPIKey"  # 实际应用中应该从配置获取
                url = f"https://api.etherscan.io/api?module=contract&action=getcontractcreation&contractaddresses={contract_address}&apikey={api_key}"
                
                async with aiohttp.ClientSession() as session:
                    async with session.get(url, timeout=timeout) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data.get("status") == "1" and data.get("result"):
                                return data["result"][0]
        
        except Exception as e:
            logger.debug(f"获取创建信息失败: {e}")
        
        return None
    
    @staticmethod
    def _parse_constructor_args(input_data: str) -> List[str]:
        """
        解析构造函数参数
        """
        args = []
        
        try:
            # 移除函数选择器（前8个字符）
            if len(input_data) > 10:
                data = input_data[10:]
                
                # 每32字节为一个参数
                for i in range(0, len(data), 64):
                    if i + 64 <= len(data):
                        arg = data[i:i+64]
                        # 检查是否为地址（后40个字符）
                        if arg.startswith("000000000000000000000000"):
                            address = "0x" + arg[24:]
                            if AdvancedProxyAnalyzer._is_valid_address(address):
                                args.append(address)
                        else:
                            args.append("0x" + arg)
        
        except Exception as e:
            logger.debug(f"解析构造函数参数失败: {e}")
        
        return args
    
    @staticmethod
    async def _check_factory_pattern(
        creator_address: str,
        rpc_url: str,
        timeout: int
    ) -> Optional[Dict[str, Any]]:
        """
        检查是否为工厂模式代理
        """
        try:
            # 检查创建者是否为已知的代理工厂
            known_factories = {
                "0xa6b71e26c5e0845f74c812102ca7114b6a896ab2": "gnosis_safe_factory",
                "0x76e2cfc1f5fa8f6a5b3fc4c8f4788f0116861f9b": "1967_factory",
                "0x4e59b44847b379578588920ca78fbf26c0b4956c": "create2_factory"
            }
            
            factory_type = known_factories.get(creator_address.lower())
            if factory_type:
                return {
                    "is_factory_pattern": True,
                    "factory_type": factory_type,
                    "factory_address": creator_address
                }
        
        except Exception as e:
            logger.debug(f"工厂模式检查失败: {e}")
        
        return None
    
    @staticmethod
    async def _check_special_proxy_patterns(
        contract_address: str,
        rpc_url: str,
        timeout: int
    ) -> set:
        """
        检查特殊的代理合约模式和已知映射
        """
        special_addresses = set()
        
        try:
            # 调试信息
            logger.info(f"正在检查特殊代理模式，输入地址: {contract_address}")
            
            # 尝试一些特殊的存储槽读取模式
            special_slots = [
                # 一些自定义代理可能使用的特殊槽位
                "0x" + "0" * 63 + "3",  # slot 3
                "0x" + "0" * 63 + "4",  # slot 4
                "0x" + "0" * 63 + "5",  # slot 5
                # 基于合约地址计算的槽位 - 先注释掉Web3依赖，使用固定值
                # Web3.keccak(text="implementation.address").hex(),
                # Web3.keccak(text="proxy.implementation").hex(),
                "0xa8cc81bb9aed42d7ab3ea5baecdfee05e7a3f2ad00ae99c5d91ebf481b9d6b2c",  # 常见实现槽
                "0x7050c9e0f4ca769c69bd3a8ef740bc37934f8e2c036e5a723fd8ee048ed3f8c3",  # 备用槽
            ]
            
            for slot in special_slots:
                try:
                    result = await ProxyContractDetector._read_storage_slot(
                        contract_address, slot, rpc_url, timeout
                    )
                    
                    if result and result != "0x" + "0" * 64:
                        # 尝试提取地址
                        if len(result) >= 42:
                            address = "0x" + result[-40:]
                            if AdvancedProxyAnalyzer._is_valid_address(address) and address != "0x" + "0" * 40:
                                special_addresses.add(address)
                                logger.info(f"从特殊存储槽 {slot} 找到地址: {address}")
                                
                except Exception as e:
                    logger.debug(f"读取特殊存储槽 {slot} 失败: {e}")
                    continue
            
            # 尝试一些特殊的方法调用
            special_methods = [
                "0x4c0195e5",  # owner()
                "0x8da5cb5b",  # owner() - 另一种签名
                "0xf851a440",  # admin()
                "0x84ef8ffc",  # proxy_admin()
                "0x21f8a721", # implementation_address()
            ]
            
            for method in special_methods:
                try:
                    result = await ProxyContractDetector._call_contract_method(
                        contract_address, method, rpc_url, timeout
                    )
                    
                    if result and result != "0x" and len(result) >= 42:
                        address = "0x" + result[-40:]
                        if AdvancedProxyAnalyzer._is_valid_address(address) and address != "0x" + "0" * 40:
                            special_addresses.add(address)
                            logger.info(f"从特殊方法 {method} 找到地址: {address}")
                            
                except Exception as e:
                    logger.debug(f"调用特殊方法 {method} 失败: {e}")
                    continue
                    
        except Exception as e:
            logger.debug(f"特殊模式检测失败: {e}")
        
        return special_addresses
    
    @staticmethod
    async def _get_event_logs(
        contract_address: str,
        topic: str,
        rpc_url: str,
        timeout: int
    ) -> List[Dict[str, Any]]:
        """
        获取事件日志
        """
        from app.config import settings
        
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getLogs",
            "params": [{
                "address": contract_address,
                "topics": [topic],
                "fromBlock": "0x0",
                "toBlock": "latest"
            }],
            "id": 1
        }
        
        timeout_config = aiohttp.ClientTimeout(total=timeout)
        proxy_url = settings.blockchain.https_proxy or settings.blockchain.http_proxy
        
        try:
            async with aiohttp.ClientSession(timeout=timeout_config) as session:
                async with session.post(rpc_url, json=payload, proxy=proxy_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("result", [])
        except Exception as e:
            logger.debug(f"获取事件日志失败: {e}")
        
        return []
    
    @staticmethod
    def _parse_upgrade_event(log: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        解析升级事件
        """
        try:
            topics = log.get("topics", [])
            data = log.get("data", "")
            
            if len(topics) >= 2:
                # 通常新实现地址在第二个topic或data中
                new_impl = topics[1] if len(topics) > 1 else None
                if new_impl and len(new_impl) == 66:  # 0x + 64字符
                    address = "0x" + new_impl[26:]  # 提取地址部分
                    if AdvancedProxyAnalyzer._is_valid_address(address):
                        return {
                            "block_number": log.get("blockNumber"),
                            "transaction_hash": log.get("transactionHash"),
                            "new_implementation": address
                        }
        
        except Exception as e:
            logger.debug(f"解析升级事件失败: {e}")
        
        return None
    
    @staticmethod
    async def _verify_implementation_address(
        address: str,
        rpc_url: str,
        timeout: int
    ) -> bool:
        """
        验证地址是否为有效的合约地址
        """
        try:
            if not AdvancedProxyAnalyzer._is_valid_address(address):
                return False
            
            # 检查是否有代码
            bytecode = await ProxyContractDetector._get_contract_bytecode(
                address, rpc_url, timeout
            )
            
            return bytecode and bytecode != "0x" and len(bytecode) > 2
        
        except Exception:
            return False
    
    @staticmethod
    def _is_valid_address(address: str) -> bool:
        """
        检查是否为有效的以太坊地址
        """
        if not address or not isinstance(address, str):
            return False
        
        if not address.startswith("0x") or len(address) != 42:
            return False
        
        try:
            int(address[2:], 16)
            return True
        except ValueError:
            return False