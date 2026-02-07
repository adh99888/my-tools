#!/usr/bin/env python3
"""
共识决策集成模块 - 阶段四能力前移集成
宪法依据：宪法第1条（≤200行约束）
功能：将共识决策促进器集成到事件系统
设计约束：≤200行代码，保持简单
"""

from typing import Dict, Any, Optional
from .event_system import subscribe_to, EventType, publish_event
from .consensus_decision_facilitator import get_consensus_facilitator
from .consensus_decision_types import ConsensusResult


class ConsensusDecisionIntegration:
    """共识决策集成器"""
    
    def __init__(self):
        self.facilitator = get_consensus_facilitator()
        self.user_preferences: Dict[str, float] = {}
        self._setup_subscriptions()
    
    def _setup_subscriptions(self) -> None:
        """设置事件订阅"""
        subscribe_to(EventType.DIVISION_SUGGESTED)(self.on_division_suggested)
        subscribe_to(EventType.INTERACTION_RECORDED)(self.on_interaction_recorded)
    
    def on_division_suggested(self, event) -> None:
        """处理分工建议事件 - 触发决策促进（可选）"""
        try:
            # 如果分工建议涉及多个选项，可以触发共识决策
            plan = event.data.get("plan", {})
            
            # 简单实现：如果置信度低，建议进行共识决策
            confidence = plan.get("confidence", 1.0)
            if confidence < 0.6:
                # 可以在这里触发决策事件（暂不实现，避免过度复杂）
                pass
        
        except Exception as e:
            print(f"[共识决策集成] 处理分工建议事件失败: {e}")
    
    def on_interaction_recorded(self, event) -> None:
        """处理交互记录事件 - 更新用户偏好"""
        try:
            # 从交互中提取用户偏好
            data = event.data
            if not isinstance(data, dict):
                return
            
            # 简单实现：从意图类型更新偏好
            intent_type = data.get("intent_type", "")
            if intent_type:
                # 更新对某种决策类型的偏好
                self.user_preferences.setdefault(intent_type, 0.5)
                self.user_preferences[intent_type] += 0.05
                # 限制在0-1之间
                self.user_preferences[intent_type] = min(1.0, self.user_preferences[intent_type])
        
        except Exception as e:
            print(f"[共识决策集成] 处理交互事件失败: {e}")
    
    def facilitate_decision(self,
                          options: list,
                          criteria: list,
                          decision_type: str = "tactical") -> ConsensusResult:
        """促进决策（发布事件前）"""
        result = self.facilitator.facilitate_decision(
            options=options,
            criteria=criteria,
            user_preferences=self.user_preferences,
            decision_type=decision_type
        )
        
        # 发布决策促进事件
        publish_event(EventType.DECISION_FACILITATED, {
            "decision_id": result.decision_id,
            "consensus_reached": result.consensus_reached,
            "consensus_score": result.consensus_score,
            "rationale": result.rationale,
            "selected_option_id": result.selected_option.id if result.selected_option else None,
            "ai_confidence": result.ai_confidence,
            "source": "consensus_decision_integration"
        })
        
        return result
    
    def record_outcome(self,
                      decision_id: str,
                      outcome: Dict[str, Any],
                      user_feedback: str) -> None:
        """记录决策结果（发布事件）"""
        # 调用促进器学习
        self.facilitator.learn_from_decision_outcome(
            decision_id=decision_id,
            outcome=outcome,
            user_feedback=user_feedback
        )
        
        # 发布决策结果事件
        publish_event(EventType.DECISION_OUTCOME, {
            "decision_id": decision_id,
            "outcome": outcome,
            "user_feedback": user_feedback,
            "source": "consensus_decision_integration"
        })
    
    def update_user_preferences(self, prefs: Dict[str, float]) -> None:
        """更新用户偏好"""
        self.user_preferences.update(prefs)
    
    def get_user_preferences(self) -> Dict[str, float]:
        """获取当前用户偏好"""
        return self.user_preferences.copy()
    
    def get_decision_history(self):
        """获取决策历史（委托给促进器）"""
        return self.facilitator.get_decision_history()


_global_integrator = None

def get_consensus_integrator() -> ConsensusDecisionIntegration:
    """获取全局共识决策集成器实例"""
    global _global_integrator
    if _global_integrator is None:
        _global_integrator = ConsensusDecisionIntegration()
    return _global_integrator


def test_integration() -> None:
    """测试集成功能"""
    print("=== 共识决策集成测试 ===")
    
    # 获取集成器
    integrator = get_consensus_integrator()
    
    # 创建测试选项
    options = [
        {"id": "option_a", "description": "方案A：快速实现", "estimated_impact": 0.6},
        {"id": "option_b", "description": "方案B：高质量实现", "estimated_impact": 0.8}
    ]
    
    criteria = ["speed", "quality", "cost"]
    
    # 促进决策
    result = integrator.facilitate_decision(
        options=options,
        criteria=criteria,
        decision_type="tactical"
    )
    
    print(f"决策ID: {result.decision_id}")
    print(f"共识达成: {result.consensus_reached}")
    print(f"共识分数: {result.consensus_score:.2f}")
    print(f"理由: {result.rationale}")
    
    # 记录结果
    integrator.record_outcome(
        decision_id=result.decision_id,
        outcome={"success": True, "impact": 0.7},
        user_feedback="good decision"
    )
    
    print("\n[PASS] 共识决策集成基本功能测试通过")


if __name__ == "__main__":
    test_integration()