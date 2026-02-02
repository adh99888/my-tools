#!/usr/bin/env python3
"""
UI显示测试 - 启动UI窗口，验证显示，然后自动关闭
"""

import sys
import os
import signal
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def setup_environment():
    """设置运行环境"""
    if sys.platform.startswith('win'):
        import ctypes
        try:
            kernel32 = ctypes.windll.kernel32
            kernel32.SetConsoleOutputCP(65001)
            kernel32.SetConsoleCP(65001)
        except Exception:
            pass
    
    os.environ.setdefault('PYTHONIOENCODING', 'utf-8')
    os.environ.setdefault('PYTHONUTF8', '1')

def main():
    """主函数"""
    setup_environment()
    
    print("=" * 60)
    print("小盘古4.0 UI显示测试")
    print("=" * 60)
    
    app = None
    ui_manager = None
    
    def close_ui():
        """关闭UI窗口"""
        print("\n测试完成，关闭UI窗口...")
        if ui_manager:
            ui_manager.stop()
        if app:
            app.stop()
            app.shutdown()
        print("测试成功！UI窗口正常显示。")
        # 强制退出，因为主循环可能还在运行
        os._exit(0)
    
    def schedule_close():
        """安排关闭任务"""
        # 使用root_window.after在UI线程中调度
        if ui_manager and ui_manager.root_window:
            ui_manager.root_window.after(5000, close_ui)  # 5秒后关闭
            print("UI窗口已显示，将在5秒后自动关闭...")
        else:
            print("错误：无法获取根窗口")
            close_ui()
    
    try:
        # 1. 创建应用实例
        from smallpangu.app import create_app
        print("创建应用实例...")
        app = create_app()
        
        # 2. 初始化应用
        print("初始化应用...")
        app.initialize()
        print("应用初始化成功")
        
        # 3. 启动应用
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
            app_name="小盘古测试"
        )
        
        # 5. 初始化UI管理器
        print("初始化UI管理器...")
        ui_manager.initialize()
        print("UI管理器初始化成功")
        
        # 6. 启动UI系统（不运行主循环）
        print("启动UI系统...")
        ui_manager.start()
        print("UI系统启动成功")
        
        # 7. 验证根窗口
        root = ui_manager.root_window
        if root:
            print(f"根窗口创建成功: {root.title()}")
            print(f"窗口大小: {root.winfo_geometry()}")
            # 检查子组件
            children = root.winfo_children()
            print(f"根窗口子组件数量: {len(children)}")
            
            # 安排关闭任务
            root.after(5000, close_ui)
            
            # 8. 运行主循环（阻塞）
            print("\n进入UI主循环，窗口应已显示...")
            print("等待5秒后自动关闭...")
            ui_manager.run()
        else:
            print("错误：根窗口未创建")
            return 1
            
    except KeyboardInterrupt:
        print("\n用户中断")
        close_ui()
    except Exception as e:
        print(f"\n[错误] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        # 清理资源
        try:
            if ui_manager:
                ui_manager.stop()
                ui_manager.shutdown()
        except:
            pass
        try:
            if app:
                app.stop()
                app.shutdown()
        except:
            pass
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())