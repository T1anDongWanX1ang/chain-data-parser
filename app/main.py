"""FastAPI应用主入口"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.utils.logger import setup_logger
from app.services.database_service import database_service
from app.api.router import api_router
from app.startup import startup_event, shutdown_event
import uvicorn
import sys
import os


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    setup_logger()
    
    # 初始化数据库
    try:
        await database_service.init_db()
    except Exception as e:
        print(f"数据库初始化失败: {e}")
        raise
    
    # 初始化任务监控系统
    try:
        await startup_event()
    except Exception as e:
        print(f"任务监控系统初始化失败: {e}")
        # 不抛出异常，允许应用继续启动
    
    yield
    
    # 关闭时执行
    try:
        await shutdown_event()
    except Exception as e:
        print(f"任务监控系统关闭失败: {e}")
    
    await database_service.close()


# 创建FastAPI应用实例
app = FastAPI(
    title="链数据解析系统",
    description="支持EVM和Solana链的数据解析、存储和查询API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境中应该限制具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 全局异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """全局异常处理"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "内部服务器错误",
            "detail": str(exc) if settings.api.debug else "服务器遇到了一个问题"
        }
    )


# 健康检查端点
@app.get("/health", tags=["健康检查"])
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "message": "服务正常运行",
        "version": "1.0.0"
    }


# 根路径
@app.get("/", tags=["根路径"])
async def root():
    """根路径信息"""
    return {
        "message": "欢迎使用链数据解析系统",
        "docs_url": "/docs",
        "version": "1.0.0"
    }


# 注册API路由
app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    print("当前工作目录:", os.getcwd())
    print("Python 路径:", sys.path)
    print("文件位置:", __file__)
    
    uvicorn.run(
        "app.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload,
        log_level=settings.log.level.lower()
    )