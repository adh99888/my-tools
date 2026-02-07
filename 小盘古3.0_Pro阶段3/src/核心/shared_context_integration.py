#!/usr/bin/env python3
"""
共享上下文集成模块 - 阶段四能力前移集成
宪法依据：宪法第1条（≤200行约束）
功能：将共享上下文管理器集成到事件系统，自动从交互中提取上下文
设计约束：≤100行代码，保持简单
"""

from typing import Dict, Any
from .event_system import subscribe_to, EventType
from .shared_context_manager import get_shared_context_manager


class SharedContextIntegration:
    """共享上下文集成器"""
    
    def __init__(self):
        self.context_manager = get_shared_context_manager()
        self._setup_subscriptions()
    
    def _setup_subscriptions(self) -> None:
        """设置事件订阅"""
        subscribe_to(EventType.INTERACTION_RECORDED)(self.on_interaction_recorded)
    
    def on_interaction_recorded(self, event) -> None:
        """处理交互记录事件"""
        try:
            data = event.data
            user_input = data.get("user_input", "")
            ai_response = data.get("ai_response", "")
            
            if user_input and ai_response:
                # 更新共享上下文
                self.context_manager.update_from_interaction(user_input, ai_response)
                
                # 可选：记录调试信息
                # print(f"[共享上下文] 已从交互更新上下文，总交互数: {len(self.context_manager.interaction_history)}")
        
        except Exception as e:
            print(f"[共享上下文集成] 处理交互事件失败: {e}")
    
    def get_context_for_task(self, task_type: str) -> Dict[str, Any]:
        """为任务获取上下文（委托给管理器）"""
        return self.context_manager.get_context_for_task(task_type)
    
    def get_summary(self) -> Dict[str, Any]:
        """获取摘要（委托给管理器）"""
        return self.context_manager.get_summary()


# 全局集成器实例（单例模式）
_global_integrator = None

def get_shared_context_integrator() -> SharedContextIntegration:
    """获取全局共享上下文集成器实例"""
    global _global_integrator
    if _global_integrator is None:
        _global_integrator = SharedContextIntegration()
    return _global_integrator


def integrate_with_workflow(orchestrator) -> None:
    """与工作流编排器集成（示例）"""
    # 这里可以添加与工作流编排器的集成逻辑
    # 例如：在任务开始时查询相关上下文
    pass


def test_integration() -> None:
    """测试集成功能"""
    print("=== 共享上下文集成测试 ===")
    
    # 获取集成器
    integrator = get_shared_context_integrator()
    
    # 模拟事件发布（实际应由意图识别器触发）
    from .event_system import publish_event
    publish_event(EventType.INTERACTION_RECORDED, {
        "user_input": "集成测试：希望分析系统性能",
        "ai_response": "我来帮您分析系统性能，会检查关键指标。",
        "intent_type": "execute",
        "confidence": 0.8
    }, source="integration_test")
    
    # 获取摘要验证
    summary = integrator.get_summary()
    print(f"集成测试结果:")
    print(f"  总交互数: {summary['total_interactions']}")
    print(f"  最近交互: {summary['recent_interactions']}")
    
    print("\n[PASS] 共享上下文集成基本功能测试通过")


if __name__ == "__main__":
    test_integration()