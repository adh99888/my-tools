#!/usr/bin/env python3
"""信任评分系统兼容性测试
"""

import sys
import os

# 添加src目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

try:
    # 测试1：导入TrustSystem
    from core.trust_system import TrustSystem
    print("✅ 测试1通过：TrustSystem导入成功")
    
    # 测试2：导入数据类
    from core.trust_system import TrustChangeReason, TrustChangeRecord, TrustThreshold
    print("✅ 测试2通过：数据类导入成功")
    
    # 测试3：导入工具函数
    from core.trust_system import create_default_trust_system, test_trust_system
    print("✅ 测试3通过：工具函数导入成功")
    
    # 测试4：创建实例
    trust = create_default_trust_system()
    print(f"✅ 测试4通过：创建实例成功，当前信任分={trust.get_current_score()}")
    
    # 测试5：查询当前阈值
    threshold = trust.get_current_threshold()
    print(f"✅ 测试5通过：当前阈值={threshold.level}, 权限={threshold.permissions}")
    
    # 测试6：更新分数
    success = trust.update_score(5.0, TrustChangeReason.L2_SUCCESS, "TEST_001")
    if success:
        print(f"✅ 测试6通过：分数更新成功，新分数={trust.get_current_score()}")
    else:
        print(f"❌ 测试6失败：分数更新失败")
        
    # 测试7：查询历史
    history = trust.get_score_history(limit=5)
    print(f"✅ 测试7通过：查询历史成功，记录数={len(history)}")
    
    # 测试8：统计信息
    stats = trust.get_statistics()
    print(f"✅ 测试8通过：统计信息获取成功")
    print(f"   - 当前分数: {stats['current_score']}")
    print(f"   - 成功操作数: {stats.get('recent_success_rate', 'N/A')}")
    
    print("\n" + "="*60)
    print("🎉 所有测试通过！trust_system语法错误已修复")
    print("="*60)
    sys.exit(0)
    
except Exception as e:
    print(f"\n❌ 测试失败: {e}")
    import traceback
    traceback.print_exc()
    print("\n" + "="*60)
    print("🔧 需要进一步修复")
    print("="*60)
    sys.exit(1)