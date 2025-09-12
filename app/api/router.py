"""API路由配置"""
from fastapi import APIRouter
from .pipeline import router as pipeline_router
from .file_upload import router as file_upload_router
from .writer_config import router as writer_config_router
from .flink_job import router as flink_job_router
from .abis import router as abi_router
from .contract_methods import router as contract_methods_router
from .contract_info import router as contract_info_router

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

# 包含合约方法查询路由
api_router.include_router(contract_methods_router)

# 包含合约信息查询路由
api_router.include_router(contract_info_router)
