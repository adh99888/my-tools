#!/usr/bin/env python3
"""
Memory System Safe Test (ASCII Only)
Test basic memory system functionality without threads
"""

import os
import sys
from typing import Optional

def log(msg):
    """ASCII-only logging"""
    print(f"[TEST] {msg}")

def test_memory_modules_import():
    """Test importing all memory modules"""
    log("Testing memory module imports...")
    
    try:
        from src.记忆.working_memory import WorkingMemory, MemoryItem, MemoryPriority
        log("PASS: WorkingMemory imported")
        
        from src.记忆.short_term_memory import ShortTermMemory, ShortTermItem
        log("PASS: ShortTermMemory imported")
        
        from src.记忆.long_term_memory import LongTermMemory, LongTermItem
        log("PASS: LongTermMemory imported")
        
        # Test enums and classes
        if not hasattr(MemoryPriority, 'HIGH'):
            log("FAIL: MemoryPriority.HIGH not found")
            return False
        
        log("PASS: MemoryPriority enum found")
        return True
        
    except Exception as e:
        log(f"FAIL: Import error: {type(e).__name__}")
        return False

def test_working_memory_basic():
    """Test working memory basic functionality"""
    log("Testing working memory basic...")
    
    try:
        from src.记忆.working_memory import WorkingMemory, MemoryPriority
        
        # Create working memory instance
        wm = WorkingMemory(
            max_items=10,
            storage_file="test_wm.json"
        )
        
        # Add items
        id1 = wm.add("Task 1: Fix bug", MemoryPriority.HIGH)
        id2 = wm.add("Task 2: Write docs", MemoryPriority.MEDIUM)
        id3 = wm.add("Note: User preference", MemoryPriority.LOW)
        
        if len(wm) != 3:
            log(f"FAIL: Expected 3 items, got {len(wm)}")
            return False
        
        log(f"PASS: Added 3 items")
        
        # Get recent items
        recent = wm.get_recent(limit=5)
        if len(recent) != 3:
            log(f"FAIL: Expected 3 recent items, got {len(recent)}")
            return False
        
        log("PASS: Retrieved recent items")
        
        # Search
        results = wm.search("bug")
        if len(results) == 0:
            log("FAIL: Search should find 'bug'")
            return False
        
        log("PASS: Search functionality works")
        
        # Get by ID
        item = wm.get(id1)
        if item is None:
            log("FAIL: Cannot retrieve item by ID")
            return False
        
        log("PASS: Retrieved item by ID")
        
        # Cleanup
        wm.clear()
        
        # Clean up files
        if os.path.exists("test_wm.json"):
            os.remove("test_wm.json")
        
        log("PASS: Working memory basic test passed")
        return True
        
    except Exception as e:
        log(f"FAIL: Working memory test error: {type(e).__name__}")
        
        # Clean up
        if os.path.exists("test_wm.json"):
            os.remove("test_wm.json")
        return False

def test_short_term_memory_basic():
    """Test short-term memory basic functionality"""
    log("Testing short-term memory basic...")
    
    try:
        from src.记忆.short_term_memory import ShortTermMemory, MemoryPriority
        
        # Create short-term memory instance
        stm = ShortTermMemory(
            max_items=10,
            storage_file="test_stm.json"
        )
        
        # Add items
        id1 = stm.add("Session info: Project X", MemoryPriority.HIGH, expires_hours=1.0)
        id2 = stm.add("Context: Fixing memory system", MemoryPriority.MEDIUM, expires_hours=2.0)
        
        if len(stm) != 2:
            log(f"FAIL: Expected 2 items, got {len(stm)}")
            return False
        
        log("PASS: Added 2 items to short-term memory")
        
        # Get item (should increment access count)
        item = stm.get(id1)
        if item.access_count != 1:
            log(f"FAIL: Access count should be 1, got {item.access_count}")
            return False
        
        log("PASS: Access tracking works")
        
        # Cleanup
        stm.clear()
        
        # Clean up files
        if os.path.exists("test_stm.json"):
            os.remove("test_stm.json")
        
        log("PASS: Short-term memory basic test passed")
        return True
        
    except Exception as e:
        log(f"FAIL: Short-term memory test error: {type(e).__name__}")
        
        # Clean up
        if os.path.exists("test_stm.json"):
            os.remove("test_stm.json")
        return False

def test_long_term_memory_basic():
    """Test long-term memory basic functionality"""
    log("Testing long-term memory basic...")
    
    try:
        from src.记忆.long_term_memory import LongTermMemory, MemoryPriority
        
        # Create long-term memory instance
        ltm = LongTermMemory(storage_file="test_ltm.json")
        
        # Add items
        id1 = ltm.add("User preference: Python", category="language", importance=0.9)
        id2 = ltm.add("Project habit: Test before deploy", category="workflow", importance=0.8)
        id3 = ltm.add("Knowledge: Memory system has 3 layers", category="system", importance=0.7)
        
        if len(ltm) != 3:
            log(f"FAIL: Expected 3 items, got {len(ltm)}")
            return False
        
        log("PASS: Added 3 items to long-term memory")
        
        # Get by category
        python_prefs = ltm.get_by_category("language")
        if len(python_prefs) != 1:
            log(f"FAIL: Expected 1 language item, got {len(python_prefs)}")
            return False
        
        log("PASS: Category filtering works")
        
        # Get item by ID
        item = ltm.get(id2)
        if item is None or item.category != "workflow":
            log("FAIL: Cannot retrieve correct item by ID")
            return False
        
        log("PASS: Retrieved item by ID correctly")
        
        # Cleanup
        ltm.clear()
        
        # Clean up files
        if os.path.exists("test_ltm.json"):
            os.remove("test_ltm.json")
        
        log("PASS: Long-term memory basic test passed")
        return True
        
    except Exception as e:
        log(f"FAIL: Long-term memory test error: {type(e).__name__}")
        
        # Clean up
        if os.path.exists("test_ltm.json"):
            os.remove("test_ltm.json")
        return False

def main():
    """Main test function"""
    log("Starting Memory System Safe Test")
    log(f"Python: {sys.version_info.major}.{sys.version_info.minor}")
    log(f"Platform: {sys.platform}")
    log(f"Directory: {os.getcwd()}")
    log("")
    
    # Add src to path
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    tests = [
        ("Memory module imports", test_memory_modules_import),
        ("Working memory basic", test_working_memory_basic),
        ("Short-term memory basic", test_short_term_memory_basic),
        ("Long-term memory basic", test_long_term_memory_basic)
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
    import glob
    for pattern in ["test_*.json"]:
        for f in glob.glob(pattern):
            if os.path.exists(f):
                os.remove(f)
    
    log("=" * 60)
    log(f"RESULTS: Passed {passed}/{len(tests)}, Failed {failed}/{len(tests)}")
    
    if failed == 0:
        log("SUCCESS: All memory system tests passed!")
        log("Memory system is ready for Phase 2 integration.")
        return True
    else:
        log("ISSUES: Some memory system tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)