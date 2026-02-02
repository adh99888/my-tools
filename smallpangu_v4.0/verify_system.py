#!/usr/bin/env python3
"""
小盘古4.0 系统验证脚本
验证所有核心模块是否正常工作
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def verify_core_modules():
    """验证核心模块"""
    print("=== 核心模块验证 ===")
    
    try:
        # 核心模块
        from smallpangu.app import SmallPanguApp, create_app
        from smallpangu.config.manager import ConfigManager, get_config_manager
        from smallpangu.core.events import EventBus, Event
        from smallpangu.core.di import Container
        from smallpangu.core.logging import get_logger
        from smallpangu.core.errors import AppError, UIError
        
        print("[OK] 核心模块导入成功")
        return True
        
    except Exception as e:
        print(f"[FAIL] 核心模块导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_plugin_system():
    """验证插件系统"""
    print("\n=== 插件系统验证 ===")
    
    try:
        from smallpangu.plugins.base import Plugin, PluginType, PluginMetadata, PluginStatus
        from smallpangu.plugins.loader import PluginLoader
        from smallpangu.plugins.registry import PluginRegistry
        
        print("[OK] 插件系统模块导入成功")
        return True
        
    except Exception as e:
        print(f"[FAIL] 插件系统导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_ui_system():
    """验证UI系统"""
    print("\n=== UI系统验证 ===")
    
    try:
        # UI管理器
        from smallpangu.ui.manager import UIManager, create_ui_manager
        from smallpangu.ui.theme import ThemeManager
        from smallpangu.ui.i18n import I18nManager, Language, TextDomain
        
        # 窗口系统
        from smallpangu.ui.window import BaseWindow, MainWindow, NavigationItem, WindowState
        
        # UI组件
        from smallpangu.ui.widgets import (
            BaseWidget, Panel, Card, Button, Label, 
            InputField, TextArea, ScrollPanel, MessageCard
        )
        
        # 界面
        from smallpangu.ui.chat_interface import ChatInterface, ChatView
        from smallpangu.ui.plugin_interface import PluginInterface, PluginView
        from smallpangu.ui.config_interface import ConfigInterface, ConfigView
        from smallpangu.ui.monitor_interface import MonitorInterface, MonitorView
        from smallpangu.ui.help_interface import HelpInterface, HelpView
        from smallpangu.ui.settings_interface import SettingsInterface, SettingsView
        
        print("[OK] UI系统所有模块导入成功")
        print(f"    - 主题: dark, light, system")
        print(f"    - 语言: {Language.ZH_CN.value}, {Language.EN_US.value}")
        print(f"    - 界面数量: 6个 (聊天、插件、配置、监控、帮助、设置)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] UI系统导入失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_app_lifecycle():
    """验证应用生命周期"""
    print("\n=== 应用生命周期验证 ===")
    
    try:
        from smallpangu.app import create_app
        
        # 创建应用
        print("1. 创建应用...")
        app = create_app()
        print("   [OK] 应用创建成功")
        
        # 初始化应用
        print("2. 初始化应用...")
        app.initialize()
        print("   [OK] 应用初始化成功")
        
        # 检查状态
        print("3. 检查应用状态...")
        assert app.is_initialized, "应用应该已初始化"
        assert not app.is_running, "应用此时不应该在运行"
        print("   [OK] 应用状态正确")
        
        # 获取状态信息
        print("4. 获取应用状态...")
        status = app.get_status()
        print(f"   [OK] 状态: 初始化={status['initialized']}, 运行={status['running']}")
        print(f"   环境: {status['config']['environment']}")
        print(f"   应用: {status['config']['app_name']} v{status['config']['app_version']}")
        
        # 启动应用
        print("5. 启动应用...")
        app.start()
        print("   [OK] 应用启动成功")
        assert app.is_running, "应用应该正在运行"
        print(f"   运行时间: {app.uptime:.2f} 秒")
        
        # 停止应用
        print("6. 停止应用...")
        app.stop()
        print("   [OK] 应用停止成功")
        assert not app.is_running, "应用应该已停止"
        
        # 关闭应用
        print("7. 关闭应用...")
        app.shutdown()
        print("   [OK] 应用关闭成功")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 应用生命周期验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def verify_plugin_loading():
    """验证插件加载"""
    print("\n=== 插件加载验证 ===")
    
    try:
        from smallpangu.app import create_app
        
        # 创建并初始化应用
        print("1. 创建并初始化应用...")
        app = create_app()
        app.initialize()
        
        # 启动应用（会加载插件）
        print("2. 启动应用...")
        app.start()
        
        # 检查插件
        print("3. 检查插件...")
        if app.plugin_registry:
            all_plugins = app.plugin_registry.get_all_plugins()
            print(f"   已注册插件: {len(all_plugins)} 个")
            
            for plugin_info in all_plugins:
                print(f"   - {plugin_info.name}: {plugin_info.status.value}")
            
            # 查找TokenCounter插件
            token_counter = app.plugin_registry.get_plugin("tools.token_counter")
            if token_counter:
                print("   [OK] TokenCounter插件已加载")
                print(f"   状态: {token_counter.status.value}")
                print(f"   描述: {token_counter.metadata.description}")
            else:
                print("   [WARN] TokenCounter插件未找到")
        else:
            print("   [WARN] 插件注册表不可用")
        
        # 停止应用
        print("4. 停止应用...")
        app.stop()
        app.shutdown()
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 插件加载验证失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    print("小盘古4.0 系统验证")
    print("=" * 60)
    
    results = {}
    
    # 验证核心模块
    results['core'] = verify_core_modules()
    
    # 验证插件系统
    results['plugins'] = verify_plugin_system()
    
    # 验证UI系统
    results['ui'] = verify_ui_system()
    
    # 验证应用生命周期
    results['lifecycle'] = verify_app_lifecycle()
    
    # 验证插件加载
    results['plugin_loading'] = verify_plugin_loading()
    
    # 总结
    print("\n" + "=" * 60)
    print("验证结果汇总:")
    
    for name, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"  {status} {name}")
    
    total = len(results)
    passed = sum(results.values())
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n[SUCCESS] 所有验证通过！小盘古4.0系统工作正常。")
        return 0
    else:
        print("\n[FAIL] 部分验证失败，需要检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())