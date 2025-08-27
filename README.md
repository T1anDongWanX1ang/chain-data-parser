# 链数据解析系统

一个基于FastAPI的现代化区块链数据解析系统，支持EVM链（以太坊、BSC、Polygon）和Solana链的数据采集、解析和存储。

## 功能特性

- 🔗 **多链支持**: 支持EVM兼容链和Solana链
- 📊 **数据解析**: 自动解析区块、交易、代币转账等数据
- 🗄️ **数据存储**: 使用MySQL存储结构化数据
- 🚀 **高性能**: 基于FastAPI和异步编程，支持高并发
- 📚 **API文档**: 自动生成的Swagger/OpenAPI文档
- 🐳 **容器化**: 提供Docker部署方案
- 📝 **日志管理**: 完整的日志记录和管理

## 技术栈

- **后端框架**: FastAPI 0.104+
- **数据库**: MySQL 8.0 + SQLAlchemy 2.0
- **缓存**: Redis
- **区块链交互**: web3.py, solana-py
- **异步处理**: asyncio, aiohttp
- **数据验证**: Pydantic
- **数据库迁移**: Alembic
- **日志处理**: Loguru
- **容器化**: Docker + Docker Compose

## 项目结构

```
chain-data-parser/
├── app/                    # 应用主目录
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── config.py          # 配置管理
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── base.py        # 基础模型
│   │   ├── transaction.py # 交易模型
│   │   ├── block.py       # 区块模型
│   │   └── token.py       # 代币模型
│   ├── services/          # 业务逻辑层
│   │   ├── __init__.py
│   │   ├── database.py    # 数据库服务
│   │   ├── evm_parser.py  # EVM链解析器
│   │   └── sol_parser.py  # Solana链解析器
│   ├── api/               # API接口层
│   │   ├── __init__.py
│   │   ├── router.py      # 路由配置
│   │   └── endpoints/     # API端点
│   │       ├── __init__.py
│   │       ├── blocks.py
│   │       ├── transactions.py
│   │       ├── tokens.py
│   │       └── parser.py
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── logger.py      # 日志配置
│       └── helpers.py     # 辅助函数
├── alembic/               # 数据库迁移
├── tests/                 # 测试文件
├── logs/                  # 日志文件目录
├── requirements.txt       # Python依赖
├── alembic.ini           # Alembic配置
├── docker-compose.yml    # Docker编排
├── Dockerfile            # Docker镜像
└── README.md             # 项目说明
```

## 快速开始

### 环境要求

- Python 3.11+
- MySQL 8.0+
- Redis 6.0+
- Docker & Docker Compose (可选)

### 1. 克隆项目

```bash
git clone <repository-url>
cd chain-data-parser
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，配置数据库连接和RPC端点
```

### 3. 使用Docker部署 (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f app
```

### 4. 手动部署

```bash
# 安装依赖
pip install -r requirements.txt

# 数据库迁移
alembic upgrade head

# 启动应用
python -m app.main
```

### 5. 简化启动方式 ⭐

我们提供了多种简化的启动方式，无需记忆复杂的命令：

#### 方式1：使用Makefile（推荐）

```bash
# 查看所有可用命令
make help

# 启动服务（开发模式，带热重载）
make start

# 启动服务（生产模式，性能更好）
make start-prod

# 查看服务状态
make status

# 测试API接口
make test

# 停止服务
make stop
```

#### 方式2：使用启动脚本

```bash
# 开发模式启动（带热重载）
./start.sh

# 生产模式启动
./start_prod.sh
```

#### 方式3：传统方式

```bash
# 激活虚拟环境并启动
source .venv/bin/activate && python start_server.py
```

## 配置说明

### 环境变量

| 变量名 | 描述 | 默认值 |
|--------|------|--------|
| MYSQL_HOST | MySQL主机地址 | localhost |
| MYSQL_PORT | MySQL端口 | 3306 |
| MYSQL_USER | MySQL用户名 | root |
| MYSQL_PASSWORD | MySQL密码 | - |
| MYSQL_DATABASE | 数据库名 | chain_data |
| REDIS_HOST | Redis主机地址 | localhost |
| REDIS_PORT | Redis端口 | 6379 |
| ETH_RPC_URL | 以太坊RPC地址 | - |
| BSC_RPC_URL | BSC RPC地址 | - |
| POLYGON_RPC_URL | Polygon RPC地址 | - |
| SOLANA_RPC_URL | Solana RPC地址 | - |
| API_HOST | API服务地址 | 0.0.0.0 |
| API_PORT | API服务端口 | 8000 |
| LOG_LEVEL | 日志级别 | INFO |

## API文档

启动服务后，访问以下地址查看API文档：

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### 主要API端点

#### 区块相关
- `GET /api/v1/blocks/latest` - 获取最新区块
- `GET /api/v1/blocks/{block_number}` - 获取指定区块
- `POST /api/v1/blocks/sync` - 同步区块数据

#### 交易相关
- `GET /api/v1/transactions/{tx_hash}` - 获取交易详情
- `GET /api/v1/transactions/block/{block_number}` - 获取区块的所有交易
- `GET /api/v1/transactions/address/{address}` - 获取地址相关交易

#### 代币相关
- `GET /api/v1/tokens/{contract_address}` - 获取代币信息
- `GET /api/v1/tokens/{contract_address}/transfers` - 获取代币转账记录
- `GET /api/v1/tokens/transfers/address/{address}` - 获取地址的代币转账

#### 解析器相关
- `POST /api/v1/parser/block` - 解析单个区块
- `POST /api/v1/parser/transaction` - 解析单个交易
- `POST /api/v1/parser/sync` - 启动数据同步
- `GET /api/v1/parser/status` - 获取解析器状态

## 使用示例

### 同步以太坊区块数据

```bash
curl -X POST "http://localhost:8000/api/v1/parser/sync?chain_name=ethereum&start_block=18000000&end_block=18000010"
```

### 获取交易详情

```bash
curl "http://localhost:8000/api/v1/transactions/0x..."
```

### 获取地址相关交易

```bash
curl "http://localhost:8000/api/v1/transactions/address/0x742d35cc6b5A8e1c0935C0013B1e7b8B831C9A0C"
```

## 数据库迁移

```bash
# 创建新的迁移文件
alembic revision --autogenerate -m "描述信息"

# 执行迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black app/
isort app/
```

### 类型检查

```bash
mypy app/
```

## 监控和日志

- 日志文件位置: `logs/app.log`
- 日志级别可通过环境变量 `LOG_LEVEL` 配置
- 支持日志轮转和压缩

## 性能优化

- 使用连接池管理数据库连接
- 异步处理提高并发性能
- Redis缓存减少重复查询
- 批量处理减少数据库操作

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查MySQL服务是否启动
   - 验证连接参数是否正确

2. **RPC连接超时**
   - 检查网络连接
   - 验证RPC端点是否有效

3. **内存使用过高**
   - 调整批处理大小
   - 增加服务器内存

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码
4. 创建Pull Request

## 许可证

[MIT License](LICENSE)

## 支持

如有问题，请通过以下方式联系：

- 提交Issue
- 发送邮件
- 加入讨论群