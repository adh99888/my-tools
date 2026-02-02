#!/usr/bin/env python3
"""
监控界面集成测试

测试监控界面组件：
1. MetricData 数据模型
2. MonitorInterface 监控逻辑（非UI部分）
"""

import sys
import os
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# 添加项目路径到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from smallpangu.ui.monitor_interface import (
    MonitorViewType,
    MetricType,
    MetricData,
    MonitorInterface,
    MonitorView
)
from smallpangu.core.events import EventBus
from smallpangu.core.di import Container
from smallpangu.config.manager import ConfigManager
import tempfile
import yaml
import time


def test_metric_data():
    """测试指标数据模型"""
    print("=" * 60)
    print("测试1: MetricData 数据模型")
    print("=" * 60)
    
    try:
        # 测试CPU使用率指标
        cpu_metric = MetricData(
            metric_type=MetricType.CPU_USAGE,
            value=45.5,
            unit="%",
            timestamp=time.time(),
            label="CPU使用率",
            description="当前CPU使用率",
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        
        print(f"[OK] CPU指标创建成功: {cpu_metric.label} = {cpu_metric.value}{cpu_metric.unit}")
        print(f"[OK] 状态颜色: {cpu_metric.get_status_color()}")
        print(f"[OK] 显示值: {cpu_metric.get_display_value()}")
        
        # 测试内存使用指标
        memory_metric = MetricData(
            metric_type=MetricType.MEMORY_USAGE,
            value=2048.0,  # MB
            unit="MB",
            timestamp=time.time(),
            label="内存使用",
            description="当前内存使用量",
            threshold_warning=8192.0,  # 8GB
            threshold_critical=16384.0  # 16GB
        )
        
        print(f"[OK] 内存指标创建成功: {memory_metric.label} = {memory_metric.value}{memory_metric.unit}")
        print(f"[OK] 显示值: {memory_metric.get_display_value()}")
        
        # 测试阈值检查
        high_cpu = MetricData(
            metric_type=MetricType.CPU_USAGE,
            value=90.0,
            unit="%",
            timestamp=time.time(),
            label="高CPU",
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        
        print(f"[OK] 高CPU状态颜色: {high_cpu.get_status_color()} (应warning)")
        
        critical_cpu = MetricData(
            metric_type=MetricType.CPU_USAGE,
            value=98.0,
            unit="%",
            timestamp=time.time(),
            label="临界CPU",
            threshold_warning=80.0,
            threshold_critical=95.0
        )
        
        print(f"[OK] 临界CPU状态颜色: {critical_cpu.get_status_color()} (应critical)")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] MetricData 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitor_interface_logic():
    """测试监控界面逻辑（非UI部分）"""
    print("\n" + "=" * 60)
    print("测试2: MonitorInterface 逻辑（非UI）")
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
                "metrics": {
                    "enabled": True,
                    "collection_interval": 5,
                    "retention_days": 30
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
            with patch.object(MonitorInterface, 'create_widget', return_value=Mock()):
                with patch.object(MonitorInterface, 'initialize', return_value=None):
                    # 创建监控界面
                    monitor_interface = MonitorInterface(
                        parent=mock_parent,
                        config_manager=config_manager,
                        event_bus=event_bus,
                        container=container
                    )
            
            print(f"[OK] MonitorInterface 初始化成功")
            
            # 测试指标收集（模拟）
            metrics = monitor_interface.collect_metrics()
            print(f"[OK] 指标收集: {len(metrics)} 个指标")
            
            # 测试指标更新
            monitor_interface.update_metrics()
            print(f"[OK] 指标更新完成")
            
            # 测试视图切换
            monitor_interface.set_view_type(MonitorViewType.RESOURCES)
            print(f"[OK] 视图类型切换: {monitor_interface._view_type}")
            
            # 测试获取当前指标
            current_metrics = monitor_interface.get_current_metrics()
            print(f"[OK] 当前指标获取: {len(current_metrics)} 个指标")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] MonitorInterface 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_monitor_view_logic():
    """测试监控视图逻辑（非UI部分）"""
    print("\n" + "=" * 60)
    print("测试3: MonitorView 逻辑（非UI）")
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
                "metrics": {"enabled": True}
            }
            yaml.dump(config_data, f)
            temp_config_path = f.name
        
        try:
            config_manager = ConfigManager(config_path=temp_config_path)
            
            # 创建模拟父组件
            mock_parent = Mock()
            mock_parent.register_widget = Mock()
            
            # 使用patch避免UI组件创建
            with patch.object(MonitorView, 'create_widget', return_value=Mock()):
                with patch.object(MonitorView, 'initialize', return_value=None):
                    # 创建监控视图
                    monitor_view = MonitorView(
                        parent=mock_parent,
                        config_manager=config_manager,
                        event_bus=event_bus,
                        container=container
                    )
            
            print(f"[OK] MonitorView 初始化成功")
            print(f"[OK] 视图类型: {monitor_view._view_type}")
            
            # 测试视图类型切换
            monitor_view.set_view_type(MonitorViewType.PLUGINS)
            print(f"[OK] 视图类型切换: {monitor_view._view_type}")
            
            # 测试获取视图组件（返回mock）
            view_widget = monitor_view.get_view_widget()
            print(f"[OK] 获取视图组件: {type(view_widget)}")
            
            return True
            
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_config_path)
            except:
                pass
                
    except Exception as e:
        print(f"[FAIL] MonitorView 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主测试函数"""
    print("小盘古 4.0 监控界面集成测试")
    print("=" * 60)
    

    
    tests = [
        ("MetricData 数据模型", test_metric_data),
        ("MonitorInterface 逻辑", test_monitor_interface_logic),
        ("MonitorView 逻辑", test_monitor_view_logic),
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
        print("\n[SUCCESS] 所有监控界面测试通过！")
        return 0
    else:
        print("\n[FAILURE] 部分测试失败，请检查问题")
        return 1


if __name__ == "__main__":
    sys.exit(main())