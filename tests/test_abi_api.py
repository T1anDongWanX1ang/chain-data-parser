"""ABI管理API测试"""
import json
import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
from io import BytesIO

from app.main import app
from app.models.contract_abi import ContractAbi


class TestAbiAPI:
    """ABI管理API测试类"""
    
    @pytest.fixture
    def client(self):
        """创建测试客户端"""
        return TestClient(app)
    
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
            }
        ]
    
    def test_create_abi_manual(self, client, sample_abi):
        """测试手动创建ABI记录"""
        request_data = {
            "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_name": "ethereum",
            "abi_content": sample_abi,
            "source_type": "manual"
        }
        
        with patch('app.api.abis.get_db_session') as mock_db:
            # 模拟数据库操作
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None  # 记录不存在
            mock_session.add = AsyncMock()
            mock_session.commit = AsyncMock()
            mock_session.refresh = AsyncMock()
            
            # 模拟ABI存储服务
            with patch('app.api.abis.abi_storage_service') as mock_storage:
                mock_storage.validate_abi_format.return_value = True
                mock_storage.save_abi.return_value = "abis/ethereum/0x1234567890abcdef1234567890abcdef12345678.json"
                
                response = client.post("/api/v1/abis/", json=request_data)
                
                assert response.status_code == 201
                data = response.json()
                assert data["success"] is True
                assert "ABI记录创建成功" in data["message"]
    
    def test_create_abi_auto_fetch(self, client):
        """测试自动获取ABI记录"""
        request_data = {
            "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_name": "ethereum"
        }
        
        with patch('app.api.abis.get_db_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            # 模拟区块链浏览器服务
            with patch('app.api.abis.BlockchainExplorerService') as mock_explorer_class:
                mock_explorer = AsyncMock()
                mock_explorer_class.return_value.__aenter__.return_value = mock_explorer
                mock_explorer.get_contract_abi.return_value = [{"type": "function", "name": "test"}]
                
                with patch('app.api.abis.abi_storage_service') as mock_storage:
                    mock_storage.validate_abi_format.return_value = True
                    mock_storage.save_abi.return_value = "abis/ethereum/test.json"
                    
                    response = client.post("/api/v1/abis/auto-fetch", json=request_data)
                    
                    assert response.status_code == 201
                    data = response.json()
                    assert data["success"] is True
    
    def test_get_abi_by_address(self, client, sample_abi):
        """测试根据地址查询ABI"""
        contract_address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_name = "ethereum"
        
        with patch('app.api.abis.get_db_session') as mock_db:
            # 模拟数据库查询结果
            mock_record = ContractAbi(
                id=1,
                contract_address=contract_address,
                chain_name=chain_name,
                abi_content=json.dumps(sample_abi),
                file_path="abis/ethereum/test.json",
                source_type="manual"
            )
            mock_record.created_at = "2023-01-01T00:00:00"
            mock_record.updated_at = "2023-01-01T00:00:00"
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_record
            
            response = client.get(f"/api/v1/abis/{contract_address}?chain_name={chain_name}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["contract_address"] == contract_address
            assert data["chain_name"] == chain_name
            assert data["abi_content"] == sample_abi
    
    def test_get_abi_not_found(self, client):
        """测试查询不存在的ABI"""
        contract_address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_name = "ethereum"
        
        with patch('app.api.abis.get_db_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            response = client.get(f"/api/v1/abis/{contract_address}?chain_name={chain_name}")
            
            assert response.status_code == 404
            data = response.json()
            assert "未找到" in data["detail"]
    
    def test_list_abis(self, client):
        """测试分页查询ABI列表"""
        with patch('app.api.abis.get_db_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            
            # 模拟总数查询
            mock_session.execute.return_value.scalar.return_value = 10
            
            # 模拟分页查询结果
            mock_records = [
                ContractAbi(
                    id=i,
                    contract_address=f"0x{i:040x}",
                    chain_name="ethereum",
                    abi_content='[{"type": "function"}]',
                    file_path=f"abis/ethereum/{i}.json",
                    source_type="manual"
                ) for i in range(1, 6)
            ]
            
            for record in mock_records:
                record.created_at = "2023-01-01T00:00:00"
                record.updated_at = "2023-01-01T00:00:00"
            
            mock_session.execute.return_value.scalars.return_value.all.return_value = mock_records
            
            response = client.get("/api/v1/abis/?page=1&size=5")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total"] == 10
            assert data["page"] == 1
            assert data["size"] == 5
            assert len(data["items"]) == 5
    
    def test_update_abi(self, client, sample_abi):
        """测试更新ABI记录"""
        contract_address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_name = "ethereum"
        
        updated_abi = [{"type": "function", "name": "updated"}]
        
        with patch('app.api.abis.get_db_session') as mock_db:
            mock_record = ContractAbi(
                id=1,
                contract_address=contract_address,
                chain_name=chain_name,
                abi_content=json.dumps(sample_abi),
                file_path="abis/ethereum/test.json",
                source_type="manual"
            )
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_record
            
            with patch('app.api.abis.abi_storage_service') as mock_storage:
                mock_storage.validate_abi_format.return_value = True
                mock_storage.update_abi.return_value = "abis/ethereum/test.json"
                
                response = client.put(
                    f"/api/v1/abis/{contract_address}?chain_name={chain_name}",
                    json={"abi_content": updated_abi}
                )
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "ABI记录更新成功" in data["message"]
    
    def test_delete_abi(self, client):
        """测试删除ABI记录"""
        contract_address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_name = "ethereum"
        
        with patch('app.api.abis.get_db_session') as mock_db:
            mock_record = ContractAbi(
                id=1,
                contract_address=contract_address,
                chain_name=chain_name,
                abi_content='[]',
                file_path="abis/ethereum/test.json",
                source_type="manual"
            )
            
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = mock_record
            mock_session.delete = AsyncMock()
            
            with patch('app.api.abis.abi_storage_service') as mock_storage:
                mock_storage.delete_abi.return_value = True
                
                response = client.delete(f"/api/v1/abis/{contract_address}?chain_name={chain_name}")
                
                assert response.status_code == 200
                data = response.json()
                assert data["success"] is True
                assert "ABI记录删除成功" in data["message"]
    
    def test_upload_abi_file(self, client, sample_abi):
        """测试通过文件上传ABI"""
        contract_address = "0x1234567890abcdef1234567890abcdef12345678"
        chain_name = "ethereum"
        
        # 创建模拟的JSON文件
        json_content = json.dumps(sample_abi).encode('utf-8')
        files = {
            "file": ("test_abi.json", BytesIO(json_content), "application/json")
        }
        
        with patch('app.api.abis.get_db_session') as mock_db:
            mock_session = AsyncMock()
            mock_db.return_value = mock_session
            mock_session.execute.return_value.scalar_one_or_none.return_value = None
            
            with patch('app.api.abis.abi_storage_service') as mock_storage:
                mock_storage.validate_abi_format.return_value = True
                mock_storage.save_abi.return_value = "abis/ethereum/test.json"
                
                response = client.post(
                    f"/api/v1/abis/upload?contract_address={contract_address}&chain_name={chain_name}",
                    files=files
                )
                
                assert response.status_code == 201
                data = response.json()
                assert data["success"] is True
                assert "ABI文件上传成功" in data["message"]
    
    def test_invalid_contract_address(self, client):
        """测试无效的合约地址"""
        request_data = {
            "contract_address": "invalid_address",
            "chain_name": "ethereum",
            "abi_content": [],
            "source_type": "manual"
        }
        
        response = client.post("/api/v1/abis/", json=request_data)
        assert response.status_code == 422  # 验证错误
    
    def test_unsupported_chain(self, client):
        """测试不支持的链类型"""
        request_data = {
            "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
            "chain_name": "unsupported_chain",
            "abi_content": [],
            "source_type": "manual"
        }
        
        response = client.post("/api/v1/abis/", json=request_data)
        assert response.status_code == 422  # 验证错误