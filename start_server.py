#!/usr/bin/env python3
"""
服务启动脚本
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# 设置环境变量
os.environ.setdefault('PYTHONPATH', str(current_dir))

try:
    import uvicorn
    
    print("🚀 正在启动链数据解析系统...")
    print(f"📁 项目目录: {current_dir}")
    print(f"🐍 Python路径: {sys.path[0]}")
    
    # 启动服务
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
    
except ImportError as e:
    print(f"❌ 导入错误: {e}")
    print("请确保已安装所有依赖: pip install -r requirements_core.txt")
    sys.exit(1)
except Exception as e:
    print(f"❌ 启动失败: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
