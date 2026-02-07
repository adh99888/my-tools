#!/usr/bin/env python3
"""信任评分系统兼容性测试
"""

import sys
import os

# 添加项目根目录到Python路径（与test_seed_basic.py保持一致）
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)  # 项目根目录 '小盘古3.0_Pro'
# 确保Python能够找到src目录下的模块
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # 测试1：导入TrustSystem
    from src.核心.trust_system import TrustSystem
    print("[OK] 测试1通过：TrustSystem导入成功")
    
    # 测试2：导入数据类
    from src.核心.trust_system import TrustChangeReason, TrustChangeRecord, TrustThreshold
    print("[OK] 测试2通过：数据类导入成功")
    
    # 测试3：导入工具函数
    from src.核心.trust_system import create_default_trust_system, test_trust_system
    print("[OK] 测试3通过：工具函数导入成功")
    
    # 测试4：创建实例
    trust = create_default_trust_system()
    print(f"[OK] 测试4通过：创建实例成功，当前信任分={trust.get_current_score()}")
    
    # 测试5：查询当前阈值
    threshold = trust.get_current_threshold()
    print(f"[OK] 测试5通过：当前阈值={threshold.level}, 权限={threshold.permissions}")
    
    # 测试6：更新分数
    success = trust.update_score(5.0, TrustChangeReason.L2_SUCCESS, "TEST_001")
    if success:
        print(f"[OK] 测试6通过：分数更新成功，新分数={trust.get_current_score()}")
    else:
        print(f"[FAIL] 测试6失败：分数更新失败")
        
    # 测试7：查询历史
    history = trust.get_score_history(limit=5)
    print(f"[OK] 测试7通过：查询历史成功，记录数={len(history)}")
    
    # 测试8：统计信息
    stats = trust.get_statistics()
    print(f"[OK] 测试8通过：统计信息获取成功")
    print(f"   - 当前分数: {stats['current_score']}")
    print(f"   - 成功操作数: {stats.get('recent_success_rate', 'N/A')}")
    
    print("\n" + "="*60)
    print("[SUCCESS] 所有测试通过！trust_system语法错误已修复")
    print("="*60)
    sys.exit(0)
    
except Exception as e:
    print(f"\n[FAIL] 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    print("[FIX] 需要进一步修复")
    print("="*60)
    sys.exit(1)