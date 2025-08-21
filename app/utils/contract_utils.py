"""合约相关工具函数"""
import json
from typing import List, Dict, Any, Optional
from pathlib import Path


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