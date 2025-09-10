"""ABI存储服务测试"""
import asyncio
import json
import pytest
import tempfile
import shutil
from pathlib import Path
from app.services.abi_storage_service import AbiStorageService


class TestAbiStorageService:
    """ABI存储服务测试类"""
    
    @pytest.fixture
    def temp_dir(self):
        """创建临时目录"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def abi_service(self, temp_dir):
        """创建ABI存储服务实例"""
        return AbiStorageService(base_path=temp_dir)
    
    @pytest.fixture
    def sample_abi(self):
        """示例ABI数据"""
        return [
            {
                "type": "function",
                "name": "transfer",
                "inputs": [
                    {"name": "to", "type": "address"},
                    {"name": "value", "type": "uint256"}
                ],
                "outputs": [{"name": "", "type": "bool"}]
            },
            {
                "type": "event",
                "name": "Transfer",
                "inputs": [
                    {"name": "from", "type": "address", "indexed": True},
                    {"name": "to", "type": "address", "indexed": True},
                    {"name": "value", "type": "uint256", "indexed": False}
                ]
            }
        ]
    
    @pytest.mark.asyncio
    async def test_save_and_load_abi(self, abi_service, sample_abi):
        """测试保存和加载ABI"""
        contract_address = "0x1234567890abcdef"
        chain_name = "ethereum"
        
        # 保存ABI
        file_path = await abi_service.save_abi(contract_address, chain_name, sample_abi)
        assert file_path is not None
        assert await abi_service.file_exists(contract_address, chain_name)
        
        # 加载ABI
        loaded_abi = await abi_service.load_abi(contract_address, chain_name)
        assert loaded_abi == sample_abi
    
    @pytest.mark.asyncio
    async def test_update_abi(self, abi_service, sample_abi):
        """测试更新ABI"""
        contract_address = "0x1234567890abcdef"
        chain_name = "ethereum"
        
        # 先保存ABI
        await abi_service.save_abi(contract_address, chain_name, sample_abi)
        
        # 更新ABI
        updated_abi = [{"type": "function", "name": "approve"}]
        await abi_service.update_abi(contract_address, chain_name, updated_abi)
        
        # 验证更新
        loaded_abi = await abi_service.load_abi(contract_address, chain_name)
        assert loaded_abi == updated_abi
    
    @pytest.mark.asyncio
    async def test_delete_abi(self, abi_service, sample_abi):
        """测试删除ABI"""
        contract_address = "0x1234567890abcdef"
        chain_name = "ethereum"
        
        # 先保存ABI
        await abi_service.save_abi(contract_address, chain_name, sample_abi)
        assert await abi_service.file_exists(contract_address, chain_name)
        
        # 删除ABI
        result = await abi_service.delete_abi(contract_address, chain_name)
        assert result is True
        assert not await abi_service.file_exists(contract_address, chain_name)
    
    @pytest.mark.asyncio
    async def test_chain_directory_creation(self, abi_service, sample_abi):
        """测试按链名创建目录结构"""
        contract_address = "0x1234567890abcdef"
        chains = ["ethereum", "bsc", "polygon"]
        
        # 为不同链保存ABI
        for chain in chains:
            await abi_service.save_abi(contract_address, chain, sample_abi)
        
        # 验证目录结构
        for chain in chains:
            assert await abi_service.file_exists(contract_address, chain)
    
    def test_validate_abi_format(self, abi_service, sample_abi):
        """测试ABI格式验证"""
        # 有效格式
        assert abi_service.validate_abi_format(sample_abi)
        assert abi_service.validate_abi_format([])  # 空数组也有效
        assert abi_service.validate_abi_format({"abi": sample_abi})  # 包含abi字段的对象
        
        # 无效格式
        assert not abi_service.validate_abi_format("invalid")
        assert not abi_service.validate_abi_format(123)
        assert not abi_service.validate_abi_format(None)
    
    @pytest.mark.asyncio
    async def test_nonexistent_file_load(self, abi_service):
        """测试加载不存在的文件"""
        result = await abi_service.load_abi("nonexistent", "ethereum")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_update_nonexistent_file(self, abi_service):
        """测试更新不存在的文件"""
        with pytest.raises(FileNotFoundError):
            await abi_service.update_abi("nonexistent", "ethereum", [])