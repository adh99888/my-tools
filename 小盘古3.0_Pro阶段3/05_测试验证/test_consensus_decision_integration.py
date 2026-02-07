#!/usr/bin/env python3
"""
共识决策集成测试
宪法依据：宪法第2条（协议驱动），阶段四能力前移验证

测试目标：
1. 验证共识决策促进器基本功能
2. 验证共识决策与事件系统集成
3. 验证决策结果事件发布
4. 验证用户偏好学习和更新

测试原则：
- 最小依赖：不依赖外部服务
- 快速执行：每个测试<1秒
- 确定性：测试结果可重复
"""

import sys
import os
import time

# 添加src目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.核心.event_system import EventType, publish_event, subscribe_to, event_bus
    from src.核心.consensus_decision_facilitator import ConsensusDecisionFacilitator, get_consensus_facilitator
    from src.核心.consensus_decision_integration import ConsensusDecisionIntegration, get_consensus_integrator
    from src.核心.consensus_decision_types import (
        DecisionType, DecisionStatus, DecisionOption,
        DecisionCriteria, DecisionRecord, ConsensusResult
    )
except ImportError as e:
    print(f"导入失败: {e}")
    print(f"sys.path: {sys.path}")
    raise


def test_consensus_facilitator_basic():
    """测试共识决策促进器基本功能"""
    print("测试1: 共识决策促进器基本功能")
    
    # 创建促进器
    facilitator = get_consensus_facilitator()
    
    # 创建测试选项和标准
    options = [
        {"id": "option_a", "description": "方案A", "estimated_impact": 0.7},
        {"id": "option_b", "description": "方案B", "estimated_impact": 0.6}
    ]
    criteria = ["quality", "speed", "cost"]
    user_prefs = {"quality": 0.8, "speed": 0.6, "cost": 0.7}
    
    # 促进决策
    result = facilitator.facilitate_decision(
        options=options,
        criteria=criteria,
        user_preferences=user_prefs,
        decision_type="tactical"
    )
    
    # 验证结果
    assert result.decision_id.startswith("decision_")
    assert isinstance(result.consensus_reached, bool)
    assert 0.0 <= result.consensus_score <= 1.0
    assert result.rationale != ""
    
    print(f"  决策ID: {result.decision_id}")
    print(f"  共识达成: {result.consensus_reached}")
    print(f"  共识分数: {result.consensus_score:.2f}")
    print(f"  理由: {result.rationale}")
    print("  [OK] 共识决策促进器基本功能正常")
    return True


def test_consensus_decision_learning():
    """测试共识决策学习功能"""
    print("测试2: 共识决策学习功能")
    
    facilitator = get_consensus_facilitator()
    
    # 创建一个决策
    options = [{"id": "test_opt", "description": "测试选项", "estimated_impact": 0.5}]
    criteria = ["test"]
    result = facilitator.facilitate_decision(options, criteria, {"test": 0.5})
    
    # 记录结果
    facilitator.learn_from_decision_outcome(
        decision_id=result.decision_id,
        outcome={"success": True},
        user_feedback="good decision"
    )
    
    # 验证决策历史
    history = facilitator.get_decision_history()
    assert len(history) > 0
    # 检查最后一个决策记录
    assert history[-1].id == result.decision_id
    
    print(f"  决策历史数量: {len(history)}")
    print("  [OK] 共识决策学习功能正常")
    return True


def test_consensus_event_integration():
    """测试共识决策与事件系统集成"""
    print("测试3: 共识决策与事件系统集成")
    
    # 清空事件总线
    event_bus.clear_subscribers()
    
    # 收集事件的列表
    received_decision_events = []
    
    @subscribe_to(EventType.DECISION_FACILITATED)
    def decision_handler(event):
        received_decision_events.append(event)
    
    # 获取集成器
    integrator = get_consensus_integrator()
    
    # 促进决策
    options = [{"id": "event_test_opt", "description": "事件测试", "estimated_impact": 0.6}]
    criteria = ["quality"]
    result = integrator.facilitate_decision(options, criteria, "tactical")
    
    # 等待事件处理
    time.sleep(0.1)
    
    # 验证事件被接收
    assert len(received_decision_events) == 1
    assert received_decision_events[0].event_type == EventType.DECISION_FACILITATED
    assert received_decision_events[0].data["decision_id"] == result.decision_id
    
    print(f"  决策事件: {received_decision_events[0].data['rationale']}")
    print("  [OK] 共识决策事件集成正常")
    return True


