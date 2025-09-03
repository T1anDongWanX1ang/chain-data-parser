#!/usr/bin/env python3
"""
优化后的区块链数据管道执行器

主要改进：
1. 重构组件工厂模式，统一组件创建逻辑
2. 支持多条 dict_mapper 配置
3. 改进数据流处理逻辑，支持更灵活的组件链
4. 增强错误处理和日志记录
5. 优化配置验证和组件生命周期管理
"""

import asyncio
import json
import os
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from loguru import logger
import uuid
from dataclasses import dataclass
from enum import Enum

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

# 延迟导入，避免循环依赖和缺失依赖问题
# from app.component.event_monitor import ContractEventMonitor, EventMonitorConfig
# from app.component.contract_caller import ContractMethodCaller, MethodCallConfig
# from app.component.dict_mapper import DictMapper, MappingConfig, MappingRule
# from app.component.kafka_client import KafkaClient, KafkaConfig


class ComponentType(Enum):
    """组件类型枚举"""
    EVENT_MONITOR = "event_monitor"
    CONTRACT_CALLER = "contract_caller"
    DICT_MAPPER = "dict_mapper"
    KAFKA_PRODUCER = "kafka_producer"
    KAFKA_CONSUMER = "kafka_consumer"


@dataclass
class PipelineContext:
    """管道上下文，用于在组件间传递数据"""
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    pipeline_id: str
    step_count: int = 0
    
    def add_step_data(self, component_name: str, step_data: Dict[str, Any]):
        """添加步骤数据"""
        self.step_count += 1
        self.data[f"step_{self.step_count}_{component_name}"] = step_data
        # 将新数据合并到主数据中（不覆盖现有键）
        for key, value in step_data.items():
            if key not in self.data:
                self.data[key] = value


