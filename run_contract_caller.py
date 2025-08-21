#!/usr/bin/env python3
"""合约方法调用器启动脚本"""
import asyncio
import sys
import signal
import json
from typing import Optional, List, Any

from app.services.contract_caller import ContractMethodCaller, MethodCallConfig
from app.utils.contract_utils import get_standard_erc20_abi, load_abi_from_file, WellKnownContracts
from configs.method_call_configs import ContractMethodConfigs, QuickStartMethodConfigs


class ContractCallerRunner:
    """合约方法调用器运行管理"""
    
    def __init__(self):
        self.caller: Optional[ContractMethodCaller] = None
        self.running = False
    
    def signal_handler(self, signum, frame):
        """信号处理器"""
        print(f"\n收到信号 {signum}，正在停止调用...")
        if self.caller:
            self.caller.stop_scheduled_calls()
        self.running = False
    
    async def run_predefined_config(self, config_name: str):
        """运行预定义配置"""
        try:
            config = ContractMethodConfigs.get_config(config_name)
            
            self.caller = ContractMethodCaller(
                chain_name=config["chain_name"],
                contract_address=config["contract_address"],
                abi=config["abi"],
                config=config["config"]
            )
            
            print(f"使用预定义配置: {config_name}")
            print(f"链: {config['chain_name']}")
            print(f"合约: {config['contract_address']}")
            print("按 Ctrl+C 停止调用\n")
            
            self.running = True
            await self.caller.start_scheduled_calls()
            
        except Exception as e:
            print(f"运行失败: {e}")
    
    async def run_single_call(
        self,
        chain_name: str,
        contract_address: str,
        abi_source: str,
        method_name: str,
        method_args: Optional[str] = None,
        output_format: str = "detailed"
    ):
        """运行单次调用"""
        try:
            # 加载ABI
            if abi_source == "erc20":
                abi = get_standard_erc20_abi()
            elif abi_source.endswith(".json"):
                abi = load_abi_from_file(abi_source)
            else:
                raise ValueError("不支持的ABI源")
            
            # 解析参数
            parsed_args = []
            if method_args:
                try:
                    parsed_args = json.loads(method_args)
                    if not isinstance(parsed_args, list):
                        parsed_args = [parsed_args]
                except json.JSONDecodeError:
                    # 如果不是JSON，尝试按逗号分割
                    parsed_args = [arg.strip() for arg in method_args.split(",")]
            
            # 创建配置
            config = MethodCallConfig(
                call_type="call",
                output_format=output_format
            )
            
            self.caller = ContractMethodCaller(
                chain_name=chain_name,
                contract_address=contract_address,
                abi=abi,
                config=config
            )
            
            print(f"单次方法调用:")
            print(f"链: {chain_name}")
            print(f"合约: {contract_address}")
            print(f"方法: {method_name}")
            print(f"参数: {parsed_args}")
            print()
            
            # 执行调用
            result = await self.caller.call_method(method_name, parsed_args)
            
            if result.get("success"):
                print("✅ 调用成功!")
            else:
                print("❌ 调用失败!")
            
        except Exception as e:
            print(f"运行失败: {e}")
    
    async def run_scheduled_calls(
        self,
        chain_name: str,
        contract_address: str,
        abi_source: str,
        methods_config: str,
        interval: float = 30.0,
        output_format: str = "detailed"
    ):
        """运行定时调用"""
        try:
            # 加载ABI
            if abi_source == "erc20":
                abi = get_standard_erc20_abi()
            elif abi_source.endswith(".json"):
                abi = load_abi_from_file(abi_source)
            else:
                raise ValueError("不支持的ABI源")
            
            # 解析方法配置
            scheduled_calls = []
            try:
                methods_data = json.loads(methods_config)
                if isinstance(methods_data, list):
                    scheduled_calls = methods_data
                elif isinstance(methods_data, dict):
                    scheduled_calls = [methods_data]
                else:
                    raise ValueError("方法配置格式错误")
            except json.JSONDecodeError:
                # 如果不是JSON，尝试按逗号分割方法名
                method_names = [name.strip() for name in methods_config.split(",")]
                scheduled_calls = [{"method_name": name} for name in method_names]
            
            # 创建配置
            config = MethodCallConfig(
                call_type="call",
                scheduled_calls=scheduled_calls,
                call_interval=interval,
                output_format=output_format
            )
            
            self.caller = ContractMethodCaller(
                chain_name=chain_name,
                contract_address=contract_address,
                abi=abi,
                config=config
            )
            
            print(f"定时方法调用:")
            print(f"链: {chain_name}")
            print(f"合约: {contract_address}")
            print(f"调用间隔: {interval}秒")
            print(f"方法列表: {[call.get('method_name') for call in scheduled_calls]}")
            print("按 Ctrl+C 停止调用\n")
            
            self.running = True
            await self.caller.start_scheduled_calls()
            
        except Exception as e:
            print(f"运行失败: {e}")
    
    async def run_batch_calls(
        self,
        chain_name: str,
        contract_address: str,
        abi_source: str,
        methods_config: str,
        output_format: str = "detailed"
    ):
        """运行批量调用"""
        try:
            # 加载ABI
            if abi_source == "erc20":
                abi = get_standard_erc20_abi()
            elif abi_source.endswith(".json"):
                abi = load_abi_from_file(abi_source)
            else:
                raise ValueError("不支持的ABI源")
            
            # 解析方法配置
            method_calls = []
            try:
                methods_data = json.loads(methods_config)
                if isinstance(methods_data, list):
                    method_calls = methods_data
                elif isinstance(methods_data, dict):
                    method_calls = [methods_data]
                else:
                    raise ValueError("方法配置格式错误")
            except json.JSONDecodeError:
                # 如果不是JSON，尝试按逗号分割方法名
                method_names = [name.strip() for name in methods_config.split(",")]
                method_calls = [{"method_name": name} for name in method_names]
            
            # 创建配置
            config = MethodCallConfig(
                call_type="call",
                output_format=output_format,
                batch_delay=0.5
            )
            
            self.caller = ContractMethodCaller(
                chain_name=chain_name,
                contract_address=contract_address,
                abi=abi,
                config=config
            )
            
            print(f"批量方法调用:")
            print(f"链: {chain_name}")
            print(f"合约: {contract_address}")
            print(f"方法数量: {len(method_calls)}")
            print()
            
            # 执行批量调用
            results = await self.caller.batch_call_methods(method_calls)
            
            success_count = sum(1 for r in results if r.get("success"))
            print(f"\n批量调用完成: {success_count}/{len(results)} 成功")
            
        except Exception as e:
            print(f"运行失败: {e}")
    
    async def show_contract_info(
        self,
        chain_name: str,
        contract_address: str,
        abi_source: str
    ):
        """显示合约信息"""
        try:
            # 加载ABI
            if abi_source == "erc20":
                abi = get_standard_erc20_abi()
            elif abi_source.endswith(".json"):
                abi = load_abi_from_file(abi_source)
            else:
                raise ValueError("不支持的ABI源")
            
            config = MethodCallConfig(call_type="call")
            
            self.caller = ContractMethodCaller(
                chain_name=chain_name,
                contract_address=contract_address,
                abi=abi,
                config=config
            )
            
            print(f"合约信息分析:")
            print(f"链: {chain_name}")
            print(f"地址: {contract_address}")
            print()
            
            # 获取合约基本信息
            contract_info = self.caller.get_contract_info()
            print("基本信息:")
            for key, value in contract_info.items():
                print(f"  {key}: {value}")
            print()
            
            # 列出可用方法
            methods = self.caller.list_available_methods()
            print(f"可用方法 ({len(methods)}个):")
            for i, method in enumerate(methods):
                inputs_str = ", ".join([f"{inp['type']} {inp['name']}" for inp in method.get('inputs', [])])
                outputs_str = ", ".join([out['type'] for out in method.get('outputs', [])])
                print(f"  {i+1:2d}. {method['name']}({inputs_str}) -> {outputs_str} [{method.get('stateMutability', 'unknown')}]")
            
        except Exception as e:
            print(f"分析失败: {e}")


