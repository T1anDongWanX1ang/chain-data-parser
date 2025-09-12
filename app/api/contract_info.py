"""合约信息查询API

提供合约基本信息查询，包括decimal精度等。
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from loguru import logger
from web3 import Web3
from web3.exceptions import ContractLogicError
import asyncio

from app.services.blockchain_explorer_service import BlockchainExplorerService
from app.utils.contract_utils import get_standard_erc20_abi

router = APIRouter(prefix="/contracts", tags=["Contract Info"])


class ContractInfoResponse(BaseModel):
    """合约信息响应"""
    contract_address: str
    chain_name: str
    name: Optional[str] = None
    symbol: Optional[str] = None
    decimals: Optional[int] = None
    total_supply: Optional[str] = None
    is_erc20_compatible: bool = False
    query_metadata: dict = {}


@router.get("/{contract_address}/info")
async def get_contract_info(
    contract_address: str,
    chain_name: str = Query(..., description="区块链名称")
) -> ContractInfoResponse:
    """
    获取合约基本信息，包括ERC20代币信息
    
    Args:
        contract_address: 合约地址
        chain_name: 区块链名称
    
    Returns:
        ContractInfoResponse: 合约信息
    """
    try:
        logger.info(f"查询合约信息: {contract_address} on {chain_name}")
        
        # 获取区块链服务
        blockchain_service = BlockchainExplorerService.create_for_chain(chain_name)
        if not blockchain_service:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的区块链: {chain_name}"
            )
        
        # 初始化响应对象
        response = ContractInfoResponse(
            contract_address=contract_address,
            chain_name=chain_name,
            query_metadata={
                "query_time": "2024-09-10",
                "query_method": "direct_contract_call"
            }
        )
        
        try:
            # 获取Web3实例
            w3 = blockchain_service.get_web3_instance()
            if not w3:
                raise Exception("无法获取Web3实例")
            
            # 标准化合约地址
            contract_address = Web3.to_checksum_address(contract_address)
            
            # 使用标准ERC20 ABI尝试调用
            erc20_abi = get_standard_erc20_abi()
            contract = w3.eth.contract(address=contract_address, abi=erc20_abi)
            
            # 尝试获取ERC20代币信息
            token_info = {}
            is_erc20_compatible = True
            
            # 获取名称
            try:
                token_info["name"] = contract.functions.name().call()
                response.name = token_info["name"]
            except Exception as e:
                logger.debug(f"获取name失败: {e}")
                is_erc20_compatible = False
            
            # 获取符号
            try:
                token_info["symbol"] = contract.functions.symbol().call()
                response.symbol = token_info["symbol"]
            except Exception as e:
                logger.debug(f"获取symbol失败: {e}")
                is_erc20_compatible = False
            
            # 获取decimals（重要！）
            try:
                decimals = contract.functions.decimals().call()
                token_info["decimals"] = decimals
                response.decimals = decimals
            except Exception as e:
                logger.debug(f"获取decimals失败: {e}")
                is_erc20_compatible = False
            
            # 获取总供应量
            try:
                total_supply = contract.functions.totalSupply().call()
                token_info["total_supply"] = str(total_supply)
                response.total_supply = str(total_supply)
            except Exception as e:
                logger.debug(f"获取totalSupply失败: {e}")
            
            response.is_erc20_compatible = is_erc20_compatible
            response.query_metadata.update({
                "erc20_methods_tested": ["name", "symbol", "decimals", "totalSupply"],
                "successful_methods": list(token_info.keys()),
                "blockchain_service": f"{chain_name}_explorer"
            })
            
            logger.info(f"合约信息查询成功: {contract_address}, ERC20兼容: {is_erc20_compatible}")
            return response
            
        except ContractLogicError as e:
            logger.warning(f"合约调用逻辑错误: {e}")
            response.query_metadata.update({
                "error": f"合约调用失败: {str(e)}",
                "error_type": "CONTRACT_LOGIC_ERROR"
            })
            return response
            
        except Exception as e:
            logger.error(f"查询合约信息失败: {e}")
            response.query_metadata.update({
                "error": f"查询失败: {str(e)}",
                "error_type": "QUERY_ERROR"
            })
            return response
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取合约信息API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取合约信息失败: {str(e)}"
        )


@router.get("/{contract_address}/decimals")
async def get_contract_decimals(
    contract_address: str,
    chain_name: str = Query(..., description="区块链名称")
) -> dict:
    """
    专门获取合约的decimal精度（快速查询）
    
    Args:
        contract_address: 合约地址
        chain_name: 区块链名称
    
    Returns:
        dict: 包含decimals信息的响应
    """
    try:
        logger.info(f"查询合约decimals: {contract_address} on {chain_name}")
        
        # 获取区块链服务
        blockchain_service = BlockchainExplorerService.create_for_chain(chain_name)
        if not blockchain_service:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的区块链: {chain_name}"
            )
        
        # 获取Web3实例
        w3 = blockchain_service.get_web3_instance()
        if not w3:
            raise HTTPException(
                status_code=500,
                detail="无法获取Web3实例"
            )
        
        # 标准化合约地址
        contract_address = Web3.to_checksum_address(contract_address)
        
        # 使用标准ERC20 ABI获取decimals
        erc20_abi = [
            {
                "constant": True,
                "inputs": [],
                "name": "decimals",
                "outputs": [{"name": "", "type": "uint8"}],
                "type": "function"
            }
        ]
        
        contract = w3.eth.contract(address=contract_address, abi=erc20_abi)
        
        try:
            decimals = contract.functions.decimals().call()
            
            return {
                "success": True,
                "contract_address": contract_address,
                "chain_name": chain_name,
                "decimals": decimals,
                "query_time": "2024-09-10",
                "message": "成功获取合约decimals"
            }
            
        except ContractLogicError as e:
            logger.warning(f"合约不支持decimals方法: {e}")
            return {
                "success": False,
                "contract_address": contract_address,
                "chain_name": chain_name,
                "decimals": None,
                "error": "合约不支持decimals方法（可能不是ERC20代币）",
                "message": "查询失败"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取decimals API错误: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"获取decimals失败: {str(e)}"
        )