#!/usr/bin/env python3
"""
阶段二用户监督机制集成测试
宪法依据：宪法第5条（审查必行原则），阶段二用户监督机制设计
设计约束：全面测试监督机制各组件，确保宪法合规
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.核心.task_supervisor import TaskSupervisor
from src.核心.supervision_interface import SupervisionInterface
from src.核心.trust_adaptive_supervisor import TrustAdaptiveSupervisor
from src.核心.supervision_types import ApprovalType, ApprovalStatus
from src.核心.event_system import EventType
import time

def test_supervision_basic_workflow():
    """测试基本监督工作流"""
    print("=== 测试1: 基本监督工作流 ===")
    
    # 创建监督器
    supervisor = TaskSupervisor()
    
    # 启动监督任务
    task_id = supervisor.start_supervised_task("测试任务: 分析项目结构", "test_user")
    print(f"任务已启动: ID={task_id}")
    
    # 获取活跃任务
    active_tasks = supervisor.get_active_tasks()
    print(f"活跃任务数: {len(active_tasks)}")
    assert len(active_tasks) == 1, "应该有1个活跃任务"
    
    # 检查任务详情
    if task_id in supervisor.active_tasks:
        task = supervisor.active_tasks[task_id]
        print(f"任务目标: {task.goal}")
        print(f"信任分: {task.trust_score}")
        print(f"监督级别: {task.supervision_level}")
        print(f"步骤数: {len(task.steps)}")
        print(f"待审批数: {len(task.approval_pending)}")
        
        assert task.goal == "测试任务: 分析项目结构"
        assert task.trust_score > 0
        assert task.supervision_level in ["high", "medium", "low", "minimal"]
        assert len(task.steps) > 0
    
    # 生成进度报告
    report = supervisor.generate_progress_report(task_id)
    if report:
        print(f"进度报告生成: ID={report.report_id}")
        print(f"进度: {report.content.get('progress', 0):.1f}%")
        assert report.content.get('progress', 0) >= 0
    
    print("  [OK] 基本监督工作流测试通过")

def test_approval_process():
    """测试审批流程"""
    print("\n=== 测试2: 审批流程 ===")
    
    supervisor = TaskSupervisor()
    task_id = supervisor.start_supervised_task("测试审批流程任务", "test_user")
    
    # 检查是否有启动审批
    if task_id in supervisor.active_tasks:
        task = supervisor.active_tasks[task_id]
        
        # 如果有待审批，测试审批处理
        if task.approval_pending:
            approval_id = task.approval_pending[0]
            
            # 处理审批
            success = supervisor.process_approval(approval_id, "approved", "测试批准")
            print(f"审批处理结果: {success}")
            
            # 检查审批状态
            if approval_id in supervisor.approval_requests:
                approval = supervisor.approval_requests[approval_id]
                print(f"审批状态: {approval.status.value}")
                print(f"用户决定: {approval.user_decision}")
                print(f"用户备注: {approval.user_notes}")
                
                assert approval.status == ApprovalStatus.APPROVED
                assert approval.user_decision == "approved"
                assert approval.user_notes == "测试批准"
            
            # 检查任务待审批列表是否已更新
            updated_task = supervisor.active_tasks[task_id]
            print(f"处理后待审批数: {len(updated_task.approval_pending)}")
    
    print("  [OK] 审批流程测试通过")

def test_supervision_interface():
    """测试监督界面"""
    print("\n=== 测试3: 监督界面 ===")
    
    interface = SupervisionInterface()
    
    # 启动任务
    task_id = interface.supervisor.start_supervised_task("测试界面任务", "test_user")
    print(f"界面任务ID: {task_id}")
    
    # 显示活跃任务
    active_tasks = interface.display_active_tasks()
    print(f"界面显示任务数: {len(active_tasks)}")
    
    # 显示任务详情
    task_details = interface.show_task_details(task_id)
    if task_details:
        print(f"任务目标: {task_details.get('目标', 'N/A')}")
        print(f"任务进度: {task_details.get('总进度', 'N/A')}")
        print(f"监督级别: {task_details.get('监督级别', 'N/A')}")
    
    # 列出待审批
    pending_approvals = interface.list_pending_approvals()
    print(f"待审批数: {len(pending_approvals)}")
    
    # 生成进度报告
    report = interface.generate_progress_report(task_id)
    if report:
        print(f"报告生成成功: {report.get('报告类型', 'N/A')}")
    
    print("  [OK] 监督界面测试通过")

def test_trust_adaptive_supervisor():
    """测试信任自适应监督器"""
    print("\n=== 测试4: 信任自适应监督器 ===")
    
    adaptive_supervisor = TrustAdaptiveSupervisor()
    
    # 启动任务
    task_id = adaptive_supervisor.supervisor.start_supervised_task("测试自适应任务", "test_user")
    print(f"自适应任务ID: {task_id}")
    
    # 评估任务表现
    performance = adaptive_supervisor.evaluate_task_performance(task_id)
    print(f"任务表现评估: {performance:.2f}")
    assert 0.0 <= performance <= 1.0
    
    # 获取推荐监督配置
    config = adaptive_supervisor.get_recommended_supervision_config(task_id)
    print(f"推荐监督配置:")
    print(f"  信任分: {config.trust_score}")
    print(f"  审批频率: {config.approval_frequency}")
    print(f"  报告频率: {config.report_frequency}分钟")
    
    # 根据表现调整监督级别
    adaptive_supervisor.adjust_supervision_level(task_id, performance)
    
    # 更新信任分
    adaptive_supervisor.update_trust_based_on_performance(task_id)
    
    print("  [OK] 信任自适应监督器测试通过")

def test_event_system_integration():
    """测试事件系统集成"""
    print("\n=== 测试5: 事件系统集成 ===")
    
    # 记录事件订阅情况
    from src.核心.event_system import event_bus
    
    event_counts = {}
    
    def count_event(event):
        event_type = event.event_type.value
        event_counts[event_type] = event_counts.get(event_type, 0) + 1
    
    # 订阅监督相关事件
    for event_type in [EventType.TASK_SUPERVISION_STARTED, EventType.APPROVAL_REQUESTED, 
                       EventType.APPROVAL_RECEIVED, EventType.SUPERVISION_REPORT_GENERATED]:
        event_bus.subscribe(event_type, count_event)
    
    # 启动监督任务（应触发TASK_SUPERVISION_STARTED事件）
    supervisor = TaskSupervisor()
    task_id = supervisor.start_supervised_task("测试事件集成任务", "test_user")
    
    # 生成报告（应触发SUPERVISION_REPORT_GENERATED事件）
    supervisor.generate_progress_report(task_id)
    
    # 检查事件计数
    print(f"事件触发统计:")
    for event_type, count in event_counts.items():
        print(f"  {event_type}: {count}次")
    
    # 至少应该有监督开始事件
    assert event_counts.get("task_supervision_started", 0) >= 1
    
    print("  [OK] 事件系统集成测试通过")

def test_constitutional_compliance():
    """测试宪法合规"""
    print("\n=== 测试6: 宪法合规测试 ===")
    
    import os
    
    # 检查所有监督模块行数≤200行
    supervision_modules = [
        "src/核心/supervision_types.py",
        "src/核心/task_supervisor.py",
        "src/核心/supervision_interface.py",
        "src/核心/trust_adaptive_supervisor.py"
    ]
    
    all_compliant = True
    for module_path in supervision_modules:
        if os.path.exists(module_path):
            with open(module_path, 'r', encoding='utf-8') as f:
                lines = len(f.readlines())
                status = "PASS" if lines <= 200 else "FAIL"
                print(f"{status} {os.path.basename(module_path)}: {lines}行")
                if lines > 200:
                    all_compliant = False
        else:
            print(f"WARNING 文件不存在: {module_path}")
    
    assert all_compliant, "有模块违反宪法第1条（≤200行）"
    
    print("  [OK] 宪法合规测试通过")

def main():
    """主测试函数"""
    print("=== 阶段二用户监督机制集成测试开始 ===")
    print(f"Python版本: {sys.version}")
    print(f"工作目录: {os.getcwd()}")
    print("=" * 40)
    
    test_count = 0
    passed_count = 0
    
    tests = [
        test_supervision_basic_workflow,
        test_approval_process,
        test_supervision_interface,
        test_trust_adaptive_supervisor,
        test_event_system_integration,
        test_constitutional_compliance
    ]
    
    for test_func in tests:
        try:
            test_func()
            test_count += 1
            passed_count += 1
        except Exception as e:
            test_count += 1
            print(f"  [FAIL] 测试失败: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 40)
    print(f"测试结果: 通过 {passed_count}/{test_count}")
    
    if passed_count == test_count:
        print("[SUCCESS] 所有阶段二用户监督机制测试通过")
    else:
        print(f"[FAILURE] {test_count - passed_count}个测试失败")
    
    return passed_count == test_count

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)