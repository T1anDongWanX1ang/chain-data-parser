"""
合约方法查询服务

此服务负责：
1. 从ABI结构中解析和分类不同类型的方法(function、event)
2. 基于event_name实现智能方法匹配逻辑
3. 支持多方法并行查询和结果聚合
4. 为前端提供结构化的合约方法信息
"""
import asyncio
import re
from typing import List, Dict, Optional, Set, Tuple, Union
from enum import Enum
from dataclasses import dataclass
from app.services.database_service import database_service
from app.models.contract_abi import ContractAbi
import logging

logger = logging.getLogger(__name__)


class MethodType(str, Enum):
    """合约方法类型枚举"""
    FUNCTION = "function"
    EVENT = "event"
    CONSTRUCTOR = "constructor"
    ERROR = "error"
    FALLBACK = "fallback"
    RECEIVE = "receive"


class StateMutability(str, Enum):
    """状态可变性枚举"""
    PURE = "pure"
    VIEW = "view"
    NONPAYABLE = "nonpayable"
    PAYABLE = "payable"


@dataclass
class MethodParameter:
    """方法参数定义"""
    name: str
    type: str
    indexed: Optional[bool] = None  # 仅对事件参数有效
    internal_type: Optional[str] = None


@dataclass
class ContractMethod:
    """合约方法定义"""
    name: str
    type: MethodType
    inputs: List[MethodParameter]
    outputs: Optional[List[MethodParameter]] = None
    state_mutability: Optional[StateMutability] = None
    signature: Optional[str] = None
    selector: Optional[str] = None
    anonymous: Optional[bool] = None  # 仅对事件有效
    
    def __post_init__(self):
        """生成方法签名和选择器"""
        if self.type in [MethodType.FUNCTION, MethodType.EVENT]:
            input_types = [param.type for param in self.inputs]
            self.signature = f"{self.name}({','.join(input_types)})"
            if self.type == MethodType.FUNCTION:
                # 计算函数选择器 (前4字节的keccak256哈希)
                try:
                    from Crypto.Hash import keccak
                    hash_obj = keccak.new(digest_bits=256)
                    hash_obj.update(self.signature.encode())
                    hash_bytes = hash_obj.digest()
                    self.selector = f"0x{hash_bytes[:4].hex()}"
                except ImportError:
                    # 如果没有pycryptodome，使用sha3作为替代
                    import hashlib
                    hash_bytes = hashlib.sha3_256(self.signature.encode()).digest()
                    self.selector = f"0x{hash_bytes[:4].hex()}"


@dataclass
class MethodQueryResult:
    """方法查询结果"""
    contract_address: str
    chain_name: str
    contract_name: Optional[str] = None
    methods: List[ContractMethod] = None
    events: List[ContractMethod] = None
    functions: List[ContractMethod] = None
    matched_methods: List[ContractMethod] = None
    query_metadata: Optional[Dict] = None

    def __post_init__(self):
        if self.methods is None:
            self.methods = []
        if self.events is None:
            self.events = []
        if self.functions is None:
            self.functions = []
        if self.matched_methods is None:
            self.matched_methods = []


