"""ABI管理API接口"""
import json
from typing import List, Optional, Dict, Any, Union
from fastapi import APIRouter, HTTPException, status, Depends, Query, UploadFile, File
from pydantic import BaseModel, Field, validator
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from loguru import logger

from app.models.contract_abi import ContractAbi
from app.services import get_db_session, AbiStorageService, BlockchainExplorerService, ChainType
from app.services.blockchain_explorer_service import ChainType

router = APIRouter(prefix="/abis", tags=["合约ABI管理"])


# Pydantic 模型定义
class AbiCreateRequest(BaseModel):
    """ABI创建请求模型"""
    contract_address: str = Field(..., description="合约地址", min_length=42, max_length=42)
    chain_name: str = Field(..., description="链名称", min_length=1, max_length=32)
    contract_name: Optional[str] = Field(None, description="合约名称（用户定义的可读名称）", max_length=255)
    abi_content: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(None, description="ABI JSON内容")
    file_path: Optional[str] = Field(None, description="ABI文件路径")
    source_type: str = Field(default="manual", description="来源类型（manual: 手动上传, auto: 自动获取）")
    
    @validator('contract_address')
    def validate_contract_address(cls, v):
        """验证合约地址格式"""
        if not v.startswith('0x'):
            raise ValueError('合约地址必须以0x开头')
        if len(v) != 42:
            raise ValueError('合约地址长度必须为42字符')
        return v.lower()
    
    @validator('chain_name')
    def validate_chain_name(cls, v):
        """验证链名称"""
        supported_chains = [chain.value for chain in ChainType]
        if v.lower() not in supported_chains:
            raise ValueError(f'不支持的链类型，支持的链: {", ".join(supported_chains)}')
        return v.lower()
    
    @validator('source_type')
    def validate_source_type(cls, v):
        """验证来源类型"""
        valid_types = ['manual', 'auto']
        if v not in valid_types:
            raise ValueError(f'无效的来源类型，支持: {", ".join(valid_types)}')
        return v


class AbiAutoFetchRequest(BaseModel):
    """ABI自动获取请求模型"""
    contract_address: str = Field(..., description="合约地址", min_length=42, max_length=42)
    chain_name: str = Field(..., description="链名称", min_length=1, max_length=32)
    contract_name: Optional[str] = Field(None, description="合约名称（用户定义的可读名称）", max_length=255)
    check_proxy: bool = Field(default=True, description="是否检测代理合约并获取实现合约的ABI")
    
    @validator('contract_address')
    def validate_contract_address(cls, v):
        """验证合约地址格式"""
        if not v.startswith('0x'):
            raise ValueError('合约地址必须以0x开头')
        if len(v) != 42:
            raise ValueError('合约地址长度必须为42字符')
        return v.lower()
    
    @validator('chain_name')
    def validate_chain_name(cls, v):
        """验证链名称"""
        supported_chains = [chain.value for chain in ChainType]
        if v.lower() not in supported_chains:
            raise ValueError(f'不支持的链类型，支持的链: {", ".join(supported_chains)}')
        return v.lower()


class AbiUpdateRequest(BaseModel):
    """ABI更新请求模型"""
    abi_content: Union[Dict[str, Any], List[Dict[str, Any]]] = Field(..., description="新的ABI JSON内容")


class AbiResponse(BaseModel):
    """ABI响应模型"""
    id: int = Field(..., description="记录ID")
    contract_address: str = Field(..., description="合约地址")
    chain_name: str = Field(..., description="链名称")
    contract_name: Optional[str] = Field(None, description="合约名称（用户定义的可读名称）")
    abi_content: Optional[Union[Dict[str, Any], List[Dict[str, Any]]]] = Field(None, description="ABI JSON内容")
    file_path: Optional[str] = Field(None, description="ABI文件路径")
    source_type: str = Field(..., description="来源类型")
    created_at: str = Field(..., description="创建时间")
    updated_at: str = Field(..., description="更新时间")


