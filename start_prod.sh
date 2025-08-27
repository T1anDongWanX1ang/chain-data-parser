#!/bin/bash

# 链数据解析系统生产启动脚本

echo "🚀 启动链数据解析系统（生产模式）..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 install.sh 安装"
    exit 1
fi

# 激活虚拟环境并启动服务（生产模式，无热重载）
source .venv/bin/activate && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level info 