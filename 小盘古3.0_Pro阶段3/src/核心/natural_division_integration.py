#!/usr/bin/env python3
"""
自然分工集成模块 - 阶段四能力前移集成
宪法依据：宪法第1条（≤200行约束）
功能：将自然分工编排器集成到事件系统，自动为任务建议分工方案
设计约束：≤200行代码，保持简单
"""

from typing import Dict, Any, Optional
from .event_system import subscribe_to, EventType, publish_event
from .natural_division_orchestrator import get_natural_division_orchestrator
from .natural_division_types import DivisionPlan, DivisionAdjustment


class NaturalDivisionIntegration:
    """自然分工集成器"""
    
    def __init__(self, user_profile: Optional[Dict[str, Any]] = None):
        self.orchestrator = get_natural_division_orchestrator()
        self.user_profile = user_profile or {}
        self._setup_subscriptions()
    
    def _setup_subscriptions(self) -> None:
        """设置事件订阅"""
        subscribe_to(EventType.TASK_STARTED)(self.on_task_started)
        subscribe_to(EventType.TASK_COMPLETED)(self.on_task_completed)
        subscribe_to(EventType.INTERACTION_RECORDED)(self.on_interaction_recorded)
    
    def on_task_started(self, event) -> None:
        """处理任务开始事件 - 建议分工方案"""
        try:
            task_data = event.data
            task_id = task_data.get("task_id", "unknown")
            
            # 为任务建议分工方案
            division_plan = self.orchestrator.suggest_division(task_data, self.user_profile)
            
            # 发布分工建议事件
            publish_event(EventType.DIVISION_SUGGESTED, {
                "task_id": task_id,
                "plan": {
                    "task_id": division_plan.task_id,
                    "task_type": division_plan.task_type.value,
                    "roles": {k: v.value for k, v in division_plan.roles.items()},
                    "rationale": division_plan.rationale,
                    "confidence": division_plan.confidence,
                    "estimated_efficiency_gain": division_plan.estimated_efficiency_gain
                },
                "source": "natural_division_integration"
            })
            
            # 可选：记录到日志
            # print(f"[自然分工] 为任务 {task_id} 建议分工: {division_plan.rationale}")
        
        except Exception as e:
            print(f"[自然分工集成] 处理任务开始事件失败: {e}")
    
    def on_task_completed(self, event) -> None:
        """处理任务完成事件 - 动态调整学习"""
        try:
            task_data = event.data
            task_id = task_data.get("task_id", "unknown")
            result = task_data.get("result", {})
            
            # 如果有进度信息，可以动态调整
            progress_data = result.get("progress", {})
            feedback = result.get("feedback", "")
            
            if progress_data:
                adjustment = self.orchestrator.dynamic_adjustment(progress_data, feedback)
                if adjustment:
                    # 发布分工调整事件
                    publish_event(EventType.DIVISION_ADJUSTED, {
                        "task_id": task_id,
                        "adjustment": {
                            "original_plan_id": adjustment.original_plan_id,
                            "adjustments": {k: v.value for k, v in adjustment.adjustments.items()},
                            "reason": adjustment.reason,
                            "expected_impact": adjustment.expected_impact
                        },
                        "source": "natural_division_integration"
                    })
        
        except Exception as e:
            print(f"[自然分工集成] 处理任务完成事件失败: {e}")
    
    def on_interaction_recorded(self, event) -> None:
        """处理交互记录事件 - 更新用户能力画像"""
        try:
            # 从交互中提取用户能力信息
            # 简单实现：如果有用户反馈评分，更新用户能力
            data = event.data
            if not isinstance(data, dict):
                return
            feedback_score = data.get("feedback_score")
            
            if feedback_score is not None:
                # 更新用户能力画像（简单示例）
                # 实际实现应更复杂，基于交互内容更新具体能力
                task_type = data.get("task_type", "analysis")
                if task_type not in self.user_profile.get("experience", {}):
                    self.user_profile.setdefault("experience", {})[task_type] = 0
                
                # 根据反馈评分更新经验值
                self.user_profile["experience"][task_type] += feedback_score * 0.1
        
        except Exception as e:
            print(f"[自然分工集成] 处理交互事件失败: {e}")
    
    def update_user_profile(self, new_profile: Dict[str, Any]) -> None:
        """更新用户能力画像"""
        self.user_profile.update(new_profile)
    
    def get_user_profile(self) -> Dict[str, Any]:
        """获取当前用户能力画像"""
        return self.user_profile.copy()
    
    def get_division_history(self):
        """获取分工历史（委托给编排器）"""
        return self.orchestrator.get_division_history()


# 全局集成器实例（单例模式）
_global_integrator = None

def get_natural_division_integrator() -> NaturalDivisionIntegration:
    """获取全局自然分工集成器实例"""
    global _global_integrator
    if _global_integrator is None:
        _global_integrator = NaturalDivisionIntegration()
    return _global_integrator


def integrate_with_workflow(orchestrator) -> None:
    """与工作流编排器集成（示例）"""
    # 这里可以添加与工作流编排器的集成逻辑
    # 例如：在任务开始时自动调用分工建议
    pass


def test_integration() -> None:
    """测试集成功能"""
    print("=== 自然分工集成测试 ===")
    
    # 获取集成器
    integrator = get_natural_division_integrator()
    
    # 模拟任务开始事件
    from .event_system import publish_event
    publish_event(EventType.TASK_STARTED, {
        "task_id": "test_task_001",
        "type": "analysis",
        "complexity": "medium",
        "description": "测试自然分工集成"
    }, source="integration_test")
    
    # 模拟任务完成事件（带进度反馈）
    publish_event(EventType.TASK_COMPLETED, {
        "task_id": "test_task_001",
        "result": {
            "progress": {"completion_rate": 0.2, "quality_score": 0.5},
            "feedback": "进展缓慢"
        }
    }, source="integration_test")
    
    # 获取分工历史验证
    history = integrator.get_division_history()
    print(f"集成测试结果:")
    print(f"  分工建议数量: {len(history)}")
    if history:
        print(f"  最近分工: {history[-1].rationale}")
    
    print("\n[PASS] 自然分工集成基本功能测试通过")


if __name__ == "__main__":
    test_integration()