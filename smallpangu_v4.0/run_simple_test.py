#!/usr/bin/env python3
"""
小盘古4.0简单运行测试
测试应用是否能正常启动和运行
"""

import sys
import os
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_simple_run():
    """简单运行测试"""
    print("=== 简单运行测试 ===")
    
    try:
        # 1. 导入核心模块
        print("1. 导入核心模块...")
        from smallpangu.app import create_app
        print("   [OK] 应用模块导入成功")
        
        # 2. 创建应用实例
        print("2. 创建应用实例...")
        app = create_app()
        print("   [OK] 应用实例创建成功")
        
        # 3. 初始化应用
        print("3. 初始化应用...")
        app.initialize()
        print("   [OK] 应用初始化成功")
        
        # 4. 启动应用
        print("4. 启动应用...")
        app.start()
        print("   [OK] 应用启动成功")
        
        # 5. 检查应用状态
        print("5. 检查应用状态...")
        status = app.get_status()
        print(f"   应用状态: 初始化={status['initialized']}, 运行={status['running']}")
        print(f"   环境: {status.get('config', {}).get('environment', '未知')}")
        print(f"   插件: {status.get('plugins', {}).get('total', 0)} 个")
        
        # 6. 运行一小段时间
        print("6. 运行应用（3秒）...")
        import time
        start_time = time.time()
        
        # 简单运行循环
        for i in range(6):  # 运行6个0.5秒周期，总共3秒
            if not app.is_running:
                break
            time.sleep(0.5)
            uptime = app.uptime or 0
            print(f"   运行时间: {uptime:.1f} 秒")
        
        # 7. 停止应用
        print("7. 停止应用...")
        app.stop()
        print("   [OK] 应用停止成功")
        
        # 8. 关闭应用
        print("8. 关闭应用...")
        app.shutdown()
        print("   [OK] 应用关闭成功")
        
        print("\n[SUCCESS] 简单运行测试完成！")
        return True
        
    except Exception as e:
        print(f"\n[FAIL] 简单运行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_ui_import():
    """测试UI模块导入"""
    print("\n=== UI模块导入测试 ===")
    
    try:
        # 导入UI模块
        print("1. 导入UI管理器...")
        from smallpangu.ui.manager import UIManager, create_ui_manager
        print("   [OK] UI管理器导入成功")
        
        print("2. 导入主题管理器...")
        from smallpangu.ui.theme import ThemeManager, Theme
        print("   [OK] 主题管理器导入成功")
        
        print("3. 导入国际化管理器...")
        from smallpangu.ui.i18n import I18nManager, Language, TextDomain
        print("   [OK] 国际化管理器导入成功")
        
        print("4. 导入主窗口...")
        from smallpangu.ui.window import BaseWindow, MainWindow
        print("   [OK] 主窗口导入成功")
        
        print("5. 导入界面组件...")
        from smallpangu.ui.chat_interface import ChatInterface, ChatView
        from smallpangu.ui.plugin_interface import PluginInterface, PluginView
        from smallpangu.ui.config_interface import ConfigInterface, ConfigView
        from smallpangu.ui.monitor_interface import MonitorInterface, MonitorView
        from smallpangu.ui.help_interface import HelpInterface, HelpView
        from smallpangu.ui.settings_interface import SettingsInterface, SettingsView
        print("   [OK] 所有界面组件导入成功")
        
        print("\n[SUCCESS] UI模块导入测试完成！")
        print(f"   - 主题: {Theme.LIGHT.value}, {Theme.DARK.value}, {Theme.SYSTEM.value}")
        print(f"   - 语言: {Language.ZH_CN.value}, {Language.EN_US.value}")
        print(f"   - 文本域: {TextDomain.UI.value}, {TextDomain.ERROR.value}")
        
        return True
        
    except Exception as e:
        print(f"\n[FAIL] UI模块导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("小盘古4.0简单运行测试")
    print("=" * 60)
    
    success_count = 0
    total_tests = 2
    
    # 测试1: 简单运行
    if test_simple_run():
        success_count += 1
    
    # 测试2: UI模块导入
    if test_ui_import():
        success_count += 1
    
    print("\n" + "=" * 60)
    print(f"测试结果: {success_count}/{total_tests} 通过")
    
    if success_count == total_tests:
        print("\n[SUCCESS] 所有测试通过！小盘古4.0可以正常运行。")
        return 0
    else:
        print("\n[FAIL] 部分测试失败，需要检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(main())