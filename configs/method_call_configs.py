"""合约方法调用配置文件"""
from typing import Dict, List, Any
from app.services.contract_caller import MethodCallConfig
from app.utils.contract_utils import (
    get_standard_erc20_abi,
    get_uniswap_v2_pair_abi,
    get_uniswap_v3_pool_abi,
    WellKnownContracts
)


class ContractMethodConfigs:
    """合约方法调用配置管理类"""
    
    # ERC20代币配置
    ERC20_CONFIGS = {
        # USDT基本信息查询
        "usdt_info": {
            "chain_name": "ethereum",
            "contract_address": WellKnownContracts.ETHEREUM["USDT"],
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "name"},
                    {"method_name": "symbol"},
                    {"method_name": "decimals"},
                    {"method_name": "totalSupply"}
                ],
                call_interval=60.0,  # 1分钟查询一次
                output_format="detailed"
            )
        },
        
        # USDC信息查询
        "usdc_info": {
            "chain_name": "ethereum",
            "contract_address": WellKnownContracts.ETHEREUM["USDC"],
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "name"},
                    {"method_name": "symbol"},
                    {"method_name": "decimals"},
                    {"method_name": "totalSupply"}
                ],
                call_interval=60.0,
                output_format="json"
            )
        },
        
        # WETH信息查询
        "weth_info": {
            "chain_name": "ethereum",
            "contract_address": WellKnownContracts.ETHEREUM["WETH"],
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "name"},
                    {"method_name": "symbol"},
                    {"method_name": "decimals"},
                    {"method_name": "totalSupply"}
                ],
                call_interval=30.0,
                output_format="simple"
            )
        }
    }
    
    # BSC代币配置
    BSC_CONFIGS = {
        # BSC USDT信息
        "usdt_bsc_info": {
            "chain_name": "bsc",
            "contract_address": WellKnownContracts.BSC["USDT"],
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "name"},
                    {"method_name": "symbol"},
                    {"method_name": "decimals"},
                    {"method_name": "totalSupply"}
                ],
                call_interval=45.0,
                output_format="detailed"
            )
        },
        
        # BUSD信息
        "busd_info": {
            "chain_name": "bsc",
            "contract_address": WellKnownContracts.BSC["BUSD"],
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "name"},
                    {"method_name": "symbol"},
                    {"method_name": "decimals"},
                    {"method_name": "totalSupply"}
                ],
                call_interval=60.0,
                output_format="json"
            )
        }
    }
    
    # Uniswap配置
    UNISWAP_CONFIGS = {
        # Uniswap V2 USDT/WETH池信息
        "uniswap_v2_usdt_weth": {
            "chain_name": "ethereum",
            "contract_address": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852",  # USDT/WETH pair
            "abi": get_uniswap_v2_pair_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "token0"},
                    {"method_name": "token1"},
                    {"method_name": "getReserves"}
                ],
                call_interval=20.0,  # 20秒查询一次流动性
                output_format="detailed"
            )
        },
        
        # Uniswap V3 USDC/WETH池信息
        "uniswap_v3_usdc_weth": {
            "chain_name": "ethereum",
            "contract_address": "0x8ad599c3A0ff1De082011EFDDc58f1908eb6e6D8",  # USDC/WETH 0.3%
            "abi": get_uniswap_v3_pool_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "token0"},
                    {"method_name": "token1"},
                    {"method_name": "fee"}
                ],
                call_interval=30.0,
                output_format="detailed"
            )
        }
    }
    
    @classmethod
    def get_config(cls, config_name: str) -> Dict[str, Any]:
        """获取指定的配置"""
        all_configs = {
            **cls.ERC20_CONFIGS,
            **cls.BSC_CONFIGS,
            **cls.UNISWAP_CONFIGS
        }
        
        if config_name not in all_configs:
            raise ValueError(f"配置 '{config_name}' 不存在")
        
        return all_configs[config_name]
    
    @classmethod
    def list_available_configs(cls) -> List[str]:
        """列出所有可用的配置"""
        configs = []
        configs.extend(cls.ERC20_CONFIGS.keys())
        configs.extend(cls.BSC_CONFIGS.keys())
        configs.extend(cls.UNISWAP_CONFIGS.keys())
        return configs
    
    @classmethod
    def get_configs_by_chain(cls, chain_name: str) -> Dict[str, Dict[str, Any]]:
        """根据链名称获取配置"""
        if chain_name == "ethereum":
            return {**cls.ERC20_CONFIGS, **cls.UNISWAP_CONFIGS}
        elif chain_name == "bsc":
            return cls.BSC_CONFIGS
        else:
            return {}


# 余额监控配置
def create_balance_monitor_config(
    contract_address: str,
    addresses_to_monitor: List[str],
    chain_name: str = "ethereum",
    interval: float = 30.0
) -> Dict[str, Any]:
    """创建余额监控配置"""
    scheduled_calls = []
    for address in addresses_to_monitor:
        scheduled_calls.append({
            "method_name": "balanceOf",
            "arguments": [address]
        })
    
    return {
        "chain_name": chain_name,
        "contract_address": contract_address,
        "abi": get_standard_erc20_abi(),
        "config": MethodCallConfig(
            call_type="call",
            scheduled_calls=scheduled_calls,
            call_interval=interval,
            output_format="simple",
            custom_handler=balance_change_handler
        )
    }


