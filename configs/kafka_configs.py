"""Kafka配置文件"""
from typing import Dict, Any, Callable
from app.services.kafka_client import KafkaConfig


class KafkaTopicConfigs:
    """Kafka主题配置"""
    
    # 区块链数据主题
    BLOCKCHAIN_TOPICS = {
        "events": "blockchain-events",
        "transactions": "blockchain-transactions", 
        "blocks": "blockchain-blocks",
        "contract_calls": "contract-calls",
        "token_transfers": "token-transfers"
    }
    
    # 系统主题
    SYSTEM_TOPICS = {
        "logs": "system-logs",
        "metrics": "system-metrics",
        "alerts": "system-alerts"
    }
    
    # 分析主题
    ANALYTICS_TOPICS = {
        "price_data": "price-data",
        "volume_data": "volume-data",
        "liquidity_data": "liquidity-data"
    }


class KafkaClientConfigs:
    """Kafka客户端配置管理"""
    
    # 基础配置
    BASIC_CONFIG = {
        "bootstrap_servers": "localhost:9092",
        "consumer_group_id": "chain-parser-basic",
        "message_format": "envelope",
        "source_name": "chain-data-parser"
    }
    
    # 区块链事件配置
    BLOCKCHAIN_EVENTS_CONFIG = {
        "bootstrap_servers": "localhost:9092",
        "consumer_group_id": "blockchain-events-group",
        "message_format": "detailed",
        "source_name": "blockchain-event-monitor",
        "batch_size": 32768,
        "max_poll_records": 100,
        "auto_offset_reset": "earliest"
    }
    
    # 合约调用配置
    CONTRACT_CALLS_CONFIG = {
        "bootstrap_servers": "localhost:9092",
        "consumer_group_id": "contract-calls-group",
        "message_format": "envelope",
        "source_name": "contract-method-caller",
        "batch_size": 16384,
        "max_poll_records": 200,
        "sync_send": True
    }
    
    # 高性能配置
    HIGH_PERFORMANCE_CONFIG = {
        "bootstrap_servers": "localhost:9092",
        "consumer_group_id": "high-perf-group",
        "message_format": "simple",
        "batch_size": 65536,
        "linger_ms": 5,
        "max_poll_records": 1000,
        "batch_delay": 0.001,
        "flush_after_batch": False
    }
    
    # 可靠性配置
    RELIABLE_CONFIG = {
        "bootstrap_servers": "localhost:9092",
        "consumer_group_id": "reliable-group",
        "acks": "all",
        "retries": 5,
        "sync_send": True,
        "enable_auto_commit": False,
        "message_format": "detailed",
        "request_timeout_ms": 60000
    }
    
    @classmethod
    def get_config(cls, config_name: str) -> Dict[str, Any]:
        """获取指定配置"""
        configs = {
            "basic": cls.BASIC_CONFIG,
            "blockchain_events": cls.BLOCKCHAIN_EVENTS_CONFIG,
            "contract_calls": cls.CONTRACT_CALLS_CONFIG,
            "high_performance": cls.HIGH_PERFORMANCE_CONFIG,
            "reliable": cls.RELIABLE_CONFIG
        }
        
        if config_name not in configs:
            raise ValueError(f"配置 '{config_name}' 不存在")
        
        return configs[config_name]
    
    @classmethod
    def create_kafka_config(cls, config_name: str, **overrides) -> KafkaConfig:
        """创建Kafka配置对象"""
        base_config = cls.get_config(config_name)
        base_config.update(overrides)
        return KafkaConfig(**base_config)


# 消息处理器示例
async def blockchain_event_handler(message_data: Dict[str, Any]):
    """区块链事件消息处理器"""
    print(f"[事件处理] 主题: {message_data['topic']}")
    print(f"[事件处理] 分区: {message_data['partition']}")
    print(f"[事件处理] 偏移: {message_data['offset']}")
    
    if message_data['value']:
        event_data = message_data['value']
        if isinstance(event_data, dict):
            if 'data' in event_data:
                # envelope格式
                actual_data = event_data['data']
                print(f"[事件处理] 事件类型: {actual_data.get('event_name', 'unknown')}")
                print(f"[事件处理] 合约地址: {actual_data.get('contract_address', 'N/A')}")
                print(f"[事件处理] 交易哈希: {actual_data.get('transaction_hash', 'N/A')}")
            else:
                # simple格式
                print(f"[事件处理] 事件类型: {event_data.get('event_name', 'unknown')}")
        
        print(f"[事件处理] 消息内容: {message_data['value']}")
    print("-" * 50)


