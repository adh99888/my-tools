#!/usr/bin/env python3
"""
信任系统辅助函数 - 宪法合规拆分模块
宪法依据：宪法第1条（≤200行约束）
功能：包含信任系统的辅助函数和测试代码
"""

import json
from typing import Dict, Any
from .trust_types import TrustChangeReason
from .trust_system_core import TrustSystem


def create_default_trust_system() -> TrustSystem:
    """创建默认信任系统"""
    return TrustSystem(data_dir="data/trust")


def test_trust_system() -> bool:
    """测试信任系统"""
    try:
        # 创建信任系统
        trust_system = create_default_trust_system()
        
        print(f"[PASS] 信任系统创建成功")
        print(f"当前信任分: {trust_system.get_current_score()}")
        print(f"当前阈值: {trust_system.get_current_threshold().level}")
        
        # 测试更新
        success = trust_system.update_score(
            change_amount=5.0,
            reason=TrustChangeReason.L2_SUCCESS,
            operation_id="TEST_001",
            details={"test": True}
        )
        
        if success:
            print(f"[PASS] 信任分更新成功: {trust_system.get_current_score()}")
        else:
            print(f"[FAIL] 信任分更新失败")
            return False
        
        # 测试统计
        stats = trust_system.get_statistics()
        print(f"统计信息: {json.dumps(stats, indent=2)}")
        
        print(f"[PASS] 所有测试通过")
        return True
        
    except Exception as e:
        print(f"[FAIL] 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("信任评分系统测试")
    print("=" * 60)
    
    success = test_trust_system()
    
    print("=" * 60)
    if success:
        print("[PASS] 所有测试通过！")
    else:
        print("[FAIL] 测试失败！")
    print("=" * 60)