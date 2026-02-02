#!/usr/bin/env python3
"""
UI框架集成测试

测试UI框架的各个组件能否正确导入和初始化。
"""

import sys
import os
import tempfile
import shutil
from pathlib import Path

# 添加src目录到Python路径
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_ui_imports():
    """测试UI模块导入"""
    print("=== UI模块导入测试 ===")
    
    try:
        # 1. 导入UI管理器
        from smallpangu.ui.manager import UIManager
        print("[OK] UIManager导入成功")
        
        # 2. 导入窗口模块
        from smallpangu.ui.window import BaseWindow, MainWindow
        print("[OK] Window模块导入成功")
        
        # 3. 导入组件模块
        from smallpangu.ui.widgets import BaseWidget, Panel, Button, Label, InputField
        print("[OK] Widgets模块导入成功")
        
        # 4. 导入主题管理器
        from smallpangu.ui.theme import ThemeManager
        print("[OK] ThemeManager导入成功")
        
        # 5. 导入国际化管理器
        from smallpangu.ui.i18n import I18nManager, Language, TextDomain
        print("[OK] I18nManager导入成功")
        
        # 6. 验证枚举
        print(f"[OK] 语言枚举: {Language.ZH_CN}, {Language.EN_US}")
        print(f"[OK] 文本域枚举: {TextDomain.UI}, {TextDomain.ERROR}")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 其他错误: {e}")
        return False

def test_ui_module_structure():
    """测试UI模块结构"""
    print("\n=== UI模块结构测试 ===")
    
    try:
        # 检查__init__.py导出
        from smallpangu.ui import (
            UIManager, BaseWindow, MainWindow, BaseWidget,
            Panel, Card, Button, Label, TextArea,
            ThemeManager, I18nManager
        )
        print("[OK] __init__.py导出正确")
        
        # 验证类型
        print(f"[OK] UIManager类型: {type(UIManager)}")
        print(f"[OK] MainWindow类型: {type(MainWindow)}")
        print(f"[OK] Button类型: {type(Button)}")
        print(f"[OK] ThemeManager类型: {type(ThemeManager)}")
        print(f"[OK] I18nManager类型: {type(I18nManager)}")
        
        return True
        
    except ImportError as e:
        print(f"[ERROR] 导入失败: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] 其他错误: {e}")
        return False

def test_widget_classes():
    """测试组件类功能"""
    print("\n=== 组件类功能测试 ===")
    
    try:
        from smallpangu.ui.widgets import WidgetStyle, WidgetState, Alignment
        
        # 测试WidgetStyle
        style = WidgetStyle(
            bg_color="#ffffff",
            fg_color="#000000",
            font_size=12,
            corner_radius=5
        )
        print(f"[OK] WidgetStyle创建成功: {style}")
        
        # 测试样式转换
        style_dict = style.to_dict()
        print(f"[OK] WidgetStyle转换为字典: {len(style_dict)}个属性")
        
        # 测试样式合并
        style2 = WidgetStyle(font_size=14, padding=10)
        merged = style.merge(style2)
        print(f"[OK] WidgetStyle合并成功")
        
        # 测试枚举
        print(f"[OK] WidgetState枚举: {WidgetState.NORMAL}, {WidgetState.DISABLED}")
        print(f"[OK] Alignment枚举: {Alignment.LEFT}, {Alignment.CENTER}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 组件类测试失败: {e}")
        return False

def test_i18n_functionality():
    """测试国际化功能"""
    print("\n=== 国际化功能测试 ===")
    
    try:
        from smallpangu.ui.i18n import Translation, Language, TextDomain
        
        # 测试Translation类
        trans = Translation(
            key="app.title",
            text="小盘古 AI 助手",
            domain=TextDomain.UI
        )
        print(f"[OK] Translation创建成功: {trans.key} -> {trans.text}")
        
        # 测试Language枚举
        print(f"[OK] 支持的语言: {list(Language)}")
        
        # 测试TextDomain枚举
        print(f"[OK] 文本域: {list(TextDomain)}")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] 国际化测试失败: {e}")
        return False

def test_ui_config_integration():
    """测试UI配置集成"""
    print("\n=== UI配置集成测试 ===")
    
    try:
        from smallpangu.config.models import UIConfig, Theme, Language
        from pydantic import ValidationError
        
        # 测试UI配置模型
        ui_config = UIConfig(
            theme=Theme.DARK,
            language=Language.ZH_CN,
            window_width=1280,
            window_height=720,
            font_family="Microsoft YaHei",
            font_size=12
        )
        
        print(f"[OK] UIConfig创建成功")
        print(f"  - 主题: {ui_config.theme}")
        print(f"  - 语言: {ui_config.language}")
        print(f"  - 窗口尺寸: {ui_config.window_width}x{ui_config.window_height}")
        print(f"  - 字体: {ui_config.font_family} {ui_config.font_size}px")
        
        # 测试配置验证
        try:
            invalid_config = UIConfig(window_width=100)  # 小于最小值
            print("[ERROR] 配置验证应该失败")
            return False
        except ValidationError:
            print("[OK] 配置验证正常工作（捕获无效值）")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] UI配置测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("小盘古 4.0 UI框架集成测试")
    print("=" * 50)
    
    tests = [
        ("UI模块导入", test_ui_imports),
        ("UI模块结构", test_ui_module_structure),
        ("组件类功能", test_widget_classes),
        ("国际化功能", test_i18n_functionality),
        ("UI配置集成", test_ui_config_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[ERROR] 测试执行异常: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("测试结果汇总:")
    
    passed = 0
    total = len(results)
    
    for test_name, success in results:
        status = "[PASS]" if success else "[FAIL]"
        print(f"  {status} {test_name}")
        if success:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 通过 ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n[SUCCESS] 所有UI框架测试通过！")
        return 0
    else:
        print("\n[FAILURE] 部分测试失败，请检查问题")
        return 1

if __name__ == "__main__":
    sys.exit(main())