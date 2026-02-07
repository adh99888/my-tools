#!/usr/bin/env python3
"""
任务监督器 - 核心监督组件
宪法依据：宪法第3条（认知对齐优先），宪法第4条（生存优先）
设计约束：≤200行代码，支持监督任务全生命周期管理
"""

from typing import Dict, List, Optional
import time
import uuid
from .event_system import EventType, publish_event
from .supervision_types import (
    SupervisedTask, SupervisionReport, ApprovalRequest,
    ApprovalType, ApprovalStatus
)
from .trust_system import TrustSystem
from .task_supervisor_helpers import (
    decompose_task, create_approval_request, get_supervision_level,
    calculate_progress, format_task_for_display
)

class TaskSupervisor:
    """任务监督器 - 核心监督组件"""
    
    def __init__(self):
        self.active_tasks: Dict[str, SupervisedTask] = {}
        self.approval_requests: Dict[str, ApprovalRequest] = {}
        self.task_history: List[Dict] = []
        self.trust_system = TrustSystem()
    
    def start_supervised_task(self, task_goal: str, user_id: str = "default", task_id: Optional[str] = None) -> str:
        """启动监督任务"""
        if task_id is None:
            task_id = f"task_{uuid.uuid4().hex[:8]}"
        trust_score = self.trust_system.get_current_score()
        
        # 根据信任分分解任务
        steps = decompose_task(task_goal, trust_score)
        
        # 创建监督任务
        supervised_task = SupervisedTask(
            task_id=task_id,
            user_id=user_id,
            goal=task_goal,
            steps=steps,
            current_step_index=0,
            progress=0.0,
            status="pending",
            start_time=time.time(),
            estimated_completion_time=time.time() + sum(s.estimated_duration * 60 for s in steps),
            trust_score=trust_score,
            supervision_level=get_supervision_level(trust_score),
            approval_pending=[],
            completion_confirmation_pending=False
        )
        
        # 设置启动审批点
        if steps[0].requires_approval:
            create_approval_request(
                task_id=task_id,
                approval_type=ApprovalType.START_APPROVAL,
                data={"goal": task_goal, "steps": len(steps), "trust_score": trust_score},
                approval_requests=self.approval_requests,
                active_tasks=self.active_tasks
            )
        
        self.active_tasks[task_id] = supervised_task
        
        # 发布监督开始事件
        publish_event(EventType.TASK_SUPERVISION_STARTED, {
            "task_id": task_id,
            "goal": task_goal,
            "trust_score": trust_score,
            "supervision_level": supervised_task.supervision_level,
            "steps_count": len(steps)
        }, source="task_supervisor")
        
        return task_id
    
    def request_approval_for_step(self, task_id: str, step_index: int) -> Optional[str]:
        """为任务步骤请求审批"""
        if task_id not in self.active_tasks:
            return None
        
        task = self.active_tasks[task_id]
        if step_index >= len(task.steps):
            return None
        
        step = task.steps[step_index]
        if not step.requires_approval:
            return None
        
        approval_type = step.approval_type or ApprovalType.CRITICAL_STEP_APPROVAL
        
        approval_id = create_approval_request(
            task_id=task_id,
            approval_type=approval_type,
            data={
                "step_index": step_index,
                "step_name": step.step_name,
                "description": step.description,
                "progress": task.progress
            },
            approval_requests=self.approval_requests,
            active_tasks=self.active_tasks
        )
        
        return approval_id
    
    def process_approval(self, approval_id: str, decision: str, user_notes: str = "") -> bool:
        """处理用户审批决定"""
        if approval_id not in self.approval_requests:
            return False
        
        approval = self.approval_requests[approval_id]
        approval.status = ApprovalStatus(decision)
        approval.user_decision = decision
        approval.user_notes = user_notes
        approval.response_time = time.time()
        
        # 发布审批接收事件
        publish_event(EventType.APPROVAL_RECEIVED, {
            "approval_id": approval_id,
            "task_id": approval.task_id,
            "decision": decision,
            "user_notes": user_notes,
            "response_time": approval.response_time - approval.request_time
        }, source="task_supervisor")
        
        # 如果批准，继续任务
        if decision == "approved":
            task_id = approval.task_id
            if task_id in self.active_tasks:
                task = self.active_tasks[task_id]
                task.approval_pending = [ap for ap in task.approval_pending if ap != approval_id]
        
        return True
    
    def generate_progress_report(self, task_id: str) -> Optional[SupervisionReport]:
        """生成进度报告"""
        if task_id not in self.active_tasks:
            return None
        
        task = self.active_tasks[task_id]
        report_id = f"report_{uuid.uuid4().hex[:8]}"
        
        # 计算进度
        progress = calculate_progress(task, time.time())
        
        # 更新任务进度
        task.progress = progress
        
        # 创建报告
        report = SupervisionReport(
            report_id=report_id,
            task_id=task_id,
            generation_time=time.time(),
            report_type="progress",
            content={
                "goal": task.goal,
                "progress": progress,
                "current_step_index": task.current_step_index,
                "current_step_name": task.steps[task.current_step_index].step_name if task.steps else "N/A",
                "status": task.status,
                "approvals_pending": len(task.approval_pending),
                "estimated_time_remaining": max(0, task.estimated_completion_time - time.time())
            },
            recommendations=[],
            user_actions_required=len(task.approval_pending) > 0
        )
        
        # 发布报告生成事件
        publish_event(EventType.SUPERVISION_REPORT_GENERATED, {
            "report_id": report_id,
            "task_id": task_id,
            "report_type": "progress",
            "progress": progress,
            "user_actions_required": report.user_actions_required
        }, source="task_supervisor")
        
        return report
    
    def get_active_tasks(self) -> List[Dict]:
        """获取活跃任务列表"""
        return [format_task_for_display(task) for task in self.active_tasks.values()]
    
