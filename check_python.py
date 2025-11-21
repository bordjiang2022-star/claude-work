#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Python版本检查脚本
用于验证当前Python环境是否符合项目要求
"""

import sys
import platform

def check_python_version():
    """检查Python版本"""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"

    print("=" * 60)
    print("LiveTranslate Python环境检查")
    print("=" * 60)
    print()

    print(f"当前Python版本: {version_str}")
    print(f"Python路径: {sys.executable}")
    print(f"操作系统: {platform.system()} {platform.release()}")
    print(f"架构: {platform.machine()}")
    print()

    # 检查是否为Python 3.11
    if version_info.major == 3 and version_info.minor == 11:
        print("✅ Python版本正确！")
        print("   本项目需要Python 3.11，您的版本完全兼容。")
        print()
        return True
    else:
        print("⚠️  Python版本警告！")
        print(f"   当前版本: {version_str}")
        print("   推荐版本: 3.11.x")
        print()

        if version_info.major == 3 and version_info.minor == 14:
            print("❌ 您正在使用Python 3.14")
            print("   Python 3.14太新，部分依赖包可能需要编译，容易出错。")
            print("   强烈建议安装Python 3.11！")
            print()
            print("📥 下载Python 3.11.9:")
            print("   https://www.python.org/downloads/release/python-3119/")
            print()
        elif version_info.major == 3 and version_info.minor < 11:
            print("❌ 您的Python版本过旧")
            print("   本项目需要Python 3.11或更高版本。")
            print()
            print("📥 下载Python 3.11.9:")
            print("   https://www.python.org/downloads/release/python-3119/")
            print()
        elif version_info.major == 3 and version_info.minor > 11:
            print("⚠️  您使用的Python版本较新")
            print("   虽然可能可以运行，但推荐使用已测试的3.11版本。")
            print()

        return False

def check_pip():
    """检查pip版本"""
    try:
        import pip
        pip_version = pip.__version__
        print(f"pip版本: {pip_version}")
        print()
    except ImportError:
        print("⚠️  未检测到pip")
        print()

def check_venv():
    """检查是否在虚拟环境中"""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

    if in_venv:
        print("✅ 已在虚拟环境中")
        print(f"   虚拟环境路径: {sys.prefix}")
    else:
        print("⚠️  当前不在虚拟环境中")
        print("   建议创建虚拟环境后安装依赖：")
        print("   python -m venv venv")
        print("   venv\\Scripts\\activate  # Windows")
        print("   source venv/bin/activate  # Linux/Mac")
    print()

def main():
    """主函数"""
    is_correct = check_python_version()
    check_pip()
    check_venv()

    print("=" * 60)
    if is_correct:
        print("🎉 环境检查通过！可以继续安装依赖。")
        print()
        print("下一步:")
        print("1. pip install -r requirements.txt")
        print("2. python main.py")
    else:
        print("⚠️  请安装Python 3.11后重试。")
        print()
        print("详细说明请查看: PYTHON_VERSION.md")
    print("=" * 60)

    return 0 if is_correct else 1

if __name__ == "__main__":
    sys.exit(main())
