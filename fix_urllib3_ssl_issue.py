#!/usr/bin/env python3
"""
修复urllib3与OpenSSL版本不兼容问题
"""

import subprocess
import sys
import ssl
import urllib3
from packaging import version

def check_ssl_version():
    """检查SSL版本"""
    print("🔍 检查SSL版本信息")
    print("=" * 40)
    
    # 检查OpenSSL版本
    ssl_version = ssl.OPENSSL_VERSION
    print(f"OpenSSL版本: {ssl_version}")
    
    # 检查urllib3版本
    urllib3_version = urllib3.__version__
    print(f"urllib3版本: {urllib3_version}")
    
    # 检查是否兼容
    if "1.0.2" in ssl_version:
        print("❌ 检测到OpenSSL 1.0.2，与urllib3 v2不兼容")
        return False
    elif "1.1.1" in ssl_version or "3." in ssl_version:
        print("✅ OpenSSL版本兼容")
        return True
    else:
        print("⚠️  无法确定OpenSSL版本兼容性")
        return False

def create_fixed_requirements():
    """创建修复后的requirements.txt"""
    print("\n🔧 创建兼容的requirements.txt")
    print("=" * 40)
    
    # 读取原始requirements.txt
    with open('requirements.txt', 'r') as f:
        lines = f.readlines()
    
    # 创建修复版本
    fixed_lines = []
    for line in lines:
        line = line.strip()
        if line.startswith('urllib3=='):
            # 降级urllib3到1.26.x版本（兼容OpenSSL 1.0.2）
            fixed_lines.append('urllib3==1.26.18\n')
            print(f"  修改: {line} -> urllib3==1.26.18")
        elif line.startswith('requests=='):
            # 确保requests版本兼容
            fixed_lines.append('requests==2.31.0\n')
            print(f"  修改: {line} -> requests==2.31.0")
        else:
            fixed_lines.append(line + '\n' if line else '\n')
    
    # 保存修复后的requirements
    with open('requirements_fixed.txt', 'w') as f:
        f.writelines(fixed_lines)
    
    print("✅ 已创建 requirements_fixed.txt")

def install_fixed_packages():
    """安装修复后的包"""
    print("\n📦 安装兼容的包版本")
    print("=" * 40)
    
    try:
        # 卸载现有的urllib3
        print("卸载现有urllib3...")
        subprocess.run([sys.executable, '-m', 'pip', 'uninstall', 'urllib3', '-y'], 
                      check=False)
        
        # 安装兼容版本
        print("安装urllib3 1.26.18...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'urllib3==1.26.18'], 
                      check=True)
        
        # 安装兼容的requests版本
        print("安装requests 2.31.0...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'requests==2.31.0'], 
                      check=True)
        
        print("✅ 包安装完成")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ 安装失败: {e}")
        return False

def verify_fix():
    """验证修复结果"""
    print("\n✅ 验证修复结果")
    print("=" * 40)
    
    try:
        import urllib3
        import requests
        
        print(f"urllib3版本: {urllib3.__version__}")
        print(f"requests版本: {requests.__version__}")
        
        # 测试HTTPS请求
        print("测试HTTPS请求...")
        response = requests.get('https://httpbin.org/get', timeout=10)
        if response.status_code == 200:
            print("✅ HTTPS请求测试成功")
            return True
        else:
            print(f"❌ HTTPS请求失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 urllib3 SSL兼容性修复工具")
    print("=" * 50)
    
    # 1. 检查SSL版本
    ssl_compatible = check_ssl_version()
    
    if ssl_compatible:
        print("\n✅ 当前环境SSL版本兼容，无需修复")
        return
    
    # 2. 创建修复后的requirements
    create_fixed_requirements()
    
    # 3. 询问是否安装
    choice = input("\n是否立即安装修复后的包? (y/n): ").strip().lower()
    
    if choice == 'y':
        # 4. 安装修复后的包
        if install_fixed_packages():
            # 5. 验证修复结果
            verify_fix()
        else:
            print("❌ 安装失败，请手动执行以下命令:")
            print("pip uninstall urllib3 -y")
            print("pip install urllib3==1.26.18")
            print("pip install requests==2.31.0")
    else:
        print("\n💡 手动修复步骤:")
        print("1. pip uninstall urllib3 -y")
        print("2. pip install urllib3==1.26.18")
        print("3. pip install requests==2.31.0")
        print("4. 或使用: pip install -r requirements_fixed.txt")

if __name__ == "__main__":
    main()