async def contract_call_handler(message_data: Dict[str, Any]):
    """合约调用结果消息处理器"""
    print(f"[调用处理] 主题: {message_data['topic']}")
    print(f"[调用处理] 键: {message_data['key']}")
    
    if message_data['value']:
        call_data = message_data['value']
        if isinstance(call_data, dict):
            if 'data' in call_data:
                # envelope格式
                actual_data = call_data['data']
                print(f"[调用处理] 方法名: {actual_data.get('method_name', 'unknown')}")
                print(f"[调用处理] 合约地址: {actual_data.get('contract_address', 'N/A')}")
                print(f"[调用处理] 调用结果: {actual_data.get('result', 'N/A')}")
            else:
                # simple格式
                print(f"[调用处理] 方法名: {call_data.get('method_name', 'unknown')}")
        
        print(f"[调用处理] 消息内容: {message_data['value']}")
    print("-" * 50)


async def batch_message_handler(messages_data: list):
    """批量消息处理器"""
    print(f"[批量处理] 收到 {len(messages_data)} 条消息")
    
    # 按主题分组
    topics = {}
    for msg in messages_data:
        topic = msg['topic']
        if topic not in topics:
            topics[topic] = []
        topics[topic].append(msg)
    
    # 分别处理每个主题的消息
    for topic, msgs in topics.items():
        print(f"[批量处理] 主题 {topic}: {len(msgs)} 条消息")
        
        for msg in msgs:
            if msg['value']:
                # 简单处理：只打印关键信息
                value = msg['value']
                if isinstance(value, dict):
                    if 'data' in value:
                        data = value['data']
                        if 'event_name' in data:
                            print(f"  - 事件: {data['event_name']}")
                        elif 'method_name' in data:
                            print(f"  - 方法: {data['method_name']}")
    print("=" * 50)


# 错误处理器
async def send_error_handler(topic: str, data: Any, error: Exception):
    """发送错误处理器"""
    print(f"❌ 发送失败 - 主题: {topic}, 错误: {error}")


async def consume_error_handler(message_data: Dict[str, Any], error: Exception):
    """消费错误处理器"""
    print(f"❌ 消费失败 - 主题: {message_data.get('topic', 'unknown')}, 错误: {error}")


# 带回调函数的配置
def create_blockchain_config_with_handlers(bootstrap_servers: str = "localhost:9092") -> KafkaConfig:
    """创建带处理器的区块链配置"""
    return KafkaConfig(
        bootstrap_servers=bootstrap_servers,
        consumer_group_id="blockchain-events-group",
        message_format="envelope",
        source_name="blockchain-event-monitor",
        default_message_handler=blockchain_event_handler,
        default_batch_handler=batch_message_handler,
        on_send_error=send_error_handler,
        on_consume_error=consume_error_handler
    )


def create_contract_config_with_handlers(bootstrap_servers: str = "localhost:9092") -> KafkaConfig:
    """创建带处理器的合约调用配置"""
    return KafkaConfig(
        bootstrap_servers=bootstrap_servers,
        consumer_group_id="contract-calls-group",
        message_format="envelope",
        source_name="contract-method-caller",
        sync_send=True,
        default_message_handler=contract_call_handler,
        on_send_error=send_error_handler,
        on_consume_error=consume_error_handler
    )


# 主题路由配置
TOPIC_ROUTING = {
    "blockchain_event": KafkaTopicConfigs.BLOCKCHAIN_TOPICS["events"],
    "contract_call_result": KafkaTopicConfigs.BLOCKCHAIN_TOPICS["contract_calls"],
    "token_transfer": KafkaTopicConfigs.BLOCKCHAIN_TOPICS["token_transfers"],
    "transaction_data": KafkaTopicConfigs.BLOCKCHAIN_TOPICS["transactions"],
    "block_data": KafkaTopicConfigs.BLOCKCHAIN_TOPICS["blocks"],
    "system_log": KafkaTopicConfigs.SYSTEM_TOPICS["logs"],
    "system_metric": KafkaTopicConfigs.SYSTEM_TOPICS["metrics"],
    "price_update": KafkaTopicConfigs.ANALYTICS_TOPICS["price_data"]
}