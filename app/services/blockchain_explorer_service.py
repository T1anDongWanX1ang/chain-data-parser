"""区块链浏览器ABI获取服务"""
import re
import aiohttp
import asyncio
from typing import Dict, Any, Optional, List
from loguru import logger
from enum import Enum

from app.config import settings
from app.utils.contract_utils import ProxyContractDetector, get_contract_implementation_address, AdvancedProxyAnalyzer
from web3 import Web3


class ChainType(Enum):
    """支持的区块链类型"""
    ETHEREUM = "ethereum"
    BSC = "bsc"
    POLYGON = "polygon"
    ARBITRUM = "arbitrum"
    OPTIMISM = "optimism"
    BASE = "base"


class BlockchainExplorerService:
    """区块链浏览器ABI获取服务"""
    
    # 各链的API配置 - 统一使用 v2 API 格式
    CHAIN_CONFIGS = {
        ChainType.ETHEREUM: {
            "base_url": "https://api.etherscan.io/v2/api",
            "api_key_env": "ETHERSCAN_API_KEY",
            "rpc_url": settings.blockchain.eth_rpc_url,
            "chain_id": 1
        },
        ChainType.BSC: {
            "base_url": "https://api.etherscan.io/v2/api",
            "api_key_env": "ETHERSCAN_API_KEY",
            "rpc_url": settings.blockchain.bsc_rpc_url,
            "chain_id": 56
        },
        ChainType.POLYGON: {
            "base_url": "https://api.etherscan.io/v2/api",
            "api_key_env": "ETHERSCAN_API_KEY",
            "rpc_url": settings.blockchain.polygon_rpc_url,
            "chain_id": 137
        },
        ChainType.ARBITRUM: {
            "base_url": "https://api.etherscan.io/v2/api",
            "api_key_env": "ETHERSCAN_API_KEY",
            "rpc_url": settings.blockchain.eth_rpc_url,
            "chain_id": 42161
        },
        ChainType.OPTIMISM: {
            "base_url": "https://api.etherscan.io/v2/api",
            "api_key_env": "ETHERSCAN_API_KEY",
            "rpc_url": settings.blockchain.eth_rpc_url,
            "chain_id": 10
        },
        ChainType.BASE: {
            "base_url": "https://api.etherscan.io/v2/api",
            "api_key_env": "ETHERSCAN_API_KEY",
            "rpc_url": settings.blockchain.eth_rpc_url,
            "chain_id": 8453
        }
    }
    
    def __init__(self, chain_type: Optional[ChainType] = None, timeout: int = 60, max_retries: int = 3):
        """
        初始化区块链浏览器服务
        
        Args:
            chain_type: 区块链类型
            timeout: HTTP请求超时时间（秒）- 增加到60秒以应对慢网络
            max_retries: 最大重试次数
        """
        self.chain_type = chain_type
        self.timeout = timeout
        self.max_retries = max_retries
        self.session: Optional[aiohttp.ClientSession] = None
        self.web3_instance: Optional[Web3] = None
    
    @classmethod
    def create_for_chain(cls, chain_name: str) -> Optional['BlockchainExplorerService']:
        """
        根据区块链名称创建服务实例
        
        Args:
            chain_name: 区块链名称字符串
            
        Returns:
            BlockchainExplorerService实例或None
        """
        try:
            # 尝试将字符串转换为ChainType枚举
            chain_type = None
            for chain in ChainType:
                if chain.value.lower() == chain_name.lower():
                    chain_type = chain
                    break
            
            if chain_type:
                return cls(chain_type=chain_type)
            else:
                logger.warning(f"不支持的区块链: {chain_name}")
                return None
        except Exception as e:
            logger.error(f"创建区块链服务失败: {e}")
            return None
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取或创建HTTP会话"""
        if self.session is None or self.session.closed:
            # 设置更宽松的超时配置
            timeout = aiohttp.ClientTimeout(
                total=self.timeout,
                connect=10,  # 连接超时
                sock_read=30  # 读取超时
            )
            
            # 配置代理和连接器
            proxy_url = None
            connector_kwargs = {
                'limit': 100,  # 连接池大小
                'limit_per_host': 30,  # 每个主机的连接数
                'keepalive_timeout': 30,  # 保持活动时间
                'enable_cleanup_closed': True  # 启用关闭连接清理
            }
            
            if settings.blockchain.http_proxy or settings.blockchain.https_proxy:
                proxy_url = settings.blockchain.https_proxy or settings.blockchain.http_proxy
                logger.info(f"使用代理服务器: {proxy_url}")
            else:
                logger.info("未配置代理，使用直连")
            
            connector = aiohttp.TCPConnector(**connector_kwargs)
            
            self.session = aiohttp.ClientSession(
                timeout=timeout,
                headers={
                    "User-Agent": "Chain-Parser/1.0",
                    "Accept": "application/json"
                },
                connector=connector
            )
        return self.session
    
    async def close(self):
        """关闭HTTP会话"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    def detect_chain_type(self, contract_address: str) -> ChainType:
        """
        根据合约地址特征智能判断链类型
        
        Args:
            contract_address: 合约地址
            
        Returns:
            检测到的链类型，默认为以太坊
            
        Note:
            这是一个简化的实现，实际使用中可能需要更复杂的判断逻辑
            或者通过其他方式（如用户指定）来确定链类型
        """
        # 清理地址格式
        address = contract_address.lower().strip()
        
        # 基本格式验证
        if not re.match(r"^0x[a-f0-9]{40}$", address):
            logger.warning(f"合约地址格式可能无效: {contract_address}")
        
        # 目前所有支持的链都使用相同的地址格式，无法通过地址本身区分
        # 默认返回以太坊，实际使用时建议用户明确指定链类型
        logger.info(f"地址 {contract_address} 默认判断为以太坊链")
        return ChainType.ETHEREUM
    
    def _get_api_key(self, chain_type: ChainType) -> Optional[str]:
        """
        获取指定链的API密钥
        
        Args:
            chain_type: 链类型
            
        Returns:
            API密钥，如果未配置返回None
        """
        # 所有链统一使用 ETHERSCAN_API_KEY
        api_key = settings.blockchain.etherscan_api_key
        
        if not api_key:
            logger.warning(f"未配置 {chain_type.value} 链的API密钥")
        
        return api_key
    
    async def _make_request(
        self, 
        url: str, 
        params: Dict[str, Any], 
        retry_count: int = 0
    ) -> Optional[Dict[str, Any]]:
        """
        发送HTTP请求并处理错误和重试
        
        Args:
            url: 请求URL
            params: 请求参数
            retry_count: 当前重试次数
            
        Returns:
            响应JSON数据，失败返回None
        """
        try:
            session = await self._get_session()
            # 配置代理URL（如果有）
            proxy_url = settings.blockchain.https_proxy or settings.blockchain.http_proxy
            if proxy_url:
                logger.debug(f"使用代理发送请求: {proxy_url} -> {url}")
            async with session.get(url, params=params, proxy=proxy_url) as response:
                if response.status == 200:
                    data = await response.json()
                    return data
                elif response.status == 429:  # 限流
                    if retry_count < self.max_retries:
                        wait_time = min(2 ** retry_count, 10)  # 指数退避，最多等待10秒
                        logger.warning(f"API限流，{wait_time}秒后重试...")
                        await asyncio.sleep(wait_time)
                        return await self._make_request(url, params, retry_count + 1)
                    else:
                        logger.error("API限流，已达到最大重试次数")
                else:
                    logger.error(f"HTTP请求失败: {response.status} - {await response.text()}")
                    
        except asyncio.TimeoutError:
            logger.error(f"请求超时: {url}")
        except Exception as e:
            logger.error(f"请求异常: {e}")
            
        return None
    
    async def get_contract_abi(
        self, 
        contract_address: str, 
        chain_type: Optional[ChainType] = None,
        check_proxy: bool = True
    ) -> Optional[List[Dict[str, Any]]]:
        """
        从区块链浏览器获取合约ABI（支持代理合约检测）
        
        优化后的逻辑：
        1. 先使用 getsourcecode 检查 Proxy 和 Implementation 字段
        2. 如果是代理合约（Proxy=1），使用 Implementation 地址
        3. 使用 getabi 接口获取最终地址的ABI
        
        Args:
            contract_address: 合约地址
            chain_type: 链类型，如果不指定则自动检测
            check_proxy: 是否检测代理合约并获取实现合约的ABI
            
        Returns:
            合约ABI列表，获取失败返回None
        """
        try:
            # 如果没有指定链类型，则自动检测
            if chain_type is None:
                chain_type = self.detect_chain_type(contract_address)
            
            # 获取链配置
            config = self.CHAIN_CONFIGS.get(chain_type)
            if not config:
                logger.error(f"不支持的链类型: {chain_type}")
                return None
            
            # 实际要查询的合约地址
            target_address = contract_address
            
            # 检测代理合约 - 优先使用 getsourcecode 的 Proxy 和 Implementation 字段
            if check_proxy:
                try:
                    logger.info(f"检测合约 {contract_address} 是否为代理合约...")
                    proxy_info = await self._check_proxy_via_getsourcecode(contract_address, chain_type)
                    
                    if proxy_info and proxy_info.get("is_proxy") and proxy_info.get("implementation"):
                        target_address = proxy_info["implementation"]
                        logger.info(
                            f"通过getsourcecode检测到代理合约: "
                            f"{contract_address} -> {target_address}"
                        )
                    else:
                        logger.info(f"合约 {contract_address} 不是代理合约或无法获取实现地址")
                        
                except Exception as e:
                    logger.warning(f"代理合约检测失败: {e}，继续使用原地址")
            
            # 获取API密钥
            api_key = self._get_api_key(chain_type)
            if not api_key:
                logger.warning(f"未配置 {chain_type.value} 的API密钥，尝试使用免费额度")
            
            # 构建请求参数 - v2 API 格式
            params = {
                "chainid": config["chain_id"],
                "module": "contract", 
                "action": "getabi",
                "address": target_address
            }
            
            if api_key:
                params["apikey"] = api_key
            
            # 发送请求
            base_url = config["base_url"]
            logger.info(f"正在从 {chain_type.value} 浏览器获取合约 {target_address} 的ABI")
            
            response_data = await self._make_request(base_url, params)
            if not response_data:
                return None
            
            # 解析响应
            if response_data.get("status") == "1":
                abi_str = response_data.get("result", "")
                if abi_str and abi_str != "Contract source code not verified":
                    try:
                        # 解析ABI JSON
                        import json
                        abi_list = json.loads(abi_str)
                        logger.info(f"成功获取合约ABI，包含 {len(abi_list)} 个函数/事件")
                        return abi_list
                    except json.JSONDecodeError as e:
                        logger.error(f"ABI JSON解析失败: {e}")
                else:
                    logger.warning(f"合约 {target_address} 未验证或无ABI")
            else:
                error_msg = response_data.get("message", "未知错误")
                logger.error(f"获取ABI失败: {error_msg}")
            
            return None
            
        except Exception as e:
            logger.error(f"获取合约ABI时发生异常: {e}")
            return None
    
    async def get_contract_info(
        self, 
        contract_address: str, 
        chain_type: Optional[ChainType] = None
    ) -> Optional[Dict[str, Any]]:
        """
        获取合约的完整信息（包括ABI、名称、编译器版本等）
        
        Args:
            contract_address: 合约地址
            chain_type: 链类型，如果不指定则自动检测
            
        Returns:
            合约信息字典，获取失败返回None
        """
        try:
            # 如果没有指定链类型，则自动检测
            if chain_type is None:
                chain_type = self.detect_chain_type(contract_address)
            
            # 获取链配置
            config = self.CHAIN_CONFIGS.get(chain_type)
            if not config:
                logger.error(f"不支持的链类型: {chain_type}")
                return None
            
            # 获取API密钥
            api_key = self._get_api_key(chain_type)
            
            # 构建请求参数
            params = {
                "chainid": config["chain_id"],
                "module": "contract",
                "action": "getsourcecode",
                "address": contract_address
            }
            
            if api_key:
                params["apikey"] = api_key
            
            # 发送请求
            base_url = config["base_url"]
            logger.info(f"正在从 {chain_type.value} 浏览器获取合约 {contract_address} 的详细信息")
            
            response_data = await self._make_request(base_url, params)
            if not response_data:
                return None
            
            # 解析响应
            if response_data.get("status") == "1":
                result = response_data.get("result", [])
                if result and len(result) > 0:
                    contract_info = result[0]
                    
                    # 提取有用信息
                    info = {
                        "contract_name": contract_info.get("ContractName", ""),
                        "compiler_version": contract_info.get("CompilerVersion", ""),
                        "optimization": contract_info.get("OptimizationUsed", ""),
                        "source_code": contract_info.get("SourceCode", ""),
                        "abi": contract_info.get("ABI", ""),
                        "chain_type": chain_type.value
                    }
                    
                    # 解析ABI
                    if info["abi"] and info["abi"] != "Contract source code not verified":
                        try:
                            import json
                            info["abi_parsed"] = json.loads(info["abi"])
                        except json.JSONDecodeError:
                            logger.warning("合约信息中的ABI解析失败")
                            info["abi_parsed"] = None
                    
                    logger.info(f"成功获取合约 {contract_info.get('ContractName', '')} 的详细信息")
                    return info
                else:
                    logger.warning(f"合约 {contract_address} 信息为空")
            else:
                error_msg = response_data.get("message", "未知错误")
                logger.error(f"获取合约信息失败: {error_msg}")
            
            return None
            
        except Exception as e:
            logger.error(f"获取合约信息时发生异常: {e}")
            return None
    
    def get_web3_instance(self) -> Optional[Web3]:
        """
        获取Web3实例
        
        Returns:
            Web3实例或None
        """
        if not self.web3_instance and self.chain_type:
            try:
                config = self.CHAIN_CONFIGS.get(self.chain_type)
                if config and config.get("rpc_url"):
                    self.web3_instance = Web3(Web3.HTTPProvider(config["rpc_url"]))
                    logger.debug(f"创建Web3实例: {config['rpc_url']}")
                else:
                    logger.error(f"无法获取{self.chain_type.value}的RPC URL")
            except Exception as e:
                logger.error(f"创建Web3实例失败: {e}")
                return None
        
        return self.web3_instance
    
    async def _check_proxy_via_explorer(self, contract_address: str, chain_type: ChainType) -> Optional[Dict[str, Any]]:
        """
        通过区块链浏览器API检查代理合约信息
        
        Args:
            contract_address: 合约地址
            chain_type: 链类型
            
        Returns:
            包含代理信息的字典，如果不是代理合约或检查失败则返回None
        """
        try:
            # 获取链配置
            config = self.CHAIN_CONFIGS.get(chain_type)
            if not config:
                return None
            
            # 获取API密钥
            api_key = self._get_api_key(chain_type)
            
            # 构建请求参数
            params = {
                "chainid": config["chain_id"],
                "module": "contract",
                "action": "getsourcecode",
                "address": contract_address
            }
            
            if api_key:
                params["apikey"] = api_key
            
            # 发送请求
            base_url = config["base_url"]
            logger.debug(f"通过区块链浏览器API检查合约 {contract_address} 的代理信息")
            
            response_data = await self._make_request(base_url, params)
            if not response_data:
                return None
            
            # 解析响应
            if response_data.get("status") == "1":
                result = response_data.get("result", [])
                if result and len(result) > 0:
                    contract_info = result[0]
                    
                    # 检查是否为代理合约
                    proxy_flag = contract_info.get("Proxy", "0")
                    implementation_address = contract_info.get("Implementation", "")
                    
                    if proxy_flag == "1" and implementation_address:
                        logger.info(f"浏览器API检测到代理合约: {contract_address} -> {implementation_address}")
                        return {
                            "is_proxy": True,
                            "implementation": implementation_address,
                            "detection_method": "explorer_api"
                        }
                    else:
                        logger.debug(f"浏览器API未检测到代理合约: {contract_address}")
                        return {"is_proxy": False}
                        
        except Exception as e:
            logger.debug(f"通过浏览器API检查代理合约信息失败: {e}")
        
        return None

    async def _check_proxy_via_getsourcecode(self, contract_address: str, chain_type: ChainType) -> Optional[Dict[str, Any]]:
        """
        通过 getsourcecode 接口检查代理合约信息（优化版本）
        
        专门检查 Proxy 和 Implementation 字段来判断是否为代理合约
        
        Args:
            contract_address: 合约地址
            chain_type: 链类型
            
        Returns:
            包含代理信息的字典，如果不是代理合约或检查失败则返回None
        """
        try:
            # 获取链配置
            config = self.CHAIN_CONFIGS.get(chain_type)
            if not config:
                return None
            
            # 获取API密钥
            api_key = self._get_api_key(chain_type)
            
            # 构建请求参数
            params = {
                "chainid": config["chain_id"],
                "module": "contract",
                "action": "getsourcecode",
                "address": contract_address
            }
            
            if api_key:
                params["apikey"] = api_key
            
            # 发送请求
            base_url = config["base_url"]
            logger.debug(f"使用getsourcecode检查合约 {contract_address} 的代理信息")
            
            response_data = await self._make_request(base_url, params)
            if not response_data:
                return None
            
            # 解析响应
            if response_data.get("status") == "1":
                result = response_data.get("result", [])
                if result and len(result) > 0:
                    contract_info = result[0]
                    
                    # 检查是否为代理合约 - 优先使用 Proxy 和 Implementation 字段
                    proxy_flag = contract_info.get("Proxy", "0")
                    implementation_address = contract_info.get("Implementation", "")
                    
                    if proxy_flag == "1" and implementation_address:
                        logger.info(f"getsourcecode检测到代理合约: {contract_address} -> {implementation_address}")
                        return {
                            "is_proxy": True,
                            "implementation": implementation_address,
                            "detection_method": "getsourcecode_api"
                        }
                    else:
                        logger.debug(f"getsourcecode未检测到代理合约: {contract_address} (Proxy={proxy_flag}, Implementation={implementation_address})")
                        return {"is_proxy": False}
                        
        except Exception as e:
            logger.debug(f"使用getsourcecode检查代理合约信息失败: {e}")
        
        return None

    async def _fetch_abi_via_getabi(self, contract_address: str, chain_type: ChainType) -> Optional[List[Dict[str, Any]]]:
        """
        使用 getabi 接口获取合约ABI
        
        Args:
            contract_address: 合约地址
            chain_type: 链类型
            
        Returns:
            合约ABI列表，获取失败返回None
        """
        try:
            # 获取链配置
            config = self.CHAIN_CONFIGS.get(chain_type)
            if not config:
                return None
            
            # 获取API密钥
            api_key = self._get_api_key(chain_type)
            
            # 构建请求参数
            params = {
                "module": "contract",
                "action": "getabi",
                "address": contract_address
            }
            
            if api_key:
                params["apikey"] = api_key
            
            # 发送请求
            base_url = config["base_url"]
            logger.info(f"使用getabi接口获取合约 {contract_address} 的ABI")
            
            response_data = await self._make_request(base_url, params)
            if not response_data:
                return None
            
            # 解析响应
            if response_data.get("status") == "1":
                abi_str = response_data.get("result", "")
                if abi_str and abi_str != "Contract source code not verified":
                    try:
                        # 解析ABI JSON
                        import json
                        abi_list = json.loads(abi_str)
                        logger.info(f"成功通过getabi获取合约ABI，包含 {len(abi_list)} 个函数/事件")
                        return abi_list
                    except json.JSONDecodeError as e:
                        logger.error(f"ABI JSON解析失败: {e}")
                else:
                    logger.warning(f"合约 {contract_address} 未验证或无ABI")
            else:
                error_msg = response_data.get("message", "未知错误")
                logger.warning(f"获取ABI失败: {error_msg}")
            
            return None
            
        except Exception as e:
            logger.error(f"使用getabi获取合约ABI时发生异常: {e}")
            return None

    def get_supported_chains(self) -> List[str]:
        """获取支持的区块链列表"""
        return [chain.value for chain in ChainType]
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        await self.close()