def print_help():
    """打印帮助信息"""
    print("""
合约方法调用器使用说明:

1. 使用预定义配置:
   python run_contract_caller.py --preset <config_name>
   
   可用的预定义配置:""")
    
    configs = ContractMethodConfigs.list_available_configs()
    for config in configs:
        print(f"     - {config}")
    
    print("""
2. 单次方法调用:
   python run_contract_caller.py \\
     --chain <chain_name> \\
     --contract <contract_address> \\
     --abi <abi_source> \\
     --method <method_name> \\
     [--args <arguments>] \\
     [--format <output_format>]

3. 定时调用:
   python run_contract_caller.py \\
     --chain <chain_name> \\
     --contract <contract_address> \\
     --abi <abi_source> \\
     --scheduled <methods_config> \\
     [--interval <seconds>] \\
     [--format <output_format>]

4. 批量调用:
   python run_contract_caller.py \\
     --chain <chain_name> \\
     --contract <contract_address> \\
     --abi <abi_source> \\
     --batch <methods_config> \\
     [--format <output_format>]

5. 合约信息分析:
   python run_contract_caller.py \\
     --chain <chain_name> \\
     --contract <contract_address> \\
     --abi <abi_source> \\
     --info

参数说明:
  --chain: 链名称 (ethereum/bsc/polygon)
  --contract: 合约地址
  --abi: ABI源 (erc20 | path/to/abi.json)
  --method: 方法名称 (单次调用)
  --args: 方法参数 (JSON格式或逗号分隔)
  --scheduled: 定时调用方法配置 (JSON格式)
  --batch: 批量调用方法配置 (JSON格式)
  --interval: 定时调用间隔 (秒)
  --format: 输出格式 (simple/detailed/json)
  --info: 显示合约信息

示例:
  # 使用预定义配置
  python run_contract_caller.py --preset usdt_info
  
  # 单次调用
  python run_contract_caller.py \\
    --chain ethereum \\
    --contract 0xdAC17F958D2ee523a2206206994597C13D831ec7 \\
    --abi erc20 \\
    --method name
  
  # 查询余额
  python run_contract_caller.py \\
    --chain ethereum \\
    --contract 0xdAC17F958D2ee523a2206206994597C13D831ec7 \\
    --abi erc20 \\
    --method balanceOf \\
    --args '["0x742d35cc6b5A8e1c0935C0013B1e7b8B831C9A0C"]'
  
  # 定时调用
  python run_contract_caller.py \\
    --chain ethereum \\
    --contract 0xdAC17F958D2ee523a2206206994597C13D831ec7 \\
    --abi erc20 \\
    --scheduled 'name,symbol,totalSupply' \\
    --interval 60
  
  # 合约信息
  python run_contract_caller.py \\
    --chain ethereum \\
    --contract 0xdAC17F958D2ee523a2206206994597C13D831ec7 \\
    --abi erc20 \\
    --info
""")


