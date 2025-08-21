"""合约方法调用服务"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from web3 import Web3
from loguru import logger

from app.services.evm_parser import evm_parser_service


class ContractMethodCaller:
    """合约方法调用器 - 仅支持查询方法"""
    
    def __init__(self, chain_name: str, contract_address: str, abi: List[Dict], config: 'MethodCallConfig'):
        """
        初始化合约方法调用器
        
        Args:
            chain_name: 链名称 (ethereum/bsc/polygon)
            contract_address: 合约地址
            abi: 合约ABI
            config: 调用配置
        """
        self.chain_name = chain_name
        self.contract_address = Web3.to_checksum_address(contract_address)
        self.abi = abi
        self.config = config
        
        # 获取Web3实例
        self.w3 = evm_parser_service.get_web3(chain_name)
        if not self.w3:
            raise ValueError(f"无法获取 {chain_name} 的Web3连接")
        
        # 创建合约实例
        self.contract = self.w3.eth.contract(
            address=self.contract_address,
            abi=self.abi
        )
        
        logger.info(f"合约方法调用器已初始化 - 链: {chain_name}, 合约: {contract_address}")
    
    def _validate_method_exists(self, method_name: str) -> bool:
        """验证方法是否存在"""
        try:
            getattr(self.contract.functions, method_name)
            return True
        except AttributeError:
            return False
    
    def _prepare_method_call(self, method_name: str, method_args: List[Any] = None) -> Any:
        """准备方法调用"""
        if not self._validate_method_exists(method_name):
            raise ValueError(f"合约中不存在方法: {method_name}")
        
        method_args = method_args or []
        
        try:
            # 获取方法对象
            method = getattr(self.contract.functions, method_name)
            
            # 准备调用
            if method_args:
                return method(*method_args)
            else:
                return method()
        except Exception as e:
            raise ValueError(f"准备方法调用失败: {e}")
    
    def _format_result_data(self, method_name: str, method_args: List[Any], result: Any, call_time: datetime) -> Dict[str, Any]:
        """格式化调用结果数据"""
        try:
            # 处理返回值
            formatted_result = self._format_return_value(result)
            formatted_data = {
                f"{method_name}_result": formatted_result,
            }

            # 添加区块信息（如果配置要求）
            if self.config.include_block_info:
                try:
                    current_block = self.w3.eth.block_number
                    formatted_data["block_number"] = current_block
                except Exception:
                    pass
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"格式化结果数据失败: {e}")
            return {}
            
    
    def _format_return_value(self, value: Any) -> Any:
        """格式化返回值"""
        if isinstance(value, (list, tuple)):
            return [self._format_return_value(item) for item in value]
        elif hasattr(value, 'hex'):  # bytes类型
            return value.hex()
        elif isinstance(value, int) and value > 2**63:  # 大整数
            return str(value)
        elif hasattr(value, '__dict__'):  # 复杂对象
            try:
                return dict(value._asdict()) if hasattr(value, '_asdict') else str(value)
            except:
                return str(value)
        else:
            return value

    def call_method(self, method_name: str, method_args: List[Any] = None) -> Dict[str, Any]:
        """调用查询方法"""
        call_time = datetime.now()
        
        try:
            # 准备方法调用
            method_call = self._prepare_method_call(method_name, method_args)
            # 执行查询调用（只支持 call）
            result = method_call.call()
            # 格式化结果
            result_data = self._format_result_data(method_name, method_args, result, call_time)
            if self.config.custom_handler:
                self.config.custom_handler(result_data) 
            # 打印结果
            return result_data
            
        except Exception as e:
            logger.error(f"调用方法 {method_name} 失败: {e}")
            
            error_data = {
                "method_name": method_name,
                "contract_address": self.contract_address,
                "chain": self.chain_name,
                "call_time": call_time.isoformat(),
                "arguments": method_args or [],
                "result": None,
                "success": False,
                "error": str(e)
            }
            
            self._print_result(error_data)
            return error_data

    def get_contract_info(self) -> Dict[str, Any]:
        """获取合约信息"""
        try:
            # 尝试获取常见的合约信息
            info = {
                "address": self.contract_address,
                "chain": self.chain_name
            }
            
            # 尝试获取ERC20信息
            try:
                info["name"] = self.contract.functions.name().call()
            except:
                pass
            
            try:
                info["symbol"] = self.contract.functions.symbol().call()
            except:
                pass
            
            try:
                info["decimals"] = self.contract.functions.decimals().call()
            except:
                pass
            
            try:
                info["totalSupply"] = str(self.contract.functions.totalSupply().call())
            except:
                pass
            
            return info
            
        except Exception as e:
            logger.error(f"获取合约信息失败: {e}")
            return {
                "address": self.contract_address,
                "chain": self.chain_name,
                "error": str(e)
            }
    

        """获取调用器状态"""
        return {
            "chain_name": self.chain_name,
            "contract_address": self.contract_address,
            "current_block": self.w3.eth.block_number if self.w3 else None,
            "available_methods": len(self.list_available_methods())
        }


class MethodCallConfig:
    """方法调用配置类 - 简化版，仅支持查询"""
    
    def __init__(
        self,
        # 输出配置
        output_format: str = "detailed",  # simple | detailed | json
        include_block_info: bool = True,
        
        # 批量调用配置
        batch_delay: float = 0.1,  # 批量调用间延迟（秒）
        
        # 自定义处理
        custom_handler: Optional[Callable] = None
    ):
        """
        初始化方法调用配置
        
        Args:
            output_format: 输出格式
            include_block_info: 是否包含区块信息
            batch_delay: 批量调用间延迟
            custom_handler: 自定义处理函数
        """
        self.output_format = output_format
        self.include_block_info = include_block_info
        self.batch_delay = batch_delay
        self.custom_handler = custom_handler
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置参数"""
        if self.output_format not in ["simple", "detailed", "json"]:
            raise ValueError("output_format 必须是 'simple', 'detailed' 或 'json'")
        
        if self.batch_delay < 0:
            raise ValueError("batch_delay 必须大于等于 0")

