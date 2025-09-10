"""区块链浏览器服务测试"""
import pytest
from unittest.mock import AsyncMock, patch
from app.services.blockchain_explorer_service import BlockchainExplorerService, ChainType


class TestBlockchainExplorerService:
    """区块链浏览器服务测试类"""
    
    @pytest.fixture
    def explorer_service(self):
        """创建区块链浏览器服务实例"""
        return BlockchainExplorerService()
    
    def test_detect_chain_type(self, explorer_service):
        """测试链类型检测"""
        # 测试有效的以太坊地址
        address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_type = explorer_service.detect_chain_type(address)
        assert chain_type == ChainType.ETHEREUM
        
        # 测试地址格式处理
        address_with_space = " 0x1234567890ABCDEF1234567890ABCDEF12345678 "
        chain_type = explorer_service.detect_chain_type(address_with_space)
        assert chain_type == ChainType.ETHEREUM
    
    def test_get_supported_chains(self, explorer_service):
        """测试获取支持的区块链列表"""
        chains = explorer_service.get_supported_chains()
        expected_chains = ["ethereum", "bsc", "polygon", "arbitrum", "optimism"]
        
        assert len(chains) == len(expected_chains)
        for chain in expected_chains:
            assert chain in chains
    
    @pytest.mark.asyncio
    async def test_get_contract_abi_success(self, explorer_service):
        """测试成功获取合约ABI"""
        # 模拟API响应
        mock_response = {
            "status": "1",
            "result": '[{"type":"function","name":"transfer","inputs":[{"name":"to","type":"address"}]}]'
        }
        
        with patch.object(explorer_service, '_make_request', return_value=mock_response):
            abi = await explorer_service.get_contract_abi(
                "0x1234567890abcdef1234567890abcdef12345678",
                ChainType.ETHEREUM
            )
            
            assert abi is not None
            assert len(abi) == 1
            assert abi[0]["type"] == "function"
            assert abi[0]["name"] == "transfer"
    
    @pytest.mark.asyncio
    async def test_get_contract_abi_not_verified(self, explorer_service):
        """测试获取未验证合约的ABI"""
        # 模拟未验证合约的API响应
        mock_response = {
            "status": "1",
            "result": "Contract source code not verified"
        }
        
        with patch.object(explorer_service, '_make_request', return_value=mock_response):
            abi = await explorer_service.get_contract_abi(
                "0x1234567890abcdef1234567890abcdef12345678",
                ChainType.ETHEREUM
            )
            
            assert abi is None
    
    @pytest.mark.asyncio
    async def test_get_contract_abi_api_error(self, explorer_service):
        """测试API错误情况"""
        # 模拟API错误响应
        mock_response = {
            "status": "0",
            "message": "Invalid API key"
        }
        
        with patch.object(explorer_service, '_make_request', return_value=mock_response):
            abi = await explorer_service.get_contract_abi(
                "0x1234567890abcdef1234567890abcdef12345678",
                ChainType.ETHEREUM
            )
            
            assert abi is None
    
    @pytest.mark.asyncio
    async def test_get_contract_info_success(self, explorer_service):
        """测试成功获取合约信息"""
        # 模拟API响应
        mock_response = {
            "status": "1",
            "result": [{
                "ContractName": "TestContract",
                "CompilerVersion": "v0.8.0",
                "OptimizationUsed": "1",
                "SourceCode": "contract TestContract {}",
                "ABI": '[{"type":"function","name":"test"}]'
            }]
        }
        
        with patch.object(explorer_service, '_make_request', return_value=mock_response):
            info = await explorer_service.get_contract_info(
                "0x1234567890abcdef1234567890abcdef12345678",
                ChainType.ETHEREUM
            )
            
            assert info is not None
            assert info["contract_name"] == "TestContract"
            assert info["compiler_version"] == "v0.8.0"
            assert info["chain_type"] == "ethereum"
            assert info["abi_parsed"] is not None
            assert len(info["abi_parsed"]) == 1
    
    @pytest.mark.asyncio
    async def test_auto_detect_chain_type(self, explorer_service):
        """测试自动检测链类型"""
        mock_response = {
            "status": "1",
            "result": '[{"type":"function"}]'
        }
        
        with patch.object(explorer_service, '_make_request', return_value=mock_response):
            # 不指定chain_type，应该自动检测
            abi = await explorer_service.get_contract_abi(
                "0x1234567890abcdef1234567890abcdef12345678"
            )
            
            assert abi is not None
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """测试异步上下文管理器"""
        async with BlockchainExplorerService() as service:
            assert service is not None
            chains = service.get_supported_chains()
            assert len(chains) > 0
    
    @pytest.mark.asyncio
    async def test_request_retry_on_rate_limit(self, explorer_service):
        """测试在限流时的重试机制"""
        # 模拟HTTP 429响应
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 429
        mock_session.get.return_value.__aenter__.return_value = mock_response
        
        with patch.object(explorer_service, '_get_session', return_value=mock_session):
            result = await explorer_service._make_request("http://test.com", {})
            assert result is None  # 达到重试限制后返回None