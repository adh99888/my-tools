#!/usr/bin/env python3
"""
守护者模块安全测试（单线程）
宪法依据：宪法第4条（生存优先原则）
目的：安全地测试守护者模块功能，避免线程和编码问题
"""

import os
import sys
import json
import time
from datetime import datetime, timedelta

# 添加src到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def log_test(message):
    """安全的日志输出（使用纯ASCII避免编码问题）"""
    # 移除所有非ASCII字符
    ascii_message = message.encode('ascii', 'ignore').decode('ascii')
    print(f"[TEST] {ascii_message}")

def test_heartbeat_monitor_file_operations():
    """测试心跳监控器文件操作"""
    log_test("测试心跳监控器文件操作...")
    
    try:
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        
        # 使用简单文件名
        heartbeat_file = "test_safe_heartbeat.json"
        stats_file = "test_safe_stats.json"
        
        monitor = HeartbeatMonitor(
            heartbeat_file=heartbeat_file,
            stats_file=stats_file,
            max_age_sec=5.0
        )
        
        # 写入心跳
        success = monitor.write_heartbeat(
            pid=os.getpid(),
            system_status="testing",
            trust_score=99.5
        )
        
        if not success:
            log_test("FAIL: 写入心跳失败")
            return False
        
        # 检查心跳文件是否存在
        if not os.path.exists(heartbeat_file):
            log_test("FAIL: 心跳文件未创建")
            return False
        
        # 读取并验证心跳文件
        with open(heartbeat_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if "pid" not in data or "timestamp" not in data:
            log_test("FAIL: 心跳文件缺少必要字段")
            return False
        
        # 检查心跳（不涉及长时间等待）
        ok, error, age = monitor.check_heartbeat()
        if not ok:
            log_test(f"FAIL: 心跳检查失败: {error}")
            return False
        
        # 获取统计信息
        stats = monitor.get_stats()
        if stats.total_beats < 1:
            log_test("FAIL: 统计信息不正确")
            return False
        
        # 清理
        for f in [heartbeat_file, stats_file]:
            if os.path.exists(f):
                os.remove(f)
        
        log_test("PASS: 心跳监控器文件操作测试通过")
        return True
        
    except Exception as e:
        log_test(f"FAIL: 心跳监控器测试异常: {type(e).__name__}: {e}")
        # 清理残留文件
        for f in ["test_safe_heartbeat.json", "test_safe_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_safety_mode_configuration():
    """测试安全模式配置管理"""
    log_test("测试安全模式配置管理...")
    
    try:
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        
        # 使用简单配置文件名
        config_file = "test_safe_safety_config.json"
        
        manager = SafetyModeManager(config_file=config_file)
        
        # 初始状态应该是正常模式
        if manager.is_in_safety_mode():
            log_test("FAIL: 初始状态应该是正常模式")
            return False
        
        # 检查配置加载
        config = manager.config
        if config.level != SafetyModeLevel.NORMAL:
            log_test(f"FAIL: 初始配置级别不正确: {config.level}")
            return False
        
        # 测试功能检查
        if not manager.check_feature_allowed("heartbeat"):
            log_test("FAIL: heartbeat功能应该允许")
            return False
        
        # 检查不应该在安全模式时允许的功能
        # 注意：在正常模式下，L2-L4协议应该允许
        if manager.is_in_safety_mode():
            if manager.check_feature_allowed("protocol_l3"):
                log_test("FAIL: L3协议在安全模式不应该允许")
                return False
        
        # 清理
        if os.path.exists(config_file):
            os.remove(config_file)
        
        log_test("PASS: 安全模式配置管理测试通过")
        return True
        
    except Exception as e:
        log_test(f"FAIL: 安全模式测试异常: {type(e).__name__}: {e}")
        # 清理
        for f in ["test_safe_safety_config.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_death_switch_validation():
    """测试死亡开关验证逻辑（不启动线程）"""
    log_test("测试死亡开关验证逻辑...")
    
    try:
        from src.守护者.death_switch import DeathSwitch
        
        # 准备测试文件
        heartbeat_file = "test_safe_ds_heartbeat.json"
        pid_file = "test_safe_ds_pid.pid"
        
        # 创建有效的心跳文件
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
        
        # 创建PID文件
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        
        # 创建死亡开关实例（不启动线程）
        death_switch = DeathSwitch(
            heartbeat_file=heartbeat_file,
            pid_file=pid_file,
            check_interval=60,  # 长间隔，避免任何可能的触发
            max_misses=10
        )
        
        # 测试心跳检查
        heartbeat_ok = death_switch._check_heartbeat()
        if not heartbeat_ok:
            log_test("FAIL: 有效心跳检查失败")
            return False
        
        # 测试进程检查
        process_ok = death_switch._check_process()
        if not process_ok:
            log_test("FAIL: 有效进程检查失败")
            return False
        
        # 测试过时心跳检测
        old_time = datetime.now() - timedelta(minutes=10)
        heartbeat_data["timestamp"] = old_time.isoformat()
        
        # 重新计算校验和
        data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
        heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        with open(heartbeat_file, 'w', encoding='utf-8') as f:
            json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
        
        heartbeat_ok = death_switch._check_heartbeat()
        if heartbeat_ok:  # 应该返回False，因为心跳已过期
            log_test("FAIL: 过时心跳检查应该失败")
            return False
        
        # 清理
        for f in [heartbeat_file, pid_file]:
            if os.path.exists(f):
                os.remove(f)
        
        log_test("PASS: 死亡开关验证逻辑测试通过")
        return True
        
    except Exception as e:
        log_test(f"FAIL: 死亡开关测试异常: {type(e).__name__}: {e}")
        # 清理
        for f in ["test_safe_ds_heartbeat.json", "test_safe_ds_pid.pid"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_module_interoperability():
    """测试模块间互操作性"""
    log_test("测试模块间互操作性...")
    
    try:
        # 导入所有模块
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        from src.守护者.death_switch import DeathSwitch
        
        # 创建临时文件
        base_name = f"test_interop_{os.getpid()}"
        heartbeat_file = f"{base_name}_heartbeat.json"
        stats_file = f"{base_name}_stats.json"
        pid_file = f"{base_name}_pid.pid"
        config_file = f"{base_name}_config.json"
        
        # 1. 心跳监控器写入心跳
        monitor = HeartbeatMonitor(
            heartbeat_file=heartbeat_file,
            stats_file=stats_file,
            max_age_sec=10.0
        )
        
        monitor.write_heartbeat(
            pid=os.getpid(),
            system_status="interop_test",
            trust_score=95.0
        )
        
        # 2. 死亡开关读取心跳
        death_switch = DeathSwitch(
            heartbeat_file=heartbeat_file,
            pid_file=pid_file,
            check_interval=60,
            max_misses=5
        )
        
        # 创建PID文件
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(os.getpid()))
        
        heartbeat_ok = death_switch._check_heartbeat()
        if not heartbeat_ok:
            log_test("FAIL: 死亡开关无法读取心跳监控器创建的心跳")
            return False
        
        # 3. 安全模式管理器正常操作
        safety_manager = SafetyModeManager(config_file=config_file)
        
        # 所有模块应该可以共存
        if not (hasattr(monitor, 'write_heartbeat') and 
                hasattr(death_switch, '_check_heartbeat') and 
                hasattr(safety_manager, 'is_in_safety_mode')):
            log_test("FAIL: 模块缺少预期方法")
            return False
        
        # 清理
        for f in [heartbeat_file, stats_file, pid_file, config_file]:
            if os.path.exists(f):
                os.remove(f)
        
        log_test("PASS: 模块间互操作性测试通过")
        return True
        
    except Exception as e:
        log_test(f"FAIL: 互操作性测试异常: {type(e).__name__}: {e}")
        # 清理
        import glob
        for f in glob.glob("test_interop_*"):
            if os.path.exists(f):
                os.remove(f)
        return False

def main():
    """主测试函数"""
    log_test("开始守护者模块安全测试（单线程）")
    log_test(f"Python版本: {sys.version_info.major}.{sys.version_info.minor}")
    log_test(f"工作目录: {os.getcwd()}")
    log_test("")
    
    tests = [
        ("心跳监控器文件操作", test_heartbeat_monitor_file_operations),
        ("安全模式配置管理", test_safety_mode_configuration),
        ("死亡开关验证逻辑", test_death_switch_validation),
        ("模块间互操作性", test_module_interoperability)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            log_test(f"开始测试: {test_name}")
            if test_func():
                passed += 1
                log_test(f"✓ {test_name} 通过")
            else:
                failed += 1
                log_test(f"✗ {test_name} 失败")
        except Exception as e:
            failed += 1
            log_test(f"✗ {test_name} 异常: {type(e).__name__}: {e}")
        
        log_test("")
    
    # 最终清理
    import glob
    for pattern in ["test_safe_*.json", "test_safe_*.pid", "test_interop_*"]:
        for f in glob.glob(pattern):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
    
    log_test("=" * 60)
    log_test(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        log_test("🎉 所有安全测试通过！")
        return True
    else:
        log_test("⚠️ 部分安全测试失败，需要进一步检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)