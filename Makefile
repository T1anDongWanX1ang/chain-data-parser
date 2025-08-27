.PHONY: start start-prod install status stop help

# 默认目标
help:
	@echo "链数据解析系统 - 可用命令:"
	@echo ""
	@echo "  make install     - 安装依赖和初始化环境"
	@echo "  make start       - 启动服务（开发模式，带热重载）"
	@echo "  make start-prod  - 启动服务（生产模式）"
	@echo "  make status      - 查看服务状态"
	@echo "  make stop        - 停止服务"
	@echo "  make test        - 测试pipeline/tree接口"
	@echo "  make test-writer - 测试save-ingestion-config接口"
	@echo ""

# 安装依赖
install:
	@echo "🔧 安装系统依赖..."
	./install.sh

# 启动服务（开发模式）
start:
	@echo "🚀 启动服务（开发模式）..."
	./start.sh

# 启动服务（生产模式）
start-prod:
	@echo "🚀 启动服务（生产模式）..."
	./start_prod.sh

# 查看服务状态
status:
	@echo "📊 检查服务状态..."
	@curl -s http://localhost:8000/health || echo "❌ 服务未运行"

# 停止服务
stop:
	@echo "🛑 停止服务..."
	@pkill -f "uvicorn" || echo "没有找到运行的服务"
	@pkill -f "start_server.py" || true

# 测试API
test:
	@echo "🧪 测试pipeline/tree接口..."
	@curl -s -X GET "http://localhost:8000/api/v1/pipeline/tree" -H "accept: application/json" | python -m json.tool

# 测试新的writer配置接口
test-writer:
	@echo "🧪 测试save-ingestion-config接口..."
	@curl -s -X POST "http://localhost:8000/api/v1/save-ingestion-config" \
		-H "accept: application/json" \
		-H "Content-Type: application/json" \
		-d '{"component_id": 999, "module_content": {"test": "data", "timestamp": "'$$(date +%s)'"}}' | python -m json.tool 