class ContractMethodService:
    """合约方法查询服务"""
    
    def __init__(self):
        pass
        
    async def parse_abi_methods(self, abi_content: List[Dict]) -> Tuple[List[ContractMethod], List[ContractMethod]]:
        """
        解析ABI内容，提取所有方法并分类
        
        Args:
            abi_content: ABI JSON内容
            
        Returns:
            Tuple[functions, events]: 函数列表和事件列表
        """
        functions = []
        events = []
        
        for item in abi_content:
            try:
                # 解析输入参数
                inputs = []
                if 'inputs' in item:
                    for input_param in item['inputs']:
                        param = MethodParameter(
                            name=input_param.get('name', ''),
                            type=input_param['type'],
                            indexed=input_param.get('indexed'),
                            internal_type=input_param.get('internalType')
                        )
                        inputs.append(param)
                
                # 解析输出参数（仅函数有）
                outputs = []
                if 'outputs' in item:
                    for output_param in item['outputs']:
                        param = MethodParameter(
                            name=output_param.get('name', ''),
                            type=output_param['type'],
                            internal_type=output_param.get('internalType')
                        )
                        outputs.append(param)
                
                # 创建方法对象
                method = ContractMethod(
                    name=item.get('name', ''),
                    type=MethodType(item['type']),
                    inputs=inputs,
                    outputs=outputs if outputs else None,
                    state_mutability=StateMutability(item['stateMutability']) if 'stateMutability' in item else None,
                    anonymous=item.get('anonymous')
                )
                
                # 分类存储
                if method.type == MethodType.FUNCTION:
                    functions.append(method)
                elif method.type == MethodType.EVENT:
                    events.append(method)
                    
            except Exception as e:
                logger.warning(f"解析ABI方法时出错: {item}, 错误: {e}")
                continue
                
        return functions, events
    
    def match_methods_by_event_name(self, event_name: str, functions: List[ContractMethod], events: List[ContractMethod]) -> List[ContractMethod]:
        """
        根据事件名称智能匹配相关方法
        
        匹配策略:
        1. 精确匹配：方法名与事件名完全相同
        2. 前缀匹配：方法名以事件名开头
        3. 语义匹配：基于常见的区块链命名模式
        4. 关键词匹配：基于常见动作词汇匹配
        
        Args:
            event_name: 目标事件名称
            functions: 合约函数列表
            events: 合约事件列表
            
        Returns:
            匹配的方法列表
        """
        matched_methods = []
        event_name_lower = event_name.lower()
        
        # 1. 精确匹配和前缀匹配
        for func in functions:
            func_name_lower = func.name.lower()
            
            # 精确匹配
            if func_name_lower == event_name_lower:
                matched_methods.append(func)
                continue
                
            # 前缀匹配
            if func_name_lower.startswith(event_name_lower):
                matched_methods.append(func)
                continue
                
        # 2. 语义匹配 - 常见的区块链操作模式
        semantic_patterns = {
            'transfer': ['transfer', 'send', 'move', 'swap'],
            'approval': ['approve', 'allow', 'permit'],
            'deposit': ['deposit', 'stake', 'lock'],
            'withdraw': ['withdraw', 'unstake', 'unlock', 'redeem'],
            'mint': ['mint', 'create', 'issue'],
            'burn': ['burn', 'destroy', 'remove'],
            'pause': ['pause', 'stop', 'disable'],
            'unpause': ['unpause', 'resume', 'enable'],
            'borrow': ['borrow', 'loan', 'debt'],
            'repay': ['repay', 'payback', 'return'],
            'liquidate': ['liquidate', 'seize', 'liquidation'],
            'supply': ['supply', 'provide', 'add'],
        }
        
        # 查找语义匹配
        for pattern_key, keywords in semantic_patterns.items():
            if pattern_key in event_name_lower:
                for func in functions:
                    func_name_lower = func.name.lower()
                    if func not in matched_methods:
                        for keyword in keywords:
                            if keyword in func_name_lower:
                                matched_methods.append(func)
                                break
                                
        # 3. 关键词匹配 - 基于常见动作词汇
        action_words = ['get', 'set', 'update', 'change', 'modify', 'execute', 'call', 'invoke']
        for func in functions:
            func_name_lower = func.name.lower()
            if func not in matched_methods:
                for action in action_words:
                    if action in func_name_lower and event_name_lower in func_name_lower:
                        matched_methods.append(func)
                        break
                        
        # 4. 相关事件匹配 - 如果查询的是事件名，也返回该事件
        for event in events:
            if event.name.lower() == event_name_lower:
                matched_methods.append(event)
                
        # 去重并按相关性排序
        unique_methods = []
        seen_signatures = set()
        
        for method in matched_methods:
            if method.signature not in seen_signatures:
                unique_methods.append(method)
                seen_signatures.add(method.signature)
                
        return unique_methods
    
    async def query_contract_methods(
        self, 
        contract_address: str, 
        chain_name: Optional[str] = None,
        event_name: Optional[str] = None,
        method_types: Optional[List[MethodType]] = None
    ) -> MethodQueryResult:
        """
        查询合约方法
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            event_name: 事件名称（用于智能匹配）
            method_types: 要查询的方法类型列表
            
        Returns:
            方法查询结果
        """
        try:
            # 1. 获取合约ABI
            async with database_service.get_session() as session:
                from sqlalchemy import and_, select
                
                query = select(ContractAbi).where(
                    ContractAbi.contract_address == contract_address.lower()
                )
                
                if chain_name:
                    query = query.where(ContractAbi.chain_name == chain_name.lower())
                
                result = await session.execute(query)
                abi_record = result.scalar_one_or_none()
            
            if not abi_record:
                return MethodQueryResult(
                    contract_address=contract_address,
                    chain_name=chain_name or "unknown",
                    query_metadata={
                        "error": "Contract ABI not found",
                        "searched_address": contract_address,
                        "searched_chain": chain_name
                    }
                )
            
            # 2. 解析ABI方法
            # 如果abi_content是字符串，需要先解析为JSON
            import json
            abi_content = abi_record.abi_content
            if isinstance(abi_content, str):
                try:
                    abi_content = json.loads(abi_content)
                except json.JSONDecodeError as e:
                    logger.error(f"ABI内容JSON解析失败: {e}")
                    return MethodQueryResult(
                        contract_address=contract_address,
                        chain_name=abi_record.chain_name,
                        query_metadata={
                            "error": f"ABI内容格式错误: {str(e)}",
                            "error_type": "JSON_DECODE_ERROR"
                        }
                    )
            
            functions, events = await self.parse_abi_methods(abi_content)
            
            # 3. 根据类型过滤
            filtered_functions = functions
            filtered_events = events
            
            if method_types:
                if MethodType.FUNCTION not in method_types:
                    filtered_functions = []
                if MethodType.EVENT not in method_types:
                    filtered_events = []
            
            # 4. 智能匹配（如果提供了事件名称）
            matched_methods = []
            if event_name:
                matched_methods = self.match_methods_by_event_name(
                    event_name, filtered_functions, filtered_events
                )
            
            # 5. 构建查询结果
            result = MethodQueryResult(
                contract_address=contract_address,
                chain_name=abi_record.chain_name,
                contract_name=abi_record.contract_name,
                methods=filtered_functions + filtered_events,
                events=filtered_events,
                functions=filtered_functions,
                matched_methods=matched_methods,
                query_metadata={
                    "total_functions": len(filtered_functions),
                    "total_events": len(filtered_events),
                    "matched_methods_count": len(matched_methods),
                    "query_event_name": event_name,
                    "abi_source_type": abi_record.source_type,
                    "contract_abi_id": abi_record.id
                }
            )
            
            return result
            
        except Exception as e:
            logger.error(f"查询合约方法时出错: {e}")
            return MethodQueryResult(
                contract_address=contract_address,
                chain_name=chain_name or "unknown",
                query_metadata={
                    "error": str(e),
                    "error_type": type(e).__name__
                }
            )
    
    async def batch_query_contract_methods(
        self,
        queries: List[Dict[str, Union[str, List[MethodType]]]]
    ) -> List[MethodQueryResult]:
        """
        批量查询多个合约的方法
        
        Args:
            queries: 查询参数列表，每个元素包含 {
                'contract_address': str,
                'chain_name': Optional[str],
                'event_name': Optional[str],
                'method_types': Optional[List[MethodType]]
            }
            
        Returns:
            查询结果列表
        """
        tasks = []
        
        for query in queries:
            task = self.query_contract_methods(
                contract_address=query['contract_address'],
                chain_name=query.get('chain_name'),
                event_name=query.get('event_name'),
                method_types=query.get('method_types')
            )
            tasks.append(task)
        
        # 并行执行所有查询
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    MethodQueryResult(
                        contract_address=queries[i]['contract_address'],
                        chain_name=queries[i].get('chain_name', 'unknown'),
                        query_metadata={
                            "error": str(result),
                            "error_type": type(result).__name__,
                            "batch_index": i
                        }
                    )
                )
            else:
                processed_results.append(result)
                
        return processed_results