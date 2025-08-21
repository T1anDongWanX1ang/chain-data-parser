#!/usr/bin/env python3
"""
区块链数据管道执行器

根据 JSON 配置文件执行完整的数据处理流程
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from loguru import logger
import uuid

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
project_root = current_dir.parent.parent
sys.path.insert(0, str(project_root))

from app.component.event_monitor import ContractEventMonitor, EventMonitorConfig
from app.component.contract_caller import ContractMethodCaller, MethodCallConfig
from app.component.dict_mapper import DictMapper, MappingConfig, MappingRule
from app.component.kafka_client import KafkaClient, KafkaConfig


class BlockchainDataPipeline:
    """区块链数据管道执行器"""

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
        self.components = {}
        self.log_path = log_path
        
        # 为每个实例创建唯一的logger标识
        self.instance_id = str(uuid.uuid4())[:8]
        self.logger_ids = []
        
        # 配置日志输出
        self._setup_logging()
        
        # 加载配置
        if config_dict:
            self.config = config_dict
            logger.info(f"从配置字典加载管道配置 - {self.config.get('pipeline_name', 'unknown')}")
        elif config_path:
            self._load_config()
        else:
            raise ValueError("必须提供 config_path 或 config_dict 参数")

        logger.info(f"区块链数据管道初始化完成 - {self.config.get('pipeline_name', 'unknown')}")
        if self.log_path:
            logger.info(f"日志输出路径: {self.log_path}")
        self._init_pipeline_components()

    def _load_config(self):
        """加载JSON配置文件"""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"配置文件不存在: {self.config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = json.load(f)

            logger.info(f"配置文件加载成功: {self.config_path}")
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            raise

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

    async def _process_data(self, pipeline_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        处理事件数据，可根据需要进行字段转换、过滤或增强。

        Args:
            event_data: 原始事件数据字典

        Returns:
            处理后的事件数据字典
        """
        # 添加处理时间戳
        processed_data = pipeline_data.copy()
        components_config = self.config.get('components', [])
        # 按顺序执行组件
        for  comp_config in components_config:
            comp_name = comp_config.get('name')
            # 跳过第一个组件，不执行
            if comp_name == components_config[0].get('name'):
                continue
            comp_type = comp_config.get('type')
            try:
                # 使用已创建的组件对象
                if comp_type == 'contract_caller':
                    method_params = comp_config['method_params']
                    method_args = []
                    if method_params and len(method_params) > 0:
                        method_args = [self._resolve_parameter(item, processed_data) for item in method_params]
                    contract_caller = self.components[comp_name]
                    call_data = contract_caller.call_method(comp_config['method_name'], method_args)
                    processed_data = self._merge_data(processed_data, call_data, comp_name)
                elif comp_type == 'dict_mapper':
                    dict_mapper = self.components[comp_name]
                    processed_data = dict_mapper.map_dict(processed_data)
                elif comp_type == 'kafka_producer':
                    topic = comp_config['topic']
                    kafka_client = self.components[comp_name]
                    kafka_client.send_message(topic, processed_data, processed_data)
                logger.info(f"步骤 {comp_name} 执行后数据: {processed_data}")
            except Exception as e:
                logger.error(f"组件 {comp_name} 执行失败: {e}")

        return processed_data

    
    def _load_abi_file(self, abi_path: str) -> List[Dict[str, Any]]:
        """加载ABI文件"""
        try:
            if not os.path.isabs(abi_path):
                # 相对于配置文件的路径
                config_dir = Path(self.config_path).parent
                abi_file = config_dir / abi_path
            else:
                abi_file = Path(abi_path)

            if not abi_file.exists():
                logger.warning(f"ABI文件不存在: {abi_file}")
                return []

            with open(abi_file, 'r', encoding='utf-8') as f:
                abi_data = json.load(f)

            logger.info(f"ABI文件加载成功: {abi_file}")
            return abi_data
        except Exception as e:
            logger.error(f"ABI文件加载失败: {abi_path}, 错误: {e}")
            return []

    def _create_event_monitor(self, comp_name: str, comp_config: Dict[str, Any], process_data: Callable) -> ContractEventMonitor:
        """创建事件监控器"""
        # 加载ABI
        abi = self._load_abi_file(comp_config.get('abi_path', ''))
        # 创建监控配置
        monitor_config = EventMonitorConfig(
            mode=comp_config.get('mode', 'realtime'),
            events_to_monitor=comp_config.get('events_to_monitor'),
            output_format=comp_config.get('output_format', 'detailed'),
            poll_interval=comp_config.get('poll_interval', 1.0),
            custom_handler=process_data
        )
        return ContractEventMonitor(
            chain_name=comp_config['chain_name'],
            contract_address=comp_config['contract_address'],
            abi=abi,
            config=monitor_config,
        )

    def _create_contract_caller(self, comp_name: str, comp_config: Dict[str, Any]) -> ContractMethodCaller:
        """创建合约调用器"""
        # 加载ABI
        abi = self._load_abi_file(comp_config.get('abi_path', ''))

        # 创建调用配置
        call_config = MethodCallConfig(
            output_format="json",
            include_block_info=False
        )
        return ContractMethodCaller(
            chain_name=comp_config['chain_name'],
            contract_address=comp_config['contract_address'],
            abi=abi,
            config=call_config
        )

    def _create_dict_mapper(self, comp_name: str, comp_config: Dict[str, Any]) -> DictMapper:
        """创建字典映射器"""
        # 创建映射规则
        mapping_rules = []
        for rule_config in comp_config.get('mapping_rules', []):
            rule = MappingRule(
                source_key=rule_config['source_key'],
                target_key=rule_config['target_key'],
                transformer=rule_config.get('transformer'),
                condition=rule_config.get('condition'),
                default_value=rule_config.get('default_value')
            )
            mapping_rules.append(rule)

        # 创建映射配置
        mapper_config = MappingConfig(
            mapping_rules=mapping_rules
        )

        return DictMapper(mapper_config)

    def _create_kafka_client(self, comp_name: str, comp_config: Dict[str, Any]) -> KafkaClient:
        """创建Kafka客户端"""
        # 创建Kafka配置
        kafka_config = KafkaConfig(
            bootstrap_servers=comp_config.get('bootstrap_servers', 'localhost:9092'),
            # client_id=f"pipeline-{comp_name}",
            acks=comp_config.get('acks', 1),
            sync_send=comp_config.get('sync_send', False),
            retries=comp_config.get('retries', 3),
            batch_size=comp_config.get('batch_size', 16384),
            linger_ms=comp_config.get('linger_ms', 0)
        )

        return KafkaClient(kafka_config)

    def _merge_data(self, existing_data: Dict[str, Any], new_data: Dict[str, Any], component_name: str) -> Dict[
        str, Any]:
        """合并组件数据"""
        merged_data = existing_data.copy()

        # 添加组件输出数据
        merged_data[component_name] = new_data

        # 将新数据的键值对合并到顶层（如果不冲突）
        if isinstance(new_data, dict):
            for key, value in new_data.items():
                if key not in merged_data:
                    merged_data[key] = value

        return merged_data

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
                    logger.warning(f"无法解析参数引用: {param}")
                    return None

            return current

        # 直接键引用
        return data.get(param)


    async def _execute_dict_mapper(self, comp_name: str, comp_config: Dict[str, Any], pipeline_data: Dict[str, Any]) -> \
            Dict[str, Any]:
        """执行字典映射器"""
        logger.info(f"执行字典映射器: {comp_name}")

        try:
            # 创建字典映射器
            mapper = self._create_dict_mapper(comp_name, comp_config)

            # 执行映射
            mapped_data = mapper.map_dict(pipeline_data)

            logger.info(f"字典映射器 {comp_name} 完成映射，输出 {len(mapped_data)} 个字段")
            return mapped_data
        except Exception as e:
            logger.error(f"字典映射器 {comp_name} 执行失败: {e}")
            return {}

    async def execute_pipeline(self) -> Dict[str, Any]:
        """执行完整管道"""
        logger.info(f"开始执行管道: {self.config.get('pipeline_name', 'unknown')}")
        # 获取组件配置
        components_config = self.config.get('components', [])
        if not components_config:
            raise ValueError("组件配置为空，无法执行管道")
        first_components_config = next(iter(components_config))
        first_comp_type = first_components_config.get('type')
        first_comp_name = first_components_config.get('name')
        if first_comp_type == 'event_monitor':
            # 启动 监听
            event_monitor = self._create_event_monitor(first_comp_name, first_components_config,self._process_data)
            await event_monitor.start_monitoring()
        if first_comp_type == 'kafka_consumer':
            event_monitor = self._create_kafka_client(first_comp_name, first_components_config)
            topics = components_config[0].get('topic')
            group_id = first_comp_name
            event_monitor.consume_messages(topics, group_id,self._process_data())
    def _init_pipeline_components(self):
       components_config = self.config.get('components', [])
       for comp_config in components_config:
            comp_name = comp_config.get('name')
            # 跳过第一个组件，不执行
            if comp_name == components_config[0].get('name'):
                continue
            comp_type = comp_config.get('type')
            # 检查组件是否已创建，未创建则创建并缓存
            if comp_name not in self.components:
                if comp_type == 'contract_caller':
                    self.components[comp_name] = self._create_contract_caller(comp_name, comp_config)
                elif comp_type == 'dict_mapper':
                    self.components[comp_name] = self._create_dict_mapper(comp_name, comp_config)
                elif comp_type == 'kafka_producer':
                    kafka_client = self._create_kafka_client(comp_name, comp_config)
                    kafka_client.init_producer()
                    self.components[comp_name] = kafka_client
                else:
                    raise ValueError(f"未知的组件类型: {comp_type}")

async def main():
    """主函数"""
    print("区块链数据管道执行器")
    print("基于 JSON 配置文件执行数据处理流程")
    print("-" * 50)
    try:
        # 创建管道，指定配置文件路径
        config_path = "configs/usdc_transfer_pipeline_config.json"
        pipeline = BlockchainDataPipeline(config_path)
        # 执行管道
        await pipeline.execute_pipeline()

    except Exception as e:
        logger.error(f"管道执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    # 运行管道（日志配置在 BlockchainDataPipeline 类中进行）
    asyncio.run(main())
