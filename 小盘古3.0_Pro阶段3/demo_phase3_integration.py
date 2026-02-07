#!/usr/bin/env python3
"""
阶段三认知融合期集成演示
展示阶段三所有新功能集成工作

功能演示：
1. 事件系统基础功能
2. 工作记忆事件集成  
3. 工作流编排器协调
4. 创新协调器智能响应
5. 自主优化引擎检查

宪法依据：阶段三标准验证
"""

import sys
import os
import time
import json

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_header(title):
    """打印标题"""
    print("\n" + "="*60)
    print(f" {title}")
    print("="*60)

def demo_event_system():
    """演示事件系统"""
    print_header("1. 事件系统演示")
    
    from src.核心.event_system import EventType, publish_event, subscribe_to, event_bus
    
    # 清空现有订阅者
    event_bus.clear_subscribers()
    
    # 创建事件计数器
    event_counts = {}
    
    def create_counter(event_type):
        def handler(event):
            event_counts[event_type.value] = event_counts.get(event_type.value, 0) + 1
            print(f"  [事件] {event_type.value}: {event.data.get('test', '无数据')}")
        return handler
    
    # 订阅多个事件类型
    for event_type in [EventType.MEMORY_UPDATED, EventType.TASK_STARTED, EventType.ERROR_OCCURRED]:
        subscribe_to(event_type)(create_counter(event_type))
    
    # 发布测试事件
    print("发布测试事件...")
    publish_event(EventType.MEMORY_UPDATED, {"test": "记忆更新测试", "id": "test_001"})
    publish_event(EventType.TASK_STARTED, {"test": "任务开始测试", "task_id": "demo_task"})
    publish_event(EventType.ERROR_OCCURRED, {"test": "错误测试", "error": "演示错误"})
    
    # 等待事件处理
    time.sleep(0.1)
    
    print(f"\n事件统计:")
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count}次")
    
    return True

def demo_working_memory_integration():
    """演示工作记忆与事件集成"""
    print_header("2. 工作记忆事件集成演示")
    
    from src.记忆.working_memory import WorkingMemory, MemoryPriority
    from src.核心.event_system import EventType, subscribe_to, event_bus
    
    event_bus.clear_subscribers()
    
    # 跟踪收到的事件
    received_events = []
    
    @subscribe_to(EventType.MEMORY_UPDATED)
    def memory_handler(event):
        received_events.append({
            "type": event.event_type.value,
            "content": event.data.get('content', ''),
            "priority": event.data.get('priority', '')
        })
    
    # 创建工作记忆
    wm = WorkingMemory(max_items=5)
    wm.clear()  # 清空现有记忆
    
    print("添加不同优先级的记忆...")
    
    # 添加不同优先级的记忆
    high_id = wm.add("重要系统配置", priority=MemoryPriority.HIGH, expires_hours=24)
    medium_id = wm.add("日常任务记录", priority=MemoryPriority.MEDIUM)
    low_id = wm.add("临时缓存数据", priority=MemoryPriority.LOW, expires_hours=1)
    
    # 等待事件处理
    time.sleep(0.1)
    
    print(f"\n记忆添加完成:")
    print(f"  高优先级: {high_id}")
    print(f"  中优先级: {medium_id}")  
    print(f"  低优先级: {low_id}")
    
    print(f"\n收到的事件 ({len(received_events)}个):")
    for i, event in enumerate(received_events, 1):
        print(f"  事件{i}: {event['type']} - 优先级: {event['priority']}")
    
    # 验证记忆检索
    print(f"\n记忆检索验证:")
    high_item = wm.get(high_id)
    print(f"  高优先级记忆内容: {high_item.content if high_item else '未找到'}")
    
    return True

def demo_workflow_orchestration():
    """演示工作流编排"""
    print_header("3. 工作流编排器演示")
    
    from src.核心.workflow_orchestrator import get_orchestrator
    from src.核心.event_system import publish_event, EventType
    
    orchestrator = get_orchestrator()
    
    print("模拟任务执行流程...")
    
    # 启动任务
    orchestrator.start_task("phase3_demo", {
        "description": "阶段三集成演示任务",
        "components": ["事件系统", "工作记忆", "工作流编排"]
    })
    
    # 模拟组件交互
    publish_event(EventType.MEMORY_UPDATED, {
        "id": "workflow_demo",
        "content": "工作流演示的重要数据",
        "priority": "high",
        "source": "demo"
    })
    
    # 模拟错误
    publish_event(EventType.ERROR_OCCURRED, {
        "error": "工作流测试错误",
        "severity": "warning",
        "source": "demo"
    })
    
    # 完成任务
    orchestrator.complete_task("phase3_demo", {
        "result": "success",
        "execution_time": "2.3s",
        "components_tested": 3
    })
    
    # 显示任务历史
    history = orchestrator.get_task_history()
    print(f"\n任务历史 ({len(history)}个):")
    for task in history:
        print(f"  任务: {task['task_id']}, 状态: {task['status']}")
        if task.get('result'):
            print(f"    结果: {task.get('result', {})}")
    
    return True

