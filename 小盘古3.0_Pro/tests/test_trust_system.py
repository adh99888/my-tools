#!/usr/bin/env python3
"""
信任评分系统基础测试

测试目标：
1. 验证信任分初始化和存储
2. 验证协议结果应用和分数计算
3. 验证权限检查阈值机制
4. 验证统计信息生成

测试原则：
- 隔离测试：使用临时目录存储数据
- 确定性：测试结果可重复
- 完整性：覆盖主要使用场景
"""

import sys
import os
import tempfile
import shutil
import json

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.trust_system import TrustSystem, TrustChangeReason, TrustThreshold

def test_initialization():
    """测试系统初始化"""
    print("测试1: 系统初始化")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        # 验证初始状态
        assert trust.current_score == 50.0, f"初始信任分应为50.0，实际为{trust.current_score}"
        assert trust.version == "trust-v0.1.0"
        
        # 验证阈值定义
        assert len(trust.thresholds) == 5  # critical, low, medium, high, excellent
        assert "medium" in trust.thresholds
        
        # 验证历史记录
        assert len(trust.history) == 1  # 应有初始记录
        initial_record = trust.history[0]
        assert initial_record.old_score == 0.0
        assert initial_record.new_score == 50.0
        assert initial_record.reason == TrustChangeReason.MANUAL_ADJUSTMENT
        
        print("  [OK] 系统初始化测试通过")

def test_score_updates():
    """测试分数更新"""
    print("测试2: 分数更新")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        initial_score = trust.current_score
        
        # 测试增加分数
        record = trust.update_score(
            change_amount=10.0,
            reason=TrustChangeReason.L2_SUCCESS,
            operation_id="test_op_001",
            details={"note": "测试增加"}
        )
        
        assert record.old_score == initial_score
        assert record.new_score == initial_score + 10.0
        assert record.change_amount == 10.0
        assert record.reason == TrustChangeReason.L2_SUCCESS
        
        # 验证当前分数已更新
        assert trust.current_score == initial_score + 10.0
        
        # 测试减少分数
        record = trust.update_score(
            change_amount=-5.0,
            reason=TrustChangeReason.L2_FAILURE,
            operation_id="test_op_002",
            details={"note": "测试减少"}
        )
        
        assert record.new_score == initial_score + 5.0  # 50 + 10 - 5 = 55
        
        # 测试分数边界（不超过0-100）
        record = trust.update_score(
            change_amount=200.0,  # 尝试超过100
            reason=TrustChangeReason.MANUAL_ADJUSTMENT
        )
        assert record.new_score == 100.0  # 应被限制到100
        
        record = trust.update_score(
            change_amount=-200.0,  # 尝试低于0
            reason=TrustChangeReason.MANUAL_ADJUSTMENT
        )
        assert record.new_score == 0.0  # 应被限制到0
        
        print("  [OK] 分数更新测试通过")

def test_threshold_detection():
    """测试阈值检测"""
    print("测试3: 阈值检测")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        # 测试各个分数区间的阈值
        test_cases = [
            (10.0, "critical"),
            (35.0, "low"),
            (55.0, "medium"),
            (75.0, "high"),
            (95.0, "excellent")
        ]
        
        for score, expected_threshold in test_cases:
            # 直接设置分数
            trust.current_score = score
            threshold = trust.get_current_threshold()
            
            assert threshold.level == expected_threshold, \
                f"分数{score}应属于{expected_threshold}阈值，实际为{threshold.level}"
            
            # 验证阈值属性
            assert isinstance(threshold, TrustThreshold)
            assert hasattr(threshold, "permissions")
            assert hasattr(threshold, "restrictions")
            
        print("  [OK] 阈值检测测试通过")

def test_permission_checking():
    """测试权限检查"""
    print("测试4: 权限检查")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        # 测试不同分数下的权限
        test_cases = [
            (25.0, "L1", True),   # critical: 只允许L1
            (25.0, "L2", False),  # critical: 不允许L2
            (25.0, "L3", False),  # critical: 不允许L3
            (25.0, "L4", False),  # critical: 不允许L4
            
            (40.0, "L1", True),   # low: 允许L1
            (40.0, "L2", True),   # low: 允许L2（严格审批）
            (40.0, "L3", False),  # low: 不允许L3
            (40.0, "L4", False),  # low: 不允许L4
            
            (60.0, "L1", True),   # medium: 允许L1
            (60.0, "L2", True),   # medium: 允许L2
            (60.0, "L3", True),   # medium: 允许L3（正常审批）
            (60.0, "L4", False),  # medium: 不允许L4
            
            (80.0, "L1", True),   # high: 允许L1
            (80.0, "L2", True),   # high: 允许L2
            (80.0, "L3", True),   # high: 允许L3
            (80.0, "L4", True),   # high: 允许L4申请资格
            
            (95.0, "L1", True),   # excellent: 允许所有
            (95.0, "L2", True),
            (95.0, "L3", True),
            (95.0, "L4", True)
        ]
        
        for score, protocol_level, expected_allowed in test_cases:
            trust.current_score = score
            allowed, reason = trust.can_perform_operation(protocol_level)
            
            assert allowed == expected_allowed, \
                f"分数{score}的{protocol_level}操作应{'允许' if expected_allowed else '禁止'}，实际{'允许' if allowed else '禁止'}。原因: {reason}"
            
        print("  [OK] 权限检查测试通过")

