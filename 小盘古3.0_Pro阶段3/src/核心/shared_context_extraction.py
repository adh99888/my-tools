#!/usr/bin/env python3
"""
共享上下文提取模块 - 阶段四能力前移
宪法依据：宪法第1条（≤200行约束）
功能：从用户-AI交互中提取隐含上下文信息
"""

import re
from typing import Dict, Any, List
from .shared_context_types import InteractionRecord


def extract_implicit_goals(user_input: str, ai_response: str) -> List[str]:
    """提取隐含目标"""
    goals = []
    
    # 关键词检测
    goal_keywords = ["希望", "想要", "需要", "目标", "目的", "为了", "以便"]
    for keyword in goal_keywords:
        if keyword in user_input:
            # 提取目标短语
            pattern = rf'{keyword}[：: ]?(.+?)(?:[。！？?!]|$)'
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            goals.extend(matches)
    
    # 从AI响应中提取确认的目标
    if "目标" in ai_response or "目的" in ai_response:
        # 简单提取，后续可增强
        pass
    
    return goals[:5]  # 限制数量


def extract_implicit_constraints(user_input: str, ai_response: str) -> List[str]:
    """提取隐含约束"""
    constraints = []
    
    # 约束关键词
    constraint_keywords = ["不能", "不要", "避免", "限制", "必须", "要求", "时间", "尽快"]
    for keyword in constraint_keywords:
        if keyword in user_input:
            constraints.append(f"用户提到'{keyword}'：可能表示约束")
    
    # 从AI响应中提取约束确认
    if "约束" in ai_response or "限制" in ai_response:
        # 简单记录
        constraints.append("AI讨论了约束条件")
    
    return constraints[:5]


def extract_user_preferences(user_input: str, ai_response: str) -> List[str]:
    """提取用户偏好"""
    preferences = []
    
    # 偏好关键词
    preference_keywords = ["喜欢", "偏好", "习惯", "通常", "常用", "最好", "优先"]
    for keyword in preference_keywords:
        if keyword in user_input:
            preferences.append(f"用户偏好关键词：'{keyword}'")
    
    # AI响应中提及的用户偏好
    if "建议" in ai_response and "你" in user_input:
        preferences.append("用户寻求建议，可能开放于新方法")
    
    return preferences[:5]


def update_mental_models(interaction_history: List[InteractionRecord], 
                        shared_context: Dict[str, Any]) -> None:
    """更新心智模型"""
    if len(interaction_history) >= 2:
        last_two = interaction_history[-2:]
        pattern = {
            "user_pattern": "连续交互" if len(last_two) == 2 else "单次交互",
            "time_gap": "未知"
        }
        shared_context["mental_models"].append(pattern)
        
        # 限制心智模型数量
        if len(shared_context["mental_models"]) > 10:
            shared_context["mental_models"] = shared_context["mental_models"][-10:]