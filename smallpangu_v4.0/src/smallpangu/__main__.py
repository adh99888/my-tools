#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
小盘古4.0 主入口点
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "src"))

def setup_environment():
    """设置运行环境"""
    # 设置控制台编码为UTF-8
    if sys.platform.startswith('win'):
        import ctypes
        try:
            # 尝试设置控制台代码页为UTF-8
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    
    # 设置环境变量
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('PYTHONUTF8', '1')

def main():
    """主函数"""
    setup_environment()
    
    print("=" * 60)
    print("小盘古 4.0 - 轻量级、插件化的个人AI数字分身助手")
    print("=" * 60)
    
    try:
        from smallpangu import run_app
        
        # 解析命令行参数
        config_path = None
        if len(sys.argv) > 1:
            arg = sys.argv[1]
            if arg.endswith('.yaml') or arg.endswith('.yml'):
                config_path = arg
            elif arg in ['-h', '--help']:
                print("\n使用方法:")
                print("  python -m smallpangu [config_file.yaml]")
                print("  python -m smallpangu --help")
                print("\n示例:")
                print("  python -m smallpangu configs/development.yaml")
                return 0
            elif arg in ['-v', '--version']:
                from smallpangu import __version__
                print(f"小盘古版本: {__version__}")
                return 0
        
        # 运行应用
        run_app(config_path)
        return 0
        
    except KeyboardInterrupt:
        print("\n\n应用程序被用户中断")
        return 0
    except Exception as e:
        print(f"\n[错误] 应用程序启动失败: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())