class AbiListResponse(BaseModel):
    """ABI列表响应模型"""
    total: int = Field(..., description="总记录数")
    page: int = Field(..., description="当前页码")
    size: int = Field(..., description="每页大小")
    items: List[AbiResponse] = Field(..., description="ABI记录列表")


class OperationResponse(BaseModel):
    """操作响应模型"""
    success: bool = Field(..., description="操作是否成功")
    message: str = Field(..., description="响应消息")
    data: Optional[Any] = Field(None, description="返回数据")


# 创建服务实例
abi_storage_service = AbiStorageService()


@router.post("/", response_model=OperationResponse, summary="创建ABI记录", status_code=status.HTTP_201_CREATED)
async def create_abi(
    request: AbiCreateRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    创建合约ABI记录
    
    支持两种方式：
    1. 手动上传：在请求中提供abi_content
    2. 自动获取：不提供abi_content，系统自动从区块链浏览器获取
    """
    try:
        # 检查记录是否已存在
        query = select(ContractAbi).where(
            ContractAbi.contract_address == request.contract_address,
            ContractAbi.chain_name == request.chain_name
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"合约地址 {request.contract_address} 在 {request.chain_name} 链上的ABI记录已存在"
            )
        
        abi_content = None
        file_path = None
        
        if request.abi_content is not None:
            # 手动上传模式
            abi_content = request.abi_content
            source_type = "manual"
        else:
            # 自动获取模式，使用更长的超时时间（60秒）
            async with BlockchainExplorerService(timeout=60) as explorer:
                chain_type = ChainType(request.chain_name)
                abi_list = await explorer.get_contract_abi(
                    request.contract_address, 
                    chain_type, 
                    check_proxy=True  # 默认启用代理合约检测
                )
                
                if not abi_list:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"无法从 {request.chain_name} 链浏览器获取合约 {request.contract_address} 的ABI"
                    )
                
                abi_content = abi_list
                source_type = "auto"
        
        # 验证ABI格式
        if not abi_storage_service.validate_abi_format(abi_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的ABI格式"
            )
        
        # 保存ABI文件 - 如果请求中有file_path则使用，否则生成新的
        if request.file_path:
            file_path = request.file_path
        else:
            file_path = await abi_storage_service.save_abi(
                request.contract_address,
                request.chain_name,
                abi_content
            )
        
        # 创建数据库记录
        abi_record = ContractAbi(
            contract_address=request.contract_address,
            chain_name=request.chain_name,
            contract_name=request.contract_name,
            abi_content=json.dumps(abi_content, ensure_ascii=False),
            file_path=file_path,
            source_type=source_type
        )
        
        db.add(abi_record)
        await db.commit()
        await db.refresh(abi_record)
        
        logger.info(f"成功创建ABI记录: {request.contract_address} on {request.chain_name}")
        
        return OperationResponse(
            success=True,
            message="ABI记录创建成功",
            data={
                "id": abi_record.id,
                "contract_address": abi_record.contract_address,
                "chain_name": abi_record.chain_name,
                "source_type": abi_record.source_type,
                "file_path": abi_record.file_path
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"创建ABI记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"创建ABI记录失败: {str(e)}"
        )


@router.post("/fetch-only", response_model=OperationResponse, summary="仅获取ABI数据（不保存）", status_code=status.HTTP_200_OK)
async def fetch_abi_only(
    request: AbiAutoFetchRequest
):
    """
    仅从区块链浏览器获取合约ABI数据，不创建记录，用于前端预览
    """
    try:
        # 自动获取ABI，使用更长的超时时间（60秒）
        async with BlockchainExplorerService(timeout=60) as explorer:
            chain_type = ChainType(request.chain_name)
            abi_list = await explorer.get_contract_abi(
                request.contract_address, 
                chain_type, 
                check_proxy=request.check_proxy
            )
            
            if not abi_list:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"无法从 {request.chain_name} 链浏览器获取合约 {request.contract_address} 的ABI"
                )
        
        # 验证ABI格式
        if not abi_storage_service.validate_abi_format(abi_list):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的ABI格式"
            )
        
        # 生成file_path（但不实际保存文件）
        file_path = await abi_storage_service.save_abi(
            request.contract_address,
            request.chain_name,
            abi_list
        )
        
        logger.info(f"成功获取ABI数据（未保存到数据库）: {request.contract_address} on {request.chain_name}")
        
        return OperationResponse(
            success=True,
            message="ABI数据获取成功",
            data={
                "abi_content": abi_list,
                "contract_address": request.contract_address,
                "chain_name": request.chain_name,
                "file_path": file_path,
                "functions_count": len([item for item in abi_list if isinstance(item, dict) and item.get('type') == 'function']) if isinstance(abi_list, list) else 0,
                "events_count": len([item for item in abi_list if isinstance(item, dict) and item.get('type') == 'event']) if isinstance(abi_list, list) else 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取ABI数据失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取ABI数据失败: {str(e)}"
        )


@router.post("/auto-fetch", response_model=OperationResponse, summary="自动获取ABI并保存", status_code=status.HTTP_201_CREATED)
async def auto_fetch_abi(
    request: AbiAutoFetchRequest,
    db: AsyncSession = Depends(get_db_session)
):
    """
    自动从区块链浏览器获取合约ABI并创建记录
    """
    try:
        # 检查记录是否已存在
        query = select(ContractAbi).where(
            ContractAbi.contract_address == request.contract_address,
            ContractAbi.chain_name == request.chain_name
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"合约地址 {request.contract_address} 在 {request.chain_name} 链上的ABI记录已存在"
            )
        
        # 自动获取ABI，使用更长的超时时间（60秒）
        async with BlockchainExplorerService(timeout=60) as explorer:
            chain_type = ChainType(request.chain_name)
            abi_list = await explorer.get_contract_abi(
                request.contract_address, 
                chain_type, 
                check_proxy=request.check_proxy
            )
            
            if not abi_list:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"无法从 {request.chain_name} 链浏览器获取合约 {request.contract_address} 的ABI"
                )
        
        # 保存ABI文件
        file_path = await abi_storage_service.save_abi(
            request.contract_address,
            request.chain_name,
            abi_list
        )
        
        # 创建数据库记录
        abi_record = ContractAbi(
            contract_address=request.contract_address,
            chain_name=request.chain_name,
            contract_name=request.contract_name,
            abi_content=json.dumps(abi_list, ensure_ascii=False),
            file_path=file_path,
            source_type="auto_fetch"
        )
        
        db.add(abi_record)
        await db.commit()
        await db.refresh(abi_record)
        
        logger.info(f"成功自动获取并创建ABI记录: {request.contract_address} on {request.chain_name}")
        
        return OperationResponse(
            success=True,
            message="ABI记录自动获取并创建成功",
            data={
                "id": abi_record.id,
                "contract_address": abi_record.contract_address,
                "chain_name": abi_record.chain_name,
                "source_type": abi_record.source_type,
                "file_path": abi_record.file_path,
                "abi_functions_count": len(abi_list) if isinstance(abi_list, list) else 0
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"自动获取ABI失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"自动获取ABI失败: {str(e)}"
        )


@router.get("/{contract_address}", response_model=AbiResponse, summary="根据合约地址查询ABI")
async def get_abi_by_address(
    contract_address: str,
    chain_name: str = Query(..., description="链名称"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    根据合约地址和链名称查询ABI信息
    """
    try:
        # 标准化参数
        contract_address = contract_address.lower()
        chain_name = chain_name.lower()
        
        # 查询数据库记录
        query = select(ContractAbi).where(
            ContractAbi.contract_address == contract_address,
            ContractAbi.chain_name == chain_name
        )
        result = await db.execute(query)
        abi_record = result.scalar_one_or_none()
        
        if not abi_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到合约地址 {contract_address} 在 {chain_name} 链上的ABI记录"
            )
        
        # 解析ABI内容
        abi_content = None
        if abi_record.abi_content:
            try:
                abi_content = json.loads(abi_record.abi_content)
            except json.JSONDecodeError:
                logger.warning(f"ABI内容JSON解析失败: {abi_record.id}")
        
        return AbiResponse(
            id=abi_record.id,
            contract_address=abi_record.contract_address,
            chain_name=abi_record.chain_name,
            contract_name=abi_record.contract_name,
            abi_content=abi_content,
            file_path=abi_record.file_path,
            source_type=abi_record.source_type,
            created_at=abi_record.created_at.isoformat() if abi_record.created_at else "",
            updated_at=abi_record.updated_at.isoformat() if abi_record.updated_at else ""
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询ABI失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询ABI失败: {str(e)}"
        )