class PipelineComponent(ABC):
    """管道组件抽象基类"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.logger = logger.bind(component=name)
    
    @abstractmethod
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """执行组件逻辑"""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """初始化组件"""
        pass
    
    @abstractmethod
    async def cleanup(self):
        """清理组件资源"""
        pass


class EventMonitorComponent(PipelineComponent):
    """事件监控组件"""
    
    def __init__(self, name: str, config: Dict[str, Any], data_processor: Callable):
        super().__init__(name, config)
        self.data_processor = data_processor
        self.monitor = None
    
    async def initialize(self) -> bool:
        """初始化事件监控器"""
        try:
            # 延迟导入
            from app.component.event_monitor import ContractEventMonitor, EventMonitorConfig
            
            # 加载ABI
            abi = self._load_abi_file(self.config.get('abi_path', ''))
            
            # 创建监控配置
            monitor_config = EventMonitorConfig(
                mode=self.config.get('mode', 'realtime'),
                events_to_monitor=self.config.get('events_to_monitor'),
                output_format=self.config.get('output_format', 'detailed'),
                poll_interval=self.config.get('poll_interval', 1.0),
                custom_handler=self.data_processor
            )
            
            self.monitor = ContractEventMonitor(
                chain_name=self.config['chain_name'],
                contract_address=self.config['contract_address'],
                abi=abi,
                config=monitor_config,
            )
            
            self.logger.info(f"事件监控器初始化成功: {self.config['contract_address']}")
            return True
            
        except Exception as e:
            self.logger.error(f"事件监控器初始化失败: {e}")
            return False
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """启动事件监控"""
        if self.monitor:
            self.logger.info("启动事件监控...")
            await self.monitor.start_monitoring()
        return context
    
    async def cleanup(self):
        """清理监控器资源"""
        if self.monitor:
            # 这里可以添加停止监控的逻辑
            pass
    
    def _load_abi_file(self, abi_path: str) -> List[Dict[str, Any]]:
        """加载ABI文件"""
        try:
            if not os.path.isabs(abi_path):
                # 相对于项目根目录
                abi_file = project_root / abi_path
            else:
                abi_file = Path(abi_path)

            if not abi_file.exists():
                self.logger.warning(f"ABI文件不存在: {abi_file}")
                return []

            with open(abi_file, 'r', encoding='utf-8') as f:
                abi_data = json.load(f)

            self.logger.info(f"ABI文件加载成功: {abi_file}")
            return abi_data
        except Exception as e:
            self.logger.error(f"ABI文件加载失败: {abi_path}, 错误: {e}")
            return []


class ContractCallerComponent(PipelineComponent):
    """合约调用组件 - 支持多个合约调用器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.callers = {}  # 存储多个调用器，key为event_name
        self.single_caller = None  # 单个调用器（向后兼容）
    
    async def initialize(self) -> bool:
        """初始化合约调用器"""
        try:
            # 延迟导入
            from app.component.contract_caller import ContractMethodCaller, MethodCallConfig
            
            # 检查是否有多个合约调用器配置
            contract_callers_config = self.config.get('contract_callers', [])
            
            if contract_callers_config:
                # 新格式：多个合约调用器
                for caller_config in contract_callers_config:
                    event_name = caller_config.get('event_name')
                    if not event_name:
                        self.logger.warning("合约调用器配置缺少 event_name，跳过")
                        continue
                    
                    # 加载ABI
                    abi = self._load_abi_file(caller_config.get('abi_path', ''))
                    
                    # 创建调用配置
                    call_config = MethodCallConfig(
                        output_format="json",
                        include_block_info=False
                    )
                    
                    caller = ContractMethodCaller(
                        chain_name=caller_config['chain_name'],
                        contract_address=caller_config['contract_address'],
                        abi=abi,
                        config=call_config
                    )
                    
                    # 存储调用器配置
                    self.callers[event_name] = {
                        'caller': caller,
                        'method_name': caller_config.get('method_name'),
                        'method_params': caller_config.get('method_params', [])
                    }
                    
                    self.logger.info(f"合约调用器初始化成功: {event_name} -> {caller_config['contract_address']}")
                
                return len(self.callers) > 0
            else:
                # 旧格式：单个合约调用器（向后兼容）
                abi = self._load_abi_file(self.config.get('abi_path', ''))
                
                call_config = MethodCallConfig(
                    output_format="json",
                    include_block_info=False
                )
                
                self.single_caller = ContractMethodCaller(
                    chain_name=self.config['chain_name'],
                    contract_address=self.config['contract_address'],
                    abi=abi,
                    config=call_config
                )
                
                self.logger.info(f"单个合约调用器初始化成功: {self.config['contract_address']}")
                return True
            
        except Exception as e:
            self.logger.error(f"合约调用器初始化失败: {e}")
            return False
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """执行合约调用"""
        try:
            if self.callers:
                # 多个合约调用器：根据 event_name 选择调用器
                event_name = context.data.get('event_name')
                if not event_name:
                    self.logger.warning("数据中缺少 event_name 字段，无法选择合约调用器")
                    return context
                
                caller_info = self.callers.get(event_name)
                if not caller_info:
                    self.logger.warning(f"未找到 event_name '{event_name}' 对应的合约调用器")
                    return context
                
                # 执行合约调用
                method_name = caller_info['method_name']
                method_params = caller_info['method_params']
                caller = caller_info['caller']
                
                # 解析参数
                method_args = []
                if method_params:
                    method_args = [self._resolve_parameter(param, context.data) for param in method_params]
                
                # 调用合约方法
                call_result = caller.call_method(method_name, method_args)
                
                # 将结果以方法名作为key添加到上下文数据中
                if method_name and call_result:
                    # 提取方法调用的结果值
                    method_result_key = f"{method_name}_result"
                    if method_result_key in call_result:
                        context.data[method_name] = call_result[method_result_key]
                    else:
                        context.data[method_name] = call_result
                
                # 同时保留完整的调用结果
                context.add_step_data(self.name, call_result)
                
                self.logger.info(f"合约调用成功: {event_name} -> {method_name}, 结果已添加到数据中")
                
            elif self.single_caller:
                # 单个合约调用器（向后兼容）
                method_name = self.config.get('method_name')
                method_params = self.config.get('method_params', [])
                
                # 解析参数
                method_args = []
                if method_params:
                    method_args = [self._resolve_parameter(param, context.data) for param in method_params]
                
                # 调用合约方法
                call_result = self.single_caller.call_method(method_name, method_args)
                
                # 添加结果到上下文
                context.add_step_data(self.name, call_result)
                
                self.logger.info(f"单个合约调用成功: {method_name}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"合约调用失败: {e}")
            return context
    
    async def cleanup(self):
        """清理调用器资源"""
        pass
    
    def _load_abi_file(self, abi_path: str) -> List[Dict[str, Any]]:
        """加载ABI文件"""
        try:
            if not os.path.isabs(abi_path):
                abi_file = project_root / abi_path
            else:
                abi_file = Path(abi_path)

            if not abi_file.exists():
                self.logger.warning(f"ABI文件不存在: {abi_file}")
                return []

            with open(abi_file, 'r', encoding='utf-8') as f:
                abi_data = json.load(f)

            return abi_data
        except Exception as e:
            self.logger.error(f"ABI文件加载失败: {abi_path}, 错误: {e}")
            return []
    
    def _resolve_parameter(self, param: str, data: Dict[str, Any]) -> Any:
        """解析参数引用"""
        if not isinstance(param, str):
            return param

        # 解析形如 "args.to" 或 "event_args.to" 的引用
        if '.' in param:
            keys = param.split('.')
            current = data

            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    self.logger.warning(f"无法解析参数引用: {param}")
                    return None

            return current

        # 直接键引用
        return data.get(param)


class DictMapperComponent(PipelineComponent):
    """字典映射组件 - 支持多条映射器"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.mappers = []  # 存储多个映射器
    
    async def initialize(self) -> bool:
        """初始化字典映射器"""
        try:
            # 延迟导入
            from app.component.dict_mapper import DictMapper, MappingConfig, MappingRule
            
            # 支持新的多条配置格式
            dict_mappers_config = self.config.get('dict_mappers', [])
            
            # 向后兼容：如果没有 dict_mappers 但有 mapping_rules
            if not dict_mappers_config and self.config.get('mapping_rules'):
                dict_mappers_config = [{
                    'event_name': None,
                    'mapping_rules': self.config.get('mapping_rules', [])
                }]
            
            # 创建多个映射器
            for i, mapper_config in enumerate(dict_mappers_config):
                event_name = mapper_config.get('event_name')
                mapping_rules = mapper_config.get('mapping_rules', [])
                
                # 创建映射规则
                rules = []
                for rule_config in mapping_rules:
                    rule = MappingRule(
                        source_key=rule_config['source_key'],
                        target_key=rule_config['target_key'],
                        transformer=rule_config.get('transformer'),
                        condition=rule_config.get('condition'),
                        default_value=rule_config.get('default_value')
                    )
                    rules.append(rule)
                
                # 创建映射配置
                config = MappingConfig(mapping_rules=rules)
                
                # 创建映射器
                mapper = DictMapper(config)
                
                self.mappers.append({
                    'event_name': event_name,
                    'mapper': mapper,
                    'rules_count': len(rules)
                })
            
            self.logger.info(f"字典映射器初始化成功: 创建了 {len(self.mappers)} 个映射器")
            return True
            
        except Exception as e:
            self.logger.error(f"字典映射器初始化失败: {e}")
            return False
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """执行字典映射"""
        try:
            # 获取当前事件名称（如果有的话）
            current_event_name = context.data.get('event_name') or context.data.get('event')
            
            # 初始化结果数据，只保留映射后的字段
            final_mapped_data = {}
            
            # 执行所有适用的映射器
            for mapper_info in self.mappers:
                event_name = mapper_info['event_name']
                mapper = mapper_info['mapper']
                
                # 判断是否应该应用此映射器
                should_apply = (
                    event_name is None or  # 通用映射器
                    event_name == current_event_name or  # 匹配特定事件
                    current_event_name is None  # 没有事件名称时应用所有映射器
                )
                
                if should_apply:
                    try:
                        # 使用原始数据进行映射
                        mapped_result = mapper.map_dict(context.data)
                        
                        # 只保留映射后的字段，不合并原始数据
                        final_mapped_data.update(mapped_result)
                        
                        self.logger.info(f"应用映射器成功: event_name={event_name}, 规则数={mapper_info['rules_count']}, 映射字段数={len(mapped_result)}")
                    except Exception as e:
                        self.logger.error(f"映射器执行失败: event_name={event_name}, 错误: {e}")
            
            # 如果没有任何映射结果，记录警告
            if not final_mapped_data:
                self.logger.warning(f"字典映射未产生任何结果: event_name={current_event_name}")
            
            # 更新上下文数据，只保留映射后的字段
            context.add_step_data(self.name, final_mapped_data)
            context.data = final_mapped_data
            
            return context
            
        except Exception as e:
            self.logger.error(f"字典映射执行失败: {e}")
            return context
    
    async def cleanup(self):
        """清理映射器资源"""
        self.mappers.clear()


class KafkaProducerComponent(PipelineComponent):
    """Kafka生产者组件"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.kafka_client = None
    
    async def initialize(self) -> bool:
        """初始化Kafka客户端"""
        try:
            # 延迟导入
            from app.component.kafka_client import KafkaClient, KafkaConfig
            
            # 创建Kafka配置
            kafka_config = KafkaConfig(
                bootstrap_servers=self.config.get('bootstrap_servers', 'localhost:9092'),
                acks=self.config.get('acks', 1),
                sync_send=self.config.get('sync_send', False),
                retries=self.config.get('retries', 3),
                batch_size=self.config.get('batch_size', 16384),
                linger_ms=self.config.get('linger_ms', 0),
                message_format=self.config.get('message_format', 'simple')  # 默认只发送数据部分
            )
            
            self.kafka_client = KafkaClient(kafka_config)
            self.kafka_client.init_producer()
            
            self.logger.info(f"Kafka生产者初始化成功: {self.config.get('bootstrap_servers')}")
            return True
            
        except Exception as e:
            self.logger.error(f"Kafka生产者初始化失败: {e}")
            return False
    
    async def execute(self, context: PipelineContext) -> PipelineContext:
        """发送消息到Kafka"""
        try:
            topic = self.config.get('topic')
            if not topic:
                self.logger.error("未配置Kafka主题")
                return context
            
            # 打印要发送到Kafka的数据
            import json
            self.logger.info(f"准备发送到Kafka - topic: {topic}")
            self.logger.info(f"发送数据: {json.dumps(context.data, ensure_ascii=False, indent=2)}")
            
            # 发送消息
            success = self.kafka_client.send_message(topic, context.data)
            
            if success:
                self.logger.info(f"✅ Kafka消息发送成功: topic={topic}")
            else:
                self.logger.error(f"❌ Kafka消息发送失败: topic={topic}")
            
            return context
            
        except Exception as e:
            self.logger.error(f"Kafka消息发送失败: {e}")
            return context
    
    async def cleanup(self):
        """清理Kafka客户端资源"""
        if self.kafka_client:
            # 这里可以添加关闭生产者的逻辑
            pass


class ComponentFactory:
    """组件工厂类"""
    
    @staticmethod
    def create_component(comp_type: str, name: str, config: Dict[str, Any], **kwargs) -> PipelineComponent:
        """创建组件实例"""
        try:
            component_type = ComponentType(comp_type)
            
            if component_type == ComponentType.EVENT_MONITOR:
                data_processor = kwargs.get('data_processor')
                if not data_processor:
                    raise ValueError("事件监控器需要 data_processor 参数")
                return EventMonitorComponent(name, config, data_processor)
            
            elif component_type == ComponentType.CONTRACT_CALLER:
                return ContractCallerComponent(name, config)
            
            elif component_type == ComponentType.DICT_MAPPER:
                return DictMapperComponent(name, config)
            
            elif component_type == ComponentType.KAFKA_PRODUCER:
                return KafkaProducerComponent(name, config)
            
            else:
                raise ValueError(f"不支持的组件类型: {comp_type}")
                
        except ValueError as e:
            logger.error(f"创建组件失败: {e}")
            raise


class OptimizedBlockchainDataPipeline:
    """优化后的区块链数据管道执行器"""

    def __init__(self, config_path: str = None, config_dict: Dict[str, Any] = None, log_path: str = None):
        """
        初始化管道
        
        Args:
            config_path: JSON配置文件路径（可选）
            config_dict: 配置字典（可选）
            log_path: 日志文件路径（可选）
        """
        self.config_path = config_path
        self.config = None
        self.components: List[PipelineComponent] = []
        self.log_path = log_path
        
        # 为每个实例创建唯一的标识
        self.instance_id = str(uuid.uuid4())[:8]
        self.logger_ids = []
        
        # 配置日志输出
        self._setup_logging()
        
        # 加载配置
        if config_dict:
            self.config = config_dict
            logger.bind(instance_id=self.instance_id).info(f"从配置字典加载管道配置 - {self.config.get('pipeline_name', 'unknown')}")
        elif config_path:
            self._load_config()
        else:
            raise ValueError("必须提供 config_path 或 config_dict 参数")

        # 验证配置
        self._validate_config()
        
        logger.bind(instance_id=self.instance_id).info(f"优化版区块链数据管道初始化完成 - {self.config.get('pipeline_name', 'unknown')}")
        if self.log_path:
            logger.bind(instance_id=self.instance_id).info(f"日志输出路径: {self.log_path}")

    def _load_config(self):
        """加载JSON配置文件"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            logger.bind(instance_id=self.instance_id).info(f"配置文件加载成功: {self.config_path}")
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            raise

    def _validate_config(self):
        """验证配置文件"""
        if not self.config:
            raise ValueError("配置为空")
        
        components = self.config.get('components', [])
        if not components:
            raise ValueError("组件配置为空")
        
        # 验证第一个组件必须是数据源组件
        first_component = components[0]
        first_type = first_component.get('type')
        
        if first_type not in ['event_monitor', 'kafka_consumer']:
            raise ValueError(f"第一个组件必须是数据源组件(event_monitor/kafka_consumer)，当前为: {first_type}")
        
        logger.bind(instance_id=self.instance_id).info(f"配置验证通过: {len(components)} 个组件")

    def _setup_logging(self):
        """配置日志输出 - 同时支持控制台和文件输出"""
        # 存储日志处理器ID列表
        self.logger_ids = []
        
        # 定义日志格式
        # 带实例ID的日志格式
        instance_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>[{extra[instance_id]}]</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        # 普通日志格式
        general_log_format = "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>[global]</cyan> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        
        # 添加控制台输出 - 带实例ID的日志
        instance_console_handler_id = logger.add(
            sys.stdout,
            format=instance_log_format,
            level="INFO",
            filter=lambda record: record["extra"].get("instance_id") == self.instance_id
        )
        self.logger_ids.append(instance_console_handler_id)
        
        # 添加控制台输出 - 普通日志（没有实例ID的）
        general_console_handler_id = logger.add(
            sys.stdout,
            format=general_log_format,
            level="INFO",
            filter=lambda record: record["extra"].get("instance_id") is None
        )
        self.logger_ids.append(general_console_handler_id)
        
        # 如果指定了日志文件路径，同时添加文件输出
        if self.log_path:
            # 如果是相对路径，则相对于工程根目录
            if not os.path.isabs(self.log_path):
                # 获取工程根目录（当前文件的上上级目录）
                project_root = Path(__file__).parent.parent.parent
                log_file = project_root / self.log_path
            else:
                log_file = Path(self.log_path)
            
            # 确保日志目录存在
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 添加文件输出 - 带实例ID的日志
            instance_file_handler_id = logger.add(
                str(log_file),
                format=instance_log_format,
                level="INFO",
                rotation="10 MB",  # 日志文件大小达到10MB时轮转
                retention="7 days",  # 保留7天的日志文件
                compression="zip",  # 压缩旧的日志文件
                encoding="utf-8",
                filter=lambda record: record["extra"].get("instance_id") == self.instance_id
            )
            self.logger_ids.append(instance_file_handler_id)
            
            # 添加文件输出 - 普通日志（没有实例ID的）
            general_file_handler_id = logger.add(
                str(log_file),
                format=general_log_format,
                level="INFO",
                rotation="10 MB",  # 日志文件大小达到10MB时轮转
                retention="7 days",  # 保留7天的日志文件
                compression="zip",  # 压缩旧的日志文件
                encoding="utf-8",
                filter=lambda record: record["extra"].get("instance_id") is None
            )
            self.logger_ids.append(general_file_handler_id)
            
            # 绑定实例ID到logger
            logger.bind(instance_id=self.instance_id).info(f"实例 {self.instance_id} 日志配置完成 - 控制台输出 + 文件输出: {log_file}")
        else:
            # 只有控制台输出
            logger.bind(instance_id=self.instance_id).info(f"实例 {self.instance_id} 日志配置完成 - 仅控制台输出")

    def _cleanup_logging(self):
        """清理日志处理器"""
        for handler_id in self.logger_ids:
            try:
                logger.remove(handler_id)
            except Exception as e:
                # 忽略清理错误，避免影响程序正常退出
                pass
        self.logger_ids.clear()

    def __del__(self):
        """析构函数 - 清理日志处理器"""
        self._cleanup_logging()

    async def _initialize_components(self):
        """初始化所有组件"""
        components_config = self.config.get('components', [])
        
        for i, comp_config in enumerate(components_config):
            comp_name = comp_config.get('name')
            comp_type = comp_config.get('type')
            
            try:
                # 为第一个组件（数据源）提供数据处理器
                if i == 0 and comp_type == 'event_monitor':
                    component = ComponentFactory.create_component(
                        comp_type, comp_name, comp_config,
                        data_processor=self._process_pipeline_data
                    )
                else:
                    component = ComponentFactory.create_component(comp_type, comp_name, comp_config)
                
                # 初始化组件
                if await component.initialize():
                    self.components.append(component)
                    logger.bind(instance_id=self.instance_id).info(f"组件初始化成功: {comp_name} ({comp_type})")
                else:
                    logger.error(f"组件初始化失败: {comp_name} ({comp_type})")
                    
            except Exception as e:
                logger.error(f"创建组件失败: {comp_name} ({comp_type}), 错误: {e}")
                raise

    async def _process_pipeline_data(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理管道数据 - 这是事件监控器的回调函数
        
        Args:
            event_data: 来自事件监控器的原始事件数据
            
        Returns:
            处理后的数据
        """
        try:
            # 创建管道上下文
            context = PipelineContext(
                data=event_data.copy(),
                metadata={
                    'pipeline_name': self.config.get('pipeline_name'),
                    'start_time': datetime.now().isoformat(),
                    'instance_id': self.instance_id
                },
                pipeline_id=self.instance_id
            )
            
            logger.bind(instance_id=self.instance_id).info(f"开始处理管道数据: {len(event_data)} 个字段")
            
            # 打印初始数据
            import json
            initial_json = json.dumps(context.data, ensure_ascii=False, indent=2, default=str)
            logger.bind(instance_id=self.instance_id).info(f"初始输入数据:")
            logger.bind(instance_id=self.instance_id).info(f"\n{initial_json}")
            
            # 跳过第一个组件（数据源），从第二个组件开始执行
            for component in self.components[1:]:
                try:
                    context = await component.execute(context)
                    logger.bind(instance_id=self.instance_id).info(f"组件 {component.name} 执行完成")
                    
                    # 打印每个步骤后的JSON数据
                    step_json = json.dumps(context.data, ensure_ascii=False, indent=2, default=str)
                    logger.bind(instance_id=self.instance_id).info(f"组件 {component.name} 执行后的数据:")
                    logger.bind(instance_id=self.instance_id).info(f"\n{step_json}")
                    
                except Exception as e:
                    logger.error(f"组件 {component.name} 执行失败: {e}")
                    # 继续执行下一个组件，不中断整个流程
            
            logger.bind(instance_id=self.instance_id).info(f"管道数据处理完成: 执行了 {context.step_count} 个步骤")
            return context.data
            
        except Exception as e:
            logger.error(f"管道数据处理失败: {e}")
            return event_data

    async def execute_pipeline(self) -> Dict[str, Any]:
        """执行完整管道"""
        try:
            logger.bind(instance_id=self.instance_id).info(f"开始执行优化版管道: {self.config.get('pipeline_name', 'unknown')}")
            
            # 初始化所有组件
            await self._initialize_components()
            
            if not self.components:
                raise ValueError("没有成功初始化的组件")
            
            # 执行第一个组件（数据源组件）
            first_component = self.components[0]
            
            # 创建初始上下文
            initial_context = PipelineContext(
                data={},
                metadata={
                    'pipeline_name': self.config.get('pipeline_name'),
                    'start_time': datetime.now().isoformat(),
                    'instance_id': self.instance_id
                },
                pipeline_id=self.instance_id
            )
            
            # 启动数据源组件（通常是长期运行的）
            await first_component.execute(initial_context)
            
        except Exception as e:
            logger.error(f"管道执行失败: {e}")
            raise
        finally:
            # 清理资源
            await self._cleanup_components()

    async def _cleanup_components(self):
        """清理所有组件资源"""
        for component in self.components:
            try:
                await component.cleanup()
                logger.bind(instance_id=self.instance_id).info(f"组件清理完成: {component.name}")
            except Exception as e:
                logger.error(f"组件清理失败: {component.name}, 错误: {e}")
        
        # 清理日志处理器
        for handler_id in self.logger_ids:
            try:
                logger.remove(handler_id)
            except Exception:
                pass
        self.logger_ids.clear()

    def __del__(self):
        """析构函数"""
        # 清理日志处理器
        for handler_id in self.logger_ids:
            try:
                logger.remove(handler_id)
            except Exception:
                pass




async def test_full_pipeline():
    """测试完整的管道配置"""
    print("🧪 测试完整的管道配置")
    print("-" * 50)
    
    try:
        # 创建管道，使用完整配置文件
        config_path = "configs/optimized_pipeline_example.json"
        pipeline = OptimizedBlockchainDataPipeline(config_path)
        await pipeline.execute_pipeline()
        return True
        
    except Exception as e:
        print(f"❌ 完整管道测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    asyncio.run(test_full_pipeline())
