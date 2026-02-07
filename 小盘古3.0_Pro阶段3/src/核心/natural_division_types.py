#!/usr/bin/env python3
"""
自然分工类型定义 - 阶段四能力前移
宪法依据：宪法第1条（≤200行约束）
功能：定义自然分工编排器使用的枚举和数据类
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List


class TaskType(Enum):
    """任务类型枚举"""
    CODE_REVIEW = "code_review"
    DESIGN = "design"
    TESTING = "testing"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"


class DivisionRole(Enum):
    """分工角色"""
    AI_PRIMARY = "ai_primary"      # AI主导
    USER_PRIMARY = "user_primary"  # 用户主导
    COLLABORATIVE = "collaborative" # 协作完成
    PARALLEL = "parallel"          # 并行处理


@dataclass
class DivisionPlan:
    """分工方案"""
    task_id: str
    task_type: TaskType
    roles: Dict[str, DivisionRole]  # 组件->角色映射
    rationale: str
    confidence: float
    estimated_efficiency_gain: float  # 预计效率提升（百分比）


@dataclass
class DivisionAdjustment:
    """分工调整"""
    original_plan_id: str
    adjustments: Dict[str, DivisionRole]
    reason: str
    expected_impact: float