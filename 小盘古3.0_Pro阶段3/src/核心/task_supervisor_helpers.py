#!/usr/bin/env python3
"""
任务监督器辅助函数
宪法依据：宪法第1条（最小生命单元原则）
设计约束：≤200行代码，包含TaskSupervisor的辅助函数
"""

from typing import Dict, List
import time
import uuid
from .supervision_types import TaskStep, ApprovalRequest, ApprovalType, ApprovalStatus
from .event_system import EventType, publish_event

def decompose_task(task_goal: str, trust_score: float) -> List[TaskStep]:
    """根据信任分分解任务"""
    steps = []
    
    if trust_score < 60:
        # 细粒度分解（3-5步，每步需审批）
        step_count = 4
        for i in range(step_count):
            step = TaskStep(
                step_id=f"step_{i}",
                step_name=f"步骤 {i+1}",
                description=f"任务 '{task_goal}' 的第 {i+1} 步",
                requires_approval=True,
                approval_type=ApprovalType.CRITICAL_STEP_APPROVAL,
                estimated_duration=5.0,
                dependencies=[f"step_{i-1}"] if i > 0 else []
            )
            steps.append(step)
    elif trust_score < 80:
        # 中粒度分解（2-3步，关键步骤审批）
        step_count = 3
        for i in range(step_count):
            step = TaskStep(
                step_id=f"step_{i}",
                step_name=f"阶段 {i+1}",
                description=f"任务 '{task_goal}' 的第 {i+1} 阶段",
                requires_approval=(i == 0 or i == step_count - 1),  # 开始和结束需审批
                approval_type=ApprovalType.CRITICAL_STEP_APPROVAL if i == 0 else ApprovalType.COMPLETION_CONFIRMATION,
                estimated_duration=10.0,
                dependencies=[f"step_{i-1}"] if i > 0 else []
            )
            steps.append(step)
    else:
        # 粗粒度分解（1-2步，仅最终结果审批）
        step_count = 2
        for i in range(step_count):
            step = TaskStep(
                step_id=f"step_{i}",
                step_name=f"主要阶段 {i+1}",
                description=f"任务 '{task_goal}' 的第 {i+1} 主要阶段",
                requires_approval=(i == step_count - 1),  # 仅最后阶段需审批
                approval_type=ApprovalType.COMPLETION_CONFIRMATION,
                estimated_duration=15.0,
                dependencies=[f"step_{i-1}"] if i > 0 else []
            )
            steps.append(step)
    
    return steps

def create_approval_request(task_id: str, approval_type: ApprovalType, data: Dict, 
                           approval_requests: Dict[str, ApprovalRequest],
                           active_tasks: Dict) -> str:
    """创建审批请求"""
    approval_id = f"approval_{uuid.uuid4().hex[:8]}"
    
    approval_request = ApprovalRequest(
        approval_id=approval_id,
        task_id=task_id,
        approval_type=approval_type,
        request_time=time.time(),
        data=data,
        status=ApprovalStatus.PENDING,
        user_decision=None,
        user_notes=None,
        response_time=None
    )
    
    approval_requests[approval_id] = approval_request
    
    # 添加到任务的待审批列表
    if task_id in active_tasks:
        active_tasks[task_id].approval_pending.append(approval_id)
    
    # 发布审批请求事件
    publish_event(EventType.APPROVAL_REQUESTED, {
        "approval_id": approval_id,
        "task_id": task_id,
        "approval_type": approval_type.value,
        "data": data
    }, source="task_supervisor")
    
    return approval_id

def get_supervision_level(trust_score: float) -> str:
    """根据信任分获取监督级别"""
    if trust_score < 30:
        return "high"
    elif trust_score < 60:
        return "medium"
    elif trust_score < 80:
        return "low"
    else:
        return "minimal"

def calculate_progress(task, current_time: float) -> float:
    """计算任务进度"""
    if task.status == "completed":
        return 100.0
    elif task.status == "failed":
        return task.progress
    else:
        elapsed = current_time - task.start_time
        total_estimated = task.estimated_completion_time - task.start_time
        return min(100.0, (elapsed / total_estimated * 100) if total_estimated > 0 else 0)

def format_task_for_display(task) -> Dict:
    """格式化任务用于显示"""
    return {
        "task_id": task.task_id,
        "goal": task.goal,
        "progress": task.progress,
        "status": task.status,
        "supervision_level": task.supervision_level,
        "approvals_pending": len(task.approval_pending)
    }