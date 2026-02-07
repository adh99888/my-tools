#!/usr/bin/env python3
"""
自然分工编排器 - 阶段四能力前移（宪法合规版）
宪法依据：宪法第1条（≤200行约束），宪法第3条（认知对齐优先）
功能：基于AI能力和用户能力评估，建议任务自然分工方案
设计约束：≤200行代码，集成到工作流系统
"""

from typing import Dict, Any, List, Optional
from .natural_division_types import TaskType, DivisionRole, DivisionPlan, DivisionAdjustment


class NaturalDivisionOrchestrator:
    """自然分工编排器 - 阶段四能力前移"""
    
    def __init__(self, ai_capabilities: Dict[str, float], user_profile: Optional[Dict[str, Any]] = None):
        """
        初始化编排器
        
        Args:
            ai_capabilities: AI能力评估，例如{"code_review": 0.8, "design": 0.7}
            user_profile: 用户能力画像（可选）
        """
        self.ai_capabilities = ai_capabilities
        self.user_profile = user_profile or {}
        self.division_history: List[DivisionPlan] = []
        
        # 默认能力映射（如果未提供）
        if not ai_capabilities:
            self.ai_capabilities = {
                "code_review": 0.8,
                "design": 0.6,
                "testing": 0.9,
                "analysis": 0.7,
                "documentation": 0.5,
                "debugging": 0.8
            }
    
    def suggest_division(self, task: Dict[str, Any], user_profile_override: Optional[Dict[str, Any]] = None) -> DivisionPlan:
        """建议自然分工方案"""
        user_profile = user_profile_override or self.user_profile
        
        # 提取任务信息
        task_id = task.get("task_id", task.get("id", "unknown"))
        task_type_str = task.get("type", "analysis")
        task_type = TaskType(task_type_str) if task_type_str in [t.value for t in TaskType] else TaskType.ANALYSIS
        
        # 评估AI和用户能力对比
        ai_score = self._evaluate_ai_capability(task_type)
        user_score = self._evaluate_user_capability(task_type, user_profile)
        
        # 决定分工角色
        roles = self._determine_roles(ai_score, user_score, task)
        
        # 生成解释
        rationale = self._generate_rationale(ai_score, user_score, task_type)
        
        # 计算置信度和效率提升估计
        confidence = min(1.0, (ai_score + user_score) / 2.0)
        efficiency_gain = self._estimate_efficiency_gain(ai_score, user_score)
        
        plan = DivisionPlan(
            task_id=task_id,
            task_type=task_type,
            roles=roles,
            rationale=rationale,
            confidence=confidence,
            estimated_efficiency_gain=efficiency_gain
        )
        
        self.division_history.append(plan)
        return plan
    
    def _evaluate_ai_capability(self, task_type: TaskType) -> float:
        """评估AI能力"""
        capability_key = task_type.value
        return self.ai_capabilities.get(capability_key, 0.5)
    
    def _evaluate_user_capability(self, task_type: TaskType, user_profile: Dict[str, Any]) -> float:
        """评估用户能力"""
        # 简单实现：如果用户有相关经验，则能力较高
        user_experience = user_profile.get("experience", {})
        task_key = task_type.value
        
        if task_key in user_experience:
            return min(1.0, user_experience[task_key] / 10.0)  # 假设经验值0-10
        
        # 默认基于用户整体技能水平
        default_skill = user_profile.get("default_skill_level", 0.5)
        return default_skill
    
    def _determine_roles(self, ai_score: float, user_score: float, task: Dict[str, Any]) -> Dict[str, DivisionRole]:
        """决定分工角色"""
        roles = {}
        
        # 简单规则：谁得分高谁主导
        score_diff = ai_score - user_score
        
        if score_diff > 0.3:  # AI明显更强
            roles["main_executor"] = DivisionRole.AI_PRIMARY
            roles["supporter"] = DivisionRole.USER_PRIMARY
        elif score_diff < -0.3:  # 用户明显更强
            roles["main_executor"] = DivisionRole.USER_PRIMARY
            roles["supporter"] = DivisionRole.AI_PRIMARY
        else:  # 能力相近，协作
            roles["main_executor"] = DivisionRole.COLLABORATIVE
            roles["supporter"] = DivisionRole.COLLABORATIVE
        
        # 考虑任务复杂度
        complexity = task.get("complexity", "medium")
        if complexity == "high":
            # 高复杂度任务建议并行处理
            roles["approach"] = DivisionRole.PARALLEL
        
        return roles
    
    def _generate_rationale(self, ai_score: float, user_score: float, task_type: TaskType) -> str:
        """生成分工解释"""
        if ai_score > user_score + 0.3:
            return f"AI在{task_type.value}任务上能力更强（AI:{ai_score:.1f} vs 用户:{user_score:.1f}），建议AI主导"
        elif user_score > ai_score + 0.3:
            return f"用户在{task_type.value}任务上能力更强（用户:{user_score:.1f} vs AI:{ai_score:.1f}），建议用户主导"
        else:
            return f"AI和用户在{task_type.value}任务上能力相近（AI:{ai_score:.1f}, 用户:{user_score:.1f}），建议协作完成"
    
    def _estimate_efficiency_gain(self, ai_score: float, user_score: float) -> float:
        """估计效率提升"""
        # 简单模型：能力匹配度越高，效率提升越大
        match_quality = 1.0 - abs(ai_score - user_score)  # 能力差异越小，匹配质量越高
        base_gain = 0.1  # 基础提升10%
        additional_gain = match_quality * 0.3  # 最多额外30%
        return base_gain + additional_gain
    
    def dynamic_adjustment(self, progress: Dict[str, Any], feedback: str) -> Optional[DivisionAdjustment]:
        """基于进展动态调整分工"""
        if not self.division_history:
            return None
        
        current_plan = self.division_history[-1]
        
        # 简单实现：根据进展和反馈决定是否调整
        progress_score = progress.get("completion_rate", 0.0)
        quality_score = progress.get("quality_score", 0.0)
        
        # 如果进展缓慢或质量低，考虑调整
        if progress_score < 0.3 or quality_score < 0.6:
            # 调整方案：切换主导角色
            new_roles = {}
            for role_key, role in current_plan.roles.items():
                if role == DivisionRole.AI_PRIMARY:
                    new_roles[role_key] = DivisionRole.USER_PRIMARY
                elif role == DivisionRole.USER_PRIMARY:
                    new_roles[role_key] = DivisionRole.AI_PRIMARY
                else:
                    new_roles[role_key] = role
            
            adjustment = DivisionAdjustment(
                original_plan_id=current_plan.task_id,
                adjustments=new_roles,
                reason=f"进展缓慢（完成率:{progress_score:.0%}，质量:{quality_score:.0%}），建议切换主导角色",
                expected_impact=0.2  # 预计提升20%
            )
            return adjustment
        
        return None
    
    def get_division_history(self) -> List[DivisionPlan]:
        """获取分工历史"""
        return self.division_history.copy()
    
    def clear_history(self) -> None:
        """清空分工历史"""
        self.division_history.clear()


# 全局编排器实例（单例模式）
_global_orchestrator = None

def get_natural_division_orchestrator() -> NaturalDivisionOrchestrator:
    """获取全局自然分工编排器实例"""
    global _global_orchestrator
    if _global_orchestrator is None:
        _global_orchestrator = NaturalDivisionOrchestrator({})
    return _global_orchestrator