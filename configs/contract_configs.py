"""合约监控配置文件"""
from typing import Dict, List, Any
from app.services.event_monitor import EventMonitorConfig
from app.utils.contract_utils import (
    get_standard_erc20_abi, 
    get_uniswap_v2_pair_abi, 
    get_uniswap_v3_pool_abi,
    WellKnownContracts
)


class ContractMonitorConfigs:
    """合约监控配置管理类"""
    
    # 以太坊主网配置
    ETHEREUM_CONFIGS = {
        # USDT监控配置
        "usdt_transfers": {
            "chain_name": "ethereum",
            "contract_address": WellKnownContracts.ETHEREUM["USDT"],
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Transfer"],
                output_format="detailed",
                poll_interval=2.0,
                custom_handler=None
            )
        },
        
        # USDC监控配置
        "usdc_transfers": {
            "chain_name": "ethereum",
            "contract_address": WellKnownContracts.ETHEREUM["USDC"],
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Transfer"],
                output_format="json",
                poll_interval=3.0
            )
        },
        
        # WETH监控配置
        "weth_all_events": {
            "chain_name": "ethereum",
            "contract_address": WellKnownContracts.ETHEREUM["WETH"],
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=None,  # 监控所有事件
                output_format="simple",
                poll_interval=5.0
            )
        }
    }
    
    # BSC配置
    BSC_CONFIGS = {
        # USDT BSC监控
        "usdt_bsc_transfers": {
            "chain_name": "bsc",
            "contract_address": WellKnownContracts.BSC["USDT"],
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Transfer"],
                output_format="detailed",
                poll_interval=1.0  # BSC出块更快
            )
        },
        
        # BUSD监控
        "busd_transfers": {
            "chain_name": "bsc",
            "contract_address": WellKnownContracts.BSC["BUSD"],
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Transfer", "Approval"],
                output_format="json",
                poll_interval=2.0
            )
        }
    }
    
    # Polygon配置
    POLYGON_CONFIGS = {
        # USDT Polygon监控
        "usdt_polygon_transfers": {
            "chain_name": "polygon",
            "contract_address": WellKnownContracts.POLYGON["USDT"],
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Transfer"],
                output_format="detailed",
                poll_interval=1.0  # Polygon出块快
            )
        }
    }
    
    # DEX监控配置（示例）
    DEX_CONFIGS = {
        # Uniswap V2监控配置示例
        "uniswap_v2_example": {
            "chain_name": "ethereum",
            "contract_address": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852",  # USDT/WETH pair
            "abi": get_uniswap_v2_pair_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Swap"],
                output_format="detailed",
                poll_interval=2.0
            )
        },
        
        # Uniswap V3监控配置示例
        "uniswap_v3_example": {
            "chain_name": "ethereum", 
            "contract_address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",  # USDC/WETH 0.3%
            "abi": get_uniswap_v3_pool_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Swap"],
                output_format="detailed",
                poll_interval=2.0
            )
        }
    }
    
    @classmethod
    def get_config(cls, config_name: str) -> Dict[str, Any]:
        """获取指定的配置"""
        all_configs = {
            **cls.ETHEREUM_CONFIGS,
            **cls.BSC_CONFIGS,
            **cls.POLYGON_CONFIGS,
            **cls.DEX_CONFIGS
        }
        
        if config_name not in all_configs:
            raise ValueError(f"配置 '{config_name}' 不存在")
        
        return all_configs[config_name]
    
    @classmethod
    def list_available_configs(cls) -> List[str]:
        """列出所有可用的配置"""
        configs = []
        configs.extend(cls.ETHEREUM_CONFIGS.keys())
        configs.extend(cls.BSC_CONFIGS.keys())
        configs.extend(cls.POLYGON_CONFIGS.keys())
        configs.extend(cls.DEX_CONFIGS.keys())
        return configs
    
    @classmethod
    def get_configs_by_chain(cls, chain_name: str) -> Dict[str, Dict[str, Any]]:
        """根据链名称获取配置"""
        if chain_name == "ethereum":
            return cls.ETHEREUM_CONFIGS
        elif chain_name == "bsc":
            return cls.BSC_CONFIGS
        elif chain_name == "polygon":
            return cls.POLYGON_CONFIGS
        else:
            return {}


