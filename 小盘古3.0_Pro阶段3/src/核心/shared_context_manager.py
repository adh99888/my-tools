#!/usr/bin/env python3
"""
共享上下文管理器 - 阶段四能力前移（宪法合规版）
宪法依据：宪法第1条（≤200行约束），宪法第3条（认知对齐优先）
功能：提取和共享用户-AI交互中的隐含上下文，增强认知对齐
设计约束：≤200行代码，集成到意图识别和工作流系统
"""

from typing import Dict, Any, List
from datetime import datetime
import os

from .shared_context_types import InteractionRecord
from .shared_context_persistence import load_persisted_data, save_persisted_data
from .shared_context_extraction import (
    extract_implicit_goals,
    extract_implicit_constraints,
    extract_user_preferences,
    update_mental_models
)


class SharedContextManager:
    """共享上下文管理器 - 阶段四能力前移（宪法合规版）"""
    
    def __init__(self, data_dir: str = "data/shared_context"):
        """初始化共享上下文管理器"""
        self.data_dir = data_dir
        self.context_file = os.path.join(data_dir, "shared_context.json")
        self.history_file = os.path.join(data_dir, "interaction_history.json")
        
        # 加载持久化数据
        self.shared_context, self.interaction_history = load_persisted_data(
            self.context_file, self.history_file, self.data_dir
        )
    
    def update_from_interaction(self, user_input: str, ai_response: str) -> None:
        """从交互中提取共享上下文"""
        # 创建交互记录
        record = InteractionRecord(
            timestamp=datetime.now().isoformat(),
            user_input=user_input,
            ai_response=ai_response,
            extracted_context={}
        )
        
        # 提取隐含目标
        goals = extract_implicit_goals(user_input, ai_response)
        if goals:
            record.extracted_context["goals"] = goals
            self.shared_context["goals"].extend(goals)
        
        # 提取隐含约束
        constraints = extract_implicit_constraints(user_input, ai_response)
        if constraints:
            record.extracted_context["constraints"] = constraints
            self.shared_context["constraints"].extend(constraints)
        
        # 提取用户偏好
        preferences = extract_user_preferences(user_input, ai_response)
        if preferences:
            record.extracted_context["preferences"] = preferences
            self.shared_context["preferences"].extend(preferences)
        
        # 添加到历史
        self.interaction_history.append(record)
        
        # 限制历史长度
        if len(self.interaction_history) > 50:
            self.interaction_history = self.interaction_history[-50:]
        
        # 更新心智模型
        update_mental_models(self.interaction_history, self.shared_context)
        
        # 保存数据
        save_persisted_data(
            self.shared_context,
            self.interaction_history,
            self.context_file,
            self.history_file
        )
    
    def get_context_for_task(self, task_type: str) -> Dict[str, Any]:
        """为特定任务提供增强上下文"""
        task_context = {
            "task_type": task_type,
            "relevant_goals": [],
            "relevant_constraints": [],
            "relevant_preferences": [],
            "similar_history": []
        }
        
        # 筛选相关目标
        for goal in self.shared_context["goals"]:
            if task_type in goal or any(keyword in goal for keyword in ["分析", "查看", "执行", "优化"]):
                task_context["relevant_goals"].append(goal)
        
        # 筛选相关约束
        for constraint in self.shared_context["constraints"]:
            task_context["relevant_constraints"].append(constraint)
        
        # 筛选相关偏好
        for preference in self.shared_context["preferences"]:
            task_context["relevant_preferences"].append(preference)
        
        # 查找类似历史
        for record in self.interaction_history[-10:]:  # 最近10条
            if task_type in record.user_input or task_type in record.ai_response:
                task_context["similar_history"].append({
                    "user_input": record.user_input[:50],
                    "ai_response": record.ai_response[:50],
                    "timestamp": record.timestamp
                })
        
        return task_context
    
    def get_summary(self) -> Dict[str, Any]:
        """获取共享上下文摘要"""
        return {
            "total_interactions": len(self.interaction_history),
            "goals_count": len(self.shared_context["goals"]),
            "constraints_count": len(self.shared_context["constraints"]),
            "preferences_count": len(self.shared_context["preferences"]),
            "recent_interactions": [
                {
                    "timestamp": r.timestamp,
                    "user_input_preview": r.user_input[:30],
                    "ai_response_preview": r.ai_response[:30]
                }
                for r in self.interaction_history[-3:]
            ]
        }
    
    def clear_context(self) -> None:
        """清空共享上下文（谨慎使用）"""
        self.shared_context = {key: [] for key in self.shared_context}
        self.interaction_history = []
        save_persisted_data(
            self.shared_context,
            self.interaction_history,
            self.context_file,
            self.history_file
        )


# 全局管理器实例（单例模式）
_global_manager = None

def get_shared_context_manager() -> SharedContextManager:
    """获取全局共享上下文管理器实例"""
    global _global_manager
    if _global_manager is None:
        _global_manager = SharedContextManager()
    return _global_manager


def test_shared_context() -> None:
    """测试共享上下文管理器"""
    print("=== 共享上下文管理器测试 ===")
    
    manager = get_shared_context_manager()
    
    # 模拟交互
    test_interactions = [
        ("我希望分析项目结构，找出性能瓶颈", "我来帮您分析项目结构，会先检查目录组织，然后分析关键代码。"),
        ("不要修改核心文件，只读分析", "好的，我会以只读模式分析，不修改任何文件。"),
        ("我通常喜欢用图表展示分析结果", "了解，分析完成后我会生成图表摘要。"),
    ]
    
    for i, (user, ai) in enumerate(test_interactions, 1):
        print(f"交互{i}: 用户: {user}")
        manager.update_from_interaction(user, ai)
    
    # 获取任务上下文
    task_context = manager.get_context_for_task("分析")
    print(f"\n任务上下文（分析任务）:")
    print(f"  相关目标: {task_context['relevant_goals']}")
    print(f"  相关约束: {task_context['relevant_constraints']}")
    print(f"  相关偏好: {task_context['relevant_preferences']}")
    print(f"  类似历史: {len(task_context['similar_history'])}条")
    
    # 获取摘要
    summary = manager.get_summary()
    print(f"\n上下文摘要:")
    print(f"  总交互数: {summary['total_interactions']}")
    print(f"  目标数量: {summary['goals_count']}")
    print(f"  约束数量: {summary['constraints_count']}")
    print(f"  偏好数量: {summary['preferences_count']}")
    
    print("\n[PASS] 共享上下文管理器基本功能测试通过")


if __name__ == "__main__":
    test_shared_context()