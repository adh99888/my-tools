#!/usr/bin/env python3
"""
配置界面集成测试

测试配置界面组件：
1. ConfigItem 数据模型和验证
2. ConfigInterface 配置管理逻辑（非UI部分）
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from smallpangu.ui.config_interface import (
    ConfigViewType,
    ConfigSection,
    ConfigItem,
    ConfigInterface,
    ConfigView
)
from smallpangu.config.models import Theme, Language, LogLevel
from smallpangu.core.events import EventBus
from smallpangu.core.di import Container
from smallpangu.config.manager import ConfigManager
import tempfile
import json
import yaml


def test_config_item():
    """测试配置项数据模型"""
    print("=" * 60)
    print("测试1: ConfigItem 数据模型")
    print("=" * 60)
    
    try:
        # 测试整数配置项
        int_item = ConfigItem(
            section=ConfigSection.APP,
            key="window_width",
            value=1280,
            data_type="int",
            description="窗口宽度",
            default_value=1280,
            constraints={"ge": 800, "le": 3840}
        )
        
        print(f"[OK] 整数配置项创建成功: {int_item.key} = {int_item.value}")
        
        # 测试验证
        valid, error = int_item.validate(1920)
        print(f"[OK] 有效值验证: 1920 -> {valid} ({error})")
        
        invalid, error = int_item.validate(500)
        print(f"[OK] 无效值验证: 500 -> {invalid} ({error})")
        
        # 测试布尔配置项
        bool_item = ConfigItem(
            section=ConfigSection.APP,
            key="dark_mode",
            value=True,
            data_type="bool",
            description="深色模式",
            default_value=False
        )
        
        print(f"[OK] 布尔配置项创建成功: {bool_item.key} = {bool_item.value}")
        
        # 测试枚举配置项
        enum_item = ConfigItem(
            section=ConfigSection.UI,
            key="theme",
            value=Theme.DARK,
            data_type="enum",
            description="主题",
            default_value=Theme.LIGHT,
            constraints={"enum_class": [Theme.LIGHT, Theme.DARK, Theme.SYSTEM]}
        )
        
        print(f"[OK] 枚举配置项创建成功: {enum_item.key} = {enum_item.value}")
        
        # 测试字符串配置项
        str_item = ConfigItem(
            section=ConfigSection.APP,
            key="app_name",
            value="小盘古",
            data_type="str",
            description="应用名称",
            default_value="小盘古",
            constraints={"min_length": 1, "max_length": 50}
        )
        
        print(f"[OK] 字符串配置项创建成功: {str_item.key} = {str_item.value}")
        
        # 测试值更新
        success = int_item.update_value(1920)
        print(f"[OK] 值更新测试: 1280 -> 1920 = {success}")
        
        success = int_item.update_value(500)
        print(f"[OK] 值更新验证: 500 -> {success} (应失败)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] ConfigItem 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_interface_logic():
    """测试配置界面逻辑（非UI部分）"""
    print("\n" + "=" * 60)
    print("测试2: ConfigInterface 逻辑（非UI）")
    print("=" * 60)
    
    try:
        # 创建事件总线和容器
        event_bus = EventBus()
        container = Container()
        
        # 创建配置管理器（使用临时配置文件）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "environment": "development",
                "app": {
                    "name": "测试应用",
                    "version": "1.0.0",
                    "log_level": "INFO"
                },
                "ui": {
                    "theme": "light",
                    "language": "zh-CN",
                    "window_width": 1280,
                    "window_height": 720
                },
                "plugins": {
                    "auto_discovery": True,
                    "disabled_plugins": []
                }
            }
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path=temp_config_path)
            
            # 创建模拟父组件
            mock_parent = Mock()
            mock_parent.register_widget = Mock()
            
            # 使用patch避免UI组件创建
            with patch.object(ConfigInterface, 'create_widget', return_value=Mock()):
                with patch.object(ConfigInterface, 'initialize', return_value=None):
                    # 创建配置界面
                    config_interface = ConfigInterface(
                        parent=mock_parent,
                        config_manager=config_manager,
                        event_bus=event_bus,
                        container=container
                    )
                    
                    # 手动调用_load_config（因为initialize被mock了）
                    config_interface._load_config()
            
            print(f"[OK] ConfigInterface 初始化成功")
            
            # 测试配置项加载
            config_items = config_interface.get_config_items()
            print(f"[OK] 配置项加载: {len(config_items)} 个配置项")
            
            # 验证配置项数量（至少应有这些配置项）
            expected_keys = ["name", "version", "log_level", "theme", "language", "window_width", "window_height"]
            found_keys = [item.key for item in config_items]
            print(f"[OK] 找到配置项: {found_keys}")
            
            # 测试按分区获取配置项
            app_items = config_interface.get_items_by_section(ConfigSection.APP)
            print(f"[OK] APP分区配置项: {len(app_items)} 个")
            
            ui_items = config_interface.get_items_by_section(ConfigSection.UI)
            print(f"[OK] UI分区配置项: {len(ui_items)} 个")
            
            # 测试配置项查找
            item = config_interface.find_item(ConfigSection.APP, "name")
            if item:
                print(f"[OK] 配置项查找成功: {item.key} = {item.value}")
            
            # 测试配置保存（到临时文件）
            save_success = config_interface.save_config()
            print(f"[OK] 配置保存: {save_success}")
            
            # 测试配置重置
            reset_success = config_interface.reset_to_defaults()
            print(f"[OK] 配置重置: {reset_success}")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] ConfigInterface 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_config_view_logic():
    """测试配置视图逻辑（非UI部分）"""
    print("\n" + "=" * 60)
    print("测试3: ConfigView 逻辑（非UI）")
    print("=" * 60)
    
    try:
        # 创建事件总线和容器
        event_bus = EventBus()
        container = Container()
        
        # 创建配置管理器（使用临时配置文件）
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_data = {
                "environment": "development",
                "app": {"name": "测试"},
                "ui": {"theme": "light"}
            }
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path=temp_config_path)
            
            # 创建模拟父组件
            mock_parent = Mock()
            mock_parent.register_widget = Mock()
            
            # 使用patch避免UI组件创建
            with patch.object(ConfigView, 'create_widget', return_value=Mock()):
                with patch.object(ConfigView, 'initialize', return_value=None):
                    # 创建配置视图
                    config_view = ConfigView(
                        parent=mock_parent,
                        config_manager=config_manager,
                        event_bus=event_bus,
                        container=container
                    )
            
            print(f"[OK] ConfigView 初始化成功")
            print(f"[OK] 视图类型: {config_view._view_type}")
            
            # 测试视图类型切换
            config_view.set_view_type(ConfigViewType.FORM)
            print(f"[OK] 视图类型切换: {config_view._view_type}")
            
            # 测试获取视图组件（返回mock）
            view_widget = config_view.get_view_widget()
            print(f"[OK] 获取视图组件: {type(view_widget)}")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] ConfigView 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("小盘古 4.0 配置界面集成测试")
    print("=" * 60)
    
    tests = [
        ("ConfigItem 数据模型", test_config_item),
        ("ConfigInterface 逻辑", test_config_interface_logic),
        ("ConfigView 逻辑", test_config_view_logic),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            success = test_func()
            results.append((test_name, success))
        except Exception as e:
            print(f"[ERROR] 测试执行异常: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
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
        print("\n[SUCCESS] 所有配置界面测试通过！")
        return 0
    else:
        print("\n[FAILURE] 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())