# 自定义处理函数示例
async def balance_change_handler(result_data: Dict[str, Any]):
    """余额变化处理函数"""
    if result_data.get("success") and result_data.get("method_name") == "balanceOf":
        args = result_data.get("arguments", [])
        balance = result_data.get("result", 0)
        
        if args:
            address = args[0]
            # 这里可以添加余额变化检测逻辑
            # 例如：存储历史余额，比较变化等
            if isinstance(balance, (int, str)) and int(balance) > 0:
                formatted_balance = int(balance) / 10**6  # 假设是USDT，6位小数
                if formatted_balance > 1000000:  # 大于100万
                    print(f"💰 发现巨鲸地址: {address}")
                    print(f"   余额: {formatted_balance:,.2f} USDT")
                    print()


async def price_change_handler(result_data: Dict[str, Any]):
    """价格变化处理函数"""
    if result_data.get("success") and result_data.get("method_name") == "getReserves":
        reserves = result_data.get("result", [])
        
        if len(reserves) >= 2:
            reserve0 = int(reserves[0])
            reserve1 = int(reserves[1])
            
            # 计算价格（简化计算）
            if reserve0 > 0 and reserve1 > 0:
                # 假设token0是USDT(6位小数)，token1是WETH(18位小数)
                price = (reserve0 / 10**6) / (reserve1 / 10**18)
                print(f"📈 当前ETH价格: ${price:,.2f}")
                print(f"   储备量 - USDT: {reserve0/10**6:,.2f}, WETH: {reserve1/10**18:,.4f}")
                print()


# 带自定义处理函数的配置
CUSTOM_HANDLER_CONFIGS = {
    # 巨鲸地址监控
    "whale_balance_monitor": {
        "chain_name": "ethereum",
        "contract_address": WellKnownContracts.ETHEREUM["USDT"],
        "abi": get_standard_erc20_abi(),
        "config": MethodCallConfig(
            call_type="call",
            scheduled_calls=[
                {"method_name": "balanceOf", "arguments": ["0x742d35cc6b5A8e1c0935C0013B1e7b8B831C9A0C"]},
                {"method_name": "balanceOf", "arguments": ["0x28C6c06298d514Db089934071355E5743bf21d60"]},
                {"method_name": "balanceOf", "arguments": ["0x21a31Ee1afC51d94C2eFcCAa2092aD1028285549"]}
            ],
            call_interval=60.0,
            output_format="simple",
            custom_handler=balance_change_handler
        )
    },
    
    # 价格监控
    "eth_price_monitor": {
        "chain_name": "ethereum",
        "contract_address": "0x0d4a11d5EEaaC28EC3F61d100daF4d40471f1852",  # USDT/WETH pair
        "abi": get_uniswap_v2_pair_abi(),
        "config": MethodCallConfig(
            call_type="call",
            scheduled_calls=[
                {"method_name": "getReserves"}
            ],
            call_interval=30.0,
            output_format="simple",
            custom_handler=price_change_handler
        )
    }
}


class QuickStartMethodConfigs:
    """快速启动方法配置"""
    
    @staticmethod
    def get_basic_erc20_info(contract_address: str, chain_name: str = "ethereum") -> Dict[str, Any]:
        """获取基本ERC20信息配置"""
        return {
            "chain_name": chain_name,
            "contract_address": contract_address,
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[
                    {"method_name": "name"},
                    {"method_name": "symbol"},
                    {"method_name": "decimals"},
                    {"method_name": "totalSupply"}
                ],
                call_interval=60.0,
                output_format="detailed"
            )
        }
    
    @staticmethod
    def get_single_method_call(
        contract_address: str,
        method_name: str,
        method_args: List[Any] = None,
        chain_name: str = "ethereum"
    ) -> Dict[str, Any]:
        """获取单方法调用配置"""
        return {
            "chain_name": chain_name,
            "contract_address": contract_address,
            "abi": get_standard_erc20_abi(),  # 可以根据需要更换ABI
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=[{
                    "method_name": method_name,
                    "arguments": method_args or []
                }],
                call_interval=3600.0,  # 用于单次调用
                output_format="detailed"
            )
        }
    
    @staticmethod
    def get_balance_monitor(
        contract_address: str,
        addresses: List[str],
        chain_name: str = "ethereum",
        interval: float = 30.0
    ) -> Dict[str, Any]:
        """获取余额监控配置"""
        scheduled_calls = []
        for address in addresses:
            scheduled_calls.append({
                "method_name": "balanceOf",
                "arguments": [address]
            })
        
        return {
            "chain_name": chain_name,
            "contract_address": contract_address,
            "abi": get_standard_erc20_abi(),
            "config": MethodCallConfig(
                call_type="call",
                scheduled_calls=scheduled_calls,
                call_interval=interval,
                output_format="simple"
            )
        }