async def main():
    """主函数"""
    if len(sys.argv) < 2:
        print_help()
        return
    
    runner = ContractCallerRunner()
    
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
            # 解析参数
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
                elif args[i] == "--method" and i + 1 < len(args):
                    params["method_name"] = args[i + 1]
                    i += 2
                elif args[i] == "--args" and i + 1 < len(args):
                    params["method_args"] = args[i + 1]
                    i += 2
                elif args[i] == "--scheduled" and i + 1 < len(args):
                    params["methods_config"] = args[i + 1]
                    params["mode"] = "scheduled"
                    i += 2
                elif args[i] == "--batch" and i + 1 < len(args):
                    params["methods_config"] = args[i + 1]
                    params["mode"] = "batch"
                    i += 2
                elif args[i] == "--interval" and i + 1 < len(args):
                    params["interval"] = float(args[i + 1])
                    i += 2
                elif args[i] == "--format" and i + 1 < len(args):
                    params["output_format"] = args[i + 1]
                    i += 2
                elif args[i] == "--info":
                    params["mode"] = "info"
                    i += 1
                else:
                    i += 1
            
            # 检查必需参数
            required = ["chain_name", "contract_address", "abi_source"]
            missing = [p for p in required if p not in params]
            if missing:
                print(f"错误: 缺少必需参数: {', '.join(missing)}")
                print_help()
                return
            
            # 根据模式执行
            mode = params.get("mode", "single")
            
            if mode == "info":
                await runner.show_contract_info(
                    params["chain_name"],
                    params["contract_address"],
                    params["abi_source"]
                )
            elif mode == "scheduled":
                await runner.run_scheduled_calls(
                    params["chain_name"],
                    params["contract_address"],
                    params["abi_source"],
                    params["methods_config"],
                    params.get("interval", 30.0),
                    params.get("output_format", "detailed")
                )
            elif mode == "batch":
                await runner.run_batch_calls(
                    params["chain_name"],
                    params["contract_address"],
                    params["abi_source"],
                    params["methods_config"],
                    params.get("output_format", "detailed")
                )
            else:  # single call
                if "method_name" not in params:
                    print("错误: 单次调用需要指定 --method")
                    return
                
                await runner.run_single_call(
                    params["chain_name"],
                    params["contract_address"],
                    params["abi_source"],
                    params["method_name"],
                    params.get("method_args"),
                    params.get("output_format", "detailed")
                )
    
    except KeyboardInterrupt:
        print("\n调用已停止")
    except Exception as e:
        print(f"运行错误: {e}")


if __name__ == "__main__":
    asyncio.run(main())