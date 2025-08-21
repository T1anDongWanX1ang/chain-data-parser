"""文件上传API接口"""
from typing import List, Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, status
from pydantic import BaseModel, Field
from loguru import logger

from app.services.file_upload_service import FileUploadService

router = APIRouter(prefix="/file", tags=["文件上传"])


class FileUploadResponse(BaseModel):
    """文件上传响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    file_path: str = Field(..., description="文件保存路径")
    file_name: str = Field(..., description="文件名")
    file_size: int = Field(..., description="文件大小(字节)")
    upload_time: str = Field(..., description="上传时间")


class MultiFileUploadResponse(BaseModel):
    """多文件上传响应模型"""
    success: bool = Field(..., description="是否成功")
    message: str = Field(..., description="响应消息")
    total_files: int = Field(..., description="总文件数")
    uploaded_files: List[dict] = Field(..., description="上传成功的文件列表")
    failed_files: List[dict] = Field(default_factory=list, description="上传失败的文件列表")





# 创建文件上传服务实例
upload_service = FileUploadService()


@router.post("/upload", response_model=FileUploadResponse, summary="上传单个文件")
async def upload_file(
    file: UploadFile = File(..., description="要上传的文件"),
    custom_path: Optional[str] = None
):
    """
    上传单个文件到项目目录
    
    Args:
        file: 要上传的文件
        custom_path: 自定义保存路径（可选，相对于项目根目录）
                    例如: "configs", "data/input", "temp"
                    如果不指定，文件将直接保存到项目根目录
    
    Returns:
        FileUploadResponse: 上传结果
        
    Note:
        - 文件默认上传到项目根目录
        - 支持通过 custom_path 指定子目录
        - 文件名会自动添加时间戳和唯一标识符避免冲突
    """
    try:
        file_info = await upload_service.save_file(file, custom_path)
        
        return FileUploadResponse(
            success=True,
            message="文件上传成功",
            file_path=file_info["file_path"],
            file_name=file_info["file_name"],
            file_size=file_info["file_size"],
            upload_time=file_info["upload_time"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"文件上传失败: {str(e)}"
        )


@router.post("/upload/multiple", response_model=MultiFileUploadResponse, summary="上传多个文件")
async def upload_multiple_files(
    files: List[UploadFile] = File(..., description="要上传的文件列表"),
    custom_path: Optional[str] = None
):
    """
    批量上传多个文件到项目目录
    
    Args:
        files: 要上传的文件列表
        custom_path: 自定义保存路径（可选，相对于项目根目录）
                    例如: "configs", "data/batch", "temp"
                    如果不指定，文件将直接保存到项目根目录
    
    Returns:
        MultiFileUploadResponse: 批量上传结果
        
    Note:
        - 所有文件将保存到相同的目录
        - 每个文件名会自动添加时间戳和唯一标识符
        - 支持部分成功上传，失败的文件会在响应中列出
    """
    try:
        if not files:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="请选择要上传的文件"
            )
        
        result = await upload_service.save_multiple_files(files, custom_path)
        
        success_count = len(result["uploaded_files"])
        failed_count = len(result["failed_files"])
        
        return MultiFileUploadResponse(
            success=failed_count == 0,
            message=f"批量上传完成: 成功 {success_count} 个，失败 {failed_count} 个",
            total_files=result["total_files"],
            uploaded_files=result["uploaded_files"],
            failed_files=result["failed_files"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"批量文件上传失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"批量文件上传失败: {str(e)}"
        )


@router.get("/info", summary="获取上传配置信息")
async def get_upload_info():
    """
    获取文件上传配置信息
    
    Returns:
        dict: 上传配置信息
    """
    return upload_service.get_upload_info()


@router.delete("/delete/{file_path:path}", summary="删除文件")
async def delete_file(file_path: str):
    """
    删除指定文件
    
    Args:
        file_path: 文件路径
    
    Returns:
        dict: 删除结果
    """
    return upload_service.delete_file(file_path)
