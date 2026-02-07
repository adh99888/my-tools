#!/usr/bin/env python3
"""
监督界面 - 用户交互层
宪法依据：宪法第3条（认知对齐优先），阶段二用户监督机制
设计约束：≤200行代码，提供监督任务的基础用户界面
"""

from typing import Dict, List, Optional
import time
from .task_supervisor import TaskSupervisor
from .supervision_types import ApprovalStatus

class SupervisionInterface:
    """监督界面 - 用户交互层"""
    
    def __init__(self, supervisor: Optional[TaskSupervisor] = None):
        self.supervisor = supervisor or TaskSupervisor()
    
    def display_active_tasks(self) -> List[Dict]:
        """显示活跃任务列表"""
        tasks = self.supervisor.get_active_tasks()
        formatted_tasks = [{
            "任务ID": task["task_id"],
            "目标": task["goal"][:50] + ("..." if len(task["goal"]) > 50 else ""),
            "进度": f"{task['progress']:.1f}%",
            "状态": task["status"],
            "监督级别": task["supervision_level"],
            "待审批数": task["approvals_pending"]
        } for task in tasks]
        
        return formatted_tasks
    
    def show_task_details(self, task_id: str) -> Optional[Dict]:
        """显示任务详情"""
        if task_id not in self.supervisor.active_tasks:
            return None
        
        task = self.supervisor.active_tasks[task_id]
        
        # 获取待审批请求详情
        approval_details = []
        for approval_id in task.approval_pending:
            if approval_id in self.supervisor.approval_requests:
                approval = self.supervisor.approval_requests[approval_id]
                approval_details.append({
                    "审批ID": approval.approval_id,
                    "类型": approval.approval_type.value,
                    "请求时间": approval.request_time,
                    "数据": approval.data
                })
        
        # 获取步骤详情
        step_details = [{
            "步骤ID": step.step_id,
            "名称": step.step_name,
            "描述": step.description[:100] + ("..." if len(step.description) > 100 else ""),
            "需审批": "是" if step.requires_approval else "否",
            "预计时长": f"{step.estimated_duration}分钟",
            "依赖": ", ".join(step.dependencies) if step.dependencies else "无"
        } for step in task.steps]
        
        details = {
            "任务ID": task.task_id,
            "用户ID": task.user_id,
            "目标": task.goal,
            "总进度": f"{task.progress:.1f}%",
            "状态": task.status,
            "当前步骤": task.current_step_index + 1 if task.steps else 0,
            "总步骤数": len(task.steps),
            "开始时间": task.start_time,
            "预计完成时间": task.estimated_completion_time,
            "信任分": task.trust_score,
            "监督级别": task.supervision_level,
            "待审批数": len(task.approval_pending),
            "待审批详情": approval_details,
            "步骤详情": step_details,
            "确认待处理": task.completion_confirmation_pending
        }
        
        return details
    
    def show_approval_request(self, approval_id: str) -> Optional[Dict]:
        """显示审批请求"""
        if approval_id not in self.supervisor.approval_requests:
            return None
        
        approval = self.supervisor.approval_requests[approval_id]
        
        # 获取任务信息
        task_info = {}
        if approval.task_id in self.supervisor.active_tasks:
            task = self.supervisor.active_tasks[approval.task_id]
            task_info = {
                "任务目标": task.goal,
                "当前进度": f"{task.progress:.1f}%",
                "监督级别": task.supervision_level
            }
        
        approval_info = {
            "审批ID": approval.approval_id,
            "任务ID": approval.task_id,
            "审批类型": approval.approval_type.value,
            "状态": approval.status.value,
            "请求时间": approval.request_time,
            "等待时间": time.time() - approval.request_time if approval.response_time is None else None,
            "数据": approval.data,
            "任务信息": task_info,
            "用户决定": approval.user_decision,
            "用户备注": approval.user_notes,
            "响应时间": approval.response_time
        }
        
        return approval_info
    
    def submit_approval_decision(self, approval_id: str, decision: str, user_notes: str = "") -> bool:
        """提交审批决定"""
        valid_decisions = ["approved", "rejected", "skipped", "modified"]
        if decision not in valid_decisions:
            print(f"错误: 无效的审批决定 '{decision}'，有效选项: {valid_decisions}")
            return False
        
        success = self.supervisor.process_approval(approval_id, decision, user_notes)
        
        if success:
            print(f"审批决定 '{decision}' 已提交，审批ID: {approval_id}")
            if user_notes:
                print(f"用户备注: {user_notes}")
        else:
            print(f"错误: 无法提交审批决定，审批ID {approval_id} 不存在")
        
        return success
    
    def generate_progress_report(self, task_id: str) -> Optional[Dict]:
        """生成并显示进度报告"""
        report = self.supervisor.generate_progress_report(task_id)
        
        if not report:
            print(f"错误: 任务ID {task_id} 不存在或无法生成报告")
            return None
        
        formatted_report = {
            "报告ID": report.report_id,
            "任务ID": report.task_id,
            "生成时间": report.generation_time,
            "报告类型": report.report_type,
            "内容": report.content,
            "建议": report.recommendations,
            "需用户操作": "是" if report.user_actions_required else "否"
        }
        
        # 打印报告摘要
        report_content = report.content
        print(f"""=== 监督进度报告 ===
任务目标: {report_content.get('goal', 'N/A')}
当前进度: {report_content.get('progress', 0):.1f}%
状态: {report_content.get('status', 'N/A')}
当前步骤: {report_content.get('current_step_name', 'N/A')}
待审批数: {report_content.get('approvals_pending', 0)}
预计剩余时间: {report_content.get('estimated_time_remaining', 0):.1f}秒
需用户操作: {'是' if report.user_actions_required else '否'}
===================""")
        
        return formatted_report
    
    def list_pending_approvals(self) -> List[Dict]:
        """列出所有待审批请求"""
        pending_approvals = []
        
        for approval_id, approval in self.supervisor.approval_requests.items():
            if approval.status == ApprovalStatus.PENDING:
                # 获取任务信息
                task_goal = "未知任务"
                if approval.task_id in self.supervisor.active_tasks:
                    task_goal = self.supervisor.active_tasks[approval.task_id].goal[:50]
                
                pending_approvals.append({
                    "审批ID": approval_id,
                    "任务ID": approval.task_id,
                    "任务目标": task_goal,
                    "审批类型": approval.approval_type.value,
                    "请求时间": approval.request_time,
                    "等待时间秒数": time.time() - approval.request_time,
                    "数据摘要": {k: v for k, v in approval.data.items() if not isinstance(v, (list, dict))}
                })
        
        # 按等待时间排序（等待最久的排前面）
        pending_approvals.sort(key=lambda x: x["请求时间"])
        
        return pending_approvals

# 全局监督界面实例
_global_supervision_interface = None

def get_supervision_interface() -> SupervisionInterface:
    """获取全局监督界面实例"""
    global _global_supervision_interface
    if _global_supervision_interface is None:
        _global_supervision_interface = SupervisionInterface()
    return _global_supervision_interface