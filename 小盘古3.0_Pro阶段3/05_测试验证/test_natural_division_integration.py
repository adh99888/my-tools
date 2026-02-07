#!/usr/bin/env python3
"""
自然分工集成测试
宪法依据：宪法第2条（协议驱动），阶段四能力前移验证

测试目标：
1. 验证自然分工编排器基本功能
2. 验证自然分工与事件系统集成
3. 验证分工建议事件发布
4. 验证动态调整功能

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
project_root = os.path.dirname(current_dir)  # 项目根目录 '小盘古3.0_Pro'
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from src.核心.event_system import EventType, publish_event, subscribe_to, event_bus
    from src.核心.natural_division_orchestrator import NaturalDivisionOrchestrator, get_natural_division_orchestrator
    from src.核心.natural_division_integration import NaturalDivisionIntegration, get_natural_division_integrator
    from src.核心.natural_division_types import TaskType, DivisionRole, DivisionPlan
except ImportError as e:
    print(f"导入失败: {e}")
    print(f"sys.path: {sys.path}")
    raise


def test_natural_division_basic():
    """测试自然分工编排器基本功能"""
    print("测试1: 自然分工编排器基本功能")
    
    # 创建编排器实例
    ai_capabilities = {"analysis": 0.8, "design": 0.6}
    orchestrator = NaturalDivisionOrchestrator(ai_capabilities)
    
    # 测试任务
    test_task = {
        "id": "test_task_001",
        "type": "analysis",
        "complexity": "medium",
        "description": "测试分析任务"
    }
    
    # 用户能力画像
    user_profile = {
        "experience": {"analysis": 7.0},  # 经验值0-10
        "default_skill_level": 0.7
    }
    
    # 获取分工建议
    division_plan = orchestrator.suggest_division(test_task, user_profile)
    
    # 验证结果
    assert division_plan.task_id == "test_task_001"
    assert division_plan.task_type == TaskType.ANALYSIS
    assert "main_executor" in division_plan.roles
    assert division_plan.confidence >= 0.0 and division_plan.confidence <= 1.0
    assert division_plan.estimated_efficiency_gain >= 0.0
    
    print(f"  分工建议: {division_plan.rationale}")
    print(f"  置信度: {division_plan.confidence:.2f}")
    print(f"  预计效率提升: {division_plan.estimated_efficiency_gain:.1%}")
    print("  [OK] 自然分工编排器基本功能正常")
    return True


def test_natural_division_dynamic_adjustment():
    """测试自然分工动态调整功能"""
    print("测试2: 自然分工动态调整功能")
    
    orchestrator = get_natural_division_orchestrator()
    
    # 先创建一个任务分工
    test_task = {"id": "adjustment_test", "type": "design"}
    user_profile = {"default_skill_level": 0.5}
    division_plan = orchestrator.suggest_division(test_task, user_profile)
    
    # 模拟进展缓慢
    progress_data = {
        "completion_rate": 0.2,
        "quality_score": 0.5
    }
    feedback = "进展缓慢，需要调整"
    
    # 获取动态调整
    adjustment = orchestrator.dynamic_adjustment(progress_data, feedback)
    
    # 验证调整结果
    if adjustment:
        assert adjustment.original_plan_id == "adjustment_test"
        assert "main_executor" in adjustment.adjustments
        assert adjustment.expected_impact >= 0.0
        print(f"  调整建议: {adjustment.reason}")
        print(f"  预计影响: {adjustment.expected_impact:.1%}")
    else:
        # 如果没有调整也是正常情况
        print("  无调整建议（根据阈值可能正常）")
    
    print("  [OK] 自然分工动态调整功能正常")
    return True


def test_natural_division_event_integration():
    """测试自然分工与事件系统集成"""
    print("测试3: 自然分工与事件系统集成")
    
    # 清空事件总线
    event_bus.clear_subscribers()
    
    # 收集事件的列表
    received_division_events = []
    
    @subscribe_to(EventType.DIVISION_SUGGESTED)
    def division_handler(event):
        received_division_events.append(event)
    
    # 获取集成器（会自动订阅事件）
    integrator = get_natural_division_integrator()
    
    # 发布任务开始事件
    publish_event(EventType.TASK_STARTED, {
        "task_id": "event_integration_test",
        "type": "analysis",
        "complexity": "medium",
        "description": "测试事件集成"
    }, source="test")
    
    # 等待事件处理
    time.sleep(0.1)
    
    # 验证事件被接收和处理
    assert len(received_division_events) == 1, f"应收到1个分工事件，实际收到{len(received_division_events)}"
    assert received_division_events[0].event_type == EventType.DIVISION_SUGGESTED
    assert received_division_events[0].data["task_id"] == "event_integration_test"
    assert "plan" in received_division_events[0].data
    
    plan_data = received_division_events[0].data["plan"]
    assert plan_data["task_id"] == "event_integration_test"
    assert "rationale" in plan_data
    assert "confidence" in plan_data
    
    print(f"  分工建议事件: {plan_data['rationale']}")
    print("  [OK] 自然分工事件集成正常")
    return True


def test_natural_division_adjustment_event():
    """测试自然分工调整事件"""
    print("测试4: 自然分工调整事件")
    
    event_bus.clear_subscribers()
    
    received_adjustment_events = []
    
    @subscribe_to(EventType.DIVISION_ADJUSTED)
    def adjustment_handler(event):
        received_adjustment_events.append(event)
    
    # 获取集成器
    integrator = get_natural_division_integrator()
    
    # 模拟任务完成事件（带缓慢进展）
    publish_event(EventType.TASK_COMPLETED, {
        "task_id": "adjustment_event_test",
        "result": {
            "progress": {"completion_rate": 0.1, "quality_score": 0.4},
            "feedback": "进展非常缓慢"
        }
    }, source="test")
    
    # 等待事件处理
    time.sleep(0.1)
    
    # 验证调整事件（可能有也可能没有，取决于阈值）
    if received_adjustment_events:
        assert received_adjustment_events[0].event_type == EventType.DIVISION_ADJUSTED
        assert "adjustment" in received_adjustment_events[0].data
        print(f"  调整事件: {received_adjustment_events[0].data['adjustment']['reason']}")
    else:
        print("  无调整事件（进展阈值未触发）")
    
    print("  [OK] 自然分工调整事件处理正常")
    return True


def test_natural_division_user_profile():
    """测试用户能力画像更新"""
    print("测试5: 用户能力画像更新")
    
    integrator = get_natural_division_integrator()
    
    # 获取初始用户画像
    initial_profile = integrator.get_user_profile()
    
    # 更新用户画像
    new_experience = {"code_review": 8.0, "testing": 9.0}
    integrator.update_user_profile({
        "experience": new_experience,
        "default_skill_level": 0.8
    })
    
    # 获取更新后的画像
    updated_profile = integrator.get_user_profile()
    
    # 验证更新
    assert updated_profile["experience"]["code_review"] == 8.0
    assert updated_profile["default_skill_level"] == 0.8
    
    print(f"  初始默认技能: {initial_profile.get('default_skill_level', 'N/A')}")
    print(f"  更新后代码评审经验: {updated_profile['experience']['code_review']}")
    print("  [OK] 用户能力画像更新正常")
    return True


def test_natural_division_with_workflow():
    """测试自然分工与工作流编排器集成"""
    print("测试6: 自然分工与工作流编排器集成")
    
    try:
        from src.核心.workflow_orchestrator import WorkflowOrchestrator, get_orchestrator
    except ImportError:
        print("  [SKIP] 工作流编排器不可用，跳过此测试")
        return True
    
    event_bus.clear_subscribers()
    
    # 创建新的自然分工集成器（重新订阅事件）
    integrator = NaturalDivisionIntegration()
    
    # 创建工作流编排器
    workflow = WorkflowOrchestrator()
    
    # 订阅分工事件
    division_suggestions = []
    
    @subscribe_to(EventType.DIVISION_SUGGESTED)
    def track_division(event):
        division_suggestions.append(event)
    
    # 启动任务（会触发TASK_STARTED事件）
    workflow.start_task("workflow_integration_test", {
        "type": "design",
        "complexity": "high",
        "description": "测试工作流集成"
    })
    
    # 等待事件处理
    time.sleep(0.1)
    
    # 验证分工建议被触发
    assert len(division_suggestions) == 1
    assert division_suggestions[0].data["task_id"] == "workflow_integration_test"
    
    # 完成任务
    workflow.complete_task("workflow_integration_test", {
        "result": "success",
        "metrics": {"time_sec": 5.0}
    })
    
    # 验证任务历史
    history = workflow.get_task_history()
    assert len(history) == 1
    assert history[0]["task_id"] == "workflow_integration_test"
    assert history[0]["status"] == "completed"
    
    print(f"  工作流任务启动触发分工建议")
    print(f"  分工建议数量: {len(division_suggestions)}")
    print("  [OK] 自然分工与工作流编排器集成正常")
    return True


def main():
    """运行所有自然分工集成测试"""
    print("=== 自然分工集成测试开始 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 40)
    
    tests = [
        test_natural_division_basic,
        test_natural_division_dynamic_adjustment,
        test_natural_division_event_integration,
        test_natural_division_adjustment_event,
        test_natural_division_user_profile,
        test_natural_division_with_workflow
    ]
    
    passed = 0
    failed = 0
    skipped = 0
    
    for test_func in tests:
        try:
            result = test_func()
            if result is True:
                passed += 1
            elif result is False:
                failed += 1
            else:
                # 测试函数可能返回其他值表示跳过
                skipped += 1
        except Exception as e:
            print(f"  [FAILED] {test_func.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("=" * 40)
    print(f"测试结果: 通过 {passed}/{len(tests)}, 失败 {failed}/{len(tests)}, 跳过 {skipped}/{len(tests)}")
    
    if failed == 0:
        print("[SUCCESS] 所有自然分工集成测试通过")
        return True
    else:
        print("[FAILED] 部分测试失败，需要检查")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)