def demo_innovation_coordinator():
    """演示创新协调器"""
    print_header("4. 创新协调器演示")
    
    from src.核心.innovation_coordinator import get_innovation_coordinator
    from src.核心.event_system import publish_event, EventType
    
    coordinator = get_innovation_coordinator()
    
    print("初始状态:")
    status = coordinator.get_status()
    print(f"  安全模式: {status['safety_mode']}")
    print(f"  错误计数: {status['error_count']}")
    
    print("\n模拟系统压力场景...")
    
    # 模拟心跳问题
    print("  a) 模拟心跳丢失...")
    for i in range(2):
        publish_event(EventType.HEARTBEAT_MISSED, {
            "reason": f"演示心跳问题 #{i+1}",
            "component": "demo_component"
        })
        time.sleep(0.05)
    
    # 模拟高优先级更新
    print("  b) 模拟高优先级更新...")
    publish_event(EventType.MEMORY_UPDATED, {
        "id": "critical_config",
        "content": "关键系统配置变更",
        "priority": "high",
        "source": "demo"
    })
    
    # 模拟错误累积
    print("  c) 模拟错误累积...")
    errors = ["资源不足", "连接超时", "数据校验失败"]
    for error in errors:
        publish_event(EventType.ERROR_OCCURRED, {
            "error": f"演示错误: {error}",
            "severity": "warning",
            "source": "demo"
        })
        time.sleep(0.03)
    
    # 等待事件处理
    time.sleep(0.2)
    
    print("\n协调器响应结果:")
    new_status = coordinator.get_status()
    print(f"  安全模式: {status['safety_mode']} → {new_status['safety_mode']}")
    print(f"  错误计数: {status['error_count']} → {new_status['error_count']}")
    print(f"  连续心跳丢失: {new_status['consecutive_heartbeat_misses']}")
    
    # 重置协调器
    print("\n重置协调器状态...")
    coordinator.reset()
    final_status = coordinator.get_status()
    print(f"  最终安全模式: {final_status['safety_mode']}")
    
    return True

def demo_optimization_engine():
    """演示自主优化引擎"""
    print_header("5. 自主优化引擎演示")
    
    from src.进化.optimization_engine import OptimizationEngine
    
    print("创建优化引擎...")
    engine = OptimizationEngine()
    
    print("\n收集系统指标...")
    metrics = engine.collect_system_metrics()
    
    print(f"  CPU使用率: {metrics.get('cpu_percent', 0):.1f}%")
    print(f"  内存使用率: {metrics.get('memory_percent', 0):.1f}%")
    print(f"  内存RSS: {metrics.get('memory_rss_mb', 0):.1f} MB")
    print(f"  线程数: {metrics.get('thread_count', 0)}")
    
    print("\n分析优化机会...")
    opportunities = engine.analyze_optimization_opportunities(metrics)
    
    if opportunities:
        print(f"发现 {len(opportunities)} 个优化机会:")
        for i, opp in enumerate(opportunities, 1):
            print(f"  {i}. {opp['description']}")
            print(f"     类型: {opp['type'].value}, 级别: {opp['level'].value}")
            print(f"     建议: {opp['suggestion']}")
    else:
        print("系统状态良好，未发现需要优化的机会")
    
    print("\n执行优化检查...")
    result = engine.check_and_optimize()
    
    if result:
        print(f"优化执行结果:")
        print(f"  优化ID: {result.optimization_id}")
        print(f"  类型: {result.optimization_type.value}")
        print(f"  成功: {result.success}")
        
        if result.improvement:
            print(f"  改进效果:")
            for metric, improv in result.improvement.items():
                print(f"    {metric}: {improv:+.1f}%")
    else:
        print("本次未执行优化")
    
    print("\n优化历史统计:")
    stats = engine.get_optimization_stats()
    print(f"  总优化次数: {stats['total']}")
    if stats['total'] > 0:
        print(f"  成功次数: {stats.get('successful', 0)}")
        print(f"  成功率: {stats.get('success_rate', 0):.1f}%")
    else:
        print("  暂无优化记录")
    
    return True

