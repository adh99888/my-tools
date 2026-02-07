#!/usr/bin/env python3
"""
共识决策类型定义 - 阶段四能力前移
宪法依据：宪法第1条（≤200行约束）
功能：定义共识决策促进器使用的枚举和数据类
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, List, Optional
from datetime import datetime


class DecisionType(Enum):
    """决策类型枚举"""
    STRATEGIC = "strategic"       # 战略决策
    TACTICAL = "tactical"         # 战术决策
    OPERATIONAL = "operational"   # 操作决策
    TECHNICAL = "technical"       # 技术决策


class DecisionStatus(Enum):
    """决策状态"""
    PROPOSED = "proposed"         # 已提出
    FACILITATING = "facilitating" # 协调中
    CONSENSUS_REACHED = "consensus_reached" # 达成共识
    REJECTED = "rejected"         # 已拒绝
    POSTPONED = "postponed"       # 已推迟


@dataclass
class DecisionOption:
    """决策选项"""
    id: str
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    estimated_impact: float = 0.0  # 预估影响


@dataclass
class DecisionCriteria:
    """决策标准"""
    name: str
    weight: float  # 权重
    direction: str  # "max"或"min"


@dataclass
class DecisionRecord:
    """决策记录"""
    id: str
    decision_type: DecisionType
    status: DecisionStatus
    options: List[DecisionOption]
    criteria: List[DecisionCriteria]
    user_preferences: Dict[str, float]
    ai_recommendation: Optional[Dict[str, Any]] = None
    final_decision: Optional[str] = None  # 选择的选项ID
    consensus_score: float = 0.0  # 共识程度
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()


@dataclass
class ConsensusResult:
    """共识结果"""
    decision_id: str
    consensus_reached: bool
    selected_option: Optional[DecisionOption] = None
    consensus_score: float = 0.0
    rationale: str = ""
    iterations: int = 1  # 达成共识的迭代次数
    ai_confidence: float = 0.0