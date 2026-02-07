#!/usr/bin/env python3
"""
事件系统集成测试
宪法依据：宪法第2条（协议驱动），阶段三P1任务验证

测试目标：
1. 验证事件系统基本功能
2. 验证工作记忆与事件系统集成
3. 验证工作流编排器事件协调
4. 验证多组件事件传递

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
    from src.记忆.working_memory import WorkingMemory, MemoryPriority
    from src.核心.workflow_orchestrator import WorkflowOrchestrator
    from src.守护者.heartbeat_monitor import HeartbeatMonitor
except ImportError as e:
    print(f"导入失败: {e}")
    print(f"sys.path: {sys.path}")
    raise

def test_basic_event_system():
    """测试基础事件系统功能"""
    print("测试1: 基础事件系统功能")
    
    # 清空事件总线
    event_bus.clear_subscribers()
    
    # 收集事件的列表
    received_events = []
    
    @subscribe_to(EventType.MEMORY_UPDATED)
    def test_handler(event):
        received_events.append(event)
    
    # 发布测试事件
    test_data = {"test": "data", "id": "test_001"}
    publish_event(EventType.MEMORY_UPDATED, test_data, "test")
    
    # 等待事件处理
    time.sleep(0.1)
    
    assert len(received_events) == 1, f"应收到1个事件，实际收到{len(received_events)}"
    assert received_events[0].event_type == EventType.MEMORY_UPDATED
    assert received_events[0].data["test"] == "data"
    assert received_events[0].source == "test"
    
    print("  [OK] 基础事件发布-订阅功能正常")
    return True

def test_working_memory_event_integration():
    """测试工作记忆与事件系统集成"""
    print("测试2: 工作记忆与事件系统集成")
    
    event_bus.clear_subscribers()
    received_events = []
    
    @subscribe_to(EventType.MEMORY_UPDATED)
    def memory_handler(event):
        received_events.append(event)
    
    # 创建工作记忆实例
    wm = WorkingMemory(max_items=10)
    wm.clear()  # 清空现有记忆
    
    # 添加记忆（应触发事件）
    item_id = wm.add(
        content="测试事件集成内容",
        priority=MemoryPriority.MEDIUM,
        expires_hours=1.0,
        metadata={"test": "metadata"}
    )
    
    # 等待事件处理
    time.sleep(0.1)
    
    assert len(received_events) == 1, f"应收到1个事件，实际收到{len(received_events)}"
    assert received_events[0].event_type == EventType.MEMORY_UPDATED
    assert "content" in received_events[0].data
    assert received_events[0].data["priority"] == "medium"
    
    # 验证记忆内容
    item = wm.get(item_id)
    assert item is not None
    assert item.content == "测试事件集成内容"
    assert item.priority == MemoryPriority.MEDIUM
    
    print("  [OK] 工作记忆事件集成正常")
    return True

def test_workflow_orchestrator_integration():
    """测试工作流编排器事件协调"""
    print("测试3: 工作流编排器事件协调")
    
    event_bus.clear_subscribers()
    
    # 创建工作流编排器（会自动订阅事件）
    orchestrator = WorkflowOrchestrator()
    
    # 启动测试任务
    orchestrator.start_task("integration_test", {"description": "集成测试"})
    
    # 模拟记忆更新事件
    publish_event(EventType.MEMORY_UPDATED, {
        "id": "workflow_test",
        "content": "工作流编排测试内容",
        "priority": "high",
        "source": "test"
    })
    
    # 模拟错误事件
    publish_event(EventType.ERROR_OCCURRED, {
        "error": "测试错误：心跳超时",
        "source": "test"
    })
    
    # 完成任务
    orchestrator.complete_task("integration_test", {"result": "success"})
    
    # 获取任务历史
    history = orchestrator.get_task_history()
    assert len(history) == 1
    assert history[0]["task_id"] == "integration_test"
    assert history[0]["status"] == "completed"
    
    print("  [OK] 工作流编排器事件协调正常")
    return True

def test_multi_component_event_flow():
    """测试多组件事件流"""
    print("测试4: 多组件事件流")
    
    event_bus.clear_subscribers()
    
    # 创建事件计数器
    event_counts = {
        EventType.MEMORY_UPDATED: 0,
        EventType.HEARTBEAT_MISSED: 0,
        EventType.TASK_STARTED: 0,
        EventType.TASK_COMPLETED: 0,
        EventType.ERROR_OCCURRED: 0
    }
    
    # 创建通用事件处理器
    def create_counter_handler(event_type):
        def handler(event):
            event_counts[event_type] += 1
        return handler
    
    # 订阅多个事件类型
    for event_type in event_counts.keys():
        subscribe_to(event_type)(create_counter_handler(event_type))
    
    # 模拟多组件交互场景
    publish_event(EventType.TASK_STARTED, {"task_id": "multi_component_test"})
    
    # 工作记忆更新
    wm = WorkingMemory(max_items=5)
    wm.add("多组件测试内容", priority=MemoryPriority.HIGH)
    
    # 模拟心跳丢失
    publish_event(EventType.HEARTBEAT_MISSED, {"reason": "组件协调测试"})
    
    # 模拟错误
    publish_event(EventType.ERROR_OCCURRED, {"error": "组件通信超时"})
    
    # 完成任务
    publish_event(EventType.TASK_COMPLETED, {"task_id": "multi_component_test"})
    
    # 等待事件处理
    time.sleep(0.2)
    
    # 验证事件计数
    assert event_counts[EventType.TASK_STARTED] == 1
    assert event_counts[EventType.MEMORY_UPDATED] == 1
    assert event_counts[EventType.HEARTBEAT_MISSED] == 1
    assert event_counts[EventType.ERROR_OCCURRED] == 1
    assert event_counts[EventType.TASK_COMPLETED] == 1
    
    print("  [OK] 多组件事件流正常")
    return True

def test_priority_enum_usage():
    """测试优先级枚举正确使用（修复KeyError问题）"""
    print("测试5: 优先级枚举正确使用")
    
    # 测试正确的优先级枚举用法
    wm = WorkingMemory(max_items=5)
    
    # 测试各种优先级设置
    test_cases = [
        (MemoryPriority.HIGH, "high"),
        (MemoryPriority.MEDIUM, "medium"),
        (MemoryPriority.LOW, "low")
    ]
    
    for priority_enum, expected_value in test_cases:
        item_id = wm.add(f"测试优先级 {expected_value}", priority=priority_enum)
        item = wm.get(item_id)
        assert item is not None
        assert item.priority == priority_enum
        assert item.priority.value == expected_value
        
        # 验证PRIORITY_ORDER字典正确访问
        priority_order = wm.PRIORITY_ORDER
        assert priority_order[priority_enum] in [0, 1, 2]
    
    print("  [OK] 优先级枚举使用正确，无KeyError")
    return True

def main():
    """运行所有集成测试"""
    print("=== 事件系统集成测试开始 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 40)
    
    tests = [
        test_basic_event_system,
        test_working_memory_event_integration,
        test_workflow_orchestrator_integration,
        test_multi_component_event_flow,
        test_priority_enum_usage
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
        print("[SUCCESS] 所有事件系统集成测试通过")
        return True
    else:
        print("[FAILED] 部分测试失败，需要检查")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)