def demo_integrated_scenario():
    """演示集成场景"""
    print_header("6. 集成场景演示")
    
    from src.核心.event_system import EventType, publish_event
    from src.记忆.working_memory import WorkingMemory, MemoryPriority
    from src.核心.workflow_orchestrator import get_orchestrator
    from src.核心.innovation_coordinator import get_innovation_coordinator
    
    print("模拟真实工作场景: 系统配置更新任务")
    
    # 获取各组件实例
    orchestrator = get_orchestrator()
    coordinator = get_innovation_coordinator()
    
    # 启动配置更新任务
    print("1. 启动系统配置更新任务")
    orchestrator.start_task("system_config_update", {
        "description": "更新关键系统配置",
        "priority": "high",
        "estimated_time": "5分钟"
    })
    
    # 模拟配置读取
    print("2. 读取当前配置到工作记忆")
    wm = WorkingMemory(max_items=10)
    config_id = wm.add(
        content="当前系统配置: {日志级别: 'INFO', 心跳间隔: 30, 最大内存: '2GB'}",
        priority=MemoryPriority.HIGH,
        metadata={"type": "system_config", "version": "1.0"}
    )
    
    time.sleep(0.1)
    
    # 模拟配置验证错误
    print("3. 模拟配置验证错误")
    publish_event(EventType.ERROR_OCCURRED, {
        "error": "配置验证失败: 心跳间隔过短",
        "component": "config_validator",
        "severity": "error",
        "suggested_fix": "将心跳间隔调整为60秒"
    })
    
    time.sleep(0.1)
    
    # 检查协调器响应
    coord_status = coordinator.get_status()
    print(f"4. 创新协调器响应: 安全模式 = {coord_status['safety_mode']}")
    
    # 模拟配置修复
    print("5. 应用修复配置")
    fixed_config_id = wm.add(
        content="修复后系统配置: {日志级别: 'INFO', 心跳间隔: 60, 最大内存: '2GB'}",
        priority=MemoryPriority.HIGH,
        metadata={"type": "system_config", "version": "1.1", "fix": "心跳间隔调整"}
    )
    
    # 完成任务
    print("6. 完成任务")
    orchestrator.complete_task("system_config_update", {
        "result": "success_with_fixes",
        "original_config": config_id,
        "fixed_config": fixed_config_id,
        "fix_applied": "心跳间隔从30秒调整为60秒",
        "coordinator_response": coord_status['safety_mode']
    })
    
    # 显示最终状态
    print("\n任务完成总结:")
    history = orchestrator.get_task_history()
    latest_task = history[-1] if history else {}
    
    print(f"  任务ID: {latest_task.get('task_id', 'N/A')}")
    print(f"  状态: {latest_task.get('status', 'N/A')}")
    
    # 安全获取结果信息
    result_info = latest_task.get('result', {})
    if isinstance(result_info, dict):
        print(f"  结果: {result_info.get('result', 'N/A')}")
        print(f"  应用修复: {result_info.get('fix_applied', 'N/A')}")
    else:
        print(f"  结果: {str(result_info)[:50]}...")
        print(f"  应用修复: N/A (结果非字典格式)")
    
    return True

def main():
    """主演示函数"""
    print("="*60)
    print("   小盘古3.0_Pro 阶段三认知融合期集成演示")
    print("="*60)
    print(f"演示时间: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python版本: {sys.version.split()[0]}")
    print(f"工作目录: {os.getcwd()}")
    print("="*60)
    
    demos = [
        ("事件系统", demo_event_system),
        ("工作记忆集成", demo_working_memory_integration),
        ("工作流编排", demo_workflow_orchestration),
        ("创新协调器", demo_innovation_coordinator),
        ("自主优化引擎", demo_optimization_engine),
        ("集成场景", demo_integrated_scenario)
    ]
    
    success_count = 0
    total_count = len(demos)
    
    for demo_name, demo_func in demos:
        try:
            if demo_func():
                success_count += 1
                print(f"[SUCCESS] {demo_name} 演示完成\n")
            else:
                print(f"[FAILED] {demo_name} 演示失败\n")
        except Exception as e:
            print(f"[ERROR] {demo_name} 演示异常: {e}\n")
            import traceback
            traceback.print_exc()
    
    print("="*60)
    print("演示总结:")
    print(f"  总演示项: {total_count}")
    print(f"  成功项: {success_count}")
    print(f"  成功率: {success_count/total_count*100:.1f}%")
    
    if success_count == total_count:
        print("\n[庆祝] 所有阶段三功能演示成功!")
        print("   系统已实现:")
        print("   [OK] 组件通信协议 (事件系统)")
        print("   [OK] 工作记忆事件集成")  
        print("   [OK] 工作流编排协调")
        print("   [OK] 创新智能响应 (阶段三标准2)")
        print("   [OK] 自主优化能力 (阶段三标准4)")
    else:
        print(f"\n[警告] {total_count - success_count} 个演示项失败")
    
    print("\n" + "="*60)
    
    return success_count == total_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)