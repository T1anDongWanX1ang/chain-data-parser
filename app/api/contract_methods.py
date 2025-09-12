"""
合约方法查询API路由

提供合约方法查询相关的RESTful API端点：
1. 单个合约方法查询
2. 批量合约方法查询
3. 支持基于事件名称的智能方法匹配
"""
from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional, Union
from pydantic import BaseModel, Field
import logging

from app.services.contract_method_service import (
    ContractMethodService, 
    MethodQueryResult, 
    MethodType,
    ContractMethod,
    MethodParameter
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/contracts", tags=["合约方法"])


# 请求和响应模型
class MethodParameterResponse(BaseModel):
    """方法参数响应模型"""
    name: str
    type: str
    indexed: Optional[bool] = None
    internal_type: Optional[str] = None


class ContractMethodResponse(BaseModel):
    """合约方法响应模型"""
    name: str
    type: str
    inputs: List[MethodParameterResponse]
    outputs: Optional[List[MethodParameterResponse]] = None
    state_mutability: Optional[str] = None
    signature: Optional[str] = None
    selector: Optional[str] = None
    anonymous: Optional[bool] = None


class MethodQueryResponse(BaseModel):
    """方法查询响应模型"""
    contract_address: str
    chain_name: str
    contract_name: Optional[str] = None
    methods: List[ContractMethodResponse] = Field(default_factory=list)
    events: List[ContractMethodResponse] = Field(default_factory=list)
    functions: List[ContractMethodResponse] = Field(default_factory=list)
    matched_methods: List[ContractMethodResponse] = Field(default_factory=list)
    query_metadata: Optional[dict] = None


class BatchQueryRequest(BaseModel):
    """批量查询请求模型"""
    queries: List[dict] = Field(..., description="查询参数列表")


class BatchQueryResponse(BaseModel):
    """批量查询响应模型"""
    success: bool
    data: List[MethodQueryResponse]
    total_queries: int
    successful_queries: int
    failed_queries: int


# 依赖注入
async def get_contract_method_service() -> ContractMethodService:
    """获取合约方法服务实例"""
    return ContractMethodService()


def convert_method_parameter(param: MethodParameter) -> MethodParameterResponse:
    """转换方法参数对象"""
    return MethodParameterResponse(
        name=param.name,
        type=param.type,
        indexed=param.indexed,
        internal_type=param.internal_type
    )


def convert_contract_method(method: ContractMethod) -> ContractMethodResponse:
    """转换合约方法对象"""
    return ContractMethodResponse(
        name=method.name,
        type=method.type.value,
        inputs=[convert_method_parameter(param) for param in method.inputs],
        outputs=[convert_method_parameter(param) for param in method.outputs] if method.outputs else None,
        state_mutability=method.state_mutability.value if method.state_mutability else None,
        signature=method.signature,
        selector=method.selector,
        anonymous=method.anonymous
    )


def convert_query_result(result: MethodQueryResult) -> MethodQueryResponse:
    """转换查询结果对象"""
    return MethodQueryResponse(
        contract_address=result.contract_address,
        chain_name=result.chain_name,
        contract_name=result.contract_name,
        methods=[convert_contract_method(method) for method in result.methods],
        events=[convert_contract_method(event) for event in result.events],
        functions=[convert_contract_method(func) for func in result.functions],
        matched_methods=[convert_contract_method(method) for method in result.matched_methods],
        query_metadata=result.query_metadata
    )


@router.get(
    "/{contract_address}/methods/query",
    response_model=MethodQueryResponse,
    summary="查询合约方法",
    description="根据合约地址查询合约的所有方法，支持基于事件名称的智能匹配"
)
async def query_contract_methods(
    contract_address: str,  # 路径参数不能使用Query
    chain_name: Optional[str] = Query(None, description="区块链名称"),
    event_name: Optional[str] = Query(None, description="事件名称（用于智能匹配相关方法）"),
    method_types: Optional[str] = Query(None, description="方法类型，多个用逗号分隔（function,event）"),
    service: ContractMethodService = Depends(get_contract_method_service)
):
    """
    查询指定合约的方法信息
    
    - **contract_address**: 合约地址（必填）
    - **chain_name**: 区块链名称（可选，用于精确匹配）
    - **event_name**: 事件名称（可选，用于智能匹配相关方法）
    - **method_types**: 要查询的方法类型（可选，支持：function, event, constructor, error, fallback, receive）
    
    返回合约的所有方法信息，包括函数和事件，如果提供了event_name会返回匹配的相关方法。
    """
    try:
        # 解析方法类型参数
        parsed_method_types = None
        if method_types:
            try:
                type_list = [t.strip().upper() for t in method_types.split(',')]
                parsed_method_types = [MethodType(t.lower()) for t in type_list if t in ['FUNCTION', 'EVENT', 'CONSTRUCTOR', 'ERROR', 'FALLBACK', 'RECEIVE']]
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"无效的方法类型参数: {method_types}. 支持的类型: function, event, constructor, error, fallback, receive"
                )
        
        # 调用服务查询方法
        result = await service.query_contract_methods(
            contract_address=contract_address,
            chain_name=chain_name,
            event_name=event_name,
            method_types=parsed_method_types
        )
        
        # 检查是否有错误
        if result.query_metadata and "error" in result.query_metadata:
            error_msg = result.query_metadata["error"]
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=f"合约ABI未找到: {error_msg}")
            else:
                raise HTTPException(status_code=500, detail=f"查询方法时出错: {error_msg}")
        
        return convert_query_result(result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询合约方法API出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询合约方法时发生未知错误: {str(e)}")


@router.post(
    "/batch/methods/query",
    response_model=BatchQueryResponse,
    summary="批量查询合约方法",
    description="批量查询多个合约的方法，支持并行处理"
)
async def batch_query_contract_methods(
    request: BatchQueryRequest,
    service: ContractMethodService = Depends(get_contract_method_service)
):
    """
    批量查询多个合约的方法信息
    
    请求体格式：
    ```json
    {
        "queries": [
            {
                "contract_address": "0x...",
                "chain_name": "ethereum",
                "event_name": "Transfer",
                "method_types": ["function", "event"]
            }
        ]
    }
    ```
    
    支持并行处理多个查询，提高查询效率。
    """
    try:
        if not request.queries:
            raise HTTPException(status_code=400, detail="查询列表不能为空")
        
        if len(request.queries) > 50:  # 限制批量查询数量
            raise HTTPException(status_code=400, detail="批量查询数量不能超过50个")
        
        # 验证和处理查询参数
        processed_queries = []
        for i, query in enumerate(request.queries):
            try:
                if "contract_address" not in query:
                    raise ValueError(f"第{i+1}个查询缺少contract_address参数")
                
                # 处理method_types参数
                method_types = None
                if "method_types" in query and query["method_types"]:
                    if isinstance(query["method_types"], list):
                        method_types = [MethodType(t.lower()) for t in query["method_types"]]
                    elif isinstance(query["method_types"], str):
                        type_list = [t.strip().lower() for t in query["method_types"].split(',')]
                        method_types = [MethodType(t) for t in type_list]
                
                processed_query = {
                    "contract_address": query["contract_address"],
                    "chain_name": query.get("chain_name"),
                    "event_name": query.get("event_name"),
                    "method_types": method_types
                }
                processed_queries.append(processed_query)
                
            except (ValueError, KeyError) as e:
                raise HTTPException(
                    status_code=400, 
                    detail=f"第{i+1}个查询参数错误: {str(e)}"
                )
        
        # 执行批量查询
        results = await service.batch_query_contract_methods(processed_queries)
        
        # 统计结果
        successful_queries = 0
        failed_queries = 0
        
        response_data = []
        for result in results:
            if result.query_metadata and "error" in result.query_metadata:
                failed_queries += 1
            else:
                successful_queries += 1
            response_data.append(convert_query_result(result))
        
        return BatchQueryResponse(
            success=True,
            data=response_data,
            total_queries=len(request.queries),
            successful_queries=successful_queries,
            failed_queries=failed_queries
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量查询合约方法API出错: {e}")
        raise HTTPException(status_code=500, detail=f"批量查询时发生未知错误: {str(e)}")


@router.get(
    "/{contract_address}/methods/{method_name}",
    response_model=List[ContractMethodResponse],
    summary="查询特定方法",
    description="查询合约中的特定方法（支持重载方法）"
)
async def get_specific_method(
    contract_address: str,
    method_name: str,
    chain_name: Optional[str] = Query(None, description="区块链名称"),
    service: ContractMethodService = Depends(get_contract_method_service)
):
    """
    查询合约中的特定方法
    
    - **contract_address**: 合约地址
    - **method_name**: 方法名称
    - **chain_name**: 区块链名称（可选）
    
    返回所有匹配该名称的方法（包括重载方法）。
    """
    try:
        # 先查询所有方法
        result = await service.query_contract_methods(
            contract_address=contract_address,
            chain_name=chain_name
        )
        
        if result.query_metadata and "error" in result.query_metadata:
            error_msg = result.query_metadata["error"]
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=f"合约ABI未找到: {error_msg}")
            else:
                raise HTTPException(status_code=500, detail=f"查询方法时出错: {error_msg}")
        
        # 筛选特定方法
        matching_methods = []
        for method in result.methods:
            if method.name.lower() == method_name.lower():
                matching_methods.append(method)
        
        if not matching_methods:
            raise HTTPException(
                status_code=404, 
                detail=f"在合约 {contract_address} 中未找到方法 '{method_name}'"
            )
        
        return [convert_contract_method(method) for method in matching_methods]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询特定方法API出错: {e}")
        raise HTTPException(status_code=500, detail=f"查询特定方法时发生未知错误: {str(e)}")


@router.get(
    "/methods/types",
    summary="获取支持的方法类型",
    description="获取所有支持的合约方法类型列表"
)
async def get_supported_method_types():
    """
    获取系统支持的所有合约方法类型
    
    返回可用的方法类型列表，用于前端选择和API参数验证。
    """
    return {
        "method_types": [
            {
                "value": "function",
                "label": "函数",
                "description": "合约中的可调用函数"
            },
            {
                "value": "event", 
                "label": "事件",
                "description": "合约发出的事件"
            },
            {
                "value": "constructor",
                "label": "构造函数", 
                "description": "合约构造函数"
            },
            {
                "value": "error",
                "label": "错误",
                "description": "自定义错误类型"
            },
            {
                "value": "fallback",
                "label": "回退函数",
                "description": "默认函数"
            },
            {
                "value": "receive",
                "label": "接收函数",
                "description": "接收ETH的函数"
            }
        ]
    }