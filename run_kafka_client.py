#!/usr/bin/env python3
"""Kafka客户端启动脚本"""
import asyncio
import json
import signal
import sys
from typing import Optional, Dict, Any

from app.services.kafka_client import KafkaClient, KafkaConfig
from configs.kafka_configs import KafkaClientConfigs, KafkaTopicConfigs


class KafkaClientRunner:
    """Kafka客户端运行器"""
    
    def __init__(self):
        self.client: Optional[KafkaClient] = None
        self.running = False
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}，正在停止...")
        if self.client:
            self.client.close()
        self.running = False
    
    async def run_producer(
        self,
        config_name: str,
        topic: str,
        message: str,
        key: str = None,
        count: int = 1
    ):
        """运行生产者"""
        try:
            # 创建配置
            config = KafkaClientConfigs.create_kafka_config(config_name)
            self.client = KafkaClient(config)
            
            print(f"生产者配置: {config_name}")
            print(f"目标主题: {topic}")
            print(f"消息数量: {count}")
            
            # 解析消息
            try:
                data = json.loads(message)
            except json.JSONDecodeError:
                data = {"message": message}
            
            if count == 1:
                # 发送单条消息
                success = await self.client.send_message(
                    topic=topic,
                    data=data,
                    key=key
                )
                print(f"消息发送: {'成功' if success else '失败'}")
            else:
                # 批量发送
                messages = []
                for i in range(count):
                    msg_data = data.copy()
                    msg_data["sequence"] = i + 1
                    messages.append({
                        "data": msg_data,
                        "key": f"{key}_{i}" if key else None
                    })
                
                result = await self.client.send_batch_messages(topic, messages)
                print(f"批量发送结果: {result}")
            
            # 显示状态
            status = self.client.get_status()
            print(f"客户端状态: {status}")
            
        except Exception as e:
            print(f"生产者运行失败: {e}")
        finally:
            if self.client:
                self.client.close()
    
    async def run_consumer(
        self,
        config_name: str,
        topics: str,
        group_id: str = None,
        batch_mode: bool = False,
        batch_size: int = 10
    ):
        """运行消费者"""
        try:
            # 自定义消息处理器
            async def message_handler(message_data):
                print(f"📨 收到消息:")
                print(f"   主题: {message_data['topic']}")
                print(f"   分区: {message_data['partition']}")
                print(f"   偏移: {message_data['offset']}")
                print(f"   键: {message_data['key']}")
                print(f"   时间戳: {message_data['timestamp']}")
                print(f"   内容: {message_data['value']}")
                print("-" * 50)
            
            async def batch_handler(messages_batch):
                print(f"📦 批量收到 {len(messages_batch)} 条消息:")
                for i, msg in enumerate(messages_batch):
                    print(f"   {i+1}. 主题: {msg['topic']}, 键: {msg['key']}")
                    if msg['value']:
                        print(f"      内容: {msg['value']}")
                print("=" * 50)
            
            # 创建配置
            config = KafkaClientConfigs.create_kafka_config(config_name)
            if group_id:
                config.consumer_group_id = group_id
            
            self.client = KafkaClient(config)
            
            # 解析主题
            topics_list = [t.strip() for t in topics.split(",")]
            
            print(f"消费者配置: {config_name}")
            print(f"订阅主题: {topics_list}")
            print(f"消费者组: {config.consumer_group_id}")
            print(f"批量模式: {batch_mode}")
            if batch_mode:
                print(f"批量大小: {batch_size}")
            print("按 Ctrl+C 停止消费")
            print("-" * 50)
            
            self.running = True
            
            if batch_mode:
                await self.client.consume_messages_batch(
                    topics=topics_list,
                    batch_handler=batch_handler,
                    batch_size=batch_size,
                    batch_timeout=5.0
                )
            else:
                await self.client.consume_messages(
                    topics=topics_list,
                    message_handler=message_handler
                )
                
        except KeyboardInterrupt:
            print("\n收到停止信号")
        except Exception as e:
            print(f"消费者运行失败: {e}")
        finally:
            if self.client:
                self.client.close()
    
    async def test_connection(self, config_name: str):
        """测试连接"""
        try:
            config = KafkaClientConfigs.create_kafka_config(config_name)
            self.client = KafkaClient(config)
            
            print(f"测试配置: {config_name}")
            print(f"服务器: {config.bootstrap_servers}")
            
            # 尝试初始化生产者
            self.client.init_producer()
            print("✅ 生产者连接成功")
            
            # 获取状态
            status = self.client.get_status()
            print(f"状态: {status}")
            
        except Exception as e:
            print(f"❌ 连接测试失败: {e}")
        finally:
            if self.client:
                self.client.close()


