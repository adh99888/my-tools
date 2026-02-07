#!/usr/bin/env python3
"""
信任自适应监督器 - 根据表现动态调整监督强度
宪法依据：宪法第3条（认知对齐优先），阶段二用户监督机制
设计约束：≤200行代码，基于任务表现动态调整监督强度
"""

from typing import Dict, Optional
import time
from .task_supervisor import TaskSupervisor
from .supervision_types import SupervisedTask, SupervisionConfig, get_default_supervision_config
from .trust_system import TrustSystem

class TrustAdaptiveSupervisor:
    """信任自适应监督器"""
    
    def __init__(self, supervisor: Optional[TaskSupervisor] = None):
        self.supervisor = supervisor or TaskSupervisor()
        self.trust_system = TrustSystem()
        self.performance_history: Dict[str, list] = {}  # task_id -> [performance_scores]
    
    def adjust_supervision_level(self, task_id: str, performance_score: float) -> None:
        """根据表现调整监督强度"""
        if task_id not in self.supervisor.active_tasks:
            return
        
        task = self.supervisor.active_tasks[task_id]
        
        # 记录表现历史
        if task_id not in self.performance_history:
            self.performance_history[task_id] = []
        self.performance_history[task_id].append(performance_score)
        
        # 计算平均表现
        avg_performance = sum(self.performance_history[task_id]) / len(self.performance_history[task_id])
        
        # 获取当前信任分
        current_trust = self.trust_system.get_current_score()
        
        # 根据表现调整监督级别
        new_supervision_level = self._calculate_new_supervision_level(
            current_trust, avg_performance, task.supervision_level
        )
        
        # 如果监督级别需要调整
        if new_supervision_level != task.supervision_level:
            old_level = task.supervision_level
            task.supervision_level = new_supervision_level
            
            # 发布监督级别变更事件
            from .event_system import EventType, publish_event
            publish_event(EventType.SUPERVISION_LEVEL_CHANGED, {
                "task_id": task_id,
                "old_level": old_level,
                "new_level": new_supervision_level,
                "reason": f"performance_adjustment: avg_performance={avg_performance:.2f}",
                "trust_score": current_trust,
                "performance_score": performance_score
            }, source="trust_adaptive_supervisor")
    
    def evaluate_task_performance(self, task_id: str) -> float:
        """评估任务表现（0-1分）"""
        if task_id not in self.supervisor.active_tasks:
            return 0.0
        
        task = self.supervisor.active_tasks[task_id]
        
        # 评估维度
        scores = []
        
        # 1. 进度效率（实际进度 vs 预计进度）
        elapsed = time.time() - task.start_time
        expected_progress = min(100.0, (elapsed / (task.estimated_completion_time - task.start_time) * 100) if task.estimated_completion_time > task.start_time else 0)
        actual_progress = task.progress
        progress_efficiency = min(1.0, actual_progress / max(1.0, expected_progress))
        scores.append(progress_efficiency * 0.3)
        
        # 2. 审批响应效率（如果适用）
        if task.approval_pending:
            # 计算平均审批等待时间
            total_wait = 0
            count = 0
            for approval_id in task.approval_pending:
                if approval_id in self.supervisor.approval_requests:
                    approval = self.supervisor.approval_requests[approval_id]
                    wait_time = time.time() - approval.request_time
                    total_wait += wait_time
                    count += 1
            
            if count > 0:
                avg_wait = total_wait / count
                # 等待时间越短，分数越高（理想等待时间<60秒）
                approval_efficiency = max(0.0, 1.0 - (avg_wait / 300.0))  # 5分钟为0分
                scores.append(approval_efficiency * 0.2)
            else:
                scores.append(0.2)  # 无待审批，满分
        else:
            scores.append(0.2)  # 无待审批，满分
        
        # 3. 风险处理（如果任务有风险记录）
        risk_score = 0.2  # 默认满分
        
        # 4. 用户满意度（如果有用户反馈）
        user_satisfaction = 0.3  # 默认中等满意度
        
        scores.append(user_satisfaction)
        
        # 计算总分
        total_score = sum(scores)
        
        return min(1.0, max(0.0, total_score))
    
    def get_recommended_supervision_config(self, task_id: str) -> SupervisionConfig:
        """获取推荐的监督配置"""
        if task_id not in self.supervisor.active_tasks:
            return get_default_supervision_config(50.0)  # 默认中等信任
        
        task = self.supervisor.active_tasks[task_id]
        current_trust = self.trust_system.get_current_score()
        
        # 获取任务表现
        performance = 0.7  # 默认表现
        if task_id in self.performance_history and self.performance_history[task_id]:
            performance = sum(self.performance_history[task_id]) / len(self.performance_history[task_id])
        
        # 根据信任分和表现调整配置
        adjusted_trust = current_trust * performance
        
        return get_default_supervision_config(adjusted_trust)
    
    def _calculate_new_supervision_level(self, trust_score: float, 
                                         performance_score: float, 
                                         current_level: str) -> str:
        """计算新的监督级别"""
        # 计算调整因子：表现好则降低监督，表现差则提高监督
        adjustment_factor = 1.0 - performance_score  # 表现差（低分）→ 提高监督
        
        # 基础监督级别基于信任分
        if trust_score < 30:
            base_level = "high"
        elif trust_score < 60:
            base_level = "medium"
        elif trust_score < 80:
            base_level = "low"
        else:
            base_level = "minimal"
        
        # 根据表现调整
        if adjustment_factor > 0.3:  # 表现较差
            if base_level == "minimal":
                return "low"
            elif base_level == "low":
                return "medium"
            elif base_level == "medium":
                return "high"
            else:
                return "high"
        elif adjustment_factor < 0.1:  # 表现很好
            if base_level == "high":
                return "medium"
            elif base_level == "medium":
                return "low"
            elif base_level == "low":
                return "minimal"
            else:
                return "minimal"
        else:
            return base_level
    
    def update_trust_based_on_performance(self, task_id: str) -> None:
        """根据任务表现更新信任分"""
        if task_id not in self.supervisor.active_tasks:
            return
        
        task = self.supervisor.active_tasks[task_id]
        
        # 评估任务表现
        performance = self.evaluate_task_performance(task_id)
        
        # 根据表现调整信任分

        if performance > 0.8:
            adjustment = min(5.0, (performance - 0.8) * 25)  # 最多+5分
            print(f"任务 {task_id} 表现优秀 ({performance:.2f})，建议信任分增加 {adjustment:.1f} 分")
        elif performance < 0.5:

            adjustment = max(-5.0, (performance - 0.5) * 10)  # 最多-5分
            print(f"任务 {task_id} 表现不佳 ({performance:.2f})，建议信任分减少 {abs(adjustment):.1f} 分")
        else:
            print(f"任务 {task_id} 表现正常 ({performance:.2f})，信任分保持不变")

# 全局信任自适应监督器实例
_global_trust_adaptive_supervisor = None

def get_trust_adaptive_supervisor() -> TrustAdaptiveSupervisor:
    """获取全局信任自适应监督器实例"""
    global _global_trust_adaptive_supervisor
    if _global_trust_adaptive_supervisor is None:
        _global_trust_adaptive_supervisor = TrustAdaptiveSupervisor()
    return _global_trust_adaptive_supervisor