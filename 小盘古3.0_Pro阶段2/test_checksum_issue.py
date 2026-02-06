#!/usr/bin/env python3
"""
Test HeartbeatMonitor checksum issue
"""

import os
import sys
import json
import hashlib
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_checksum_consistency():
    """Test if checksum calculation is consistent between write and check"""
    print("Testing checksum consistency...")
    
    try:
        from src.守护者.heartbeat_monitor import HeartbeatMonitor
        
        # Create monitor
        monitor = HeartbeatMonitor(
            heartbeat_file="test_checksum.json",
            stats_file="test_stats.json",
            max_age_sec=30.0
        )
        
        # Write heartbeat
        success = monitor.write_heartbeat(
            pid=12345,
            system_status="test",
            trust_score=99.5
        )
        
        if not success:
            print("FAIL: write_heartbeat returned False")
            return False
        
        # Manually read and inspect the file
        with open("test_checksum.json", 'r', encoding='utf-8') as f:
            written_data = json.load(f)
        
        print(f"Written data keys: {list(written_data.keys())}")
        print(f"Written checksum: {written_data.get('checksum', 'MISSING')[:16]}...")
        
        # Now check heartbeat
        ok, error, age = monitor.check_heartbeat()
        
        print(f"Check result: ok={ok}, error={error}, age={age}")
        
        if not ok:
            print(f"FAIL: check_heartbeat failed with error: {error}")
            
            # Let's manually verify the checksum
            with open("test_checksum.json", 'r', encoding='utf-8') as f:
                test_data = json.load(f)
            
            saved_checksum = test_data.get('checksum', '')
            print(f"Saved checksum in file: {saved_checksum[:16]}...")
            
            # Remove checksum for recalculation
            test_data['checksum'] = ''
            recalc_str = json.dumps(test_data, sort_keys=True, ensure_ascii=False)
            recalc_checksum = hashlib.sha256(recalc_str.encode('utf-8')).hexdigest()
            print(f"Recalculated checksum: {recalc_checksum[:16]}...")
            
            print(f"Data string for checksum: {recalc_str[:100]}...")
            
            if saved_checksum == recalc_checksum:
                print("INTERESTING: Manual recalculation matches saved checksum!")
                # This suggests the issue is in check_heartbeat's logic
            else:
                print("Checksum mismatch - issue in write_heartbeat")
        
        # Clean up
        for f in ["test_checksum.json", "test_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        
        return ok
        
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        
        # Clean up
        for f in ["test_checksum.json", "test_stats.json"]:
            if os.path.exists(f):
                os.remove(f)
        return False

def test_direct_checksum_logic():
    """Test the checksum logic directly"""
    print("\nTesting direct checksum logic...")
    
    # Simulate write_heartbeat logic
    test_data = {
        "pid": 12345,
        "timestamp": datetime.now().isoformat(),
        "system_status": "test",
        "trust_score": 99.5,
        "checksum": ""
    }
    
    # Calculate checksum the way write_heartbeat does
    write_str = json.dumps(test_data, sort_keys=True, ensure_ascii=False)
    write_checksum = hashlib.sha256(write_str.encode('utf-8')).hexdigest()
    
    print(f"Write string (for checksum): {write_str[:100]}...")
    print(f"Write checksum: {write_checksum[:16]}...")
    
    # Now simulate check_heartbeat logic
    test_data["checksum"] = write_checksum  # This is what gets saved to file
    
    # In check_heartbeat, we pop the checksum
    check_data = test_data.copy()
    saved_checksum = check_data.pop('checksum', '')
    
    check_str = json.dumps(check_data, sort_keys=True, ensure_ascii=False)
    check_checksum = hashlib.sha256(check_str.encode('utf-8')).hexdigest()
    
    print(f"Check string (after pop): {check_str[:100]}...")
    print(f"Check checksum: {check_checksum[:16]}...")
    print(f"Saved checksum: {saved_checksum[:16]}...")
    
    if write_checksum == check_checksum:
        print("PASS: Checksum logic is consistent")
        return True
    else:
        print("FAIL: Checksum logic inconsistent!")
        print(f"Write str length: {len(write_str)}")
        print(f"Check str length: {len(check_str)}")
        print(f"Write str == Check str: {write_str == check_str}")
        return False

def main():
    print("Testing HeartbeatMonitor checksum issue")
    print(f"Python: {sys.version}")
    print(f"Platform: {sys.platform}")
    print()
    
    test1 = test_direct_checksum_logic()
    print()
    test2 = test_checksum_consistency()
    
    print("\n" + "="*60)
    print(f"Direct logic test: {'PASS' if test1 else 'FAIL'}")
    print(f"Monitor test: {'PASS' if test2 else 'FAIL'}")
    
    if test1 and test2:
        print("SUCCESS: All tests passed")
        return True
    else:
        print("ISSUE: Some tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)