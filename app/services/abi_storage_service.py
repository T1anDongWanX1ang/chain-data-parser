"""ABI文件存储管理服务"""
import json
import os
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


class AbiStorageService:
    """ABI文件存储管理服务"""
    
    def __init__(self, base_path: str = "abis"):
        """
        初始化ABI存储服务
        
        Args:
            base_path: ABI文件存储的根目录
        """
        # 确保使用绝对路径
        if not Path(base_path).is_absolute():
            current_dir = Path.cwd()
            self.base_path = current_dir / base_path
        else:
            self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
    def _get_file_path(self, contract_address: str, chain_name: str) -> Path:
        """
        获取ABI文件的完整路径
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            
        Returns:
            ABI文件的完整路径
        """
        chain_dir = self.base_path / chain_name.lower()
        chain_dir.mkdir(parents=True, exist_ok=True)
        
        # 使用合约地址作为文件名，确保文件名安全
        safe_address = contract_address.replace("/", "_").replace("\\", "_")
        return chain_dir / f"{safe_address}.json"
    
    async def save_abi(
        self, 
        contract_address: str, 
        chain_name: str, 
        abi_content: Dict[Any, Any]
    ) -> str:
        """
        保存ABI文件
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            abi_content: ABI内容（字典格式）
            
        Returns:
            保存的文件路径
            
        Raises:
            ValueError: 当ABI内容无效时
            IOError: 当文件操作失败时
        """
        try:
            # 验证ABI内容格式
            if not isinstance(abi_content, (dict, list)):
                raise ValueError("ABI内容必须是有效的JSON对象或数组")
            
            file_path = self._get_file_path(contract_address, chain_name)
            
            # 异步写入文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(abi_content, ensure_ascii=False, indent=2))
            
            logger.info(f"成功保存ABI文件: {file_path}")
            return str(file_path.relative_to(Path.cwd()))
            
        except Exception as e:
            logger.error(f"保存ABI文件失败 - 合约地址: {contract_address}, 链: {chain_name}, 错误: {e}")
            raise IOError(f"保存ABI文件失败: {e}")
    
    async def load_abi(self, contract_address: str, chain_name: str) -> Optional[Dict[Any, Any]]:
        """
        读取ABI文件
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            
        Returns:
            ABI内容（字典格式），如果文件不存在返回None
            
        Raises:
            IOError: 当文件读取失败时
            ValueError: 当ABI文件格式无效时
        """
        try:
            file_path = self._get_file_path(contract_address, chain_name)
            
            if not file_path.exists():
                logger.warning(f"ABI文件不存在: {file_path}")
                return None
            
            # 异步读取文件
            async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                content = await f.read()
            
            abi_content = json.loads(content)
            logger.info(f"成功读取ABI文件: {file_path}")
            return abi_content
            
        except json.JSONDecodeError as e:
            logger.error(f"ABI文件JSON格式错误 - 文件: {file_path}, 错误: {e}")
            raise ValueError(f"ABI文件JSON格式错误: {e}")
        except Exception as e:
            logger.error(f"读取ABI文件失败 - 合约地址: {contract_address}, 链: {chain_name}, 错误: {e}")
            raise IOError(f"读取ABI文件失败: {e}")
    
    async def update_abi(
        self, 
        contract_address: str, 
        chain_name: str, 
        abi_content: Dict[Any, Any]
    ) -> str:
        """
        更新ABI文件
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            abi_content: 新的ABI内容（字典格式）
            
        Returns:
            更新的文件路径
            
        Raises:
            FileNotFoundError: 当原文件不存在时
            ValueError: 当ABI内容无效时
            IOError: 当文件操作失败时
        """
        try:
            file_path = self._get_file_path(contract_address, chain_name)
            
            if not file_path.exists():
                raise FileNotFoundError(f"要更新的ABI文件不存在: {file_path}")
            
            # 验证ABI内容格式
            if not isinstance(abi_content, (dict, list)):
                raise ValueError("ABI内容必须是有效的JSON对象或数组")
            
            # 异步更新文件
            async with aiofiles.open(file_path, 'w', encoding='utf-8') as f:
                await f.write(json.dumps(abi_content, ensure_ascii=False, indent=2))
            
            logger.info(f"成功更新ABI文件: {file_path}")
            return str(file_path.relative_to(Path.cwd()))
            
        except Exception as e:
            logger.error(f"更新ABI文件失败 - 合约地址: {contract_address}, 链: {chain_name}, 错误: {e}")
            if isinstance(e, (FileNotFoundError, ValueError)):
                raise
            raise IOError(f"更新ABI文件失败: {e}")
    
    async def delete_abi(self, contract_address: str, chain_name: str) -> bool:
        """
        删除ABI文件
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            
        Returns:
            删除是否成功
            
        Raises:
            IOError: 当文件删除失败时
        """
        try:
            file_path = self._get_file_path(contract_address, chain_name)
            
            if not file_path.exists():
                logger.warning(f"要删除的ABI文件不存在: {file_path}")
                return False
            
            # 删除文件
            file_path.unlink()
            
            logger.info(f"成功删除ABI文件: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"删除ABI文件失败 - 合约地址: {contract_address}, 链: {chain_name}, 错误: {e}")
            raise IOError(f"删除ABI文件失败: {e}")
    
    def get_file_path_str(self, contract_address: str, chain_name: str) -> str:
        """
        获取ABI文件路径的字符串表示（相对于当前工作目录）
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            
        Returns:
            文件路径字符串
        """
        file_path = self._get_file_path(contract_address, chain_name)
        return str(file_path.relative_to(Path.cwd()))
    
    async def file_exists(self, contract_address: str, chain_name: str) -> bool:
        """
        检查ABI文件是否存在
        
        Args:
            contract_address: 合约地址
            chain_name: 链名称
            
        Returns:
            文件是否存在
        """
        file_path = self._get_file_path(contract_address, chain_name)
        return file_path.exists()
    
    def validate_abi_format(self, abi_content: Any) -> bool:
        """
        验证ABI格式是否正确
        
        Args:
            abi_content: 要验证的ABI内容
            
        Returns:
            是否为有效的ABI格式
        """
        try:
            # 基本格式检查
            if not isinstance(abi_content, (dict, list)):
                return False
            
            # 如果是字典，检查是否包含ABI相关字段
            if isinstance(abi_content, dict):
                # 可能是包含ABI的完整合约信息
                if 'abi' in abi_content:
                    return isinstance(abi_content['abi'], list)
                # 或者本身就是一个ABI项
                return 'type' in abi_content or 'name' in abi_content
            
            # 如果是列表，检查是否为ABI数组
            if isinstance(abi_content, list):
                # 空数组也是有效的ABI
                if len(abi_content) == 0:
                    return True
                # 检查第一个元素是否符合ABI项格式
                first_item = abi_content[0]
                return isinstance(first_item, dict) and ('type' in first_item or 'name' in first_item)
            
            return False
            
        except Exception:
            return False