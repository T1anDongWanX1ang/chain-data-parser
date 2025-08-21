"""日志配置工具"""
import sys
import os
from pathlib import Path
from loguru import logger

from app.config import settings


def setup_logger():
    """设置日志配置"""
    # 移除默认的控制台输出
    logger.remove()
    
    # 添加控制台输出
    logger.add(
        sys.stdout,
        level=settings.log.level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # 确保日志目录存在
    log_file_path = Path(settings.log.file)
    log_file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 添加文件输出
    logger.add(
        settings.log.file,
        level=settings.log.level,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        rotation="100 MB",  # 文件大小达到100MB时轮转
        retention="7 days",  # 保留7天的日志文件
        compression="zip",   # 压缩旧的日志文件
        encoding="utf-8"
    )
    
    logger.info("日志系统初始化完成")