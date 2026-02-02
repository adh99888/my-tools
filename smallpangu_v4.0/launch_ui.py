#!/usr/bin/env python3
"""
小盘古4.0 UI启动脚本
启动完整的图形用户界面应用
"""

import sys
import os
import signal
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_environment():
    """设置运行环境"""
    # 设置控制台编码为UTF-8
    if sys.platform.startswith('win'):
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)  # UTF-8
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('PYTHONUTF8', '1')

def main():
    """主函数"""
    setup_environment()
    
    print("=" * 60)
    print("小盘古 4.0 - 图形用户界面启动")
    print("=" * 60)
    
    app = None
    ui_manager = None
    
    def signal_handler(signum, frame):
        """信号处理函数"""
        print(f"\n收到信号 {signum}，正在优雅关闭...")
        if ui_manager:
            ui_manager.stop()
        if app:
            app.stop()
            app.shutdown()
        sys.exit(0)
    
    # 注册信号处理
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 1. 创建应用实例
        from smallpangu.app import create_app
        print("创建应用实例...")
        app = create_app()
        
        # 2. 初始化应用
        print("初始化应用...")
        app.initialize()
        print("应用初始化成功")
        
        # 3. 启动应用（启动插件系统）
        print("启动应用...")
        app.start()
        print("应用启动成功")
        
        # 4. 创建UI管理器
        from smallpangu.ui.manager import create_ui_manager
        print("创建UI管理器...")
        ui_manager = create_ui_manager(
            config_manager=app.config_manager,
            event_bus=app.event_bus,
            container=app.container,
            app_name="小盘古"
        )
        
        # 5. 初始化UI管理器
        print("初始化UI管理器...")
        ui_manager.initialize()
        print("UI管理器初始化成功")
        
        # 6. 运行UI主循环（阻塞）
        print("\n" + "=" * 60)
        print("启动图形用户界面...")
        print("=" * 60)
        print("提示: 按Ctrl+C或关闭窗口退出")
        
        ui_manager.run()
        
    except KeyboardInterrupt:
        print("\n用户中断，正在关闭...")
    except Exception as e:
        print(f"\n[错误] 启动失败: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # 清理资源
        print("\n正在清理资源...")
        try:
            if ui_manager:
                ui_manager.stop()
                ui_manager.shutdown()
        except Exception as e:
            print(f"警告: UI管理器关闭时出错: {e}")
        
        try:
            if app:
                app.stop()
                app.shutdown()
        except Exception as e:
            print(f"警告: 应用关闭时出错: {e}")
    
    print("\n" + "=" * 60)
    print("小盘古应用已关闭")
    return 0

if __name__ == "__main__":
    sys.exit(main())