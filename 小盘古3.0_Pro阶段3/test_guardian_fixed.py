#!/usr/bin/env python3
"""
Guardian Safe Test (ASCII only)
Test guardian modules with checksum fix verification
"""

import os
import sys
import json
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def log(msg):
    """ASCII-only logging"""
    print(f"[TEST] {msg}")

def test_heartbeat_checksum_fix():
    """Test that checksum calculation is now correct"""
    log("Testing heartbeat checksum fix...")
    
    try:
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        
        # Create monitor
        monitor = HeartbeatMonitor(
            heartbeat_file="test_fix_heartbeat.json",
            stats_file="test_fix_stats.json",
            max_age_sec=30.0
        )
        
        # Write heartbeat
        success = monitor.write_heartbeat(
            pid=os.getpid(),
            system_status="test",
            trust_score=99.5
        )
        
        if not success:
            log("FAIL: write_heartbeat returned False")
            return False
        
        # Check heartbeat
        ok, error, age = monitor.check_heartbeat()
        
        if not ok:
            log(f"FAIL: check_heartbeat failed: {error}")
            
            # Let's manually debug
            with open("test_fix_heartbeat.json", 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            log(f"Data in file: {json.dumps(data, indent=2)[:100]}...")
            return False
        
        log(f"PASS: Heartbeat check successful (age: {age:.1f}s)")
        
        # Clean up
        for f in ["test_fix_heartbeat.json", "test_fix_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        
        return True
        
    except Exception as e:
        log(f"FAIL: Test error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up
        for f in ["test_fix_heartbeat.json", "test_fix_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_safety_mode_basic():
    """Test safety mode basic operations"""
    log("Testing safety mode basic operations...")
    
    try:
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        
        manager = SafetyModeManager(config_file="test_fix_safety.json")
        
        # Should start in normal mode
        if manager.is_in_safety_mode():
            log("FAIL: Should start in normal mode")
            return False
        
        # Enter safety mode
        success = manager.enter_safety_mode(SafetyModeLevel.SAFE)
        if not success:
            log("FAIL: Failed to enter safety mode")
            return False
        
        if not manager.is_in_safety_mode():
            log("FAIL: Should be in safety mode after entering")
            return False
        
        # Exit safety mode
        success = manager.exit_safety_mode()
        if not success:
            log("FAIL: Failed to exit safety mode")
            return False
        
        if manager.is_in_safety_mode():
            log("FAIL: Should be back to normal mode")
            return False
        
        # Clean up
        if os.path.exists("test_fix_safety.json"):
            os.remove("test_fix_safety.json")
        
        log("PASS: Safety mode operations successful")
        return True
        
    except Exception as e:
        log(f"FAIL: Test error: {type(e).__name__}: {e}")
        
        # Clean up
        if os.path.exists("test_fix_safety.json"):
            os.remove("test_fix_safety.json")
        return False

def test_death_switch_validation():
    """Test death switch validation without threads"""
    log("Testing death switch validation...")
    
    try:
        from src.守护者.death_switch import DeathSwitch
        
        # Create test files
        pid = os.getpid()
        pid_file = "test_fix_pid.pid"
        heartbeat_file = "test_fix_ds_heartbeat.json"
        
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(pid))
        
        # Create heartbeat data
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        monitor = HeartbeatMonitor(
            heartbeat_file=heartbeat_file,
            stats_file="test_fix_ds_stats.json",
            max_age_sec=30.0
        )
        
        monitor.write_heartbeat(
            pid=pid,
            system_status="normal",
            trust_score=100.0
        )
        
        # Create death switch (don't start thread)
        death_switch = DeathSwitch(
            heartbeat_file=heartbeat_file,
            pid_file=pid_file,
            check_interval=60,
            max_misses=10
        )
        
        # Test heartbeat check
        heartbeat_ok = death_switch._check_heartbeat()
        if not heartbeat_ok:
            log("FAIL: Heartbeat check failed")
            return False
        
        # Test process check
        process_ok = death_switch._check_process()
        if not process_ok:
            log("FAIL: Process check failed")
            return False
        
        log("PASS: Death switch validation successful")
        
        # Clean up
        for f in [pid_file, heartbeat_file, "test_fix_ds_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        
        return True
        
    except Exception as e:
        log(f"FAIL: Test error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up
        for f in ["test_fix_pid.pid", "test_fix_ds_heartbeat.json", "test_fix_ds_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_module_integration():
    """Test integration between modules"""
    log("Testing module integration...")
    
    try:
        # Import all modules
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        from src.守护者.death_switch import DeathSwitch
        
        # Create unique test files
        import time
        timestamp = int(time.time())
        
        heartbeat_file = f"test_int_{timestamp}_heartbeat.json"
        stats_file = f"test_int_{timestamp}_stats.json"
        pid_file = f"test_int_{timestamp}_pid.pid"
        config_file = f"test_int_{timestamp}_safety.json"
        
        # 1. Create heartbeat
        monitor = HeartbeatMonitor(
            heartbeat_file=heartbeat_file,
            stats_file=stats_file,
            max_age_sec=30.0
        )
        
        pid = os.getpid()
        monitor.write_heartbeat(pid=pid, system_status="integration", trust_score=95.0)
        
        # 2. Verify with death switch
        death_switch = DeathSwitch(
            heartbeat_file=heartbeat_file,
            pid_file=pid_file,
            check_interval=60,
            max_misses=5
        )
        
        # Write PID file
        with open(pid_file, 'w', encoding='utf-8') as f:
            f.write(str(pid))
        
        heartbeat_ok = death_switch._check_heartbeat()
        if not heartbeat_ok:
            log("FAIL: Death switch cannot read heartbeat")
            return False
        
        # 3. Test safety mode
        manager = SafetyModeManager(config_file=config_file)
        
        # All modules should work together
        log("PASS: All modules integrated successfully")
        
        # Clean up
        import glob
        for f in glob.glob(f"test_int_{timestamp}_*"):
            if os.path.exists(f):
                os.remove(f)
        
        return True
        
    except Exception as e:
        log(f"FAIL: Integration test error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up
        import glob
        for f in glob.glob("test_int_*"):
            if os.path.exists(f):
                os.remove(f)
        return False

def main():
    log("Starting Guardian Safe Test (with checksum fix)")
    log(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
    log(f"Platform: {sys.platform}")
    log(f"Directory: {os.getcwd()}")
    log("")
    
    tests = [
        ("Heartbeat checksum fix", test_heartbeat_checksum_fix),
        ("Safety mode basic", test_safety_mode_basic),
        ("Death switch validation", test_death_switch_validation),
        ("Module integration", test_module_integration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            log(f"Running: {test_name}")
            if test_func():
                log("  Result: PASS")
                passed += 1
            else:
                log("  Result: FAIL")
                failed += 1
        except Exception as e:
            log(f"  Result: ERROR - {type(e).__name__}: {e}")
            failed += 1
        
        log("")
    
    # Final cleanup
    import glob
    for pattern in ["test_fix_*.json", "test_fix_*.pid", "test_int_*"]:
        for f in glob.glob(pattern):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
    
    log("=" * 60)
    log(f"RESULTS: Passed {passed}/{len(tests)}, Failed {failed}/{len(tests)}")
    
    if failed == 0:
        log("SUCCESS: All safe tests passed!")
        log("Guardian modules are functioning correctly.")
        return True
    else:
        log("ISSUES: Some tests failed. Guardian modules need attention.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)