"""管道配置服务"""
import json
import asyncio
import math
from datetime import datetime
from typing import Dict, Any, List, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException, status
from loguru import logger

from app.models.pipeline import Pipeline
from app.models.pipeline_component import PipelineComponent
from app.models.pipeline_task import PipelineTask
from app.models.evm_event_monitor import EvmEventMonitor
from app.models.evm_contract_caller import EvmContractCaller
from app.models.kafka_producer import KafkaProducer
from app.models.dict_mapper import DictMapper
from sqlalchemy import select


class PipelineConfigService:
    """管道配置服务"""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def parse_and_save_pipeline(self, pipeline_id: int, pipeline_info_str: str) -> Dict[str, Any]:
        """解析并保存管道配置"""
        try:
            # 解析JSON
            pipeline_info = json.loads(pipeline_info_str)
            logger.info(f"开始解析管道配置: {pipeline_info.get('pipeline_name', 'unknown')}")

            # 更新或创建管道
            pipeline = await self._update_or_create_pipeline(pipeline_id, pipeline_info)

            # 解析并保存组件
            components_created = await self._parse_and_save_components(pipeline.id, pipeline_info.get('components', []))

            # 提交事务
            await self.session.commit()

            logger.info(f"管道配置保存成功: pipeline_id={pipeline.id}, components={components_created}")

            return {
                "success": True,
                "message": "管道配置保存成功",
                "pipeline_id": pipeline.id,
                "components_created": components_created
            }

        except json.JSONDecodeError as e:
            logger.error(f"JSON解析失败: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"JSON格式错误: {str(e)}"
            )
        except Exception as e:
            logger.error(f"管道配置保存失败: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"保存失败: {str(e)}"
            )

    async def _update_or_create_pipeline(self, pipeline_id: int, pipeline_info: Dict[str, Any]) -> Pipeline:
        """更新或创建管道"""
        # 查找现有管道
        result = await self.session.get(Pipeline, pipeline_id)

        if result:
            # 更新现有管道
            pipeline = result
            if 'classification_id' in pipeline_info:
                pipeline.classification_id = pipeline_info.get('classification_id')
            pipeline.name = pipeline_info.get('pipeline_name')
            pipeline.description = pipeline_info.get('description')
            pipeline.update_time = datetime.now()
            logger.info(f"更新现有管道: {pipeline_id}")
        else:
            # 创建新管道
            pipeline = Pipeline(
                id=pipeline_id,
                classification_id=pipeline_info.get('classification_id', 1),  # 默认分类ID为1
                name=pipeline_info.get('pipeline_name'),
                description=pipeline_info.get('description'),
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            self.session.add(pipeline)
            logger.info(f"创建新管道: {pipeline_id}")

        await self.session.flush()  # 确保获得ID
        return pipeline

    async def _parse_and_save_components(self, pipeline_id: int, components: List[Dict[str, Any]]) -> int:
        """解析并保存组件"""
        components_created = 0
        # 先根据 pipeline_id 删除所有 pipeline_component
        await self.session.execute(
            PipelineComponent.__table__.delete().where(PipelineComponent.pipeline_id == pipeline_id)
        )
        pre_component_id = None
        for i, component_info in enumerate(components):
            try:
                # 创建管道组件
                component = PipelineComponent(
                    pipeline_id=pipeline_id,
                    pre_component_id=pre_component_id,
                    name=component_info.get('name'),
                    type=component_info.get('type'),
                    create_time=datetime.now()
                )
                self.session.add(component)
                await self.session.flush()  # 获得component ID
                pre_component_id = component.id

                # 根据组件类型创建对应的配置
                component_type = component_info.get('type')
                if component_type == 'event_monitor':
                    await self._create_event_monitor(component.id, component_info)
                elif component_type == 'contract_caller':
                    await self._create_contract_caller(component.id, component_info)
                elif component_type == 'dict_mapper':
                    await self._create_dict_mapper(component.id, component_info)
                elif component_type == 'kafka_producer':
                    await self._create_kafka_producer(component.id, component_info)
                else:
                    logger.warning(f"未知的组件类型: {component_type}")

                components_created += 1
                logger.info(f"创建组件成功: {component.name} ({component_type})")

            except Exception as e:
                logger.error(f"创建组件失败: {component_info.get('name', 'unknown')}, 错误: {e}")
                raise

        return components_created

    async def _create_event_monitor(self, component_id: int, component_info: Dict[str, Any]):
        """创建事件监控器配置"""
        events_to_monitor = component_info.get('events_to_monitor', [])
        events_str = json.dumps(events_to_monitor) if events_to_monitor else None

        event_monitor = EvmEventMonitor(
            component_id=component_id,
            chain_name=component_info.get('chain_name'),
            contract_address=component_info.get('contract_address'),
            abi_path=component_info.get('abi_path'),
            events_to_monitor=events_str
        )
        self.session.add(event_monitor)

    async def _create_contract_caller(self, component_id: int, component_info: Dict[str, Any]):
        """创建合约调用器配置 - 支持多条记录"""
        # 支持两种配置格式：
        # 1. 旧格式：单个合约调用器配置
        # 2. 新格式：contract_callers 数组，支持多个合约调用器
        
        contract_callers_config = component_info.get('contract_callers', [])
        
        if contract_callers_config:
            # 新格式：多个合约调用器
            for caller_config in contract_callers_config:
                method_params = caller_config.get('method_params', [])
                params_str = json.dumps(method_params) if method_params else None

                contract_caller = EvmContractCaller(
                    component_id=component_id,
                    event_name=caller_config.get('event_name'),
                    chain_name=caller_config.get('chain_name'),
                    abi_path=caller_config.get('abi_path'),
                    contract_address=caller_config.get('contract_address'),
                    method_name=caller_config.get('method_name'),
                    method_params=params_str,
                    create_time=datetime.now(),
                    update_time=datetime.now()
                )
                self.session.add(contract_caller)
        else:
            # 旧格式：单个合约调用器（向后兼容）
            method_params = component_info.get('method_params', [])
            params_str = json.dumps(method_params) if method_params else None

            contract_caller = EvmContractCaller(
                component_id=component_id,
                event_name=component_info.get('event_name'),
                chain_name=component_info.get('chain_name'),
                abi_path=component_info.get('abi_path'),
                contract_address=component_info.get('contract_address'),
                method_name=component_info.get('method_name'),
                method_params=params_str,
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            self.session.add(contract_caller)

    async def _create_dict_mapper(self, component_id: int, component_info: Dict[str, Any]):
        """创建字典映射器配置"""
        # 只支持新的 dict_mappers 配置格式
        dict_mappers_config = component_info.get('dict_mappers', [])
        
        # 如果没有 dict_mappers 配置，抛出错误
        if not dict_mappers_config:
            raise ValueError("dict_mapper 组件必须包含 dict_mappers 配置")
        
        # 创建多条 dict_mapper 记录
        for mapper_config in dict_mappers_config:
            event_name = mapper_config.get('event_name')
            mapping_rules = mapper_config.get('mapping_rules', [])
            
            # 验证必需字段
            if not mapping_rules:
                raise ValueError(f"dict_mapper 配置必须包含 mapping_rules: event_name={event_name}")
            
            # 构建配置JSON
            config_dict = {
                'mapping_rules': mapping_rules
            }
            config_str = json.dumps(config_dict, ensure_ascii=False)

            dict_mapper = DictMapper(
                component_id=component_id,
                event_name=event_name,
                dict_mapper=config_str,
                create_time=datetime.now(),
                update_time=datetime.now()
            )
            self.session.add(dict_mapper)

    async def _create_kafka_producer(self, component_id: int, component_info: Dict[str, Any]):
        """创建Kafka生产者配置"""
        kafka_producer = KafkaProducer(
            component_id=component_id,
            bootstrap_servers=component_info.get('bootstrap_servers'),
            topic=component_info.get('topic'),
            create_time=datetime.now(),
            update_time=datetime.now()
        )
        self.session.add(kafka_producer)

    async def get_pipeline_config(self, pipeline_id: int) -> Dict[str, Any]:
        """获取管道配置"""
        try:
            # 查询管道基本信息
            pipeline = await self.session.get(Pipeline, pipeline_id)
            if not pipeline:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"管道不存在: {pipeline_id}"
                )

            # 查询管道组件
            result = await self.session.execute(
                select(PipelineComponent).where(PipelineComponent.pipeline_id == pipeline_id)
                .order_by(PipelineComponent.id)
            )
            components = result.scalars().all()

            # 构建响应数据
            pipeline_config = {
                "pipeline_id": pipeline.id,
                "pipeline_name": pipeline.name,
                "description": pipeline.description,
                "create_time": pipeline.create_time.isoformat() if pipeline.create_time else None,
                "update_time": pipeline.update_time.isoformat() if pipeline.update_time else None,
                "components": []
            }

            # 获取每个组件的详细配置
            for component in components:
                component_data = {
                    "id": component.id,
                    "name": component.name,
                    "type": component.type,
                    "create_time": component.create_time.isoformat() if component.create_time else None
                }

                # 根据组件类型和component_id查询对应配置表
                if component.type == 'event_monitor':
                    em_result = await self.session.execute(
                        select(EvmEventMonitor).where(EvmEventMonitor.component_id == component.id)
                    )
                    em = em_result.scalar_one_or_none()
                    if em:
                        component_data.update({
                            "chain_name": em.chain_name,
                            "contract_address": em.contract_address,
                            "abi_path": em.abi_path,
                            "events_to_monitor": json.loads(em.events_to_monitor) if em.events_to_monitor else []
                        })

                elif component.type == 'contract_caller':
                    cc_result = await self.session.execute(
                        select(EvmContractCaller).where(EvmContractCaller.component_id == component.id)
                    )
                    contract_callers = cc_result.scalars().all()
                    
                    if len(contract_callers) == 1:
                        # 单个合约调用器，使用旧格式（向后兼容）
                        cc = contract_callers[0]
                        component_data.update({
                            "event_name": cc.event_name,
                            "chain_name": cc.chain_name,
                            "abi_path": cc.abi_path,
                            "contract_address": cc.contract_address,
                            "method_name": cc.method_name,
                            "method_params": json.loads(cc.method_params) if cc.method_params else []
                        })
                    elif len(contract_callers) > 1:
                        # 多个合约调用器，使用新格式
                        contract_callers_config = []
                        for cc in contract_callers:
                            caller_config = {
                                "id": cc.id,
                                "event_name": cc.event_name,
                                "chain_name": cc.chain_name,
                                "abi_path": cc.abi_path,
                                "contract_address": cc.contract_address,
                                "method_name": cc.method_name,
                                "method_params": json.loads(cc.method_params) if cc.method_params else [],
                                "create_time": cc.create_time.isoformat() if cc.create_time else None,
                                "update_time": cc.update_time.isoformat() if cc.update_time else None
                            }
                            contract_callers_config.append(caller_config)
                        
                        component_data.update({
                            "contract_callers": contract_callers_config
                        })

                elif component.type == 'dict_mapper':
                    dm_result = await self.session.execute(
                        select(DictMapper).where(DictMapper.component_id == component.id)
                    )
                    dict_mappers = dm_result.scalars().all()
                    
                    # 构建多条 dict_mapper 配置
                    dict_mappers_config = []
                    for dm in dict_mappers:
                        mapper_config = json.loads(dm.dict_mapper) if dm.dict_mapper else {}
                        dict_mapper_item = {
                            "id": dm.id,
                            "event_name": dm.event_name,
                            "mapping_rules": mapper_config.get('mapping_rules', []),
                            "create_time": dm.create_time.isoformat() if dm.create_time else None,
                            "update_time": dm.update_time.isoformat() if dm.update_time else None
                        }
                        dict_mappers_config.append(dict_mapper_item)
                    
                    component_data.update({
                        "dict_mappers": dict_mappers_config
                    })

                elif component.type == 'kafka_producer':
                    kp_result = await self.session.execute(
                        select(KafkaProducer).where(KafkaProducer.component_id == component.id)
                    )
                    kp = kp_result.scalar_one_or_none()
                    if kp:
                        component_data.update({
                            "bootstrap_servers": kp.bootstrap_servers,
                            "topic": kp.topic
                        })

                pipeline_config["components"].append(component_data)

            return pipeline_config

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取管道配置失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取配置失败: {str(e)}"
            )

    async def get_pipelines_paginated(self, page: int = 1, page_size: int = 10) -> Tuple[List[Pipeline], int]:
        """分页查询管道列表
        
        Args:
            page: 页码，从1开始
            page_size: 每页大小
            
        Returns:
            Tuple[List[Pipeline], int]: (管道列表, 总记录数)
        """
        try:
            # 计算偏移量
            offset = (page - 1) * page_size

            # 查询总记录数
            count_result = await self.session.execute(
                select(func.count(Pipeline.id))
            )
            total = count_result.scalar()

            # 分页查询管道列表
            result = await self.session.execute(
                select(Pipeline)
                .order_by(Pipeline.id.desc())  # 按ID降序排列，最新的在前面
                .offset(offset)
                .limit(page_size)
            )
            pipelines = result.scalars().all()

            logger.info(f"分页查询管道列表成功: page={page}, page_size={page_size}, total={total}")
            return pipelines, total

        except Exception as e:
            logger.error(f"分页查询管道列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )

    async def start_pipeline_task(self, pipeline_id: int, log_path: str = None) -> Dict[str, Any]:
        """启动管道任务
        
        Args:
            pipeline_id: 管道ID
            log_path: 日志文件路径（可选）
            
        Returns:
            Dict[str, Any]: 启动结果
        """
        try:
            # 查询管道配置
            pipeline_config = await self.get_pipeline_config(pipeline_id)

            # 创建任务记录
            # 使用传入的日志路径或生成默认路径
            if log_path:
                task_log_path = log_path
            else:
                task_log_path = f"logs/pipeline_{pipeline_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            task = PipelineTask(
                pipeline_id=pipeline_id,
                create_time=datetime.now(),
                status=0,  # 正在运行
                log_path=task_log_path
            )
            self.session.add(task)
            await self.session.flush()  # 获取任务ID

            # 异步启动管道（直接使用查询到的配置）
            asyncio.create_task(self._execute_pipeline_async(task.id, pipeline_config))

            # 提交事务
            await self.session.commit()

            logger.info(f"管道任务启动成功: pipeline_id={pipeline_id}, task_id={task.id}")

            return {
                "success": True,
                "message": "管道任务启动成功",
                "task_id": task.id,
                "pipeline_id": pipeline_id
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"启动管道任务失败: {e}")
            await self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"启动失败: {str(e)}"
            )

    async def _execute_pipeline_async(self, task_id: int, config: Dict[str, Any]):
        """异步执行管道任务"""
        try:
            # 这里应该使用独立的数据库会话
            from app.services.database_service import database_service

            async with database_service.get_session() as session:
                # 更新任务状态为运行中
                task = await session.get(PipelineTask, task_id)
                if task:
                    task.status = 0  # 正在运行
                    await session.commit()

                # 创建管道执行器并运行
                logger.info(f"开始执行管道任务: task_id={task_id}")

                # 使用优化版配置字典创建管道执行器
                from app.component.pipeline_executor_optimized import OptimizedBlockchainDataPipeline
                pipeline = OptimizedBlockchainDataPipeline(config_dict=config, log_path=task.log_path)

                # 执行管道
                await pipeline.execute_pipeline()

                # 更新任务状态为成功
                task = await session.get(PipelineTask, task_id)
                if task:
                    task.status = 1  # 成功
                    await session.commit()

                logger.info(f"管道任务执行完成: task_id={task_id}")

        except Exception as e:
            logger.error(f"管道任务执行失败: task_id={task_id}, 错误: {e}")

            # 更新任务状态为失败
            try:
                from app.services.database_service import database_service
                async with database_service.get_session() as session:
                    task = await session.get(PipelineTask, task_id)
                    if task:
                        task.status = 2  # 失败
                        await session.commit()
            except Exception as update_error:
                logger.error(f"更新任务状态失败: {update_error}")

    async def get_tasks_paginated(self, page: int = 1, page_size: int = 10, status_filter: int = None,
                                  pipeline_name: str = None) -> Tuple[List[Dict[str, Any]], int]:
        """分页查询任务列表并关联管道信息
        
        Args:
            page: 页码，从1开始
            page_size: 每页大小
            status_filter: 状态过滤，可选值：0(运行中)、1(成功)、2(失败)
            pipeline_name: 管道名称关键字过滤
            
        Returns:
            Tuple[List[Dict[str, Any]], int]: (任务列表, 总记录数)
        """
        try:
            # 计算偏移量
            offset = (page - 1) * page_size

            # 构建查询条件
            query = select(PipelineTask, Pipeline).join(
                Pipeline, PipelineTask.pipeline_id == Pipeline.id
            )

            # 构建计数查询条件
            count_query = select(func.count(PipelineTask.id)).join(
                Pipeline, PipelineTask.pipeline_id == Pipeline.id
            )

            # 添加状态过滤
            if status_filter is not None:
                query = query.where(PipelineTask.status == status_filter)
                count_query = count_query.where(PipelineTask.status == status_filter)

            # 添加管道名称关键字过滤
            if pipeline_name:
                pipeline_name_filter = Pipeline.name.like(f"%{pipeline_name}%")
                query = query.where(pipeline_name_filter)
                count_query = count_query.where(pipeline_name_filter)

            # 查询总记录数
            count_result = await self.session.execute(count_query)
            total = count_result.scalar()

            # 分页查询任务列表
            query = query.order_by(PipelineTask.create_time.desc()).offset(offset).limit(page_size)
            result = await self.session.execute(query)
            rows = result.all()

            # 构建返回数据
            tasks = []
            for task, pipeline in rows:
                task_data = {
                    "task_id": task.id,
                    "pipeline_id": task.pipeline_id,
                    "pipeline_name": pipeline.name,
                    "pipeline_description": pipeline.description,
                    "status": task.status,
                    "status_text": task.status_text,
                    "create_time": task.create_time.isoformat() if task.create_time else None,
                    "log_path": task.log_path
                }
                tasks.append(task_data)

            logger.info(
                f"分页查询任务列表成功: page={page}, page_size={page_size}, total={total}, status_filter={status_filter}, pipeline_name={pipeline_name}")
            return tasks, total

        except Exception as e:
            logger.error(f"分页查询任务列表失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"查询失败: {str(e)}"
            )

    async def get_task_log(self, task_id: int, lines: int = 900) -> Dict[str, Any]:
        """获取任务日志内容
        
        Args:
            task_id: 任务ID
            lines: 读取的行数，默认900行
            
        Returns:
            Dict[str, Any]: 日志信息
        """
        try:
            # 查询任务信息
            task = await self.session.get(PipelineTask, task_id)
            if not task:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"任务不存在: {task_id}"
                )

            log_path = task.log_path
            if not log_path:
                return {
                    "task_id": task_id,
                    "log_path": None,
                    "log_content": "该任务没有配置日志文件路径",
                    "total_lines": 0,
                    "returned_lines": 0
                }

            # 处理相对路径和绝对路径
            import os
            from pathlib import Path

            if not os.path.isabs(log_path):
                # 相对路径，相对于项目根目录
                project_root = Path(__file__).parent.parent.parent
                full_log_path = project_root / log_path
            else:
                full_log_path = Path(log_path)

            # 检查日志文件是否存在
            if not full_log_path.exists():
                return {
                    "task_id": task_id,
                    "log_path": str(full_log_path),
                    "log_content": f"日志文件不存在: {full_log_path}",
                    "total_lines": 0,
                    "returned_lines": 0
                }

            # 读取日志文件的最后N行
            log_content, total_lines, returned_lines = self._read_last_lines(full_log_path, lines)

            logger.info(
                f"读取任务日志成功: task_id={task_id}, log_path={full_log_path}, returned_lines={returned_lines}")

            return {
                "task_id": task_id,
                "log_path": str(full_log_path),
                "log_content": log_content,
                "total_lines": total_lines,
                "returned_lines": returned_lines
            }

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取任务日志失败: task_id={task_id}, 错误: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取日志失败: {str(e)}"
            )

    def _read_last_lines(self, file_path, lines: int):
        """读取文件的最后N行
        
        Args:
            file_path: 文件路径
            lines: 要读取的行数
            
        Returns:
            tuple: (日志内容, 总行数, 实际返回行数)
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                # 读取所有行
                all_lines = f.readlines()
                total_lines = len(all_lines)

                # 获取最后N行
                last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                returned_lines = len(last_lines)

                # 合并为字符串
                log_content = ''.join(last_lines)

                return log_content, total_lines, returned_lines

        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk', errors='ignore') as f:
                    all_lines = f.readlines()
                    total_lines = len(all_lines)
                    last_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                    returned_lines = len(last_lines)
                    log_content = ''.join(last_lines)
                    return log_content, total_lines, returned_lines
            except Exception:
                pass

            # 如果所有编码都失败，返回错误信息
            return f"无法读取日志文件，编码格式不支持: {file_path}", 0, 0

        except Exception as e:
            logger.error(f"读取日志文件失败: {file_path}, 错误: {e}")
            return f"读取日志文件失败: {str(e)}", 0, 0
