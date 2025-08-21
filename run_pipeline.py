#!/usr/bin/env python3
"""
区块链数据管道启动脚本

使用方法:
    python run_pipeline.py                           # 使用默认配置
    python run_pipeline.py --config custom.json     # 使用自定义配置
    python run_pipeline.py --help                   # 显示帮助
"""

import argparse
import asyncio
import sys
from pathlib import Path
from loguru import logger

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent))

from app.component.pipeline_executor import BlockchainDataPipeline


def setup_logging(level="INFO", log_file=None):
    """设置日志"""
    logger.remove()
    
    # 控制台输出
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=level
    )
    
    # 文件输出（可选）
    if log_file:
        logger.add(
            log_file,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level=level,
            rotation="10 MB"
        )


async def run_pipeline(config_path: str, output_dir: str = "output"):
    """运行管道"""
    try:
        logger.info(f"启动管道 - 配置文件: {config_path}")
        
        # 创建管道
        pipeline = BlockchainDataPipeline(config_path)
        
        # 执行管道
        result = await pipeline.execute_pipeline()
        
        # 打印摘要
        pipeline.print_execution_summary(result)
        
        # 保存结果
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)
        
        from datetime import datetime
        import json
        
        output_file = output_path / f"pipeline_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.success(f"管道执行完成，结果已保存到: {output_file}")
        return result
        
    except Exception as e:
        logger.error(f"管道执行失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="区块链数据管道执行器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python run_pipeline.py
    python run_pipeline.py --config configs/custom_pipeline.json
    python run_pipeline.py --config configs/uniswap_pipeline.json --output results/
    python run_pipeline.py --debug --log-file pipeline.log
        """
    )
    
    parser.add_argument(
        '--config', '-c',
        default='configs/pipeline_config.json',
        help='配置文件路径 (默认: configs/pipeline_config.json)'
    )
    
    parser.add_argument(
        '--output', '-o',
        default='output',
        help='输出目录 (默认: output)'
    )
    
    parser.add_argument(
        '--debug', '-d',
        action='store_true',
        help='启用调试模式'
    )
    
    parser.add_argument(
        '--log-file', '-l',
        help='日志文件路径'
    )
    
    args = parser.parse_args()
    
    # 设置日志
    log_level = "DEBUG" if args.debug else "INFO"
    setup_logging(log_level, args.log_file)
    
    # 检查配置文件
    config_file = Path(args.config)
    if not config_file.exists():
        logger.error(f"配置文件不存在: {config_file}")
        sys.exit(1)
    
    # 运行管道
    logger.info("区块链数据管道启动")
    logger.info(f"配置文件: {config_file}")
    logger.info(f"输出目录: {args.output}")
    
    try:
        result = asyncio.run(run_pipeline(str(config_file), args.output))
        if result:
            logger.success("管道执行成功完成")
            sys.exit(0)
        else:
            logger.error("管道执行失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.warning("用户中断执行")
        sys.exit(1)
    except Exception as e:
        logger.error(f"程序异常退出: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()