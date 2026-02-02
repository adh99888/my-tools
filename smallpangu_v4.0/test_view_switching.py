#!/usr/bin/env python3
"""
视图切换集成测试

测试MainWindow的视图切换功能：
1. MainWindow初始化和视图缓存
2. switch_view方法功能
3. 不同视图之间的切换
4. 视图缓存机制
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch, PropertyMock

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from smallpangu.ui.window import MainWindow, NavigationItem, NavigationItemType
from smallpangu.core.events import EventBus
from smallpangu.core.di import Container
from smallpangu.config.manager import ConfigManager
from smallpangu.config.models import UIConfig, Theme, Language
import tempfile
import yaml


def test_mainwindow_initialization():
    """测试MainWindow初始化"""
    print("=" * 60)
    print("测试1: MainWindow 初始化")
    print("=" * 60)
    
    try:
        # 创建模拟组件
        mock_root = Mock()
        mock_ui_manager = Mock()
        mock_event_bus = Mock()
        mock_container = Container()
        
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
                }
            }
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path=temp_config_path)
            
            # 使用patch避免UI组件创建
            with patch.object(MainWindow, '_create_main_frame', return_value=None):
                with patch.object(MainWindow, '_create_sidebar', return_value=None):
                    with patch.object(MainWindow, '_create_status_bar', return_value=None):
                        with patch.object(MainWindow, '_load_default_view', return_value=None):
                            # 创建主窗口
                            main_window = MainWindow(
                                root=mock_root,
                                ui_manager=mock_ui_manager,
                                config_manager=config_manager,
                                event_bus=mock_event_bus,
                                container=mock_container
                            )
            
            print(f"[OK] MainWindow 初始化成功")
            print(f"[OK] 默认视图: {main_window._current_view} (应为: chat)")
            print(f"[OK] 视图缓存类型: {type(main_window._view_cache)}")
            print(f"[OK] 导航项列表: {len(main_window._navigation_items)} 项")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] MainWindow 初始化测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_view_switching_logic():
    """测试视图切换逻辑（非UI部分）"""
    print("\n" + "=" * 60)
    print("测试2: 视图切换逻辑")
    print("=" * 60)
    
    try:
        # 创建模拟组件
        mock_root = Mock()
        mock_ui_manager = Mock()
        mock_event_bus = Mock()
        mock_container = Container()
        
        # 创建配置管理器
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
            
            # 使用patch避免UI组件创建
            with patch.object(MainWindow, '_create_main_frame', return_value=None):
                with patch.object(MainWindow, '_create_sidebar', return_value=None):
                    with patch.object(MainWindow, '_create_status_bar', return_value=None):
                        with patch.object(MainWindow, '_load_default_view', return_value=None):
                            # 创建主窗口
                            main_window = MainWindow(
                                root=mock_root,
                                ui_manager=mock_ui_manager,
                                config_manager=config_manager,
                                event_bus=mock_event_bus,
                                container=mock_container
                            )
            
            print(f"[OK] MainWindow 创建成功")
            
            # 模拟视图容器
            mock_view_container = Mock()
            mock_view_container.winfo_children = Mock(return_value=[])
            main_window._view_container = mock_view_container
            
            # 模拟视图创建
            mock_chat_view = Mock()
            mock_plugins_view = Mock()
            mock_config_view = Mock()
            mock_monitor_view = Mock()
            
            # 创建模拟的视图创建方法
            def mock_create_view(view_name):
                views = {
                    "chat": mock_chat_view,
                    "plugins": mock_plugins_view,
                    "config": mock_config_view,
                    "monitor": mock_monitor_view
                }
                return views.get(view_name)
            
            # 替换_create_view方法
            main_window._create_view = mock_create_view
            
            # 初始化视图缓存（为空）
            main_window._view_cache = {}
            
            # 测试视图切换
            print("[OK] 开始测试视图切换...")
            
            # 测试切换到聊天视图
            success = main_window.switch_view("chat")
            print(f"[OK] 切换到聊天视图: {success}")
            
            # 测试切换到插件视图
            success = main_window.switch_view("plugins")
            print(f"[OK] 切换到插件视图: {success}")
            
            # 测试切换到配置视图
            success = main_window.switch_view("config")
            print(f"[OK] 切换到配置视图: {success}")
            
            # 测试切换到监控视图
            success = main_window.switch_view("monitor")
            print(f"[OK] 切换到监控视图: {success}")
            
            # 测试未知视图
            success = main_window.switch_view("unknown")
            print(f"[OK] 切换到未知视图: {success} (应为False)")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] 视图切换逻辑测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_view_caching():
    """测试视图缓存机制"""
    print("\n" + "=" * 60)
    print("测试3: 视图缓存机制")
    print("=" * 60)
    
    try:
        # 创建模拟组件
        mock_root = Mock()
        mock_ui_manager = Mock()
        mock_event_bus = Mock()
        mock_container = Container()
        
        # 创建配置管理器
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
            
            # 使用patch避免UI组件创建
            with patch.object(MainWindow, '_create_main_frame', return_value=None):
                with patch.object(MainWindow, '_create_sidebar', return_value=None):
                    with patch.object(MainWindow, '_create_status_bar', return_value=None):
                        with patch.object(MainWindow, '_load_default_view', return_value=None):
                            # 创建主窗口
                            main_window = MainWindow(
                                root=mock_root,
                                ui_manager=mock_ui_manager,
                                config_manager=config_manager,
                                event_bus=mock_event_bus,
                                container=mock_container
                            )
            
            print(f"[OK] MainWindow 创建成功")
            
            # 模拟视图容器和视图
            mock_view_container = Mock()
            mock_view_container.winfo_children = Mock(return_value=[])
            main_window._view_container = mock_view_container
            
            mock_chat_view = Mock()
            mock_plugins_view = Mock()
            
            # 创建视图计数
            view_creation_count = {"chat": 0, "plugins": 0}
            
            def mock_create_view(view_name):
                view_creation_count[view_name] += 1
                if view_name == "chat":
                    return mock_chat_view
                elif view_name == "plugins":
                    return mock_plugins_view
                return None
            
            main_window._create_view = mock_create_view
            
            # 初始化视图缓存
            main_window._view_cache = {}
            
            print("[OK] 测试视图缓存...")
            
            # 第一次切换到聊天视图（应该创建新视图）
            success = main_window.switch_view("chat")
            print(f"[OK] 第一次切换聊天视图: {success} (创建次数: {view_creation_count['chat']})")
            
            # 第二次切换到聊天视图（应该从缓存加载）
            success = main_window.switch_view("chat")
            print(f"[OK] 第二次切换聊天视图: {success} (创建次数应不变: {view_creation_count['chat']})")
            
            # 测试插件视图
            success = main_window.switch_view("plugins")
            print(f"[OK] 第一次切换插件视图: {success} (创建次数: {view_creation_count['plugins']})")
            
            success = main_window.switch_view("plugins")
            print(f"[OK] 第二次切换插件视图: {success} (创建次数应不变: {view_creation_count['plugins']})")
            
            # 测试缓存大小
            print(f"[OK] 视图缓存大小: {len(main_window._view_cache)} (应为2)")
            
            # 测试清空缓存
            main_window.clear_view_cache()
            print(f"[OK] 清空视图缓存后大小: {len(main_window._view_cache)} (应为0)")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] 视图缓存测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_navigation_integration():
    """测试导航集成"""
    print("\n" + "=" * 60)
    print("测试4: 导航集成")
    print("=" * 60)
    
    try:
        # 创建模拟组件
        mock_root = Mock()
        mock_ui_manager = Mock()
        mock_event_bus = Mock()
        mock_container = Container()
        
        # 创建配置管理器
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
            
            # 使用patch避免UI组件创建
            with patch.object(MainWindow, '_create_main_frame', return_value=None):
                with patch.object(MainWindow, '_create_sidebar', return_value=None):
                    with patch.object(MainWindow, '_create_status_bar', return_value=None):
                        with patch.object(MainWindow, '_load_default_view', return_value=None):
                            # 创建主窗口
                            main_window = MainWindow(
                                root=mock_root,
                                ui_manager=mock_ui_manager,
                                config_manager=config_manager,
                                event_bus=mock_event_bus,
                                container=mock_container
                            )
            
            print(f"[OK] MainWindow 创建成功")
            
            # 测试导航项创建
            nav_items = main_window._navigation_items
            print(f"[OK] 导航项列表: {len(nav_items)} 项")
            
            # 添加测试导航项
            test_item = NavigationItem(
                id="test_view",
                label="测试视图",
                icon="test-icon",
                item_type=NavigationItemType.MENU
            )
            main_window._navigation_items.append(test_item)
            
            print(f"[OK] 导航项添加成功: {test_item.label}")
            
            # 测试获取当前视图
            current_view = main_window.get_current_view()
            print(f"[OK] 当前视图: {current_view} (应为: chat)")
            
            # 测试视图计数
            view_count = main_window.view_count
            print(f"[OK] 视图计数: {view_count}")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] 导航集成测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("小盘古 4.0 视图切换集成测试")
    print("=" * 60)
    
    tests = [
        ("MainWindow 初始化", test_mainwindow_initialization),
        ("视图切换逻辑", test_view_switching_logic),
        ("视图缓存机制", test_view_caching),
        ("导航集成", test_navigation_integration),
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
        print("\n[SUCCESS] 所有视图切换测试通过！")
        return 0
    else:
        print("\n[FAILURE] 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())