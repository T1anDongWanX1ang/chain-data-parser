"""API路由配置"""
from fastapi import APIRouter
from .pipeline import router as pipeline_router
from .file_upload import router as file_upload_router

api_router = APIRouter()

# 包含管道配置路由
api_router.include_router(pipeline_router)

# 包含文件上传路由
api_router.include_router(file_upload_router)
