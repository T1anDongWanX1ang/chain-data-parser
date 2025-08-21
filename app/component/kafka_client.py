"""Kafka客户端服务 - 包含生产者和消费者"""
import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable, Union
from kafka import KafkaProducer, KafkaConsumer
from kafka.errors import KafkaError, KafkaTimeoutError
from loguru import logger


class KafkaClient:
    """Kafka客户端 - 包含生产者和消费者功能"""
    
    def __init__(self, config: 'KafkaConfig'):
        """
        初始化Kafka客户端
        
        Args:
            config: Kafka配置
        """
        self.config = config
        self.producer: Optional[KafkaProducer] = None
        self.consumer: Optional[KafkaConsumer] = None
        self.is_producer_connected = False
        self.is_consumer_connected = False
        
        # 消息统计
        self.sent_count = 0
        self.received_count = 0
        self.failed_count = 0
        
        logger.info(f"Kafka客户端初始化 - 服务器: {self.config.bootstrap_servers}")
    
    # ===================== 生产者方法 =====================
    
    def init_producer(self):
        """初始化Kafka生产者"""
        if self.producer:
            logger.warning("Kafka生产者已经初始化")
            return
        
        try:
            producer_config = {
                'bootstrap_servers': self.config.bootstrap_servers,
                'acks': self.config.acks,
                'retries': self.config.retries,
                'batch_size': self.config.batch_size,
                'linger_ms': self.config.linger_ms,
                'buffer_memory': self.config.buffer_memory,
                'request_timeout_ms': self.config.request_timeout_ms,
            }
            
            # 添加认证配置
            if self.config.security_protocol != "PLAINTEXT":
                producer_config['security_protocol'] = self.config.security_protocol
            
            if self.config.sasl_mechanism:
                producer_config['sasl_mechanism'] = self.config.sasl_mechanism
                producer_config['sasl_plain_username'] = self.config.sasl_username
                producer_config['sasl_plain_password'] = self.config.sasl_password
            
            # 设置序列化器
            if self.config.value_serializer == "json":
                producer_config['value_serializer'] = lambda x: json.dumps(x, ensure_ascii=False, default=str).encode('utf-8')
            elif self.config.value_serializer == "string":
                producer_config['value_serializer'] = lambda x: str(x).encode('utf-8')
            
            if self.config.key_serializer == "json":
                producer_config['key_serializer'] = lambda x: json.dumps(x).encode('utf-8') if x is not None else None
            elif self.config.key_serializer == "string":
                producer_config['key_serializer'] = lambda x: str(x).encode('utf-8') if x is not None else None
            
            self.producer = KafkaProducer(**producer_config)
            self.is_producer_connected = True
            
            logger.info("Kafka生产者初始化成功")
            
        except Exception as e:
            logger.error(f"Kafka生产者初始化失败: {e}")
            self.is_producer_connected = False
            raise
    
    def send_message(
        self,
        topic: str,
        data: Any,
        key: Any = None,
        partition: int = None
    ) -> bool:
        """
        发送消息
        
        Args:
            topic: 主题名称
            data: 消息数据
            key: 消息key
            partition: 指定分区
            
        Returns:
            bool: 发送是否成功
        """
        if not self.is_producer_connected:
            self.init_producer()
        
        try:
            # 格式化消息
            message = self._format_message(data)
            
            # 发送消息
            future = self.producer.send(
                topic=topic,
                value=message,
                key=key,
                partition=partition
            )
            
            # 如果启用同步发送，等待结果
            if self.config.sync_send:
                record_metadata = future.get(timeout=self.config.send_timeout)
                logger.info(f"消息发送成功 - 主题: {topic}, 分区: {record_metadata.partition}, 偏移: {record_metadata.offset},数据:{data}")
            
            self.sent_count += 1
            
            # # 调用成功回调
            # if self.config.on_send_success:
            #     try:
            #         await self.config.on_send_success(topic, message, key)
            #     except Exception as e:
            #         logger.warning(f"发送成功回调执行失败: {e}")
            
            return True
            
        except KafkaTimeoutError as e:
            logger.error(f"发送消息超时 - 主题: {topic}, 错误: {e}")
            self.failed_count += 1
            return False
            
        except KafkaError as e:
            logger.error(f"发送消息失败 - 主题: {topic}, 错误: {e}")
            self.failed_count += 1
            return False
            
        except Exception as e:
            logger.error(f"发送消息异常 - 主题: {topic}, 错误: {e}")
            self.failed_count += 1
            return False
    
    async def send_batch_messages(
        self,
        topic: str,
        messages: List[Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        批量发送消息
        
        Args:
            topic: 主题名称
            messages: 消息列表，每个消息包含data, key等字段
            
        Returns:
            Dict[str, int]: 发送结果统计
        """
        if not self.is_producer_connected:
            self.init_producer()
        
        success_count = 0
        failed_count = 0
        
        try:
            for i, message in enumerate(messages):
                data = message.get("data")
                key = message.get("key")
                partition = message.get("partition")
                
                success =  self.send_message(
                    topic=topic,
                    data=data,
                    key=key,
                    partition=partition
                )
                
                if success:
                    success_count += 1
                else:
                    failed_count += 1
                
                # 批量发送间延迟
                if self.config.batch_delay > 0 and i < len(messages) - 1:
                    await asyncio.sleep(self.config.batch_delay)
            
            # 刷新缓冲区
            if self.config.flush_after_batch:
                self.flush_producer()
            
            logger.info(f"批量发送完成 - 成功: {success_count}, 失败: {failed_count}")
            
        except Exception as e:
            logger.error(f"批量发送异常: {e}")
        
        return {"success": success_count, "failed": failed_count}
    
    def flush_producer(self, timeout: float = None):
        """刷新生产者缓冲区"""
        if self.producer:
            self.producer.flush(timeout=timeout or self.config.flush_timeout)
    
    def close_producer(self):
        """关闭生产者"""
        if self.producer:
            try:
                self.producer.flush(timeout=self.config.flush_timeout)
                self.producer.close(timeout=self.config.close_timeout)
                logger.info("Kafka生产者已关闭")
            except Exception as e:
                logger.error(f"关闭Kafka生产者时出错: {e}")
            finally:
                self.producer = None
                self.is_producer_connected = False
    
    # ===================== 消费者方法 =====================
    
    def init_consumer(self, topics: Union[str, List[str]], group_id: str = None):
        """
        初始化Kafka消费者
        
        Args:
            topics: 订阅的主题
            group_id: 消费者组ID
        """
        if self.consumer:
            logger.warning("Kafka消费者已经初始化")
            return
        
        try:
            topics_list = [topics] if isinstance(topics, str) else topics
            
            consumer_config = {
                'bootstrap_servers': self.config.bootstrap_servers,
                'group_id': group_id or self.config.consumer_group_id,
                'auto_offset_reset': self.config.auto_offset_reset,
                'enable_auto_commit': self.config.enable_auto_commit,
                'auto_commit_interval_ms': self.config.auto_commit_interval_ms,
                'session_timeout_ms': self.config.session_timeout_ms,
                'heartbeat_interval_ms': self.config.heartbeat_interval_ms,
                'max_poll_records': self.config.max_poll_records,
                'max_poll_interval_ms': self.config.max_poll_interval_ms,
                'consumer_timeout_ms': self.config.consumer_timeout_ms
            }
            
            # 添加认证配置
            if self.config.security_protocol != "PLAINTEXT":
                consumer_config['security_protocol'] = self.config.security_protocol
            
            if self.config.sasl_mechanism:
                consumer_config['sasl_mechanism'] = self.config.sasl_mechanism
                consumer_config['sasl_plain_username'] = self.config.sasl_username
                consumer_config['sasl_plain_password'] = self.config.sasl_password
            
            # 设置反序列化器
            if self.config.value_deserializer == "json":
                consumer_config['value_deserializer'] = lambda x: json.loads(x.decode('utf-8')) if x else None
            elif self.config.value_deserializer == "string":
                consumer_config['value_deserializer'] = lambda x: x.decode('utf-8') if x else None
            
            if self.config.key_deserializer == "json":
                consumer_config['key_deserializer'] = lambda x: json.loads(x.decode('utf-8')) if x else None
            elif self.config.key_deserializer == "string":
                consumer_config['key_deserializer'] = lambda x: x.decode('utf-8') if x else None
            
            self.consumer = KafkaConsumer(*topics_list, **consumer_config)
            self.is_consumer_connected = True
            
            logger.info(f"Kafka消费者初始化成功 - 主题: {topics_list}, 消费者组: {group_id or self.config.consumer_group_id}")
            
        except Exception as e:
            logger.error(f"Kafka消费者初始化失败: {e}")
            self.is_consumer_connected = False
            raise
    
    async def consume_messages(
        self,
        topics: Union[str, List[str]],
        group_id: str = None,
        message_handler: Callable = None
    ):
        """
        消费消息
        
        Args:
            topics: 订阅的主题
            group_id: 消费者组ID
            message_handler: 消息处理函数
        """
        if not self.is_consumer_connected:
            self.init_consumer(topics, group_id)
        
        logger.info(f"开始消费消息 - 主题: {topics}")
        
        try:
            for message in self.consumer:
                try:
                    # 处理消息
                    await self._handle_message(message, message_handler)
                    self.received_count += 1
                    
                    # 手动提交偏移量
                    if not self.config.enable_auto_commit:
                        self.consumer.commit()
                        
                except Exception as e:
                    logger.error(f"处理消息失败: {e}")
                    
                    # 调用错误处理回调
                    if self.config.on_consume_error:
                        try:
                            await self.config.on_consume_error(message, e)
                        except Exception as cb_e:
                            logger.warning(f"消费错误回调执行失败: {cb_e}")
                
        except KeyboardInterrupt:
            logger.info("收到停止信号，停止消费消息")
        except Exception as e:
            logger.error(f"消费消息异常: {e}")
        finally:
            self.close_consumer()
    
    async def consume_messages_batch(
        self,
        topics: Union[str, List[str]],
        group_id: str = None,
        batch_handler: Callable = None,
        batch_size: int = 100,
        batch_timeout: float = 5.0
    ):
        """
        批量消费消息
        
        Args:
            topics: 订阅的主题
            group_id: 消费者组ID
            batch_handler: 批量消息处理函数
            batch_size: 批量大小
            batch_timeout: 批量超时时间
        """
        if not self.is_consumer_connected:
            self.init_consumer(topics, group_id)
        
        logger.info(f"开始批量消费消息 - 主题: {topics}, 批量大小: {batch_size}")
        
        messages_batch = []
        last_batch_time = datetime.now()
        
        try:
            for message in self.consumer:
                messages_batch.append(message)
                
                # 检查是否需要处理批量消息
                current_time = datetime.now()
                time_diff = (current_time - last_batch_time).total_seconds()
                
                if len(messages_batch) >= batch_size or time_diff >= batch_timeout:
                    try:
                        # 处理批量消息
                        if batch_handler:
                            await batch_handler(messages_batch)
                        else:
                            await self._handle_messages_batch(messages_batch)
                        
                        self.received_count += len(messages_batch)
                        
                        # 手动提交偏移量
                        if not self.config.enable_auto_commit:
                            self.consumer.commit()
                        
                        logger.debug(f"处理批量消息完成，数量: {len(messages_batch)}")
                        
                    except Exception as e:
                        logger.error(f"处理批量消息失败: {e}")
                    
                    # 重置批量
                    messages_batch = []
                    last_batch_time = current_time
                
        except KeyboardInterrupt:
            logger.info("收到停止信号，停止批量消费消息")
        except Exception as e:
            logger.error(f"批量消费消息异常: {e}")
        finally:
            # 处理剩余消息
            if messages_batch:
                try:
                    if batch_handler:
                        await batch_handler(messages_batch)
                    else:
                        await self._handle_messages_batch(messages_batch)
                except Exception as e:
                    logger.error(f"处理剩余批量消息失败: {e}")
            
            self.close_consumer()
    
    def close_consumer(self):
        """关闭消费者"""
        if self.consumer:
            try:
                self.consumer.close()
                logger.info("Kafka消费者已关闭")
            except Exception as e:
                logger.error(f"关闭Kafka消费者时出错: {e}")
            finally:
                self.consumer = None
                self.is_consumer_connected = False
    
    # ===================== 辅助方法 =====================
    
    def _format_message(self, data: Any) -> Any:
        """格式化消息"""
        if self.config.message_format == "envelope":
            return {
                "timestamp": datetime.now().isoformat(),
                "source": self.config.source_name,
                "data": data
            }
        elif self.config.message_format == "detailed":
            return {
                "id": f"{datetime.now().timestamp()}_{id(data)}",
                "timestamp": datetime.now().isoformat(),
                "source": self.config.source_name,
                "version": "1.0",
                "data": data
            }
        else:  # simple
            return data
    
    async def _handle_message(self, message, handler: Callable = None):
        """处理单条消息"""
        try:
            message_data = {
                "topic": message.topic,
                "partition": message.partition,
                "offset": message.offset,
                "key": message.key,
                "value": message.value,
                "timestamp": message.timestamp,
                "headers": dict(message.headers) if message.headers else {}
            }
            
            if handler:
                await handler(message_data)
            elif self.config.default_message_handler:
                await self.config.default_message_handler(message_data)
            else:
                # 默认处理：打印消息
                logger.info(f"收到消息 - 主题: {message.topic}, 值: {message.value}")
            
        except Exception as e:
            logger.error(f"处理消息时出错: {e}")
            raise
    
    async def _handle_messages_batch(self, messages):
        """处理批量消息"""
        try:
            messages_data = []
            for message in messages:
                message_data = {
                    "topic": message.topic,
                    "partition": message.partition,
                    "offset": message.offset,
                    "key": message.key,
                    "value": message.value,
                    "timestamp": message.timestamp,
                    "headers": dict(message.headers) if message.headers else {}
                }
                messages_data.append(message_data)
            
            if self.config.default_batch_handler:
                await self.config.default_batch_handler(messages_data)
            else:
                # 默认处理：打印消息数量
                logger.info(f"批量处理消息，数量: {len(messages_data)}")
            
        except Exception as e:
            logger.error(f"批量处理消息时出错: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "producer_connected": self.is_producer_connected,
            "consumer_connected": self.is_consumer_connected,
            "bootstrap_servers": self.config.bootstrap_servers,
            "sent_count": self.sent_count,
            "received_count": self.received_count,
            "failed_count": self.failed_count
        }
    
    def close(self):
        """关闭客户端"""
        self.close_producer()
        self.close_consumer()
        logger.info("Kafka客户端已关闭")


class KafkaConfig:
    """Kafka配置类"""
    
    def __init__(
        self,
        # 连接配置
        bootstrap_servers: Union[str, List[str]] = "localhost:9092",
        
        # 认证配置
        security_protocol: str = "PLAINTEXT",
        sasl_mechanism: str = None,
        sasl_username: str = None,
        sasl_password: str = None,
        
        # 生产者配置
        acks: Union[int, str] = 1,
        retries: int = 3,
        batch_size: int = 16384,
        linger_ms: int = 0,
        buffer_memory: int = 33554432,
        request_timeout_ms: int = 30000,
        sync_send: bool = False,
        send_timeout: float = 10.0,
        batch_delay: float = 0.01,
        flush_after_batch: bool = True,
        flush_timeout: float = 10.0,
        close_timeout: float = 5.0,
        
        # 消费者配置
        consumer_group_id: str = "chain-data-parser-group",
        auto_offset_reset: str = "latest",
        enable_auto_commit: bool = True,
        auto_commit_interval_ms: int = 5000,
        session_timeout_ms: int = 30000,
        heartbeat_interval_ms: int = 3000,
        max_poll_records: int = 500,
        max_poll_interval_ms: int = 300000,
        consumer_timeout_ms: int = -1,
        
        # 序列化配置
        key_serializer: str = "string",
        value_serializer: str = "json",
        key_deserializer: str = "string",
        value_deserializer: str = "json",
        
        # 消息配置
        message_format: str = "envelope",
        source_name: str = "chain-data-parser",
        
        # 回调函数
        on_send_success: Optional[Callable] = None,
        on_send_error: Optional[Callable] = None,
        on_consume_error: Optional[Callable] = None,
        default_message_handler: Optional[Callable] = None,
        default_batch_handler: Optional[Callable] = None
    ):
        """
        初始化Kafka配置
        
        Args:
            bootstrap_servers: Kafka服务器地址
            security_protocol: 安全协议
            sasl_mechanism: SASL认证机制
            sasl_username: SASL用户名
            sasl_password: SASL密码
            acks: 确认级别
            retries: 重试次数
            batch_size: 批量大小
            linger_ms: 等待时间
            buffer_memory: 缓冲区内存
            request_timeout_ms: 请求超时时间
            sync_send: 是否同步发送
            send_timeout: 发送超时时间
            batch_delay: 批量发送延迟
            flush_after_batch: 批量发送后是否刷新
            flush_timeout: 刷新超时时间
            close_timeout: 关闭超时时间
            consumer_group_id: 消费者组ID
            auto_offset_reset: 偏移量重置策略
            enable_auto_commit: 是否自动提交偏移量
            auto_commit_interval_ms: 自动提交间隔
            session_timeout_ms: 会话超时时间
            heartbeat_interval_ms: 心跳间隔
            max_poll_records: 最大轮询记录数
            max_poll_interval_ms: 最大轮询间隔
            consumer_timeout_ms: 消费者超时时间
            key_serializer: key序列化器
            value_serializer: value序列化器
            key_deserializer: key反序列化器
            value_deserializer: value反序列化器
            message_format: 消息格式
            source_name: 数据源名称
            on_send_success: 发送成功回调
            on_send_error: 发送错误回调
            on_consume_error: 消费错误回调
            default_message_handler: 默认消息处理器
            default_batch_handler: 默认批量处理器
        """
        self.bootstrap_servers = bootstrap_servers if isinstance(bootstrap_servers, list) else [bootstrap_servers]
        self.security_protocol = security_protocol
        self.sasl_mechanism = sasl_mechanism
        self.sasl_username = sasl_username
        self.sasl_password = sasl_password
        self.acks = acks
        self.retries = retries
        self.batch_size = batch_size
        self.linger_ms = linger_ms
        self.buffer_memory = buffer_memory
        self.request_timeout_ms = request_timeout_ms
        self.sync_send = sync_send
        self.send_timeout = send_timeout
        self.batch_delay = batch_delay
        self.flush_after_batch = flush_after_batch
        self.flush_timeout = flush_timeout
        self.close_timeout = close_timeout
        self.consumer_group_id = consumer_group_id
        self.auto_offset_reset = auto_offset_reset
        self.enable_auto_commit = enable_auto_commit
        self.auto_commit_interval_ms = auto_commit_interval_ms
        self.session_timeout_ms = session_timeout_ms
        self.heartbeat_interval_ms = heartbeat_interval_ms
        self.max_poll_records = max_poll_records
        self.max_poll_interval_ms = max_poll_interval_ms
        self.consumer_timeout_ms = consumer_timeout_ms
        self.key_serializer = key_serializer
        self.value_serializer = value_serializer
        self.key_deserializer = key_deserializer
        self.value_deserializer = value_deserializer
        self.message_format = message_format
        self.source_name = source_name
        self.on_send_success = on_send_success
        self.on_send_error = on_send_error
        self.on_consume_error = on_consume_error
        self.default_message_handler = default_message_handler
        self.default_batch_handler = default_batch_handler
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置参数"""
        if not self.bootstrap_servers:
            raise ValueError("bootstrap_servers 不能为空")
        
        if self.security_protocol not in ["PLAINTEXT", "SSL", "SASL_PLAINTEXT", "SASL_SSL"]:
            raise ValueError("security_protocol 必须是 PLAINTEXT, SSL, SASL_PLAINTEXT 或 SASL_SSL")
        
        if self.auto_offset_reset not in ["earliest", "latest", "none"]:
            raise ValueError("auto_offset_reset 必须是 earliest, latest 或 none")