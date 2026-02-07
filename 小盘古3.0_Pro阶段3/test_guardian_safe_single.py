#!/usr/bin/env python3
"""
Guardian Module Safe Test (Single Thread, ASCII Only)
Purpose: Safely test guardian modules without threads or encoding issues
"""

import os
import sys

def log(msg):
    """ASCII-only logging"""
    print(f"[TEST] {msg}")

def test_module_imports():
    """Test importing all guardian modules"""
    log("Testing module imports...")
    
    modules = [
        ("death_switch", "DeathSwitch"),
        ("heartbeat_monitor", "HeartbeatMonitor"), 
        ("safety_mode", ["SafetyModeManager", "SafetyModeLevel"])
    ]
    
    all_good = True
    results = []
    
    for module_name, class_names in modules:
        try:
            # Construct import path
            full_module_name = f"src.守护者.{module_name}"
            module = __import__(full_module_name, fromlist=["*"])
            results.append(f"{module_name}: imported")
            
            # Check classes
            if isinstance(class_names, list):
                for cls in class_names:
                    if hasattr(module, cls):
                        results.append(f"  {cls}: found")
                    else:
                        results.append(f"  {cls}: MISSING")
                        all_good = False
            else:
                if hasattr(module, class_names):
                    results.append(f"  {class_names}: found")
                else:
                    results.append(f"  {class_names}: MISSING")
                    all_good = False
                    
        except Exception as e:
            results.append(f"{module_name}: FAILED - {type(e).__name__}")
            all_good = False
    
    for result in results:
        log(result)
    
    return all_good

