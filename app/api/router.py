"""API路由配置"""
from fastapi import APIRouter
from .pipeline import router as pipeline_router
from .file_upload import router as file_upload_router
from .writer_config import router as writer_config_router
from .flink_job import router as flink_job_router
from .abis import router as abi_router

api_router = APIRouter()

# 包含管道配置路由
api_router.include_router(pipeline_router)

# 包含文件上传路由
api_router.include_router(file_upload_router)

# 包含Writer配置路由
api_router.include_router(writer_config_router)

# 包含Flink作业管理路由
api_router.include_router(flink_job_router)

# 包含ABI管理路由
api_router.include_router(abi_router)
