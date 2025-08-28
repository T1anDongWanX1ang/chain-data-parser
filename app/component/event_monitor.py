"""合约事件监控服务"""
import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Any, Callable
from web3 import Web3
from loguru import logger

from app.services.evm_parser import evm_parser_service


class ContractEventMonitor():
    """合约事件监控器"""
    
    def __init__(self, chain_name: str, contract_address: str, abi: List[Dict], config: 'EventMonitorConfig'):
        """
        初始化事件监控器
        
        Args:
            chain_name: 链名称 (ethereum/bsc/polygon)
            contract_address: 合约地址
            abi: 合约ABI
            config: 监控配置
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
        
        # 监控状态
        self.is_running = False
        self.last_processed_block = None
        
        logger.info(f"事件监控器已初始化 - 链: {chain_name}, 合约: {contract_address}")

    def _get_event_filters(self) -> Dict[str, Any]:
        """获取事件过滤器"""
        filters = {}
        
        # 如果配置了特定事件，只监控这些事件
        if self.config.events_to_monitor:
            for event_name in self.config.events_to_monitor:
                try:
                    event = getattr(self.contract.events, event_name)
                    filters[event_name] = event
                except AttributeError:
                    logger.warning(f"合约中未找到事件: {event_name}")
        else:
            # 监控所有事件
            for item in self.abi:
                if item.get('type') == 'event':
                    event_name = item['name']
                    try:
                        event = getattr(self.contract.events, event_name)
                        filters[event_name] = event
                    except AttributeError:
                        logger.warning(f"无法获取事件: {event_name}")
        
        return filters
    
    def _format_event_data(self, event_log) -> Dict[str, Any]:
        """格式化事件数据"""
        try:
            # 获取链ID
            chain_id = evm_parser_service.get_chain_id(self.chain_name)
            
            # 基本事件信息
            formatted_data = {
                "event_name": event_log.event,
                "contract_address": event_log.address,
                "transaction_hash": event_log.transactionHash.hex(),
                "block_number": event_log.blockNumber,
                "log_index": event_log.logIndex,
                "timestamp": datetime.now().isoformat(),
                "chain": self.chain_name,
                "chain_id": chain_id
            }
            
            # 事件参数
            if hasattr(event_log, 'args') and event_log.args:
                formatted_data["args"] = {}
                for arg_name, arg_value in event_log.args.items():
                    # 处理特殊类型
                    if hasattr(arg_value, 'hex'):  # bytes类型
                        formatted_data["args"][arg_name] = arg_value.hex()
                    elif isinstance(arg_value, int) and arg_value > 2**63:  # 大整数
                        formatted_data["args"][arg_name] = str(arg_value)
                    else:
                        formatted_data["args"][arg_name] = arg_value
            
            return formatted_data
            
        except Exception as e:
            logger.error(f"格式化事件数据失败: {e}")
            return {
                "event_name": "unknown",
                "error": str(e),
                "raw_log": str(event_log)
            }
    
    def _print_event(self, event_data: Dict[str, Any]):
        """打印事件数据"""
        if self.config.output_format == "json":
            print(json.dumps(event_data, indent=2, ensure_ascii=False))
        elif self.config.output_format == "simple":
            print(f"[{event_data.get('timestamp', 'N/A')}] "
                  f"{event_data.get('event_name', 'Unknown')} - "
                  f"Block: {event_data.get('block_number', 'N/A')} - "
                  f"TX: {event_data.get('transaction_hash', 'N/A')}")
            if event_data.get('args'):
                for arg_name, arg_value in event_data['args'].items():
                    print(f"  {arg_name}: {arg_value}")
        else:  # detailed format
            print("=" * 80)
            print(f"事件名称: {event_data.get('event_name', 'Unknown')}")
            print(f"合约地址: {event_data.get('contract_address', 'N/A')}")
            print(f"交易哈希: {event_data.get('transaction_hash', 'N/A')}")
            print(f"区块号: {event_data.get('block_number', 'N/A')}")
            print(f"日志索引: {event_data.get('log_index', 'N/A')}")
            print(f"时间: {event_data.get('timestamp', 'N/A')}")
            print(f"链: {event_data.get('chain', 'N/A')}")
            
            if event_data.get('args'):
                print("事件参数:")
                for arg_name, arg_value in event_data['args'].items():
                    print(f"  {arg_name}: {arg_value}")
            print("=" * 80)
        
        print()  # 空行分隔
    
    async def _process_events_in_block(self, block_number: int) -> int:
        """处理指定区块中的事件"""
        event_count = 0
        filters = self._get_event_filters()
        
        for event_name, event_filter in filters.items():
            try:
                # 获取该区块的事件日志
                events = event_filter.get_logs(
                    fromBlock=block_number,
                    toBlock=block_number
                )

                for event_log in events:
                    # 应用过滤条件
                    if self._should_process_event(event_log):
                        event_data = self._format_event_data(event_log)
                        # self._print_event(event_data)
                        event_count += 1

                        # 调用自定义处理函数（如果有）
                        if self.config.custom_handler:
                            try:
                                await self.config.custom_handler(event_data)
                            except Exception as e:
                                logger.error(f"自定义处理函数执行失败: {e}")
                
            except Exception as e:
                logger.error(f"处理区块 {block_number} 的事件 {event_name} 失败: {e}")
        
        return event_count
    
    def _should_process_event(self, event_log) -> bool:
        """检查是否应该处理该事件"""
        # 检查地址过滤
        if self.config.address_filters:
            # 检查from/to地址是否在过滤列表中
            if hasattr(event_log, 'args'):
                for arg_name, arg_value in event_log.args.items():
                    if isinstance(arg_value, str) and len(arg_value) == 42:  # 可能是地址
                        if arg_value.lower() in [addr.lower() for addr in self.config.address_filters]:
                            return True
                return False
        
        return True
    
    async def start_monitoring(self, start_block: Optional[int] = None):
        """开始监控事件"""
        if self.is_running:
            logger.warning("事件监控器已在运行中")
            return
        self.is_running = True
        logger.info(f"开始监控合约事件 - {self.contract_address}")
        try:
            # 确定起始区块
            if start_block is None:
                if self.config.start_from_latest:
                    current_block = self.w3.eth.block_number
                    start_block = current_block
                else:
                    start_block = self.config.start_block or 0
            
            self.last_processed_block = start_block - 1
            logger.info(f"从区块 {start_block} 开始监控")
            if self.config.mode == "realtime":
                await self._realtime_monitoring()
            else:  # historical mode
                await self._historical_monitoring(start_block, self.config.end_block)
        except Exception as e:
            logger.error(f"事件监控失败: {e}")
            raise
        finally:
            self.is_running = False

    async def _realtime_monitoring(self):
        """实时监控模式"""
        logger.info("启动实时监控模式")
        
        while self.is_running:
            try:
                current_block = self.w3.eth.block_number
                
                # 处理新区块
                if self.last_processed_block is None:
                    self.last_processed_block = current_block - 1
                
                for block_num in range(self.last_processed_block + 1, current_block + 1):
                    event_count = await self._process_events_in_block(block_num)
                    if event_count > 0:
                        logger.info(f"区块 {block_num} 处理了 {event_count} 个事件")
                    self.last_processed_block = block_num
                
                # 等待下一个检查周期
                await asyncio.sleep(self.config.poll_interval)
                
            except Exception as e:
                logger.error(f"实时监控出错: {e}")
                await asyncio.sleep(5)  # 出错时等待5秒后重试
    
    async def _historical_monitoring(self, start_block: int, end_block: Optional[int]):
        """历史数据监控模式"""
        if end_block is None:
            end_block = self.w3.eth.block_number
        
        logger.info(f"启动历史监控模式 - 区块范围: {start_block} 到 {end_block}")
        
        total_events = 0
        batch_size = self.config.batch_size
        
        for i in range(start_block, end_block + 1, batch_size):
            if not self.is_running:
                break
                
            batch_end = min(i + batch_size - 1, end_block)
            
            for block_num in range(i, batch_end + 1):
                event_count = await self._process_events_in_block(block_num)
                total_events += event_count
                self.last_processed_block = block_num
            
            logger.info(f"已处理区块 {i} 到 {batch_end}, 累计事件: {total_events}")
            
            # 批次间短暂停顿
            await asyncio.sleep(0.1)
        
        logger.info(f"历史监控完成 - 总计处理 {total_events} 个事件")
    
    def stop_monitoring(self):
        """停止监控"""
        self.is_running = False
        logger.info("事件监控已停止")
    
    def get_status(self) -> Dict[str, Any]:
        """获取监控状态"""
        return {
            "is_running": self.is_running,
            "chain_name": self.chain_name,
            "contract_address": self.contract_address,
            "last_processed_block": self.last_processed_block,
            "current_block": self.w3.eth.block_number if self.w3 else None
        }


class EventMonitorConfig:
    """事件监控配置类"""
    
    def __init__(
        self,
        # 监控模式
        mode: str = "realtime",  # realtime | historical
        
        # 区块范围
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        start_from_latest: bool = True,
        
        # 事件过滤
        events_to_monitor: Optional[List[str]] = None,  # 要监控的事件名列表，None表示全部
        address_filters: Optional[List[str]] = None,    # 地址过滤列表
        
        # 输出配置
        output_format: str = "detailed",  # simple | detailed | json
        
        # 性能配置
        poll_interval: float = 1.0,       # 实时模式轮询间隔（秒）
        batch_size: int = 100,            # 历史模式批处理大小
        
        # 自定义处理
        custom_handler: Optional[Callable] = None  # 自定义事件处理函数
    ):
        """
        初始化事件监控配置
        
        Args:
            mode: 监控模式 - "realtime" 实时监控 | "historical" 历史数据监控
            start_block: 起始区块号（历史模式必须指定）
            end_block: 结束区块号（历史模式，None表示最新区块）
            start_from_latest: 实时模式是否从最新区块开始
            events_to_monitor: 要监控的事件名列表，None表示监控所有事件
            address_filters: 地址过滤列表，只处理涉及这些地址的事件
            output_format: 输出格式 - "simple" | "detailed" | "json"
            poll_interval: 实时模式下的轮询间隔（秒）
            batch_size: 历史模式下的批处理大小
            custom_handler: 自定义事件处理函数
        """
        self.mode = mode
        self.start_block = start_block
        self.end_block = end_block
        self.start_from_latest = start_from_latest
        self.events_to_monitor = events_to_monitor
        self.address_filters = address_filters
        self.output_format = output_format
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.custom_handler = custom_handler
        
        # 验证配置
        self._validate_config()
    
    def _validate_config(self):
        """验证配置参数"""
        if self.mode not in ["realtime", "historical"]:
            raise ValueError("mode 必须是 'realtime' 或 'historical'")
        
        if self.mode == "historical" and self.start_block is None:
            raise ValueError("历史模式必须指定 start_block")
        
        if self.output_format not in ["simple", "detailed", "json"]:
            raise ValueError("output_format 必须是 'simple', 'detailed' 或 'json'")
        
        if self.poll_interval <= 0:
            raise ValueError("poll_interval 必须大于 0")
        
        if self.batch_size <= 0:
            raise ValueError("batch_size 必须大于 0")


# 预定义的常用配置
class CommonEventConfigs:
    """常用事件监控配置"""
    
    @staticmethod
    def erc20_transfer_realtime() -> EventMonitorConfig:
        """ERC20 Transfer事件实时监控配置"""
        return EventMonitorConfig(
            mode="realtime",
            events_to_monitor=["Transfer"],
            output_format="detailed",
            poll_interval=2.0
        )
    
    @staticmethod
    def erc20_transfer_historical(start_block: int, end_block: Optional[int] = None) -> EventMonitorConfig:
        """ERC20 Transfer事件历史监控配置"""
        return EventMonitorConfig(
            mode="historical",
            start_block=start_block,
            end_block=end_block,
            events_to_monitor=["Transfer"],
            output_format="json",
            batch_size=50
        )
    
    @staticmethod
    def uniswap_swap_monitor(pool_address: str) -> EventMonitorConfig:
        """Uniswap Swap事件监控配置"""
        return EventMonitorConfig(
            mode="realtime",
            events_to_monitor=["Swap"],
            output_format="detailed",
            poll_interval=1.0,
            address_filters=[pool_address]
        )
    
    @staticmethod
    def all_events_debug() -> EventMonitorConfig:
        """调试用全事件监控配置"""
        return EventMonitorConfig(
            mode="realtime",
            events_to_monitor=None,  # 监控所有事件
            output_format="json",
            poll_interval=3.0
        )