def test_heartbeat_monitor_basic():
    """Test HeartbeatMonitor basic functionality"""
    log("Testing HeartbeatMonitor basic...")
    
    try:
        # Import inside test to isolate errors
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        
        # Create with test files
        monitor = HeartbeatMonitor(
            heartbeat_file="test_simple_hb.json",
            stats_file="test_simple_stats.json",
            max_age_sec=30.0
        )
        
        # Check basic attributes
        if not hasattr(monitor, 'write_heartbeat'):
            log("FAIL: Missing write_heartbeat method")
            return False
            
        if not hasattr(monitor, 'check_heartbeat'):
            log("FAIL: Missing check_heartbeat method")
            return False
            
        if not hasattr(monitor, 'get_stats'):
            log("FAIL: Missing get_stats method")
            return False
        
        # Clean up any test files
        for f in ["test_simple_hb.json", "test_simple_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        
        log("PASS: HeartbeatMonitor basic test")
        return True
        
    except Exception as e:
        log(f"FAIL: HeartbeatMonitor test error: {type(e).__name__}")
        
        # Clean up
        for f in ["test_simple_hb.json", "test_simple_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_safety_mode_basic():
    """Test SafetyModeManager basic functionality"""
    log("Testing SafetyModeManager basic...")
    
    try:
        from src.守护者.safety_mode import SafetyModeManager, SafetyModeLevel
        
        # Create manager
        manager = SafetyModeManager(config_file="test_simple_safety.json")
        
        # Check basic methods
        if not hasattr(manager, 'enter_safety_mode'):
            log("FAIL: Missing enter_safety_mode method")
            return False
            
        if not hasattr(manager, 'exit_safety_mode'):
            log("FAIL: Missing exit_safety_mode method")
            return False
            
        if not hasattr(manager, 'is_in_safety_mode'):
            log("FAIL: Missing is_in_safety_mode method")
            return False
        
        # Check SafetyModeLevel enum
        if not hasattr(SafetyModeLevel, 'NORMAL'):
            log("FAIL: Missing NORMAL enum value")
            return False
            
        if not hasattr(SafetyModeLevel, 'SAFE'):
            log("FAIL: Missing SAFE enum value")
            return False
        
        # Clean up
        if os.path.exists("test_simple_safety.json"):
            os.remove("test_simple_safety.json")
        
        log("PASS: SafetyModeManager basic test")
        return True
        
    except Exception as e:
        log(f"FAIL: SafetyModeManager test error: {type(e).__name__}")
        
        # Clean up
        if os.path.exists("test_simple_safety.json"):
            os.remove("test_simple_safety.json")
        return False

def test_death_switch_basic():
    """Test DeathSwitch basic functionality (no thread start)"""
    log("Testing DeathSwitch basic (no threads)...")
    
    try:
        from src.守护者.death_switch import DeathSwitch
        
        # Create instance with long intervals to avoid any triggering
        death_switch = DeathSwitch(
            heartbeat_file="test_simple_ds_hb.json",
            pid_file="test_simple_ds_pid.pid",
            check_interval=300,  # 5 minutes - avoid any checks
            max_misses=10,
            log_dir="test_simple_logs"
        )
        
        # Check basic methods
        if not hasattr(death_switch, 'start'):
            log("FAIL: Missing start method")
            return False
            
        if not hasattr(death_switch, 'stop'):
            log("FAIL: Missing stop method")
            return False
            
        if not hasattr(death_switch, '_check_heartbeat'):
            log("FAIL: Missing _check_heartbeat method")
            return False
            
        if not hasattr(death_switch, '_check_process'):
            log("FAIL: Missing _check_process method")
            return False
        
        # DO NOT start the thread - that's what causes issues
        
        # Clean up
        for f in ["test_simple_ds_hb.json", "test_simple_ds_pid.pid"]:
            if os.path.exists(f):
                os.remove(f)
        
        # Clean up log directory if created
        import shutil
        if os.path.exists("test_simple_logs"):
            shutil.rmtree("test_simple_logs", ignore_errors=True)
        
        log("PASS: DeathSwitch basic test (no threads)")
        return True
        
    except Exception as e:
        log(f"FAIL: DeathSwitch test error: {type(e).__name__}")
        
        # Clean up
        for f in ["test_simple_ds_hb.json", "test_simple_ds_pid.pid"]:
            if os.path.exists(f):
                os.remove(f)
        
        import shutil
        if os.path.exists("test_simple_logs"):
            shutil.rmtree("test_simple_logs", ignore_errors=True)
        return False

def test_file_creation_cleanup():
    """Test that we can create and cleanup files properly"""
    log("Testing file creation and cleanup...")
    
    test_files = [
        "test_cleanup_1.txt",
        "test_cleanup_2.json",
        "test_cleanup_3.pid"
    ]
    
    try:
        # Create test files
        for filename in test_files:
            with open(filename, 'w') as f:
                f.write("test content")
        
        # Verify files exist
        for filename in test_files:
            if not os.path.exists(filename):
                log(f"FAIL: File not created: {filename}")
                return False
        
        # Clean up
        for filename in test_files:
            if os.path.exists(filename):
                os.remove(filename)
        
        # Verify cleanup
        for filename in test_files:
            if os.path.exists(filename):
                log(f"FAIL: File not cleaned up: {filename}")
                return False
        
        log("PASS: File creation and cleanup test")
        return True
        
    except Exception as e:
        log(f"FAIL: File test error: {type(e).__name__}")
        
        # Clean up any created files
        for filename in test_files:
            if os.path.exists(filename):
                os.remove(filename)
        
        return False

def main():
    """Main test function"""
    log("Starting Guardian Safe Single-Thread Test")
    log(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
    log(f"Platform: {sys.platform}")
    log(f"Directory: {os.getcwd()}")
    log("")
    
    # Add src to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        ("Module imports", test_module_imports),
        ("HeartbeatMonitor basic", test_heartbeat_monitor_basic),
        ("SafetyModeManager basic", test_safety_mode_basic),
        ("DeathSwitch basic (no threads)", test_death_switch_basic),
        ("File creation/cleanup", test_file_creation_cleanup)
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
            log(f"  Result: ERROR - {type(e).__name__}")
            failed += 1
        
        log("")
    
    # Final cleanup
    cleanup_patterns = [
        "test_simple_*",
        "test_cleanup_*",
        "*.json",
        "*.pid",
        "*.txt"
    ]
    
    import glob
    for pattern in cleanup_patterns:
        for f in glob.glob(pattern):
            if os.path.exists(f) and f.startswith("test_"):
                try:
                    os.remove(f)
                except:
                    pass
    
    # Clean up directories
    for d in ["test_simple_logs"]:
        import shutil
        if os.path.exists(d):
            shutil.rmtree(d, ignore_errors=True)
    
    log("=" * 60)
    log(f"RESULTS: Passed {passed}/{len(tests)}, Failed {failed}/{len(tests)}")
    
    if failed == 0:
        log("SUCCESS: All safe single-thread tests passed!")
        log("Guardian modules are ready for phase 2 testing.")
        return True
    else:
        log("ISSUES: Some tests failed. Review module implementations.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)