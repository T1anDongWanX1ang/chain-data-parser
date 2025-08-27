#!/bin/bash

# 链数据解析系统启动脚本

echo "🚀 启动链数据解析系统..."

# 检查虚拟环境
if [ ! -d ".venv" ]; then
    echo "❌ 虚拟环境不存在，请先运行 install.sh 安装"
    exit 1
fi

# 激活虚拟环境并启动服务
source .venv/bin/activate && python start_server.py 