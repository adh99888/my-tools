#!/usr/bin/env python3
"""
守护者模块诊断脚本
目的：诊断test_death_switch_integration.py失败原因
"""

import os
import sys
import json
import time
import signal
import threading
from datetime import datetime, timedelta

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=== 守护者模块诊断开始 ===")
print(f"Python版本: {sys.version}")
print(f"平台: {sys.platform}")
print(f"工作目录: {os.getcwd()}")
print()

def test_os_kill():
    """测试os.kill在Windows上的行为"""
    print("=== 测试os.kill(pid, 0) ===")
    try:
        current_pid = os.getpid()
        print(f"当前PID: {current_pid}")
        os.kill(current_pid, 0)
        print("[OK] os.kill(pid, 0) 工作正常")
        return True
    except Exception as e:
        print(f"[ERROR] os.kill(pid, 0) 失败: {type(e).__name__}: {e}")
        return False

def test_signal_constants():
    """测试信号常量是否存在"""
    print("\n=== 测试信号常量 ===")
    try:
        print(f"SIGTERM: {hasattr(signal, 'SIGTERM')}")
        if hasattr(signal, 'SIGTERM'):
            print(f"  value: {signal.SIGTERM}")
        print(f"SIGKILL: {hasattr(signal, 'SIGKILL')}")
        if hasattr(signal, 'SIGKILL'):
            print(f"  value: {signal.SIGKILL}")
        return True
    except Exception as e:
        print(f"[ERROR] 测试信号常量失败: {e}")
        return False

def test_heartbeat_monitor():
    """测试心跳监控器"""
    print("\n=== 测试心跳监控器 ===")
    try:
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        
        monitor = HeartbeatMonitor(
            heartbeat_file="test_diagnostic_heartbeat.json",
            stats_file="test_diagnostic_stats.json",
            max_age_sec=5.0
        )
        
        # 写入心跳
        success = monitor.write_heartbeat(
            pid=os.getpid(),
            system_status="testing",
            trust_score=99.5
        )
        print(f"写入心跳结果: {success}")
        
        # 检查心跳
        ok, error, age = monitor.check_heartbeat()
        print(f"检查心跳: ok={ok}, error={error}, age={age:.1f}s")
        
        # 获取统计
        stats = monitor.get_stats()
        print(f"统计信息: total_beats={stats.total_beats}")
        
        # 清理
        if os.path.exists("test_diagnostic_heartbeat.json"):
            os.remove("test_diagnostic_heartbeat.json")
        if os.path.exists("test_diagnostic_stats.json"):
            os.remove("test_diagnostic_stats.json")
            
        print("[OK] 心跳监控器测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 心跳监控器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_safety_mode():
    """测试安全模式管理器"""
    print("\n=== 测试安全模式管理器 ===")
    try:
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        
        manager = SafetyModeManager(config_file="test_diagnostic_safety_config.json")
        
        print(f"初始状态: {manager.is_in_safety_mode()}")
        
        # 进入安全模式
        success = manager.enter_safety_mode(SafetyModeLevel.SAFE)
        print(f"进入安全模式: {success}")
        print(f"安全模式状态: {manager.is_in_safety_mode()}")
        
        # 退出安全模式
        success = manager.exit_safety_mode()
        print(f"退出安全模式: {success}")
        print(f"最终状态: {manager.is_in_safety_mode()}")
        
        # 清理
        if os.path.exists("test_diagnostic_safety_config.json"):
            os.remove("test_diagnostic_safety_config.json")
            
        print("[OK] 安全模式管理器测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 安全模式管理器测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_death_switch_check_process():
    """测试死亡开关的进程检查"""
    print("\n=== 测试死亡开关进程检查 ===")
    try:
        from src.守护者.death_switch import DeathSwitch
        
        # 创建PID文件
        pid_file = "test_diagnostic_pid.pid"
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        
        # 创建死亡开关实例（不启动线程）
        death_switch = DeathSwitch(
            heartbeat_file="test_diagnostic_heartbeat2.json",
            pid_file=pid_file,
            check_interval=60,  # 长间隔，避免触发
            max_misses=10
        )
        
        # 直接调用_check_process
        result = death_switch._check_process()
        print(f"_check_process() 结果: {result}")
        
        # 测试_check_heartbeat（没有心跳文件）
        result2 = death_switch._check_heartbeat()
        print(f"_check_heartbeat() 结果（无文件）: {result2}")
        
        # 创建有效心跳文件
        heartbeat_data = {
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat(),
            "system_status": "normal",
            "trust_score": 100.0,
            "checksum": ""
        }
        data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
        import hashlib
        heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        with open("test_diagnostic_heartbeat2.json", 'w', encoding='utf-8') as f:
            json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
        
        result3 = death_switch._check_heartbeat()
        print(f"_check_heartbeat() 结果（有文件）: {result3}")
        
        # 清理
        for f in [pid_file, "test_diagnostic_heartbeat2.json"]:
            if os.path.exists(f):
                os.remove(f)
                
        print("[OK] 死亡开关检查功能测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 死亡开关检查功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_death_switch_thread():
    """测试死亡开关线程启动/停止"""
    print("\n=== 测试死亡开关线程 ===")
    try:
        from src.守护者.death_switch import DeathSwitch
        
        # 准备测试文件
        heartbeat_file = "test_thread_heartbeat.json"
        pid_file = "test_thread_pid.pid"
        
        heartbeat_data = {
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat(),
            "system_status": "normal",
            "trust_score": 100.0,
            "checksum": ""
        }
        data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
        import hashlib
        heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        with open(heartbeat_file, 'w', encoding='utf-8') as f:
            json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
        
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        
        # 创建死亡开关（短间隔）
        death_switch = DeathSwitch(
            heartbeat_file=heartbeat_file,
            pid_file=pid_file,
            check_interval=1,  # 1秒检查间隔
            max_misses=3,      # 3次丢失
            log_dir="test_diagnostic_logs"
        )
        
        print("启动死亡开关...")
        success = death_switch.start()
        print(f"启动结果: {success}")
        
        if success:
            print("等待2秒...")
            time.sleep(2)
            print(f"连续丢失计数: {death_switch.consecutive_misses}")
            
            print("停止死亡开关...")
            death_switch.stop()
            print("停止完成")
            
            # 检查线程是否存活
            if death_switch.monitor_thread:
                alive = death_switch.monitor_thread.is_alive()
                print(f"监控线程存活: {alive}")
        
        # 清理
        for f in [heartbeat_file, pid_file]:
            if os.path.exists(f):
                os.remove(f)
        
        import shutil
        if os.path.exists("test_diagnostic_logs"):
            shutil.rmtree("test_diagnostic_logs")
            
        print("[OK] 死亡开关线程测试通过")
        return True
    except Exception as e:
        print(f"[ERROR] 死亡开关线程测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主诊断函数"""
    print("开始诊断守护者模块问题...")
    
    tests = [
        test_os_kill,
        test_signal_constants,
        test_heartbeat_monitor,
        test_safety_mode,
        test_death_switch_check_process,
        test_death_switch_thread
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
    print(f"诊断结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有诊断测试通过！")
        return True
    else:
        print("[WARNING] 部分诊断测试失败，需要修复")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)