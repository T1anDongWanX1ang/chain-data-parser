"""文件上传服务"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any
from fastapi import UploadFile, HTTPException, status
from loguru import logger


class FileUploadService:
    """文件上传服务"""
    
    def __init__(self, upload_dir: str = "."):
        """
        初始化文件上传服务
        
        Args:
            upload_dir: 上传目录，默认为项目根目录
        """
        self.upload_dir = Path(upload_dir).resolve()
        # 确保上传目录存在
        if not self.upload_dir.exists():
            self.upload_dir.mkdir(parents=True, exist_ok=True)
        
        # 支持的文件类型
        self.allowed_extensions = {
            '.json', '.txt', '.csv', '.xlsx', '.xls', 
            '.pdf', '.doc', '.docx', '.png', '.jpg', 
            '.jpeg', '.gif', '.zip', '.rar', '.sol'
        }
        
        # 最大文件大小 (50MB)
        self.max_file_size = 50 * 1024 * 1024
    
    def _validate_file(self, file: UploadFile) -> None:
        """验证文件"""
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="文件名不能为空"
            )
        
        # 检查文件扩展名
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"不支持的文件类型: {file_ext}. 支持的类型: {', '.join(self.allowed_extensions)}"
            )
        
        # 检查文件大小
        if file.size and file.size > self.max_file_size:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"文件大小超过限制: {file.size} bytes > {self.max_file_size} bytes"
            )
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """生成唯一文件名"""
        file_path = Path(original_filename)
        file_ext = file_path.suffix
        file_stem = file_path.stem
        
        # 生成唯一标识符
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 构建新文件名: 原名_时间戳_唯一ID.扩展名
        new_filename = f"{file_stem}_{timestamp}_{unique_id}{file_ext}"
        return new_filename
    
    async def save_file(self, file: UploadFile, custom_path: Optional[str] = None) -> Dict[str, Any]:
        """
        保存单个文件
        
        Args:
            file: 上传的文件
            custom_path: 自定义保存路径
            
        Returns:
            dict: 文件信息
        """
        try:
            # 验证文件
            self._validate_file(file)
            
            # 确定保存路径
            if custom_path:
                # 如果是相对路径，则相对于项目根目录
                if not Path(custom_path).is_absolute():
                    save_dir = self.upload_dir / custom_path
                else:
                    save_dir = Path(custom_path)
                save_dir.mkdir(parents=True, exist_ok=True)
            else:
                # 默认保存到项目根目录
                save_dir = self.upload_dir
            
            # 生成唯一文件名
            unique_filename = self._generate_unique_filename(file.filename)
            file_path = save_dir / unique_filename
            
            # 保存文件
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            # 获取文件大小
            file_size = len(content)
            
            logger.info(f"文件保存成功: {file_path}")
            
            return {
                "file_path": str(file_path),
                "file_name": unique_filename,
                "original_name": file.filename,
                "file_size": file_size,
                "upload_time": datetime.now().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件保存失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件保存失败: {str(e)}"
            )
    
    async def save_multiple_files(self, files: List[UploadFile], custom_path: Optional[str] = None) -> Dict[str, Any]:
        """
        保存多个文件
        
        Args:
            files: 上传的文件列表
            custom_path: 自定义保存路径
            
        Returns:
            dict: 批量上传结果
        """
        uploaded_files = []
        failed_files = []
        
        for file in files:
            try:
                file_info = await self.save_file(file, custom_path)
                uploaded_files.append(file_info)
            except Exception as e:
                failed_files.append({
                    "file_name": file.filename,
                    "error": str(e)
                })
                logger.error(f"文件 {file.filename} 上传失败: {e}")
        
        return {
            "total_files": len(files),
            "uploaded_files": uploaded_files,
            "failed_files": failed_files
        }
    
    def delete_file(self, file_path: str) -> Dict[str, Any]:
        """
        删除指定文件
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 删除结果
        """
        try:
            file_to_delete = Path(file_path)
            
            # 安全检查：确保文件在项目目录内，且不删除重要的系统文件
            resolved_file = file_to_delete.resolve()
            resolved_upload_dir = self.upload_dir.resolve()
            
            # 检查文件是否在项目目录内
            if not str(resolved_file).startswith(str(resolved_upload_dir)):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="无权限删除该文件"
                )
            
            # 防止删除重要的项目文件
            protected_patterns = [
                '*.py', '*.yml', '*.yaml', '*.ini', '*.cfg', '*.conf',
                '*.sh', '*.bat', '*.md', 'requirements*.txt', 'Dockerfile',
                '.git*', '.env*', 'alembic*'
            ]
            
            file_name = file_to_delete.name.lower()
            for pattern in protected_patterns:
                if file_name.endswith(pattern.replace('*', '')) or pattern.replace('*', '') in file_name:
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="不允许删除系统文件"
                    )
            
            if not file_to_delete.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件不存在"
                )
            
            file_to_delete.unlink()
            logger.info(f"文件删除成功: {file_path}")
            
            return {
                "success": True,
                "message": "文件删除成功",
                "file_path": file_path
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件删除失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"文件删除失败: {str(e)}"
            )
    
    def get_upload_info(self) -> Dict[str, Any]:
        """
        获取文件上传配置信息
        
        Returns:
            dict: 上传配置信息
        """
        return {
            "upload_directory": str(self.upload_dir),
            "max_file_size": self.max_file_size,
            "max_file_size_mb": self.max_file_size / (1024 * 1024),
            "allowed_extensions": list(self.allowed_extensions),
            "upload_structure": "项目根目录/filename_timestamp_uuid.ext (或自定义路径)",
            "note": "文件默认上传到项目根目录，可通过 custom_path 参数指定子目录"
        }
    
    def update_config(self, 
                     max_file_size: Optional[int] = None,
                     allowed_extensions: Optional[set] = None) -> None:
        """
        更新配置
        
        Args:
            max_file_size: 最大文件大小
            allowed_extensions: 允许的文件扩展名
        """
        if max_file_size is not None:
            self.max_file_size = max_file_size
            logger.info(f"更新最大文件大小: {max_file_size} bytes")
        
        if allowed_extensions is not None:
            self.allowed_extensions = allowed_extensions
            logger.info(f"更新允许的文件类型: {allowed_extensions}")
    
    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取文件信息
        
        Args:
            file_path: 文件路径
            
        Returns:
            dict: 文件信息
        """
        try:
            file_obj = Path(file_path)
            
            if not file_obj.exists():
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="文件不存在"
                )
            
            stat = file_obj.stat()
            
            return {
                "file_path": str(file_obj),
                "file_name": file_obj.name,
                "file_size": stat.st_size,
                "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "file_extension": file_obj.suffix,
                "is_file": file_obj.is_file(),
                "is_directory": file_obj.is_dir()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"获取文件信息失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"获取文件信息失败: {str(e)}"
            )
    
    def list_files(self, directory: Optional[str] = None, 
                   pattern: str = "*") -> List[Dict[str, Any]]:
        """
        列出文件
        
        Args:
            directory: 目录路径，默认为上传目录
            pattern: 文件匹配模式
            
        Returns:
            list: 文件列表
        """
        try:
            if directory:
                search_dir = Path(directory)
            else:
                search_dir = self.upload_dir
            
            if not search_dir.exists():
                return []
            
            files = []
            for file_path in search_dir.rglob(pattern):
                if file_path.is_file():
                    stat = file_path.stat()
                    files.append({
                        "file_path": str(file_path),
                        "file_name": file_path.name,
                        "file_size": stat.st_size,
                        "created_time": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "file_extension": file_path.suffix
                    })
            
            # 按修改时间排序
            files.sort(key=lambda x: x["modified_time"], reverse=True)
            
            return files
            
        except Exception as e:
            logger.error(f"列出文件失败: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"列出文件失败: {str(e)}"
            )
