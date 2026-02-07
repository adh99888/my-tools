#!/usr/bin/env python3
"""
死亡开关集成测试
测试守护进程的基本功能
"""

import os
import sys
import json
import time

# 修复Windows控制台编码问题
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
import threading
from datetime import datetime, timedelta

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.守护者.death_switch import DeathSwitch
from src.守护者.heartbeat_monitor import HeartbeatMonitor
from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel

def test_heartbeat_monitor():
    """测试心跳监控器"""
    print("=== 测试心跳监控器 ===")
    
    # 创建监控器
    monitor = HeartbeatMonitor(
        heartbeat_file="test_integration_heartbeat.json",
        stats_file="test_integration_stats.json",
        max_age_sec=5.0
    )
    
    # 写入心跳
    success = monitor.write_heartbeat(
        pid=os.getpid(),
        system_status="testing",
        trust_score=99.5
    )
    assert success, "写入心跳失败"
    print("[OK] 心跳写入成功")
    
    # 检查心跳
    ok, error, age = monitor.check_heartbeat()
    assert ok, f"心跳检查失败: {error}"
    print(f"[OK] 心跳检查成功 (年龄: {age:.1f}秒)")
    
    # 获取统计
    stats = monitor.get_stats()
    assert stats.total_beats > 0, "统计信息不正确"
    print(f"[OK] 统计信息获取成功 (总心跳: {stats.total_beats})")
    
    # 清理
    if os.path.exists("test_integration_heartbeat.json"):
        os.remove("test_integration_heartbeat.json")
    if os.path.exists("test_integration_stats.json"):
        os.remove("test_integration_stats.json")
    
    print("心跳监控器测试通过\n")
    return True

def test_safety_mode_manager():
    """测试安全模式管理器"""
    print("=== 测试安全模式管理器 ===")
    
    # 创建管理器
    manager = SafetyModeManager(config_file="test_integration_safety_config.json")
    
    # 初始状态应该是正常模式
    assert not manager.is_in_safety_mode(), "初始状态应该是正常模式"
    print("[OK] 初始状态正常")
    
    # 进入安全模式
    success = manager.enter_safety_mode(SafetyModeLevel.SAFE)
    assert success, "进入安全模式失败"
    assert manager.is_in_safety_mode(), "应该在安全模式"
    print("[OK] 成功进入安全模式")
    
    # 测试功能检查
    assert manager.check_feature_allowed("heartbeat"), "心跳功能应该允许"
    assert not manager.check_feature_allowed("protocol_l3"), "L3协议应该禁止"
    print("[OK] 功能检查正确")
    
    # 退出安全模式
    success = manager.exit_safety_mode()
    assert success, "退出安全模式失败"
    assert not manager.is_in_safety_mode(), "应该退出安全模式"
    print("[OK] 成功退出安全模式")
    
    # 清理
    if os.path.exists("test_integration_safety_config.json"):
        os.remove("test_integration_safety_config.json")
    
    print("安全模式管理器测试通过\n")
    return True

def test_death_switch_basic():
    """测试死亡开关基本功能"""
    print("=== 测试死亡开关基本功能 ===")
    
    # 准备测试文件
    heartbeat_file = "test_integration_death_heartbeat.json"
    pid_file = "test_integration_death_pid.pid"
    
    # 写入初始心跳
    heartbeat_data = {
        "pid": os.getpid(),
        "timestamp": datetime.now().isoformat(),
        "system_status": "normal",
        "trust_score": 100.0,
        "checksum": ""
    }
    
    # 计算校验和
    data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
    import hashlib
    heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    with open(heartbeat_file, 'w', encoding='utf-8') as f:
        json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
    
    # 写入PID文件
    with open(pid_file, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    
    # 创建死亡开关（使用较短的检查间隔进行测试）
    death_switch = DeathSwitch(
        heartbeat_file=heartbeat_file,
        pid_file=pid_file,
        check_interval=2,  # 2秒检查间隔
        max_misses=2,      # 2次丢失就触发（4秒）
        log_dir="test_integration_logs"
    )
    
    # 启动死亡开关
    success = death_switch.start()
    assert success, "启动死亡开关失败"
    print("[OK] 死亡开关启动成功")
    
    # 等待3秒，系统应该正常
    time.sleep(3)
    assert death_switch.consecutive_misses == 0, "系统正常时不应该有连续丢失"
    print("[OK] 系统正常时监控正常")
    
    # 停止死亡开关
    death_switch.stop()
    print("[OK] 死亡开关停止成功")
    
    # 清理
    if os.path.exists(heartbeat_file):
        os.remove(heartbeat_file)
    if os.path.exists(pid_file):
        os.remove(pid_file)
    if os.path.exists("test_integration_logs"):
        import shutil
        shutil.rmtree("test_integration_logs")
    
    print("死亡开关基本功能测试通过\n")
    return True

def test_heartbeat_timeout():
    """测试心跳超时检测"""
    print("=== 测试心跳超时检测 ===")
    
    heartbeat_file = "test_timeout_heartbeat.json"
    pid_file = "test_timeout_pid.pid"
    
    # 写入过时的心跳（10分钟前）
    old_time = datetime.now() - timedelta(minutes=10)
    heartbeat_data = {
        "pid": os.getpid(),
        "timestamp": old_time.isoformat(),
        "system_status": "stale",
        "trust_score": 100.0,
        "checksum": ""
    }
    
    # 计算校验和
    data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
    import hashlib
    heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    with open(heartbeat_file, 'w', encoding='utf-8') as f:
        json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
    
    # 写入PID文件
    with open(pid_file, 'w', encoding='utf-8') as f:
        f.write(str(os.getpid()))
    
    # 创建死亡开关
    death_switch = DeathSwitch(
        heartbeat_file=heartbeat_file,
        pid_file=pid_file,
        check_interval=1,  # 1秒检查间隔
        max_misses=1,      # 1次丢失就触发
        log_dir="test_timeout_logs"
    )
    
    # 手动检查心跳（不启动守护进程）
    heartbeat_ok = death_switch._check_heartbeat()
    assert not heartbeat_ok, "过时心跳应该被检测到"
    print("[OK] 心跳超时检测正确")
    
    # 清理
    if os.path.exists(heartbeat_file):
        os.remove(heartbeat_file)
    if os.path.exists(pid_file):
        os.remove(pid_file)
    
    print("心跳超时检测测试通过\n")
    return True

def main():
    """主测试函数"""
    print("开始死亡开关集成测试...\n")
    
    tests = [
        test_heartbeat_monitor,
        test_safety_mode_manager,
        test_death_switch_basic,
        test_heartbeat_timeout
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
            print()
    
    print("="*60)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有集成测试通过！")
        return True
    else:
        print("[FAILED] 部分测试失败")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)