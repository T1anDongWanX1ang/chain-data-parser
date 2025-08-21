#!/usr/bin/env python3
"""
运行字典映射示例的脚本
"""

import sys
import os
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """运行字典映射示例"""
    try:
        # 导入并运行示例
        from examples.dict_mapper_example import main as run_example
        run_example()
        
    except ImportError as e:
        print(f"导入错误: {e}")
        print("请确保已安装所有依赖包")
        sys.exit(1)
    except Exception as e:
        print(f"运行示例时发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 