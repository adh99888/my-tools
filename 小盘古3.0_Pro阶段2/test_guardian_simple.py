#!/usr/bin/env python3
"""
守护者模块简单验证测试
宪法依据：宪法第4条（生存优先原则）
目的：验证守护者模块基本功能，避免复杂集成测试可能的问题
"""

import os
import sys
import json
import time
from datetime import datetime

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_death_switch_import():
    """测试DeathSwitch导入和基本功能"""
    print("=== 测试DeathSwitch导入 ===")
    try:
        from src.守护者.death_switch import DeathSwitch
        print("[OK] DeathSwitch导入成功")
        
        # 创建实例
        ds = DeathSwitch(
            heartbeat_file="test_simple_heartbeat.json",
            pid_file="test_simple_pid.pid",
            check_interval=1,
            max_misses=2
        )
        print("[OK] DeathSwitch实例创建成功")
        
        # 检查属性
        assert hasattr(ds, 'start'), "缺少start方法"
        assert hasattr(ds, 'stop'), "缺少stop方法"
        assert hasattr(ds, '_check_system'), "缺少_check_system方法"
        print("[OK] DeathSwitch基本方法存在")
        
        # 清理测试文件
        if os.path.exists("test_simple_heartbeat.json"):
            os.remove("test_simple_heartbeat.json")
        if os.path.exists("test_simple_pid.pid"):
            os.remove("test_simple_pid.pid")
            
        print("DeathSwitch导入测试通过\n")
        return True
    except Exception as e:
        print(f"[ERROR] DeathSwitch导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_heartbeat_monitor_import():
    """测试HeartbeatMonitor导入和基本功能"""
    print("=== 测试HeartbeatMonitor导入 ===")
    try:
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        print("[OK] HeartbeatMonitor导入成功")
        
        # 创建实例
        hm = HeartbeatMonitor(
            heartbeat_file="test_simple_heartbeat2.json",
            stats_file="test_simple_stats.json",
            max_age_sec=30.0
        )
        print("[OK] HeartbeatMonitor实例创建成功")
        
        # 检查属性
        assert hasattr(hm, 'write_heartbeat'), "缺少write_heartbeat方法"
        assert hasattr(hm, 'check_heartbeat'), "缺少check_heartbeat方法"
        assert hasattr(hm, 'get_stats'), "缺少get_stats方法"
        print("[OK] HeartbeatMonitor基本方法存在")
        
        # 清理测试文件
        if os.path.exists("test_simple_heartbeat2.json"):
            os.remove("test_simple_heartbeat2.json")
        if os.path.exists("test_simple_stats.json"):
            os.remove("test_simple_stats.json")
            
        print("HeartbeatMonitor导入测试通过\n")
        return True
    except Exception as e:
        print(f"[ERROR] HeartbeatMonitor导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safety_mode_import():
    """测试SafetyMode导入和基本功能"""
    print("=== 测试SafetyMode导入 ===")
    try:
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        print("[OK] SafetyModeManager导入成功")
        print("[OK] SafetyModeLevel导入成功")
        
        # 创建实例
        sm = SafetyModeManager(config_file="test_simple_safety_config.json")
        print("[OK] SafetyModeManager实例创建成功")
        
        # 检查属性
        assert hasattr(sm, 'enter_safety_mode'), "缺少enter_safety_mode方法"
        assert hasattr(sm, 'exit_safety_mode'), "缺少exit_safety_mode方法"
        assert hasattr(sm, 'is_in_safety_mode'), "缺少is_in_safety_mode方法"
        print("[OK] SafetyModeManager基本方法存在")
        
        # 检查枚举值
        assert hasattr(SafetyModeLevel, 'NORMAL'), "缺少NORMAL枚举值"
        assert hasattr(SafetyModeLevel, 'DEGRADED'), "缺少DEGRADED枚举值"
        assert hasattr(SafetyModeLevel, 'SAFE'), "缺少SAFE枚举值"
        assert hasattr(SafetyModeLevel, 'LOCKDOWN'), "缺少LOCKDOWN枚举值"
        print("[OK] SafetyModeLevel枚举值存在")
        
        # 清理测试文件
        if os.path.exists("test_simple_safety_config.json"):
            os.remove("test_simple_safety_config.json")
            
        print("SafetyMode导入测试通过\n")
        return True
    except Exception as e:
        print(f"[ERROR] SafetyMode导入测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_basic_functionality():
    """测试基本功能（不涉及文件操作）"""
    print("=== 测试基本功能 ===")
    try:
        # 测试datetime使用（基础依赖）
        now = datetime.now()
        print(f"[OK] datetime.now() 正常工作: {now}")
        
        # 测试json序列化
        test_data = {"test": True, "timestamp": now.isoformat()}
        json_str = json.dumps(test_data)
        loaded = json.loads(json_str)
        assert loaded["test"] == True, "JSON序列化/反序列化失败"
        print("[OK] JSON序列化/反序列化正常")
        
        print("基本功能测试通过\n")
        return True
    except Exception as e:
        print(f"[ERROR] 基本功能测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始守护者模块简单验证测试...\n")
    
    tests = [
        test_basic_functionality,
        test_death_switch_import,
        test_heartbeat_monitor_import,
        test_safety_mode_import
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"测试异常: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    
    print("="*60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有简单验证测试通过！")
        return True
    else:
        print("[WARNING] 部分测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)