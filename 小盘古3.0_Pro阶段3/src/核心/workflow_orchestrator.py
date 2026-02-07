#!/usr/bin/env python3
"""
工作流编排器 - 简单示例
宪法依据：宪法第2条（协议驱动），阶段三P1任务
功能：协调不同组件的事件，实现基础工作流
设计约束：≤100行代码
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from .event_system import EventType, subscribe_to, publish_event
from .supervision_interface import get_supervision_interface

class WorkflowOrchestrator:
    """工作流编排器"""
    
    def __init__(self):
        self.task_history: List[Dict[str, Any]] = []
        self.subscribe_all()
    
    def subscribe_all(self) -> None:
        """订阅所有相关事件"""
        subscribe_to(EventType.HEARTBEAT_MISSED)(self.on_heartbeat_missed)
        subscribe_to(EventType.MEMORY_UPDATED)(self.on_memory_updated)
        subscribe_to(EventType.TASK_STARTED)(self.on_task_started)
        subscribe_to(EventType.TASK_COMPLETED)(self.on_task_completed)
        subscribe_to(EventType.ERROR_OCCURRED)(self.on_error_occurred)
    
    def on_heartbeat_missed(self, event) -> None:
        """处理心跳丢失事件"""
        print(f"[工作流] 心跳丢失: {event.data.get('reason', '未知原因')}")
        # 这里可以触发安全模式或其他恢复操作
        # 例如：publish_event(EventType.SYSTEM_SHUTDOWN, {"reason": "心跳丢失"})
    
    def on_memory_updated(self, event) -> None:
        """处理记忆更新事件"""
        data = event.data
        content_preview = data.get('content', '')[:30]
        print(f"[工作流] 记忆更新: {content_preview}... (优先级: {data.get('priority', 'unknown')})")
        
        # 示例：当重要记忆更新时，可以触发备份或其他操作
        if data.get('priority') == 'high':
            print(f"[工作流] 高优先级记忆更新，建议备份")
    
    def on_task_started(self, event) -> None:
        """处理任务开始事件"""
        task_id = event.data.get('task_id', 'unknown')
        print(f"[工作流] 任务开始: {task_id}")
        
        self.task_history.append({
            "task_id": task_id,
            "start_time": datetime.now().isoformat(),
            "status": "started",
            "data": event.data
        })
    
    def on_task_completed(self, event) -> None:
        """处理任务完成事件"""
        task_id = event.data.get('task_id', 'unknown')
        print(f"[工作流] 任务完成: {task_id}")
        
        # 更新任务历史
        for task in self.task_history:
            if task.get("task_id") == task_id and task.get("status") == "started":
                task["status"] = "completed"
                task["end_time"] = datetime.now().isoformat()
                task["result"] = event.data.get("result", {})
                break
    
    def on_error_occurred(self, event) -> None:
        """处理错误事件"""
        error_msg = event.data.get('error', '未知错误')
        print(f"[工作流] 错误发生: {error_msg}")
        
        # 示例：错误计数和报警
        if "心跳" in error_msg:
            print(f"[工作流] 心跳相关错误，需要关注系统稳定性")
    
    def start_task(self, task_id: str, task_data: Optional[Dict[str, Any]] = None) -> None:
        """启动任务（发布任务开始事件）"""
        data = task_data or {}
        data["task_id"] = task_id
        publish_event(EventType.TASK_STARTED, data, "workflow_orchestrator")
        
        # 启动监督任务（如果提供目标）
        goal = data.get("goal") or data.get("description")
        if goal:
            user_id = data.get("user_id", "system")
            supervisor = get_supervision_interface().supervisor
            supervisor.start_supervised_task(goal, user_id, task_id=task_id)
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> None:
        """完成任务（发布任务完成事件）"""
        data = result or {}
        data["task_id"] = task_id
        publish_event(EventType.TASK_COMPLETED, data, "workflow_orchestrator")
    
    def get_task_history(self) -> List[Dict[str, Any]]:
        """获取任务历史"""
        return self.task_history.copy()
    
    def clear_history(self) -> None:
        """清空历史"""
        self.task_history.clear()

# 全局编排器实例（单例模式）
_orchestrator_instance = None

def get_orchestrator() -> WorkflowOrchestrator:
    """获取全局编排器实例"""
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator()
    return _orchestrator_instance

def demo_workflow() -> None:
    """演示工作流功能"""
    print("=== 工作流编排演示 ===")
    
    orchestrator = get_orchestrator()
    
    # 模拟任务执行
    orchestrator.start_task("test_task_001", {"description": "测试工作流集成"})
    
    # 模拟记忆更新
    publish_event(EventType.MEMORY_UPDATED, {
        "id": "test_memory",
        "content": "测试工作流协调的记忆更新",
        "priority": "high",
        "source": "demo"
    })
    
    # 模拟心跳丢失
    publish_event(EventType.HEARTBEAT_MISSED, {
        "reason": "演示用途",
        "source": "demo"
    })
    
    # 完成任务
    orchestrator.complete_task("test_task_001", {"result": "success", "metrics": {"time_sec": 2.5}})
    
    # 显示任务历史
    print(f"\n任务历史:")
    for task in orchestrator.get_task_history():
        print(f"  - {task['task_id']}: {task['status']}")
    
    print("=== 演示完成 ===")

if __name__ == "__main__":
    demo_workflow()