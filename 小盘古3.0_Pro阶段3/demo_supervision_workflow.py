#!/usr/bin/env python3
"""
监督机制工作流演示
展示阶段二用户监督机制的实际效果
"""

import time
from src.核心.workflow_orchestrator import get_orchestrator
from src.核心.supervision_interface import get_supervision_interface
from src.核心.trust_system import TrustSystem

def demo_supervision_workflow():
    """演示监督工作流"""
    print("=== 阶段二用户监督机制工作流演示 ===\n")
    
    # 获取组件实例
    orchestrator = get_orchestrator()
    supervision = get_supervision_interface()
    trust_system = TrustSystem()
    
    # 显示当前信任分
    current_trust = trust_system.get_current_score()
    print(f"当前系统信任分: {current_trust:.1f}")
    print(f"监督强度级别: {'minimal' if current_trust > 80 else 'low' if current_trust > 60 else 'medium' if current_trust > 30 else 'high'}")
    print()
    
    # 1. 启动一个测试任务
    print("1. 启动测试任务...")
    task_id = "demo_supervision_task"
    task_data = {
        "goal": "演示监督机制：创建用户文档并部署",
        "description": "这是一个演示任务，用于展示监督机制的完整工作流程",
        "user_id": "demo_user",
        "estimated_duration": 300,  # 5分钟
        "priority": "medium"
    }
    
    orchestrator.start_task(task_id, task_data)
    print(f"   任务ID: {task_id}")
    print(f"   任务目标: {task_data['goal']}")
    print()
    
    # 等待片刻，让事件处理
    time.sleep(0.5)
    
    # 2. 显示活跃任务
    print("2. 当前活跃监督任务:")
    active_tasks = supervision.display_active_tasks()
    if active_tasks:
        for task in active_tasks:
            print(f"   - {task['任务ID']}: {task['目标']}")
            print(f"     进度: {task['进度']}, 状态: {task['状态']}, 监督级别: {task['监督级别']}")
    else:
        print("   无活跃监督任务")
    print()
    
    # 3. 显示任务详情
    print("3. 任务详情:")
    details = supervision.show_task_details(task_id)
    if details:
        print(f"   任务ID: {details['任务ID']}")
        print(f"   用户ID: {details['用户ID']}")
        print(f"   总进度: {details['总进度']}")
        print(f"   状态: {details['状态']}")
        print(f"   监督级别: {details['监督级别']}")
        print(f"   当前步骤: {details['当前步骤']}/{details['总步骤数']}")
        print(f"   待审批数: {details['待审批数']}")
        
        if details['步骤详情']:
            print(f"   步骤分解:")
            for i, step in enumerate(details['步骤详情']):
                print(f"     {i+1}. {step['名称']} ({step['预计时长']}) - 需审批: {step['需审批']}")
    else:
        print("   任务详情不可用")
    print()
    
    # 4. 生成进度报告
    print("4. 生成监督进度报告:")
    report = supervision.generate_progress_report(task_id)
    if report:
        print(f"   报告ID: {report['报告ID']}")
        print(f"   报告类型: {report['报告类型']}")
        print(f"   需用户操作: {report['需用户操作']}")
    else:
        print("   无法生成报告")
    print()
    
    # 5. 模拟审批流程（如果有待审批）
    print("5. 审批流程演示:")
    pending_approvals = supervision.list_pending_approvals()
    if pending_approvals:
        print(f"   发现 {len(pending_approvals)} 个待审批请求")
        for i, approval in enumerate(pending_approvals):
            print(f"   {i+1}. 审批ID: {approval['审批ID']}")
            print(f"      任务: {approval['任务目标']}")
            print(f"      类型: {approval['审批类型']}")
            print(f"      等待时间: {approval['等待时间秒数']:.1f}秒")
            
            # 模拟用户批准第一个审批请求
            if i == 0:
                print(f"      → 模拟用户批准此请求...")
                success = supervision.submit_approval_decision(
                    approval['审批ID'], 
                    "approved",
                    "演示批准：继续执行"
                )
                if success:
                    print(f"      ✓ 审批已批准")
                else:
                    print(f"      ✗ 审批处理失败")
    else:
        print("   当前无待审批请求")
    print()
    
    # 6. 自适应监督演示
    print("6. 自适应监督机制演示:")
    from src.核心.trust_adaptive_supervisor import get_trust_adaptive_supervisor
    adaptive_supervisor = get_trust_adaptive_supervisor()
    
    # 评估任务表现
    performance = adaptive_supervisor.evaluate_task_performance(task_id)
    print(f"   任务表现评估: {performance:.2f}/1.0")
    
    # 获取推荐的监督配置
    config = adaptive_supervisor.get_recommended_supervision_config(task_id)
    print(f"   推荐监督配置:")
    print(f"     - 信任分: {config.trust_score:.1f}")
    print(f"     - 审批频率: {config.approval_frequency}")
    print(f"     - 报告频率: {config.report_frequency}分钟")
    print(f"     - 自主决策范围: {config.autonomous_decision_range}")
    print()
    
    # 7. 完成任务
    print("7. 完成任务演示:")
    result = {
        "status": "completed",
        "metrics": {
            "total_time": 120.5,
            "quality_score": 0.9,
            "user_satisfaction": 0.95
        }
    }
    orchestrator.complete_task(task_id, result)
    print(f"   任务 {task_id} 已完成")
    print(f"   结果: {result['status']}")
    print(f"   质量评分: {result['metrics']['quality_score']:.2f}")
    print()
    
    # 8. 最终状态
    print("8. 最终状态:")
    print(f"   系统信任分: {trust_system.get_current_score():.1f} (保持不变)")
    print(f"   监督任务历史: {len(orchestrator.get_task_history())} 个任务记录")
    
    print("\n=== 监督机制演示完成 ===")
    print("""
总结:
1. [OK] 任务启动时自动创建监督任务
2. [OK] 基于信任分自动分解任务步骤
3. [OK] 提供实时任务详情和进度报告
4. [OK] 支持用户审批流程
5. [OK] 自适应监督强度调整
6. [OK] 与现有工作流无缝集成
    """)

if __name__ == "__main__":
    demo_supervision_workflow()