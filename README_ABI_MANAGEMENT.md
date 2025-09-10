# 合约ABI管理系统

## 功能概述

合约ABI管理系统是基于FastAPI的区块链数据解析系统的扩展功能，提供完整的合约ABI增删查改操作，支持手动上传和自动获取ABI文件。

## 主要功能

### 1. 数据模型和存储
- ✅ `ContractAbi` 数据模型，包含完整的ABI记录字段
- ✅ 支持MySQL数据库存储，包含适当的索引优化
- ✅ Alembic数据库迁移支持

### 2. ABI文件存储管理
- ✅ `AbiStorageService` 文件存储服务
- ✅ 按链名组织的目录结构（如 abis/ethereum/, abis/bsc/）
- ✅ 异步文件操作，支持创建、读取、更新、删除
- ✅ ABI格式验证

### 3. 区块链浏览器集成
- ✅ `BlockchainExplorerService` 区块链浏览器API客户端
- ✅ 支持多个区块链：Ethereum、BSC、Polygon、Arbitrum、Optimism
- ✅ 智能重试机制和错误处理
- ✅ API密钥配置管理

### 4. RESTful API端点
- ✅ `POST /api/v1/abis/` - 创建ABI记录（手动/自动）
- ✅ `POST /api/v1/abis/auto-fetch` - 自动获取并创建ABI记录
- ✅ `GET /api/v1/abis/{contract_address}` - 根据合约地址查询ABI
- ✅ `GET /api/v1/abis/` - 分页查询ABI列表，支持链名过滤
- ✅ `PUT /api/v1/abis/{contract_address}` - 更新ABI记录
- ✅ `DELETE /api/v1/abis/{contract_address}` - 删除ABI记录
- ✅ `POST /api/v1/abis/upload` - 通过文件上传ABI

## API使用示例

### 1. 手动创建ABI记录

```bash
curl -X POST "http://localhost:8001/api/v1/abis/" \\
  -H "Content-Type: application/json" \\
  -d '{
    "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
    "chain_name": "ethereum",
    "abi_content": [
      {
        "type": "function",
        "name": "transfer",
        "inputs": [
          {"name": "to", "type": "address"},
          {"name": "value", "type": "uint256"}
        ]
      }
    ],
    "source_type": "manual"
  }'
```

### 2. 自动获取ABI

```bash
curl -X POST "http://localhost:8001/api/v1/abis/auto-fetch" \\
  -H "Content-Type: application/json" \\
  -d '{
    "contract_address": "0x1234567890abcdef1234567890abcdef12345678",
    "chain_name": "ethereum"
  }'
```

### 3. 查询ABI

```bash
curl -X GET "http://localhost:8001/api/v1/abis/0x1234567890abcdef1234567890abcdef12345678?chain_name=ethereum"
```

### 4. 分页查询ABI列表

```bash
curl -X GET "http://localhost:8001/api/v1/abis/?page=1&size=20&chain_name=ethereum"
```

### 5. 文件上传ABI

```bash
curl -X POST "http://localhost:8001/api/v1/abis/upload?contract_address=0x1234567890abcdef1234567890abcdef12345678&chain_name=ethereum" \\
  -F "file=@contract_abi.json"
```

## 环境配置

### 数据库迁移

```bash
# 执行数据库迁移
python -m alembic upgrade head
```

### 环境变量配置

```bash
# .env 文件
ETHERSCAN_API_KEY=your_etherscan_api_key
BSCSCAN_API_KEY=your_bscscan_api_key
POLYGONSCAN_API_KEY=your_polygonscan_api_key
ARBISCAN_API_KEY=your_arbiscan_api_key
OPTIMISM_API_KEY=your_optimism_api_key
```

## 支持的区块链

- Ethereum (etherscan.io)
- BSC (bscscan.com) 
- Polygon (polygonscan.com)
- Arbitrum (arbiscan.io)
- Optimism (optimistic.etherscan.io)

## 文件结构

```
app/
├── models/
│   └── contract_abi.py          # ABI数据模型
├── services/
│   ├── abi_storage_service.py   # ABI文件存储服务
│   └── blockchain_explorer_service.py  # 区块链浏览器服务
└── api/
    └── abis.py                  # ABI管理API端点

abis/                            # ABI文件存储目录
├── ethereum/
├── bsc/
├── polygon/
└── ...

tests/
├── test_abi_storage_service.py  # 存储服务测试
├── test_blockchain_explorer_service.py  # 浏览器服务测试
└── test_abi_api.py             # API端点测试
```

## 技术特点

- 🚀 **高性能**: 异步处理，支持并发操作
- 🛡️ **可靠性**: 完整的错误处理和重试机制
- 🔧 **可扩展**: 易于添加新的区块链支持
- 📊 **兼容性**: 与现有FastAPI架构无缝集成
- 🧪 **可测试**: 完整的单元测试覆盖

## 下一步

系统已经完全实现了PRD中定义的所有功能要求。可以开始部署和集成测试，确保与现有区块链数据解析系统的完美配合。