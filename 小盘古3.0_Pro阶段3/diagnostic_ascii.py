#!/usr/bin/env python3
"""
Guardian Module Diagnostic (ASCII only)
Purpose: Diagnose issues with guardian modules using ASCII-only output
"""

import os
import sys
import json
import hashlib
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def log(msg):
    """ASCII-only logging"""
    print(f"[DIAG] {msg}")

def test_heartbeat_checksum():
    """Test heartbeat checksum calculation"""
    log("Testing heartbeat checksum calculation...")
    
    try:
        # Create test heartbeat data
        test_data = {
            "pid": 12345,
            "timestamp": "2025-02-05T12:00:00.000000",
            "system_status": "testing",
            "trust_score": 99.5,
            "checksum": ""
        }
        
        # Calculate checksum the way HeartbeatMonitor does
        data_str = json.dumps(test_data, sort_keys=True, ensure_ascii=False)
        log(f"Data string: {data_str[:50]}...")
        
        checksum = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        log(f"Calculated checksum: {checksum[:16]}...")
        
        # Verify checksum format
        if len(checksum) == 64:
            log("PASS: Checksum format correct")
            return True
        else:
            log(f"FAIL: Checksum length incorrect: {len(checksum)}")
            return False
            
    except Exception as e:
        log(f"FAIL: Checksum test error: {type(e).__name__}: {e}")
        return False

def test_heartbeat_file_creation():
    """Test creating a heartbeat file manually"""
    log("Testing heartbeat file creation...")
    
    try:
        filename = "test_diag_heartbeat.json"
        
        # Create heartbeat data
        heartbeat_data = {
            "pid": os.getpid(),
            "timestamp": datetime.now().isoformat(),
            "system_status": "diagnostic",
            "trust_score": 100.0,
            "checksum": ""
        }
        
        # Calculate checksum
        data_str = json.dumps(heartbeat_data, sort_keys=True, ensure_ascii=False)
        heartbeat_data["checksum"] = hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        # Write to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(heartbeat_data, f, indent=2, ensure_ascii=False)
        
        # Read back
        with open(filename, 'r', encoding='utf-8') as f:
            loaded = json.load(f)
        
        # Verify checksum
        original_checksum = loaded["checksum"]
        
        # Remove checksum for recalculation
        loaded["checksum"] = ""
        recalc_str = json.dumps(loaded, sort_keys=True, ensure_ascii=False)
        recalc_checksum = hashlib.sha256(recalc_str.encode('utf-8')).hexdigest()
        
        if original_checksum == recalc_checksum:
            log("PASS: Heartbeat file checksum verification successful")
            
            # Clean up
            os.remove(filename)
            return True
        else:
            log(f"FAIL: Checksum mismatch: {original_checksum[:16]}... vs {recalc_checksum[:16]}...")
            log(f"Original string: {data_str[:100]}")
            log(f"Recalc string: {recalc_str[:100]}")
            
            # Clean up
            if os.path.exists(filename):
                os.remove(filename)
            return False
            
    except Exception as e:
        log(f"FAIL: Heartbeat file test error: {type(e).__name__}: {e}")
        # Clean up
        if os.path.exists("test_diag_heartbeat.json"):
            os.remove("test_diag_heartbeat.json")
        return False

def test_heartbeat_monitor_simple():
    """Simple test of HeartbeatMonitor without complex checks"""
    log("Testing HeartbeatMonitor simple functionality...")
    
    try:
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        
        monitor = HeartbeatMonitor(
            heartbeat_file="test_diag_monitor.json",
            stats_file="test_diag_stats.json",
            max_age_sec=30.0
        )
        
        log("HeartbeatMonitor imported successfully")
        
        # Test if we can create the monitor without errors
        log(f"Heartbeat file: {monitor.heartbeat_file}")
        log(f"Stats file: {monitor.stats_file}")
        
        # Clean up any test files
        for f in ["test_diag_monitor.json", "test_diag_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        
        log("PASS: HeartbeatMonitor basic test passed")
        return True
        
    except Exception as e:
        log(f"FAIL: HeartbeatMonitor test error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up
        for f in ["test_diag_monitor.json", "test_diag_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_all_imports():
    """Test importing all guardian modules"""
    log("Testing imports of all guardian modules...")
    
    modules_to_test = [
        ("death_switch", "DeathSwitch"),
        ("heartbeat_monitor", "HeartbeatMonitor"),
        ("safety_mode", ["SafetyModeManager", "SafetyModeLevel"])
    ]
    
    all_passed = True
    
    for module_name, class_names in modules_to_test:
        try:
            module = __import__(f"src.守护者.{module_name}", fromlist=["*"])
            log(f"  {module_name}: imported successfully")
            
            if isinstance(class_names, list):
                for class_name in class_names:
                    if hasattr(module, class_name):
                        log(f"    {class_name}: found")
                    else:
                        log(f"    {class_name}: NOT FOUND")
                        all_passed = False
            else:
                if hasattr(module, class_names):
                    log(f"    {class_names}: found")
                else:
                    log(f"    {class_names}: NOT FOUND")
                    all_passed = False
                    
        except Exception as e:
            log(f"  {module_name}: import FAILED - {type(e).__name__}: {e}")
            all_passed = False
    
    if all_passed:
        log("PASS: All module imports successful")
        return True
    else:
        log("FAIL: Some module imports failed")
        return False

def main():
    """Main diagnostic function"""
    log("Starting Guardian Module Diagnostic")
    log(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
    log(f"Platform: {sys.platform}")
    log(f"CWD: {os.getcwd()}")
    log("")
    
    tests = [
        ("Checksum calculation", test_heartbeat_checksum),
        ("Heartbeat file creation", test_heartbeat_file_creation),
        ("HeartbeatMonitor basic", test_heartbeat_monitor_simple),
        ("Module imports", test_all_imports)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            log(f"Running: {test_name}")
            if test_func():
                log(f"  PASS")
                passed += 1
            else:
                log(f"  FAIL")
                failed += 1
        except Exception as e:
            failed += 1
            log(f"  ERROR: {type(e).__name__}: {e}")
        
        log("")
    
    # Clean up any test files
    for pattern in ["test_diag_*.json", "test_diag_*.pid"]:
        import glob
        for f in glob.glob(pattern):
            if os.path.exists(f):
                try:
                    os.remove(f)
                except:
                    pass
    
    log("=" * 60)
    log(f"RESULTS: Passed {passed}/{len(tests)}, Failed {failed}/{len(tests)}")
    
    if failed == 0:
        log("SUCCESS: All diagnostic tests passed")
        return True
    else:
        log("ISSUES: Some diagnostic tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)