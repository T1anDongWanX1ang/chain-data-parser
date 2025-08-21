"""
事件查询配置文件

用于管理不同事件类型的查询配置，支持可配置的事件参数查询。
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field


@dataclass
class EventQueryMethod:
    """事件查询方法配置"""
    method_name: str
    params: List[str] = field(default_factory=list)
    description: str = ""
    required: bool = False


@dataclass
class EventMappingRule:
    """事件映射规则配置"""
    source_key: str
    target_key: str
    transformer: str = None
    description: str = ""
    required: bool = False


@dataclass
class EventQueryConfig:
    """事件查询配置"""
    event_name: str
    contract_address: str
    abi: List[Dict]
    query_methods: List[EventQueryMethod] = field(default_factory=list)
    mapping_rules: List[EventMappingRule] = field(default_factory=list)
    kafka_topic: str = "blockchain-events"
    chain_name: str = "ethereum"
    enabled: bool = True


class EventQueryConfigs:
    """事件查询配置管理器"""
    
    @staticmethod
    def get_erc20_transfer_config() -> EventQueryConfig:
        """获取ERC20转账事件配置"""
        
        # ERC20 ABI
        erc20_abi = [
            {
                "type": "event",
                "name": "Transfer",
                "inputs": [
                    {"name": "from", "type": "address", "indexed": True},
                    {"name": "to", "type": "address", "indexed": True},
                    {"name": "value", "type": "uint256", "indexed": False}
                ]
            },
            {
                "type": "function",
                "name": "name",
                "inputs": [],
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "symbol",
                "inputs": [],
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "decimals",
                "inputs": [],
                "outputs": [{"name": "", "type": "uint8"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "balanceOf",
                "inputs": [{"name": "account", "type": "address"}],
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "totalSupply",
                "inputs": [],
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view"
            }
        ]
        
        # 查询方法配置
        query_methods = [
            EventQueryMethod(
                method_name="name",
                params=[],
                description="获取代币名称",
                required=True
            ),
            EventQueryMethod(
                method_name="symbol",
                params=[],
                description="获取代币符号",
                required=True
            ),
            EventQueryMethod(
                method_name="decimals",
                params=[],
                description="获取代币精度",
                required=True
            ),
            EventQueryMethod(
                method_name="balanceOf",
                params=["event.args.to"],
                description="获取接收方余额",
                required=False
            ),
            EventQueryMethod(
                method_name="totalSupply",
                params=[],
                description="获取总供应量",
                required=False
            )
        ]
        
        # 映射规则配置
        mapping_rules = [
            EventMappingRule(
                source_key="event.args.from",
                target_key="from_address",
                transformer="to_lowercase",
                description="发送方地址"
            ),
            EventMappingRule(
                source_key="event.args.to",
                target_key="to_address",
                transformer="to_lowercase",
                description="接收方地址"
            ),
            EventMappingRule(
                source_key="event.args.value",
                target_key="transfer_amount",
                transformer="to_string",
                description="转账金额"
            ),
            EventMappingRule(
                source_key="query_results.name",
                target_key="token_name",
                description="代币名称"
            ),
            EventMappingRule(
                source_key="query_results.symbol",
                target_key="token_symbol",
                description="代币符号"
            ),
            EventMappingRule(
                source_key="query_results.decimals",
                target_key="token_decimals",
                transformer="to_int",
                description="代币精度"
            ),
            EventMappingRule(
                source_key="query_results.balanceOf",
                target_key="recipient_balance",
                transformer="to_string",
                description="接收方余额"
            ),
            EventMappingRule(
                source_key="query_results.totalSupply",
                target_key="total_supply",
                transformer="to_string",
                description="总供应量"
            )
        ]
        
        return EventQueryConfig(
            event_name="Transfer",
            contract_address="0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8",  # 示例地址
            abi=erc20_abi,
            query_methods=query_methods,
            mapping_rules=mapping_rules,
            kafka_topic="erc20-transfers",
            chain_name="ethereum",
            enabled=True
        )
    
    @staticmethod
    def get_uniswap_swap_config() -> EventQueryConfig:
        """获取Uniswap交换事件配置"""
        
        # Uniswap V2 Pair ABI
        pair_abi = [
            {
                "type": "event",
                "name": "Swap",
                "inputs": [
                    {"name": "sender", "type": "address", "indexed": True},
                    {"name": "amount0In", "type": "uint256", "indexed": False},
                    {"name": "amount1In", "type": "uint256", "indexed": False},
                    {"name": "amount0Out", "type": "uint256", "indexed": False},
                    {"name": "amount1Out", "type": "uint256", "indexed": False},
                    {"name": "to", "type": "address", "indexed": True}
                ]
            },
            {
                "type": "function",
                "name": "token0",
                "inputs": [],
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "token1",
                "inputs": [],
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "getReserves",
                "inputs": [],
                "outputs": [
                    {"name": "_reserve0", "type": "uint112"},
                    {"name": "_reserve1", "type": "uint112"},
                    {"name": "_blockTimestampLast", "type": "uint32"}
                ],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "factory",
                "inputs": [],
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view"
            }
        ]
        
        # 查询方法配置
        query_methods = [
            EventQueryMethod(
                method_name="token0",
                params=[],
                description="获取token0地址",
                required=True
            ),
            EventQueryMethod(
                method_name="token1",
                params=[],
                description="获取token1地址",
                required=True
            ),
            EventQueryMethod(
                method_name="getReserves",
                params=[],
                description="获取当前储备量",
                required=False
            ),
            EventQueryMethod(
                method_name="factory",
                params=[],
                description="获取工厂地址",
                required=False
            )
        ]
        
        # 映射规则配置
        mapping_rules = [
            EventMappingRule(
                source_key="event.args.sender",
                target_key="swap_sender",
                transformer="to_lowercase",
                description="交换发送方"
            ),
            EventMappingRule(
                source_key="event.args.to",
                target_key="swap_recipient",
                transformer="to_lowercase",
                description="交换接收方"
            ),
            EventMappingRule(
                source_key="event.args.amount0In",
                target_key="amount0_in",
                transformer="to_string",
                description="token0输入量"
            ),
            EventMappingRule(
                source_key="event.args.amount1In",
                target_key="amount1_in",
                transformer="to_string",
                description="token1输入量"
            ),
            EventMappingRule(
                source_key="event.args.amount0Out",
                target_key="amount0_out",
                transformer="to_string",
                description="token0输出量"
            ),
            EventMappingRule(
                source_key="event.args.amount1Out",
                target_key="amount1_out",
                transformer="to_string",
                description="token1输出量"
            ),
            EventMappingRule(
                source_key="query_results.token0",
                target_key="token0_address",
                transformer="to_lowercase",
                description="token0地址"
            ),
            EventMappingRule(
                source_key="query_results.token1",
                target_key="token1_address",
                transformer="to_lowercase",
                description="token1地址"
            ),
            EventMappingRule(
                source_key="query_results.factory",
                target_key="factory_address",
                transformer="to_lowercase",
                description="工厂地址"
            )
        ]
        
        return EventQueryConfig(
            event_name="Swap",
            contract_address="0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2 Router
            abi=pair_abi,
            query_methods=query_methods,
            mapping_rules=mapping_rules,
            kafka_topic="uniswap-swaps",
            chain_name="ethereum",
            enabled=True
        )
    
    @staticmethod
    def get_nft_transfer_config() -> EventQueryConfig:
        """获取NFT转账事件配置"""
        
        # ERC721 ABI
        nft_abi = [
            {
                "type": "event",
                "name": "Transfer",
                "inputs": [
                    {"name": "from", "type": "address", "indexed": True},
                    {"name": "to", "type": "address", "indexed": True},
                    {"name": "tokenId", "type": "uint256", "indexed": True}
                ]
            },
            {
                "type": "function",
                "name": "name",
                "inputs": [],
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "symbol",
                "inputs": [],
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "tokenURI",
                "inputs": [{"name": "tokenId", "type": "uint256"}],
                "outputs": [{"name": "", "type": "string"}],
                "stateMutability": "view"
            },
            {
                "type": "function",
                "name": "ownerOf",
                "inputs": [{"name": "tokenId", "type": "uint256"}],
                "outputs": [{"name": "", "type": "address"}],
                "stateMutability": "view"
            }
        ]
        
        # 查询方法配置
        query_methods = [
            EventQueryMethod(
                method_name="name",
                params=[],
                description="获取NFT名称",
                required=True
            ),
            EventQueryMethod(
                method_name="symbol",
                params=[],
                description="获取NFT符号",
                required=True
            ),
            EventQueryMethod(
                method_name="tokenURI",
                params=["event.args.tokenId"],
                description="获取token URI",
                required=False
            ),
            EventQueryMethod(
                method_name="ownerOf",
                params=["event.args.tokenId"],
                description="获取token所有者",
                required=False
            )
        ]
        
        # 映射规则配置
        mapping_rules = [
            EventMappingRule(
                source_key="event.args.from",
                target_key="from_address",
                transformer="to_lowercase",
                description="发送方地址"
            ),
            EventMappingRule(
                source_key="event.args.to",
                target_key="to_address",
                transformer="to_lowercase",
                description="接收方地址"
            ),
            EventMappingRule(
                source_key="event.args.tokenId",
                target_key="token_id",
                transformer="to_string",
                description="Token ID"
            ),
            EventMappingRule(
                source_key="query_results.name",
                target_key="nft_name",
                description="NFT名称"
            ),
            EventMappingRule(
                source_key="query_results.symbol",
                target_key="nft_symbol",
                description="NFT符号"
            ),
            EventMappingRule(
                source_key="query_results.tokenURI",
                target_key="token_uri",
                description="Token URI"
            ),
            EventMappingRule(
                source_key="query_results.ownerOf",
                target_key="current_owner",
                transformer="to_lowercase",
                description="当前所有者"
            )
        ]
        
        return EventQueryConfig(
            event_name="Transfer",
            contract_address="0x1234567890123456789012345678901234567890",  # 示例地址
            abi=nft_abi,
            query_methods=query_methods,
            mapping_rules=mapping_rules,
            kafka_topic="nft-transfers",
            chain_name="ethereum",
            enabled=True
        )
    
    @staticmethod
    def get_all_configs() -> List[EventQueryConfig]:
        """获取所有配置"""
        return [
            EventQueryConfigs.get_erc20_transfer_config(),
            EventQueryConfigs.get_uniswap_swap_config(),
            EventQueryConfigs.get_nft_transfer_config()
        ]
    
    @staticmethod
    def get_config_by_event_name(event_name: str) -> EventQueryConfig:
        """根据事件名称获取配置"""
        configs = EventQueryConfigs.get_all_configs()
        for config in configs:
            if config.event_name == event_name:
                return config
        return None
    
    @staticmethod
    def get_enabled_configs() -> List[EventQueryConfig]:
        """获取启用的配置"""
        configs = EventQueryConfigs.get_all_configs()
        return [config for config in configs if config.enabled]


# 配置验证函数
def validate_event_query_config(config: EventQueryConfig) -> bool:
    """验证事件查询配置"""
    try:
        # 检查必需字段
        if not config.event_name:
            return False
        if not config.contract_address:
            return False
        if not config.abi:
            return False
        
        # 检查ABI中是否包含指定的事件
        event_found = False
        for item in config.abi:
            if item.get('type') == 'event' and item.get('name') == config.event_name:
                event_found = True
                break
        
        if not event_found:
            return False
        
        # 检查查询方法是否在ABI中
        for method in config.query_methods:
            method_found = False
            for item in config.abi:
                if (item.get('type') == 'function' and 
                    item.get('name') == method.method_name):
                    method_found = True
                    break
            
            if not method_found:
                return False
        
        return True
        
    except Exception:
        return False


# 配置转换函数
def convert_config_to_dict(config: EventQueryConfig) -> Dict[str, Any]:
    """将配置转换为字典格式"""
    return {
        "event_name": config.event_name,
        "contract_address": config.contract_address,
        "abi": config.abi,
        "query_methods": [
            {
                "method_name": method.method_name,
                "params": method.params,
                "description": method.description,
                "required": method.required
            }
            for method in config.query_methods
        ],
        "mapping_rules": [
            {
                "source_key": rule.source_key,
                "target_key": rule.target_key,
                "transformer": rule.transformer,
                "description": rule.description,
                "required": rule.required
            }
            for rule in config.mapping_rules
        ],
        "kafka_topic": config.kafka_topic,
        "chain_name": config.chain_name,
        "enabled": config.enabled
    }


def convert_dict_to_config(config_dict: Dict[str, Any]) -> EventQueryConfig:
    """将字典转换为配置对象"""
    query_methods = [
        EventQueryMethod(
            method_name=method["method_name"],
            params=method.get("params", []),
            description=method.get("description", ""),
            required=method.get("required", False)
        )
        for method in config_dict.get("query_methods", [])
    ]
    
    mapping_rules = [
        EventMappingRule(
            source_key=rule["source_key"],
            target_key=rule["target_key"],
            transformer=rule.get("transformer"),
            description=rule.get("description", ""),
            required=rule.get("required", False)
        )
        for rule in config_dict.get("mapping_rules", [])
    ]
    
    return EventQueryConfig(
        event_name=config_dict["event_name"],
        contract_address=config_dict["contract_address"],
        abi=config_dict["abi"],
        query_methods=query_methods,
        mapping_rules=mapping_rules,
        kafka_topic=config_dict.get("kafka_topic", "blockchain-events"),
        chain_name=config_dict.get("chain_name", "ethereum"),
        enabled=config_dict.get("enabled", True)
    ) 