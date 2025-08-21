"""EVM解析服务"""
from typing import Optional
from web3 import Web3
from loguru import logger

from app.config import settings


class EVMParserService:
    """EVM解析服务"""
    
    def __init__(self):
        self._web3_instances = {}
    
    def get_web3(self, chain_name: str) -> Optional[Web3]:
        """获取Web3实例"""
        if chain_name in self._web3_instances:
            return self._web3_instances[chain_name]
        
        rpc_url = self._get_rpc_url(chain_name)
        if not rpc_url:
            logger.error(f"未找到链 {chain_name} 的RPC配置")
            return None
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                self._web3_instances[chain_name] = w3
                logger.info(f"成功连接到 {chain_name} 网络")
                return w3
            else:
                logger.error(f"无法连接到 {chain_name} 网络")
                return None
        except Exception as e:
            logger.error(f"创建 {chain_name} Web3连接失败: {e}")
            return None
    
    def _get_rpc_url(self, chain_name: str) -> Optional[str]:
        """获取RPC URL"""
        chain_mapping = {
            'ethereum': settings.blockchain.eth_rpc_url,
            'bsc': settings.blockchain.bsc_rpc_url,
            'polygon': settings.blockchain.polygon_rpc_url,
        }
        return chain_mapping.get(chain_name.lower())


# 全局实例
evm_parser_service = EVMParserService()
