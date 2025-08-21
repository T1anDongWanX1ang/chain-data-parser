#!/usr/bin/env python3
"""合约事件监控器启动脚本"""
import asyncio
import sys
import signal
from typing import Optional

from app.services.event_monitor import ContractEventMonitor, EventMonitorConfig
from app.utils.contract_utils import get_standard_erc20_abi, WellKnownContracts, load_abi_from_file
from configs.contract_configs import ContractMonitorConfigs, QuickStartConfigs


class EventMonitorRunner:
    """事件监控器运行管理"""
    
    def __init__(self):
        self.monitor: Optional[ContractEventMonitor] = None
        self.running = False
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}，正在停止监控...")
        if self.monitor:
            self.monitor.stop_monitoring()
        self.running = False
    
    async def run_predefined_config(self, config_name: str):
        """运行预定义配置"""
        try:
            config = ContractMonitorConfigs.get_config(config_name)
            
            self.monitor = ContractEventMonitor(
                chain_name=config["chain_name"],
                contract_address=config["contract_address"],
                abi=config["abi"],
                config=config["config"]
            )
            
            print(f"使用预定义配置: {config_name}")
            print(f"链: {config['chain_name']}")
            print(f"合约: {config['contract_address']}")
            print("按 Ctrl+C 停止监控\n")
            
            self.running = True
            await self.monitor.start_monitoring()
            
        except Exception as e:
            print(f"运行失败: {e}")
    
    async def run_custom_config(
        self,
        chain_name: str,
        contract_address: str,
        abi_source: str,
        events: Optional[str] = None,
        mode: str = "realtime",
        start_block: Optional[int] = None,
        end_block: Optional[int] = None,
        output_format: str = "detailed"
    ):
        """运行自定义配置"""
        try:
            # 加载ABI
            if abi_source == "erc20":
                abi = get_standard_erc20_abi()
            elif abi_source.endswith(".json"):
                abi = load_abi_from_file(abi_source)
            else:
                raise ValueError("不支持的ABI源")
            
            # 解析监控事件
            events_to_monitor = None
            if events:
                events_to_monitor = [e.strip() for e in events.split(",")]
            
            # 创建配置
            config = EventMonitorConfig(
                mode=mode,
                start_block=start_block,
                end_block=end_block,
                events_to_monitor=events_to_monitor,
                output_format=output_format,
                poll_interval=2.0
            )
            
            self.monitor = ContractEventMonitor(
                chain_name=chain_name,
                contract_address=contract_address,
                abi=abi,
                config=config
            )
            
            print(f"自定义监控配置:")
            print(f"链: {chain_name}")
            print(f"合约: {contract_address}")
            print(f"模式: {mode}")
            print(f"事件: {events_to_monitor or '全部'}")
            print("按 Ctrl+C 停止监控\n")
            
            self.running = True
            await self.monitor.start_monitoring()
            
        except Exception as e:
            print(f"运行失败: {e}")


def print_help():
    """打印帮助信息"""
    print("""
合约事件监控器使用说明:

1. 使用预定义配置:
   python run_event_monitor.py --preset <config_name>
   
   可用的预定义配置:""")
    
    configs = ContractMonitorConfigs.list_available_configs()
    for config in configs:
        print(f"     - {config}")
    
    print("""
2. 使用自定义配置:
   python run_event_monitor.py \\
     --chain <chain_name> \\
     --contract <contract_address> \\
     --abi <abi_source> \\
     [--events <event1,event2>] \\
     [--mode <realtime|historical>] \\
     [--start-block <number>] \\
     [--end-block <number>] \\
     [--format <simple|detailed|json>]

参数说明:
  --chain: 链名称 (ethereum/bsc/polygon)
  --contract: 合约地址
  --abi: ABI源 (erc20 | path/to/abi.json)
  --events: 要监控的事件名称，用逗号分隔
  --mode: 监控模式 (realtime/historical)
  --start-block: 起始区块号 (历史模式必需)
  --end-block: 结束区块号 (可选)
  --format: 输出格式 (simple/detailed/json)

示例:
  # 监控USDT Transfer事件
  python run_event_monitor.py --preset usdt_transfers
  
  # 自定义监控
  python run_event_monitor.py \\
    --chain ethereum \\
    --contract 0xdAC17F958D2ee523a2206206994597C13D831ec7 \\
    --abi erc20 \\
    --events Transfer \\
    --mode realtime \\
    --format json
""")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    runner = EventMonitorRunner()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, runner.signal_handler)
    signal.signal(signal.SIGTERM, runner.signal_handler)
    
    args = sys.argv[1:]
    
    try:
        if "--help" in args or "-h" in args:
            print_help()
            return
        
        if "--preset" in args:
            preset_idx = args.index("--preset")
            if preset_idx + 1 < len(args):
                config_name = args[preset_idx + 1]
                await runner.run_predefined_config(config_name)
            else:
                print("错误: --preset 需要指定配置名称")
                return
        
        else:
            # 解析自定义配置参数
            params = {}
            i = 0
            while i < len(args):
                if args[i] == "--chain" and i + 1 < len(args):
                    params["chain_name"] = args[i + 1]
                    i += 2
                elif args[i] == "--contract" and i + 1 < len(args):
                    params["contract_address"] = args[i + 1]
                    i += 2
                elif args[i] == "--abi" and i + 1 < len(args):
                    params["abi_source"] = args[i + 1]
                    i += 2
                elif args[i] == "--events" and i + 1 < len(args):
                    params["events"] = args[i + 1]
                    i += 2
                elif args[i] == "--mode" and i + 1 < len(args):
                    params["mode"] = args[i + 1]
                    i += 2
                elif args[i] == "--start-block" and i + 1 < len(args):
                    params["start_block"] = int(args[i + 1])
                    i += 2
                elif args[i] == "--end-block" and i + 1 < len(args):
                    params["end_block"] = int(args[i + 1])
                    i += 2
                elif args[i] == "--format" and i + 1 < len(args):
                    params["output_format"] = args[i + 1]
                    i += 2
                else:
                    i += 1
            
            # 检查必需参数
            required = ["chain_name", "contract_address", "abi_source"]
            missing = [p for p in required if p not in params]
            if missing:
                print(f"错误: 缺少必需参数: {', '.join(missing)}")
                print_help()
                return
            
            await runner.run_custom_config(**params)
    
    except KeyboardInterrupt:
        print("\n监控已停止")
    except Exception as e:
        print(f"运行错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())