def print_help():
    """打印帮助信息"""
    print("""
Kafka客户端工具使用说明:

1. 发送消息 (生产者):
   python run_kafka_client.py producer \\
     --config <config_name> \\
     --topic <topic> \\
     --message <message> \\
     [--key <key>] \\
     [--count <count>]

2. 消费消息 (消费者):
   python run_kafka_client.py consumer \\
     --config <config_name> \\
     --topics <topic1,topic2> \\
     [--group-id <group_id>] \\
     [--batch] \\
     [--batch-size <size>]

3. 测试连接:
   python run_kafka_client.py test --config <config_name>

参数说明:
  --config: 配置名称 (basic/blockchain_events/contract_calls/high_performance/reliable)
  --topic: 主题名称
  --topics: 主题列表，用逗号分隔
  --message: 消息内容 (JSON格式或普通文本)
  --key: 消息键
  --count: 发送消息数量
  --group-id: 消费者组ID
  --batch: 启用批量消费模式
  --batch-size: 批量大小

可用配置:""")
    
    configs = ["basic", "blockchain_events", "contract_calls", "high_performance", "reliable"]
    for config in configs:
        print(f"  - {config}")
    
    print(f"""
可用主题:
  区块链主题:""")
    for name, topic in KafkaTopicConfigs.BLOCKCHAIN_TOPICS.items():
        print(f"    - {topic} ({name})")
    
    print(f"""
  系统主题:""")
    for name, topic in KafkaTopicConfigs.SYSTEM_TOPICS.items():
        print(f"    - {topic} ({name})")
    
    print("""
示例:
  # 发送消息
  python run_kafka_client.py producer \\
    --config basic \\
    --topic test-topic \\
    --message '{"type": "test", "data": "hello"}' \\
    --key test-key

  # 批量发送
  python run_kafka_client.py producer \\
    --config high_performance \\
    --topic blockchain-events \\
    --message '{"event": "transfer"}' \\
    --count 10

  # 消费消息
  python run_kafka_client.py consumer \\
    --config basic \\
    --topics test-topic \\
    --group-id test-group

  # 批量消费多个主题
  python run_kafka_client.py consumer \\
    --config blockchain_events \\
    --topics blockchain-events,contract-calls \\
    --batch \\
    --batch-size 5

  # 测试连接
  python run_kafka_client.py test --config basic
""")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    runner = KafkaClientRunner()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    command = sys.argv[1]
    args = sys.argv[2:]
    
    try:
        if command == "help" or command == "--help":
            print_help()
            return
        
        # 解析参数
        params = {}
        i = 0
        while i < len(args):
            if args[i] == "--config" and i + 1 < len(args):
                params["config_name"] = args[i + 1]
                i += 2
            elif args[i] == "--topic" and i + 1 < len(args):
                params["topic"] = args[i + 1]
                i += 2
            elif args[i] == "--topics" and i + 1 < len(args):
                params["topics"] = args[i + 1]
                i += 2
            elif args[i] == "--message" and i + 1 < len(args):
                params["message"] = args[i + 1]
                i += 2
            elif args[i] == "--key" and i + 1 < len(args):
                params["key"] = args[i + 1]
                i += 2
            elif args[i] == "--count" and i + 1 < len(args):
                params["count"] = int(args[i + 1])
                i += 2
            elif args[i] == "--group-id" and i + 1 < len(args):
                params["group_id"] = args[i + 1]
                i += 2
            elif args[i] == "--batch-size" and i + 1 < len(args):
                params["batch_size"] = int(args[i + 1])
                i += 2
            elif args[i] == "--batch":
                params["batch_mode"] = True
                i += 1
            else:
                i += 1
        
        # 执行命令
        if command == "producer":
            if "config_name" not in params or "topic" not in params or "message" not in params:
                print("错误: 生产者模式需要 --config, --topic 和 --message 参数")
                return
            
            await runner.run_producer(
                config_name=params["config_name"],
                topic=params["topic"],
                message=params["message"],
                key=params.get("key"),
                count=params.get("count", 1)
            )
        
        elif command == "consumer":
            if "config_name" not in params or "topics" not in params:
                print("错误: 消费者模式需要 --config 和 --topics 参数")
                return
            
            await runner.run_consumer(
                config_name=params["config_name"],
                topics=params["topics"],
                group_id=params.get("group_id"),
                batch_mode=params.get("batch_mode", False),
                batch_size=params.get("batch_size", 10)
            )
        
        elif command == "test":
            if "config_name" not in params:
                print("错误: 测试模式需要 --config 参数")
                return
            
            await runner.test_connection(params["config_name"])
        
        else:
            print(f"未知命令: {command}")
            print_help()
    
    except Exception as e:
        print(f"运行错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())