def test_protocol_result_application():
    """测试协议结果应用"""
    print("测试5: 协议结果应用")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        initial_score = trust.current_score
        
        # 测试L1操作（不影响分数）
        record = trust.apply_protocol_result(
            protocol_level="L1",
            success=True,
            operation_id="l1_test",
            importance="medium",
            risk_level="low",
            clarity="good"
        )
        assert record.change_amount == 0.0, "L1操作不应影响信任分"
        assert record.reason == TrustChangeReason.L1_OBSERVE
        assert trust.current_score == initial_score
        
        # 测试L2成功操作
        record = trust.apply_protocol_result(
            protocol_level="L2",
            success=True,
            operation_id="l2_success",
            importance="high",  # 高重要性
            risk_level="low",   # 低风险
            clarity="good"      # 解释清晰
        )
        # 基础+4分，高重要性×1.5，低风险×0.5，清晰×1.5 = 4 * 1.5 * 0.5 * 1.5 = 4.5
        expected_change = 4.0 * 1.5 * 0.5 * 1.5
        assert abs(record.change_amount - expected_change) < 0.01
        assert record.reason == TrustChangeReason.L2_SUCCESS
        
        # 测试L2失败操作
        record = trust.apply_protocol_result(
            protocol_level="L2",
            success=False,
            operation_id="l2_failure",
            importance="medium",
            risk_level="high",  # 高风险失败惩罚更重
            clarity="poor"
        )
        # 基础-8分，中重要性×1.0，高风险乘数(2.0-1.5)=0.5，解释差×0.5 = -8 * 1.0 * 0.5 * 0.5 = -2.0
        expected_change = -8.0 * 1.0 * 0.5 * 0.5
        assert abs(record.change_amount - expected_change) < 0.01
        assert record.reason == TrustChangeReason.L2_FAILURE
        
        # 测试L3成功操作
        record = trust.apply_protocol_result(
            protocol_level="L3",
            success=True,
            operation_id="l3_success",
            importance="medium",
            risk_level="medium",
            clarity="medium"
        )
        # 基础+7分，所有乘数1.0 = +7
        assert abs(record.change_amount - 7.0) < 0.01
        assert record.reason == TrustChangeReason.L3_SUCCESS
        
        print("  [OK] 协议结果应用测试通过")

def test_statistics_generation():
    """测试统计信息生成"""
    print("测试6: 统计信息生成")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        # 生成一些测试数据
        for i in range(5):
            trust.apply_protocol_result(
                protocol_level="L2",
                success=(i % 2 == 0),  # 交替成功失败
                operation_id=f"test_op_{i}",
                importance="medium",
                risk_level="medium",
                clarity="good"
            )
        
        # 获取统计信息
        stats = trust.get_statistics(days=30)
        
        # 验证统计结构
        expected_keys = [
            "total_changes", "average_daily_change", 
            "success_rate", "current_streak", "streak_type",
            "current_score", "threshold"
        ]
        
        for key in expected_keys:
            assert key in stats, f"统计信息缺少键: {key}"
        
        # 验证具体值
        assert stats["total_changes"] >= 5  # 至少5次变化
        assert 0.0 <= stats["success_rate"] <= 1.0
        assert stats["current_score"] == trust.current_score
        assert stats["threshold"] == trust.get_current_threshold().level
        
        print("  [OK] 统计信息生成测试通过")

def test_data_persistence():
    """测试数据持久化"""
    print("测试7: 数据持久化")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建系统并执行一些操作
        trust1 = TrustSystem(data_dir=tmpdir)
        trust1.apply_protocol_result(
            protocol_level="L2",
            success=True,
            operation_id="persist_test",
            importance="medium",
            risk_level="low",
            clarity="good"
        )
        
        final_score = trust1.current_score
        history_count = len(trust1.history)
        
        # 重新创建系统，应加载之前的数据
        trust2 = TrustSystem(data_dir=tmpdir)
        
        # 验证数据被正确加载
        assert abs(trust2.current_score - final_score) < 0.01
        assert len(trust2.history) == history_count
        
        # 验证历史记录内容
        if history_count > 0:
            last_record1 = trust1.history[-1]
            last_record2 = trust2.history[-1]
            
            assert last_record1.timestamp == last_record2.timestamp
            assert abs(last_record1.new_score - last_record2.new_score) < 0.01
            assert last_record1.reason == last_record2.reason
        
        print("  [OK] 数据持久化测试通过")

def test_report_export():
    """测试报告导出"""
    print("测试8: 报告导出")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        trust = TrustSystem(data_dir=tmpdir)
        
        # 导出报告
        report = trust.export_report()
        
        # 验证报告结构
        required_sections = ["system_info", "current_state", "statistics", "recent_changes"]
        for section in required_sections:
            assert section in report, f"报告缺少部分: {section}"
        
        # 验证系统信息
        assert report["system_info"]["version"] == trust.version
        assert report["system_info"]["data_dir"] == tmpdir
        
        # 验证当前状态
        assert report["current_state"]["score"] == trust.current_score
        assert report["current_state"]["threshold"] == trust.get_current_threshold().level
        
        # 验证统计信息
        stats = report["statistics"]
        assert "total_changes" in stats
        
        # 验证最近变化
        recent = report["recent_changes"]
        assert isinstance(recent, list)
        
        print("  [OK] 报告导出测试通过")

def run_all_tests():
    """运行所有测试"""
    print("=== 信任评分系统基础测试开始 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 40)
    
    tests = [
        test_initialization,
        test_score_updates,
        test_threshold_detection,
        test_permission_checking,
        test_protocol_result_application,
        test_statistics_generation,
        test_data_persistence,
        test_report_export
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            print(f"  [FAIL] {test_func.__name__} 失败: {e}")
            failed += 1
        except Exception as e:
            print(f"  [FAIL] {test_func.__name__} 异常: {type(e).__name__}: {e}")
            failed += 1
    
    print("=" * 40)
    print(f"测试完成: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有测试通过！信任评分系统基础功能正常。")
        return 0
    else:
        print("[FAIL] 部分测试失败，请检查问题。")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())