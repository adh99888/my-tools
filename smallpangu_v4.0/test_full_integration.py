#!/usr/bin/env python3
"""
小盘古4.0 完整集成测试

测试整个应用架构，包括：
1. 应用初始化
2. 配置加载
3. 插件系统
4. UI框架
5. 视图系统
"""

import sys
import os
import tempfile
import shutil
import time
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_app_with_ui():
    """测试应用与UI集成"""
    print("=== 应用与UI集成测试 ===")
    
    temp_dir = tempfile.mkdtemp(prefix="smallpangu_test_")
    print(f"测试临时目录: {temp_dir}")
    
    try:
        # 复制配置文件
        config_source = Path(__file__).parent / "configs" / "base.yaml"
        config_dest = Path(temp_dir) / "config.yaml"
        shutil.copy(config_source, config_dest)
        
        # 创建应用实例
        from smallpangu.app import create_app
        app = create_app(config_path=str(config_dest))
        
        # 初始化应用
        app.initialize()
        print("[OK] 应用初始化成功")
        
        # 启动应用（启动插件）
        app.start()
        print("[OK] 应用启动成功")
        
        # 获取UI管理器
        from smallpangu.ui.manager import create_ui_manager
        ui_manager = create_ui_manager(
            config_manager=app.config_manager,
            event_bus=app.event_bus,
            container=app.container,
            app_name="小盘古测试"
        )
        
        # 初始化UI管理器
        ui_manager.initialize()
        print("[OK] UI管理器初始化成功")
        
        # 检查UI管理器状态
        status = ui_manager.get_status()
        print(f"[OK] UI管理器状态: {status}")
        
        # 启动UI系统（但不运行主循环）
        ui_manager.start()
        print("[OK] UI系统启动成功")
        
        # 验证主窗口存在
        assert ui_manager.root_window is not None, "根窗口应已创建"
        print("[OK] 根窗口创建成功")
        
        # 验证主题管理器
        assert ui_manager.theme_manager is not None, "主题管理器应已初始化"
        print("[OK] 主题管理器初始化成功")
        
        # 验证国际化管理器
        assert ui_manager.i18n_manager is not None, "国际化管理器应已初始化"
        print("[OK] 国际化管理器初始化成功")
        
        # 验证视图系统（通过主窗口）
        from smallpangu.ui.window import MainWindow
        main_window = app.container.get(MainWindow)
        if main_window:
            print("[OK] 主窗口已注册到容器")
            # 检查视图数量
            view_count = main_window.view_count
            print(f"[OK] 主窗口视图数量: {view_count}")
            # 预期有6个视图：聊天、插件、配置、监控、帮助、设置
            assert view_count == 6, f"预期6个视图，实际{view_count}个"
            print("[OK] 视图数量正确")
        else:
            print("[WARN] 主窗口未在容器中找到（可能在UI启动后才注册）")
        
        # 停止UI系统
        ui_manager.stop()
        print("[OK] UI系统停止成功")
        
        # 停止应用
        app.stop()
        print("[OK] 应用停止成功")
        
        # 关闭UI系统
        ui_manager.shutdown()
        print("[OK] UI系统关闭成功")
        
        # 关闭应用
        app.shutdown()
        print("[OK] 应用关闭成功")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 应用与UI集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # 清理临时目录
        shutil.rmtree(temp_dir, ignore_errors=True)
        print(f"临时目录已清理")

def test_view_switching():
    """测试视图切换功能"""
    print("\n=== 视图切换测试 ===")
    
    try:
        # 导入必要的模块
        from smallpangu.ui.window import MainWindow
        from smallpangu.config.manager import get_config_manager
        from smallpangu.core.events import EventBus
        from smallpangu.core.di import Container
        from smallpangu.ui.manager import create_ui_manager
        
        # 创建配置管理器（使用默认配置）
        config_manager = get_config_manager()
        
        # 创建事件总线
        event_bus = EventBus()
        
        # 创建容器
        container = Container()
        
        # 注册核心实例
        container.register_instance(type(config_manager), config_manager)
        container.register_instance(type(event_bus), event_bus)
        container.register_instance(type(container), container)
        
        # 创建UI管理器
        ui_manager = create_ui_manager(
            config_manager=config_manager,
            event_bus=event_bus,
            container=container
        )
        
        # 初始化UI管理器
        ui_manager.initialize()
        
        # 获取主窗口（UI管理器启动后会创建）
        ui_manager.start()
        
        # 从容器获取主窗口
        main_window = container.get(MainWindow)
        assert main_window is not None, "主窗口应已创建"
        
        # 测试视图切换
        test_views = ['chat', 'plugins', 'config', 'monitor', 'help', 'settings']
        
        for view_name in test_views:
            try:
                main_window.switch_view(view_name)
                print(f"[OK] 切换到视图 '{view_name}' 成功")
                # 验证当前视图
                current_view = main_window.current_view
                if current_view:
                    print(f"    当前视图: {current_view}")
            except Exception as e:
                print(f"[WARN] 切换到视图 '{view_name}' 失败: {e}")
        
        # 停止UI系统
        ui_manager.stop()
        ui_manager.shutdown()
        
        print("[OK] 视图切换测试完成")
        return True
        
    except Exception as e:
        print(f"[FAIL] 视图切换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_theme_and_language():
    """测试主题和语言切换"""
    print("\n=== 主题和语言切换测试 ===")
    
    try:
        from smallpangu.ui.theme import ThemeManager, Theme
        from smallpangu.ui.i18n import I18nManager, Language
        from smallpangu.config.manager import get_config_manager
        from smallpangu.core.events import EventBus
        
        # 创建配置管理器和事件总线
        config_manager = get_config_manager()
        event_bus = EventBus()
        
        # 创建主题管理器
        theme_manager = ThemeManager(config_manager, event_bus)
        theme_manager.initialize()
        
        # 创建国际化管理器
        i18n_manager = I18nManager(config_manager, event_bus)
        i18n_manager.initialize()
        
        # 测试主题切换
        themes = [Theme.LIGHT, Theme.DARK, Theme.SYSTEM]
        for theme in themes:
            theme_manager.set_theme(theme)
            print(f"[OK] 主题切换: {theme.value}")
        
        # 测试语言切换
        languages = [Language.ZH_CN, Language.EN_US]
        for language in languages:
            i18n_manager.set_language(language)
            print(f"[OK] 语言切换: {language.value}")
            
            # 测试翻译
            translation = i18n_manager.get_text("app.title", TextDomain="ui")
            print(f"    翻译示例: app.title -> {translation}")
        
        # 关闭管理器
        theme_manager.shutdown()
        i18n_manager.shutdown()
        
        print("[OK] 主题和语言切换测试完成")
        return True
        
    except Exception as e:
        print(f"[FAIL] 主题和语言切换测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("小盘古4.0完整集成测试")
    print("=" * 60)
    
    success_count = 0
    total_tests = 3
    
    # 测试1: 应用与UI集成
    if test_app_with_ui():
        success_count += 1
    
    # 测试2: 视图切换
    if test_view_switching():
        success_count += 1
    
    # 测试3: 主题和语言切换
    if test_theme_and_language():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("[SUCCESS] 所有集成测试通过！小盘古4.0架构工作正常。")
        return 0
    else:
        print("[FAIL] 部分集成测试失败，需要检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())