#!/bin/bash

# 链数据解析系统安装脚本

echo "🚀 开始安装链数据解析系统..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本需要 >= 3.9，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 创建虚拟环境
if [ ! -d ".venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv .venv
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source .venv/bin/activate

# 升级pip
echo "⬆️ 升级pip..."
pip install --upgrade pip

# 安装依赖
echo "📥 安装项目依赖..."
pip install -r requirements_main.txt

# 创建必要的目录
echo "📁 创建必要目录..."
mkdir -p logs
mkdir -p uploads
mkdir -p abis

# 复制环境配置文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建环境配置文件..."
    cat > .env << EOF
# 数据库配置
DATABASE_URL=mysql+aiomysql://chaindata_parser:2esd134jnfdsdfr3r@35.215.85.104:13306/tp_chaindata_parser

# API配置
API_HOST=0.0.0.0
API_PORT=8000
API_DEBUG=true
API_RELOAD=false

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
EOF
fi

echo "✅ 安装完成！"
echo ""
echo "🎯 使用方法："
echo "1. 激活虚拟环境: source .venv/bin/activate"
echo "2. 启动服务: python start_server.py"
echo "3. 访问API文档: http://localhost:8000/docs"
echo "4. 健康检查: curl http://localhost:8000/health"