@router.get("/", response_model=AbiListResponse, summary="分页查询ABI列表")
async def list_abis(
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页大小"),
    chain_name: Optional[str] = Query(None, description="链名称过滤"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    分页查询ABI记录列表，支持按链名称过滤
    """
    try:
        # 构建查询条件
        query = select(ContractAbi)
        count_query = select(func.count(ContractAbi.id))
        
        if chain_name:
            query = query.where(ContractAbi.chain_name == chain_name.lower())
            count_query = count_query.where(ContractAbi.chain_name == chain_name.lower())
        
        # 查询总数
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # 分页查询
        offset = (page - 1) * size
        query = query.order_by(ContractAbi.created_at.desc()).offset(offset).limit(size)
        
        result = await db.execute(query)
        records = result.scalars().all()
        
        # 构建响应数据
        items = []
        for record in records:
            abi_content = None
            if record.abi_content:
                try:
                    abi_content = json.loads(record.abi_content)
                except json.JSONDecodeError:
                    logger.warning(f"ABI内容JSON解析失败: {record.id}")
            
            items.append(AbiResponse(
                id=record.id,
                contract_address=record.contract_address,
                chain_name=record.chain_name,
                contract_name=record.contract_name,
                abi_content=abi_content,
                file_path=record.file_path,
                source_type=record.source_type,
                created_at=record.created_at.isoformat() if record.created_at else "",
                updated_at=record.updated_at.isoformat() if record.updated_at else ""
            ))
        
        return AbiListResponse(
            total=total,
            page=page,
            size=size,
            items=items
        )
        
    except Exception as e:
        logger.error(f"查询ABI列表失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询ABI列表失败: {str(e)}"
        )


@router.put("/{contract_address}", response_model=OperationResponse, summary="更新ABI记录")
async def update_abi(
    contract_address: str,
    request: AbiUpdateRequest,
    chain_name: str = Query(..., description="链名称"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    更新指定合约地址的ABI记录
    """
    try:
        # 标准化参数
        contract_address = contract_address.lower()
        chain_name = chain_name.lower()
        
        # 查询现有记录
        query = select(ContractAbi).where(
            ContractAbi.contract_address == contract_address,
            ContractAbi.chain_name == chain_name
        )
        result = await db.execute(query)
        abi_record = result.scalar_one_or_none()
        
        if not abi_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到合约地址 {contract_address} 在 {chain_name} 链上的ABI记录"
            )
        
        # 验证新的ABI格式
        if not abi_storage_service.validate_abi_format(request.abi_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的ABI格式"
            )
        
        # 更新ABI文件
        file_path = await abi_storage_service.update_abi(
            contract_address,
            chain_name,
            request.abi_content
        )
        
        # 更新数据库记录
        abi_record.abi_content = json.dumps(request.abi_content, ensure_ascii=False)
        abi_record.file_path = file_path
        abi_record.source_type = "manual"  # 手动更新的记录标记为manual
        
        await db.commit()
        await db.refresh(abi_record)
        
        logger.info(f"成功更新ABI记录: {contract_address} on {chain_name}")
        
        return OperationResponse(
            success=True,
            message="ABI记录更新成功",
            data={
                "id": abi_record.id,
                "contract_address": abi_record.contract_address,
                "chain_name": abi_record.chain_name,
                "source_type": abi_record.source_type,
                "file_path": abi_record.file_path
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"更新ABI记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"更新ABI记录失败: {str(e)}"
        )


@router.delete("/{contract_address}", response_model=OperationResponse, summary="删除ABI记录")
async def delete_abi(
    contract_address: str,
    chain_name: str = Query(..., description="链名称"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    删除指定合约地址的ABI记录和对应的文件
    """
    try:
        # 标准化参数
        contract_address = contract_address.lower()
        chain_name = chain_name.lower()
        
        # 查询现有记录
        query = select(ContractAbi).where(
            ContractAbi.contract_address == contract_address,
            ContractAbi.chain_name == chain_name
        )
        result = await db.execute(query)
        abi_record = result.scalar_one_or_none()
        
        if not abi_record:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"未找到合约地址 {contract_address} 在 {chain_name} 链上的ABI记录"
            )
        
        # 删除ABI文件
        file_deleted = await abi_storage_service.delete_abi(contract_address, chain_name)
        
        # 删除数据库记录
        await db.delete(abi_record)
        await db.commit()
        
        logger.info(f"成功删除ABI记录: {contract_address} on {chain_name}")
        
        return OperationResponse(
            success=True,
            message="ABI记录删除成功",
            data={
                "deleted_record_id": abi_record.id,
                "contract_address": contract_address,
                "chain_name": chain_name,
                "file_deleted": file_deleted
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"删除ABI记录失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除ABI记录失败: {str(e)}"
        )


@router.post("/upload", response_model=OperationResponse, summary="通过文件上传ABI", status_code=status.HTTP_201_CREATED)
async def upload_abi_file(
    contract_address: str = Query(..., description="合约地址"),
    chain_name: str = Query(..., description="链名称"),
    contract_name: Optional[str] = Query(None, description="合约名称（用户定义的可读名称）"),
    file: UploadFile = File(..., description="ABI JSON文件"),
    db: AsyncSession = Depends(get_db_session)
):
    """
    通过上传JSON文件创建ABI记录
    """
    try:
        # 验证文件类型
        if not file.content_type or 'json' not in file.content_type.lower():
            if not file.filename or not file.filename.lower().endswith('.json'):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="只支持JSON格式的文件"
                )
        
        # 标准化参数
        contract_address = contract_address.lower()
        chain_name = chain_name.lower()
        
        # 检查记录是否已存在
        query = select(ContractAbi).where(
            ContractAbi.contract_address == contract_address,
            ContractAbi.chain_name == chain_name
        )
        result = await db.execute(query)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"合约地址 {contract_address} 在 {chain_name} 链上的ABI记录已存在"
            )
        
        # 读取和解析文件内容
        content = await file.read()
        try:
            abi_content = json.loads(content.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"文件内容无效: {str(e)}"
            )
        
        # 验证ABI格式
        if not abi_storage_service.validate_abi_format(abi_content):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="无效的ABI格式"
            )
        
        # 保存ABI文件
        file_path = await abi_storage_service.save_abi(
            contract_address,
            chain_name,
            abi_content
        )
        
        # 创建数据库记录
        abi_record = ContractAbi(
            contract_address=contract_address,
            chain_name=chain_name,
            contract_name=contract_name,
            abi_content=json.dumps(abi_content, ensure_ascii=False),
            file_path=file_path,
            source_type="manual"
        )
        
        db.add(abi_record)
        await db.commit()
        await db.refresh(abi_record)
        
        logger.info(f"成功通过文件上传创建ABI记录: {contract_address} on {chain_name}")
        
        return OperationResponse(
            success=True,
            message="ABI文件上传成功",
            data={
                "id": abi_record.id,
                "contract_address": abi_record.contract_address,
                "chain_name": abi_record.chain_name,
                "source_type": abi_record.source_type,
                "file_path": abi_record.file_path,
                "original_filename": file.filename
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        logger.error(f"上传ABI文件失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"上传ABI文件失败: {str(e)}"
        )