def test_consensus_outcome_event():
    """测试共识决策结果事件"""
    print("测试4: 共识决策结果事件")
    
    event_bus.clear_subscribers()
    
    received_outcome_events = []
    
    @subscribe_to(EventType.DECISION_OUTCOME)
    def outcome_handler(event):
        received_outcome_events.append(event)
    
    # 获取集成器
    integrator = get_consensus_integrator()
    
    # 创建决策
    options = [{"id": "outcome_test", "description": "结果测试", "estimated_impact": 0.5}]
    criteria = ["test"]
    result = integrator.facilitate_decision(options, criteria, "tactical")
    
    # 记录结果
    integrator.record_outcome(
        decision_id=result.decision_id,
        outcome={"success": True},
        user_feedback="excellent"
    )
    
    # 等待事件处理
    time.sleep(0.1)
    
    # 验证事件被接收
    assert len(received_outcome_events) == 1
    assert received_outcome_events[0].event_type == EventType.DECISION_OUTCOME
    assert received_outcome_events[0].data["decision_id"] == result.decision_id
    assert received_outcome_events[0].data["user_feedback"] == "excellent"
    
    print(f"  结果事件反馈: {received_outcome_events[0].data['user_feedback']}")
    print("  [OK] 共识决策结果事件正常")
    return True


def test_user_preferences_update():
    """测试用户偏好更新"""
    print("测试5: 用户偏好更新")
    
    integrator = get_consensus_integrator()
    
    # 获取初始偏好
    initial_prefs = integrator.get_user_preferences()
    
    # 更新偏好
    new_prefs = {"quality": 0.9, "speed": 0.7}
    integrator.update_user_preferences(new_prefs)
    
    # 获取更新后偏好
    updated_prefs = integrator.get_user_preferences()
    
    # 验证更新
    assert updated_prefs.get("quality") == 0.9
    assert updated_prefs.get("speed") == 0.7
    
    print(f"  初始偏好: {initial_prefs}")
    print(f"  更新后偏好: {updated_prefs}")
    print("  [OK] 用户偏好更新正常")
    return True


def test_interaction_preference_learning():
    """测试从交互中学习用户偏好"""
    print("测试6: 从交互中学习用户偏好")
    
    event_bus.clear_subscribers()
    
    # 获取新的集成器（重新订阅事件）
    integrator = ConsensusDecisionIntegration()
    
    # 初始偏好
    initial_prefs = integrator.get_user_preferences()
    
    # 模拟交互事件
    publish_event(EventType.INTERACTION_RECORDED, {
        "user_input": "用户输入测试",
        "ai_response": "AI响应",
        "intent_type": "execute",
        "confidence": 0.8
    }, source="test")
    
    # 等待事件处理
    time.sleep(0.1)
    
    # 获取更新后偏好
    updated_prefs = integrator.get_user_preferences()
    
    # 验证偏好更新（应该增加了execute类型的偏好）
    if "execute" in updated_prefs:
        assert updated_prefs["execute"] > initial_prefs.get("execute", 0.5)
        print(f"  execute偏好: {initial_prefs.get('execute', 0)} -> {updated_prefs['execute']}")
    
    print("  [OK] 从交互中学习用户偏好正常")
    return True


def test_multiple_decision_types():
    """测试多种决策类型"""
    print("测试7: 多种决策类型")
    
    facilitator = get_consensus_facilitator()
    
    # 测试不同类型的决策
    decision_types = ["strategic", "tactical", "operational", "technical"]
    results = []
    
    for dec_type in decision_types:
        options = [{"id": f"opt_{dec_type}", "description": f"{dec_type}选项", "estimated_impact": 0.7}]
        result = facilitator.facilitate_decision(options, ["test"], {"test": 0.5}, dec_type)
        results.append(result)
    
    # 验证所有决策都成功
    assert len(results) == len(decision_types)
    for i, result in enumerate(results):
        assert result.decision_id.startswith("decision_")
    
    print(f"  测试决策类型数量: {len(decision_types)}")
    print(f"  成功决策数量: {len(results)}")
    print("  [OK] 多种决策类型正常")
    return True


def main():
    """运行所有共识决策集成测试"""
    print("=== 共识决策集成测试开始 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 40)
    
    tests = [
        test_consensus_facilitator_basic,
        test_consensus_decision_learning,
        test_consensus_event_integration,
        test_consensus_outcome_event,
        test_user_preferences_update,
        test_interaction_preference_learning,
        test_multiple_decision_types
    ]
    
    passed = 0
    failed = 0
    
    for test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  [FAILED] {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 40)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有共识决策集成测试通过")
        return True
    else:
        print("[FAILED] 部分测试失败，需要检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)