# 自定义事件处理函数示例
async def large_transfer_handler(event_data: Dict[str, Any]):
    """大额转账处理函数"""
    if event_data.get("event_name") == "Transfer":
        args = event_data.get("args", {})
        value = args.get("value", 0)
        
        # 根据不同代币设置不同的阈值
        contract_address = event_data.get("contract_address", "").lower()
        
        # USDT (6位小数)
        if contract_address == WellKnownContracts.ETHEREUM["USDT"].lower():
            threshold = 100000 * 10**6  # 10万USDT
            decimals = 6
            symbol = "USDT"
        # USDC (6位小数)
        elif contract_address == WellKnownContracts.ETHEREUM["USDC"].lower():
            threshold = 100000 * 10**6  # 10万USDC
            decimals = 6
            symbol = "USDC"
        # WETH (18位小数)
        elif contract_address == WellKnownContracts.ETHEREUM["WETH"].lower():
            threshold = 100 * 10**18  # 100 WETH
            decimals = 18
            symbol = "WETH"
        else:
            return  # 未知代币，不处理
        
        if isinstance(value, (int, str)) and int(value) > threshold:
            amount = int(value) / (10 ** decimals)
            print(f"🔥 大额{symbol}转账: {amount:,.2f} {symbol}")
            print(f"   发送方: {args.get('from', 'N/A')}")
            print(f"   接收方: {args.get('to', 'N/A')}")
            print(f"   TX: {event_data.get('transaction_hash', 'N/A')}")
            print()


async def dex_swap_handler(event_data: Dict[str, Any]):
    """DEX交换事件处理函数"""
    if event_data.get("event_name") == "Swap":
        args = event_data.get("args", {})
        
        print(f"💱 DEX交换事件:")
        print(f"   合约: {event_data.get('contract_address', 'N/A')}")
        print(f"   发起方: {args.get('sender', 'N/A')}")
        print(f"   接收方: {args.get('to', 'N/A')}")
        
        # Uniswap V2格式
        if 'amount0In' in args:
            print(f"   输入0: {args.get('amount0In', 0)}")
            print(f"   输入1: {args.get('amount1In', 0)}")
            print(f"   输出0: {args.get('amount0Out', 0)}")
            print(f"   输出1: {args.get('amount1Out', 0)}")
        
        # Uniswap V3格式
        elif 'amount0' in args:
            print(f"   数量0: {args.get('amount0', 0)}")
            print(f"   数量1: {args.get('amount1', 0)}")
            print(f"   流动性: {args.get('liquidity', 0)}")
        
        print(f"   TX: {event_data.get('transaction_hash', 'N/A')}")
        print()


# 带自定义处理函数的配置
CUSTOM_HANDLER_CONFIGS = {
    # 大额转账监控
    "large_transfers_usdt": {
        "chain_name": "ethereum",
        "contract_address": WellKnownContracts.ETHEREUM["USDT"],
        "abi": get_standard_erc20_abi(),
        "config": EventMonitorConfig(
            mode="realtime",
            events_to_monitor=["Transfer"],
            output_format="simple",
            poll_interval=2.0,
            custom_handler=large_transfer_handler
        )
    },
    
    # DEX交换监控
    "dex_swaps_monitor": {
        "chain_name": "ethereum",
        "contract_address": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852",  # USDT/WETH pair
        "abi": get_uniswap_v2_pair_abi(),
        "config": EventMonitorConfig(
            mode="realtime",
            events_to_monitor=["Swap"],
            output_format="simple",
            poll_interval=3.0,
            custom_handler=dex_swap_handler
        )
    }
}


class QuickStartConfigs:
    """快速启动配置"""
    
    @staticmethod
    def get_basic_erc20_monitor(contract_address: str, chain_name: str = "ethereum") -> Dict[str, Any]:
        """获取基本的ERC20监控配置"""
        return {
            "chain_name": chain_name,
            "contract_address": contract_address,
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="realtime",
                events_to_monitor=["Transfer"],
                output_format="detailed",
                poll_interval=2.0
            )
        }
    
    @staticmethod
    def get_historical_monitor(contract_address: str, start_block: int, end_block: int, chain_name: str = "ethereum") -> Dict[str, Any]:
        """获取历史监控配置"""
        return {
            "chain_name": chain_name,
            "contract_address": contract_address,
            "abi": get_standard_erc20_abi(),
            "config": EventMonitorConfig(
                mode="historical",
                start_block=start_block,
                end_block=end_block,
                events_to_monitor=["Transfer"],
                output_format="json",
                batch_size=50
            )
        }