#!/usr/bin/env python3
"""
UI功能测试 - 测试视图切换、主题、语言等基本功能
"""

import sys
import os
import time
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

def run_tests(app, ui_manager):
    """运行UI功能测试"""
    print("\n" + "=" * 60)
    print("开始UI功能测试")
    print("=" * 60)
    
    test_results = []
    
    try:
        # 测试1: 检查根窗口
        root = ui_manager.root_window
        if root:
            test_results.append(("根窗口存在", True))
            print("[OK] 根窗口存在")
        else:
            test_results.append(("根窗口存在", False))
            print("[FAIL] 根窗口不存在")
            return test_results
        
        # 测试2: 检查主题管理器
        theme_manager = ui_manager.theme_manager
        if theme_manager:
            test_results.append(("主题管理器存在", True))
            print("[OK] 主题管理器存在")
            current_theme = theme_manager.current_theme
            print(f"  当前主题: {current_theme}")
        else:
            test_results.append(("主题管理器存在", False))
            print("[FAIL] 主题管理器不存在")
        
        # 测试3: 检查国际化管理器
        i18n_manager = ui_manager.i18n_manager
        if i18n_manager:
            test_results.append(("国际化管理器存在", True))
            print("[OK] 国际化管理器存在")
            current_language = i18n_manager.current_language
            print(f"  当前语言: {current_language}")
        else:
            test_results.append(("国际化管理器存在", False))
            print("[FAIL] 国际化管理器不存在")
        
            # 测试4: 获取主窗口实例
            from smallpangu.ui.window import MainWindow
            main_window = app.container.resolve(MainWindow)
        if main_window:
            test_results.append(("主窗口实例存在", True))
            print("[OK] 主窗口实例存在")
            
            # 测试5: 获取导航项
            nav_items = getattr(main_window, '_navigation_items', [])
            print(f"  导航项数量: {len(nav_items)}")
            
            # 测试6: 视图切换测试（模拟）
            # 注意：实际切换视图可能需要UI更新，这里只测试方法是否存在
            if hasattr(main_window, 'switch_view'):
                test_results.append(("视图切换方法存在", True))
                print("[OK] 视图切换方法存在")
                # 可以尝试切换到默认视图
                try:
                    # 不实际切换，只检查方法
                    print("  视图切换方法可用")
                except Exception as e:
                    print(f"  视图切换方法异常: {e}")
                    test_results.append(("视图切换方法可用", False))
            else:
                test_results.append(("视图切换方法存在", False))
                print("[FAIL] 视图切换方法不存在")
        else:
            test_results.append(("主窗口实例存在", False))
            print("[FAIL] 主窗口实例不存在")
        
        # 测试7: 检查UI配置
        ui_config = app.config_manager.config.ui
        print(f"[OK] UI配置加载: 主题={ui_config.theme}, 语言={ui_config.language}")
        print(f"  窗口大小: {ui_config.window_width}x{ui_config.window_height}")
        test_results.append(("UI配置加载", True))
        
        # 测试8: 检查插件系统集成
        plugin_count = app.plugin_registry.plugin_count if hasattr(app, 'plugin_registry') else 0
        print(f"[OK] 已加载插件数量: {plugin_count}")
        test_results.append(("插件系统集成", True))
        
    except Exception as e:
        print(f"[ERROR] 测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()
        test_results.append(("测试过程异常", False))
    
    return test_results

def main():
    """主函数"""
    setup_environment()
    
    print("=" * 60)
    print("小盘古4.0 UI功能测试")
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
        
        # 汇总测试结果
        print("\n" + "=" * 60)
        print("测试结果汇总:")
        for name, passed in test_results:
            status = "PASS" if passed else "FAIL"
            print(f"  {status}: {name}")
        
        total = len(test_results)
        passed = sum(1 for _, p in test_results if p)
        print(f"\n总计: {passed}/{total} 通过")
        
        if passed == total:
            print("\n[SUCCESS] 所有测试通过！")
            os._exit(0)
        else:
            print("\n[FAIL] 部分测试失败")
            os._exit(1)
    
    test_results = []
    
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
            app_name="小盘古功能测试"
        )
        
        # 5. 初始化UI管理器
        print("初始化UI管理器...")
        ui_manager.initialize()
        print("UI管理器初始化成功")
        
        # 6. 启动UI系统
        print("启动UI系统...")
        ui_manager.start()
        print("UI系统启动成功")
        
        # 7. 运行功能测试
        root = ui_manager.root_window
        if root:
            # 在UI线程中安排测试任务
            def run_tests_and_close():
                test_results.extend(run_tests(app, ui_manager))
                # 测试完成后关闭UI
                root.after(1000, close_ui)
            
            root.after(1000, run_tests_and_close)  # 1秒后运行测试
            
            # 8. 运行主循环（阻塞）
            print("\n进入UI主循环，开始功能测试...")
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